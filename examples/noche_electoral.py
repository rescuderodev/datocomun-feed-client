"""Seguimiento del escrutinio en noche electoral.

Consulta el avance cada 10 s y, cuando cambia, pinta un resumen.

    FEED_API_URL=... FEED_API_TOKEN=... python examples/noche_electoral.py
"""

import argparse
import logging
import time

from datocomun_feed import FeedClient, FeedError


def pintar(avance):
    print(f"\n[{avance.actualizado:%H:%M:%S}] {avance.camara} · escrutado {avance.escrutado_pct:.2f} %"
          f" · mayoria {avance.mayoria_absoluta}")
    for c in avance.candidaturas:
        barra = "#" * (c.escanos // 4)
        print(f"  {c.siglas:<8} {c.escanos:>3}  {barra}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camara", default="congreso", choices=["congreso", "senado"])
    parser.add_argument("--intervalo", type=int, default=10, help="segundos entre consultas")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    ultimo = None
    with FeedClient.from_env() as feed:
        while True:
            try:
                avance = feed.avance_escrutinio(args.camara)
                # print(avance)
                if avance.actualizado != ultimo:
                    pintar(avance)
                    ultimo = avance.actualizado
                if avance.escrutado_pct >= 100:
                    break
            except FeedError as exc:
                logging.error("Error del feed: %s", exc)
            time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
