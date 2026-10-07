#!/usr/bin/env python3
"""Místní náhled webu, který se chová jako GitHub Pages.

Web běží na http://localhost:8067/67ZakladniSkola/ (stejná cesta jako na GitHub Pages),
na neexistující adresy vrací 404.html se stavem 404.

Spuštění z kořene repa:  python3 nastroje/server.py   (jiný port: python3 nastroje/server.py 8080)
"""
import http.server
import os
import sys

PREFIX = "/67ZakladniSkola"
KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8067


class Obsluha(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=KOREN, **kwargs)

    def do_GET(self):
        cesta = self.path.split("?", 1)[0].split("#", 1)[0]
        if cesta in ("/", PREFIX):
            self.send_response(301)
            self.send_header("Location", PREFIX + "/")
            self.end_headers()
            return
        if not cesta.startswith(PREFIX + "/"):
            return self.posli_404()
        self.path = self.path[len(PREFIX):]
        soubor = self.translate_path(self.path)
        if os.path.isdir(soubor):
            soubor = os.path.join(soubor, "index.html")
        if not os.path.isfile(soubor) or os.path.basename(soubor).startswith("."):
            return self.posli_404()
        return super().do_GET()

    def posli_404(self):
        with open(os.path.join(KOREN, "404.html"), "rb") as f:
            obsah = f.read()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(obsah)))
        self.end_headers()
        self.wfile.write(obsah)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


if __name__ == "__main__":
    print(f"Náhled: http://localhost:{PORT}{PREFIX}/  (Ctrl+C ukončí)")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Obsluha).serve_forever()
