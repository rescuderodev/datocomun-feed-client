import logging

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


class FeedClient:
    """Cliente minimo de Recuento API. De momento solo GET y devuelve el JSON."""

    def __init__(self, base_url, timeout=DEFAULT_TIMEOUT, transport=None):
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Accept": "application/json"},
            transport=transport,
        )

    def _error(self, resp):
        try:
            cuerpo = resp.json()
            error, detalle = cuerpo.get("error", ""), cuerpo.get("detalle", "")
        except ValueError:
            error, detalle = "", resp.text[:200]
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
