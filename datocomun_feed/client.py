import logging
import os

import httpx

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0


class FeedError(Exception):
    """Error devuelto por la API ({"error": ..., "detalle": ...})."""

    def __init__(self, status_code, error, detalle=""):
        super().__init__(f"{status_code} {error}: {detalle}")
        self.status_code = status_code
        self.error = error
        self.detalle = detalle


class AuthError(FeedError):
    """401: token ausente, caducado o de otro entorno."""


class FeedClient:
    """Cliente de Recuento API. Autentica con el token del entorno (PRE o PRO)."""

    def __init__(self, base_url, token, timeout=DEFAULT_TIMEOUT, transport=None):
        if not token:
            raise ValueError("Falta el token de la API")
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
            transport=transport,
        )

    @classmethod
    def from_env(cls, **kwargs):
        """Crea el cliente con FEED_API_URL y FEED_API_TOKEN."""
        url = os.environ.get("FEED_API_URL")
        token = os.environ.get("FEED_API_TOKEN")
        if not url or not token:
            raise ValueError("Faltan FEED_API_URL y/o FEED_API_TOKEN en el entorno")
        return cls(url, token, **kwargs)

    def _error(self, resp):
        try:
            cuerpo = resp.json()
            error, detalle = cuerpo.get("error", ""), cuerpo.get("detalle", "")
        except ValueError:
            error, detalle = "", resp.text[:200]
        if resp.status_code == 401:
            return AuthError(401, error or "no_autorizado", detalle)
        return FeedError(resp.status_code, error, detalle)

    def _get(self, path, params=None):
        log.debug("GET %s %s", path, params or "")
        resp = self._http.get(path, params=params)
        if resp.status_code >= 400:
            raise self._error(resp)
        return resp

    def estado(self):
        """Version, entorno y hora del servidor (no necesita token)."""
        return self._get("/estado").json()

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
