# datocomun-feed-client

Cliente Python para Recuento API (Dato Común).

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

    madrid = feed.resultados_congreso("28")
    for c in madrid.candidaturas:
        print(c.siglas, c.votos, c.pct, c.escanos)
```

## Endpoints

| Endpoint | Método del cliente |
| --- | --- |
| `GET /v1/estado` | `estado()` |
| `GET /v1/participacion?hora=` | `participacion(hora)` |
| `GET /v1/resultados/congreso/{circ}` | `resultados_congreso(circunscripcion)` |
| `GET /v1/resultados/senado/{circ}` | `resultados_senado(circunscripcion)` |

`circunscripcion`: código INE de dos digitos de la provincia (`"28"`).
