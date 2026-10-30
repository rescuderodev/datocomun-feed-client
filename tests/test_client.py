import httpx
import pytest
import respx

from datocomun_feed import AuthError, FeedClient, FeedError, NoEncontrado
from datocomun_feed import client as client_mod

URL = "https://feed.test/v1"


@pytest.fixture(autouse=True)
def sin_esperas(monkeypatch):
    monkeypatch.setattr(client_mod.time, "sleep", lambda s: None)


@pytest.fixture
def feed():
    with FeedClient(URL, "token-de-prueba") as f:
        yield f


@respx.mock
def test_envia_token(feed):
    ruta = respx.get(f"{URL}/estado").respond(json={"servicio": "recuento-api"})
    feed.estado()
    assert ruta.calls.last.request.headers["Authorization"] == "Bearer token-de-prueba"


def test_sin_token():
    with pytest.raises(ValueError):
        FeedClient(URL, "")


@respx.mock
def test_401(feed):
    respx.get(f"{URL}/participacion").respond(
        401, json={"error": "no_autorizado", "detalle": "Token ausente, caducado o de otro entorno."})
    with pytest.raises(AuthError) as e:
        feed.participacion()
    assert e.value.error == "no_autorizado"


@respx.mock
def test_404(feed):
    respx.get(f"{URL}/resultados/congreso/99").respond(404, json={"error": "no_encontrado"})
    with pytest.raises(NoEncontrado):
        feed.resultados_congreso("99")


@respx.mock
def test_reintenta_503(feed):
    respx.get(f"{URL}/participacion").mock(side_effect=[
        httpx.Response(503, json={"error": "sin_datos_nuevos"}),
        httpx.Response(503, json={"error": "sin_datos_nuevos"}),
        httpx.Response(200, json={"hora": "18:00"}),
    ])
    assert feed.participacion()["hora"] == "18:00"


@respx.mock
def test_respeta_retry_after(feed, monkeypatch):
    esperas = []
    monkeypatch.setattr(client_mod.time, "sleep", esperas.append)
    respx.get(f"{URL}/participacion").mock(side_effect=[
        httpx.Response(429, headers={"Retry-After": "2"}),
        httpx.Response(200, json={}),
    ])
    feed.participacion()
    assert esperas == [2.0]


@respx.mock
def test_agota_reintentos():
    ruta = respx.get(f"{URL}/participacion").respond(502)
    with FeedClient(URL, "t", max_reintentos=2) as feed:
        with pytest.raises(FeedError):
            feed.participacion()
    assert ruta.call_count == 3


@respx.mock
def test_reintenta_error_de_red(feed):
    respx.get(f"{URL}/participacion").mock(side_effect=[httpx.ConnectError("caida"), httpx.Response(200, json={})])
    feed.participacion()


@respx.mock
def test_resultados_congreso(feed):
    respx.get(f"{URL}/resultados/congreso/28").respond(json={
        "circunscripcion": {"codigo": "28", "nombre": "Madrid"},
        "escanos_en_juego": 38, "escanos_convocatoria_anterior": 37,
        "escrutado_pct": 41.2, "votos_validos": 1000, "blancos": 10, "nulos": 5,
        "candidaturas": [
            {"siglas": "B", "nombre": "B", "votos": 300, "pct": 30.0, "escanos": 12},
            {"siglas": "A", "nombre": "A", "votos": 600, "pct": 60.0, "escanos": 26},
        ],
        "actualizado": "2026-11-18T21:40:00+01:00",
    })
    madrid = feed.resultados_congreso("28")
    assert [c.siglas for c in madrid.candidaturas] == ["A", "B"]
    assert madrid.cambio_escanos == 1
