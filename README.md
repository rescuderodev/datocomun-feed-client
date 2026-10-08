# datocomun-feed-client

Cliente Python para Recuento API (Dato Común).

> En desarrollo. La interfaz puede cambiar.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Uso

```python
from datocomun_feed import FeedClient

feed = FeedClient(base_url="https://feed-pre.datocomun.com/v1")
print(feed.estado())
```
