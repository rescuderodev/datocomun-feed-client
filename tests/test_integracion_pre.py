"""Tests de integracion contra PRE.

Necesitan FEED_API_URL y FEED_API_TOKEN (tambien se leen de un .env en la
raiz del repo). Sin token se saltan.
"""

import os

import pytest
from dotenv import load_dotenv

from datocomun_feed import AuthError, FeedClient, NoEncontrado

load_dotenv()

pytestmark = pytest.mark.skipif(
    not os.environ.get("FEED_API_TOKEN"),
    reason="sin FEED_API_TOKEN no se lanzan los tests contra PRE",
)


@pytest.fixture(scope="module")
def feed():
    with FeedClient.from_env(max_reintentos=2) as cliente:
        yield cliente


def test_estado(feed):
    estado = feed.estado()
    # que no se nos escape lanzar esto contra produccion
    assert estado["entorno"] == "PRE"
    assert estado["version"].startswith("3.")


def test_avance(feed):
    congreso = feed.avance_escrutinio()
    assert congreso.escanos_total == 350
    assert sum(c.escanos for c in congreso.candidaturas) in (0, 350)
    assert feed.avance_escrutinio("senado").escanos_total == 208


def test_participacion(feed):
    datos = feed.participacion("14:00")
    assert len(datos["circunscripciones"]) == 52


def test_madrid(feed):
    madrid = feed.resultados_congreso("28")
    assert madrid.escanos_en_juego == 38
    assert madrid.cambio_escanos == 1
    assert sum(c.escanos for c in madrid.candidaturas) == 38


def test_senado_y_municipio(feed):
    assert feed.resultados_senado("38")["senadores_en_juego"] > 0
    assert feed.municipio("28079")["municipio"]["ine"] == "28079"


def test_no_existe(feed):
    with pytest.raises(NoEncontrado):
        feed.resultados_congreso("99")


def test_export(feed, tmp_path):
    datos = feed.export(ruta=tmp_path / "export_pre.json")
    assert len(datos["resultados_congreso"]) == 52


def test_token_invalido():
    with FeedClient(os.environ["FEED_API_URL"], "token-invalido", max_reintentos=0) as cliente:
        with pytest.raises(AuthError):
            cliente.avance_escrutinio()
