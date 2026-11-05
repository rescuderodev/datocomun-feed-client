# datocomun-feed-client

Cliente Python oficial de Recuento API, el feed de Dato Común, para integrarlo
en los sistemas de la redacción: avance del escrutinio, participación y
resultados por circunscripción y municipio.

Lo estamos usando para las generales del 29N. Hasta entonces las integraciones
van contra PRE (datos de simulacro, candidaturas ficticias).

> En desarrollo. La interfaz puede cambiar.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Entornos y autenticación

| Entorno | URL base | Datos |
| --- | --- | --- |
| PRE | `https://feed-pre.datocomun.com/v1` | Simulacro |
| PRO | se entrega con las credenciales de producción | Oficiales |

Cada cliente tiene un token por entorno, va en `Authorization: Bearer <token>`.
Se pide en el portal de clientes.

La config se lee de `FEED_API_URL` y `FEED_API_TOKEN`.

## Uso

```python
from datocomun_feed import FeedClient

with FeedClient.from_env() as feed:
    print(feed.estado())

    avance = feed.avance_escrutinio()  # camara="senado" para el Senado
    print(avance.escrutado_pct, avance.lider())

    madrid = feed.resultados_congreso("28")
    for c in madrid.candidaturas:
        print(c.siglas, c.votos, c.pct, c.escanos)
```

## Endpoints

| Endpoint | Método del cliente |
| --- | --- |
| `GET /v1/estado` | `estado()` |
| `GET /v1/escrutinio/avance?camara=` | `avance_escrutinio(camara)` |
| `GET /v1/participacion?hora=` | `participacion(hora)` |
| `GET /v1/resultados/congreso/{circ}` | `resultados_congreso(circunscripcion)` |
| `GET /v1/resultados/senado/{circ}` | `resultados_senado(circunscripcion)` |
| `GET /v1/municipios/{ine}` | `municipio(ine)` |

`circunscripcion`: código INE de dos digitos de la provincia (`"28"`).

## Errores y reintentos

`AuthError` (401), `NoEncontrado` (404) y `FeedError` para el resto.

Con `429`, `5xx` (incluido el `503` de "fuente sin datos nuevos") o errores de
red reintenta con backoff exponencial (4 reintentos por defecto) y respeta
`Retry-After`. Se puede tocar con `max_reintentos` y `backoff_base`.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Soporte

Dudas e incidencias, através del portal de clientes.
