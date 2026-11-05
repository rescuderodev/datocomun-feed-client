import logging
import os
import random
import time

import httpx

from .models import Avance, Circunscripcion

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0
MAX_REINTENTOS = 4
BACKOFF_BASE = 0.5
BACKOFF_MAX = 8.0
# 503 = la fuente oficial aun no tiene datos nuevos, merece la pena reintentar
REINTENTABLES = {429, 500, 502, 503, 504}


class FeedError(Exception):
    """Error devuelto por la API ({"error": ..., "detalle": ...})."""

    def __init__(self, status_code, error, detalle=""):
        super().__init__(f"{status_code} {error}: {detalle}")
        self.status_code = status_code
        self.error = error
        self.detalle = detalle


class AuthError(FeedError):
    """401: token ausente, caducado o de otro entorno."""


class NoEncontrado(FeedError):
    """404: convocatoria o circunscripcion inexistente."""


class FeedClient:
    """Cliente de Recuento API. Autentica con el token del entorno (PRE o PRO)."""

    def __init__(
        self,
        base_url,
        token,
        timeout=DEFAULT_TIMEOUT,
        max_reintentos=MAX_REINTENTOS,
        backoff_base=BACKOFF_BASE,
        transport=None,
    ):
        if not token:
            raise ValueError("Falta el token de la API")
        self.base_url = base_url.rstrip("/")
        self.max_reintentos = max_reintentos
        self.backoff_base = backoff_base
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
        if resp.status_code == 404:
            return NoEncontrado(404, error or "no_encontrado", detalle)
        return FeedError(resp.status_code, error, detalle)

    def _espera(self, intento, resp=None):
        """Segundos antes del siguiente intento: Retry-After si viene, si no backoff con jitter."""
        if resp is not None and "Retry-After" in resp.headers:
            try:
                return min(float(resp.headers["Retry-After"]), BACKOFF_MAX)
            except ValueError:
                pass  # a veces viene como fecha HTTP, pasamos
        espera = min(self.backoff_base * (2 ** intento), BACKOFF_MAX)
        return espera * random.uniform(0.5, 1.0)

    def _get(self, path, params=None):
        # en noche electoral hay picos fuertes, reintentamos 429/5xx y
        # errores de red antes de dar el dato por perdido
        for intento in range(self.max_reintentos + 1):
            log.debug("GET %s %s (intento %d)", path, params or "", intento + 1)
            try:
                resp = self._http.get(path, params=params)
            except httpx.TransportError as exc:
                if intento == self.max_reintentos:
                    raise
                espera = self._espera(intento)
                log.warning("Error de red en %s (%s), reintento en %.1fs", path, exc, espera)
                time.sleep(espera)
                continue

            if resp.status_code in REINTENTABLES and intento < self.max_reintentos:
                espera = self._espera(intento, resp)
                log.warning("%s devolvio %d, reintento en %.1fs", path, resp.status_code, espera)
                time.sleep(espera)
                continue
            break

        if resp.status_code >= 400:
            raise self._error(resp)
        return resp

    def estado(self):
        """Version, entorno y hora del servidor (no necesita token)."""
        return self._get("/estado").json()

    def avance_escrutinio(self, camara="congreso"):
        """Porcentaje escrutado y reparto provisional de escaños ("congreso" o "senado")."""
        return Avance.from_dict(self._get("/escrutinio/avance", {"camara": camara}).json())

    def participacion(self, hora="18:00"):
        """Avance de participacion: "14:00" o "18:00"."""
        # TODO: cachear? cambia dos veces en toda la noche
        return self._get("/participacion", {"hora": hora}).json()

    def resultados_congreso(self, circunscripcion):
        """Resultados al Congreso. circunscripcion: codigo INE de dos digitos ("28")."""
        return Circunscripcion.from_dict(self._get(f"/resultados/congreso/{circunscripcion}").json())

    def resultados_senado(self, circunscripcion):
        # de momento sin modelo, nadie lo usa para grafismo
        return self._get(f"/resultados/senado/{circunscripcion}").json()

    def municipio(self, ine):
        """Resultados de un municipio (codigo INE de cinco digitos)."""
        return self._get(f"/municipios/{ine}").json()

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
