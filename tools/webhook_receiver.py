"""
Récepteur de webhook minimal pour DÉMONSTRATION de l'alerting (C4.3.1).

Il écoute en HTTP, journalise chaque requête reçue (horodatage + corps JSON) dans
un fichier de preuve, et répond 200. Sert à prouver qu'une alerte est réellement
*délivrée* par la plateforme, pas seulement codée.

    python -m tools.webhook_receiver --port 9099 --sortie preuves/C4-3-1_alerte_webhook.txt

Puis on provoque un échec (DAG eckert_demo_alerte) : le on_failure_callback
d'Airflow envoie un POST ici, qui est journalisé.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def fabriquer_handler(sortie: Path):
    class Handler(BaseHTTPRequestHandler):
        def _traiter(self) -> None:
            longueur = int(self.headers.get("Content-Length", 0))
            brut = self.rfile.read(longueur).decode("utf-8", errors="replace") if longueur else ""
            horodatage = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            try:
                corps = json.dumps(json.loads(brut), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                corps = brut
            bloc = (
                f"\n===== ALERTE REÇUE {horodatage} =====\n"
                f"{self.command} {self.path}\n"
                f"{corps}\n"
            )
            with sortie.open("a", encoding="utf-8") as flux:
                flux.write(bloc)
            print(bloc, flush=True)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"recu": true}')

        def do_POST(self) -> None:  # noqa: N802
            self._traiter()

        def log_message(self, *args) -> None:  # silence le log par défaut
            return

    return Handler


def main() -> None:
    parseur = argparse.ArgumentParser(description="Récepteur de webhook de démonstration")
    parseur.add_argument("--port", type=int, default=9099)
    parseur.add_argument("--sortie", type=Path, default=Path("preuves/C4-3-1_alerte_webhook.txt"))
    args = parseur.parse_args()
    args.sortie.parent.mkdir(parents=True, exist_ok=True)

    serveur = HTTPServer(("0.0.0.0", args.port), fabriquer_handler(args.sortie))
    print(f"Récepteur de webhook à l'écoute sur le port {args.port} -> {args.sortie}", flush=True)
    serveur.serve_forever()


if __name__ == "__main__":
    main()
