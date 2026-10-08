#!/usr/bin/env python3
"""Kontrola webu před commitem. Spuštění z kořene repa:  python3 nastroje/kontrola.py

Hlídá zadání (jen HTML + CSS + Bootstrap, žádný JavaScript), SEO seznam
(titulky, popisy, nadpisy, alt texty, odkazy, sitemap…) a seznam věcí,
podle kterých web vypadá „vibecoded“ (viz AGENTS.md).
Chyba = exit 1. Varování jen upozorní.
"""
import html.parser
import json
import os
import re
import sys

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRANKY = ["index.html", "404.html"]
POVINNE = ["index.html", "404.html", "robots.txt", "sitemap.xml", "llms.txt",
           "img/og.png", "img/favicon.svg", "img/favicon-32.png", "img/apple-touch-icon.png"]
PREFIX = "/67ZakladniSkola/"  # cesta webu na GitHub Pages

chyby, varovani = [], []


def chyba(soubor, zprava):
    chyby.append(f"{soubor}: {zprava}")


def pozor(soubor, zprava):
    varovani.append(f"{soubor}: {zprava}")


class Rozbor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tagy = []        # (tag, atributy)
        self.idcka = set()
        self.zasobnik = []
        self.titulek = ""
        self.nadpisy = []     # (úroveň, text)
        self.ld_json = []
        self.texty = []       # viditelný text
        self._v_title = self._v_skriptu = False
        self._nadpis = None
        self._skript = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tagy.append((tag, a))
        if "id" in a:
            self.idcka.add(a["id"])
        if tag == "title" and not self.titulek:  # <title> v SVG se nepočítá
            self._v_title = not any(t == "svg" for t, _ in self.tagy)
        elif tag == "script":
            self._v_skriptu, self._skript = True, ""
        elif re.fullmatch(r"h[1-6]", tag):
            self._nadpis = [int(tag[1]), ""]

    def handle_endtag(self, tag):
        if tag == "title":
            self._v_title = False
        elif tag == "script":
            self._v_skriptu = False
            typ = next((a.get("type") for t, a in reversed(self.tagy) if t == "script"), None)
            if typ == "application/ld+json":
                self.ld_json.append(self._skript)
        elif re.fullmatch(r"h[1-6]", tag) and self._nadpis:
            self.nadpisy.append((self._nadpis[0], self._nadpis[1].strip()))
            self._nadpis = None

    def handle_data(self, data):
        if self._v_title:
            self.titulek += data
        elif self._v_skriptu:
            self._skript += data
        else:
            self.texty.append(data)
            if self._nadpis:
                self._nadpis[1] += data


def zkontroluj_stranku(jmeno, titulky):
    cesta = os.path.join(KOREN, jmeno)
    zdroj = open(cesta, encoding="utf-8").read()
    r = Rozbor()
    r.feed(zdroj)

    if not re.search(r'<html[^>]*\blang="cs"', zdroj):
        chyba(jmeno, 'chybí <html lang="cs">')

    titulek = r.titulek.strip()
    if not titulek:
        chyba(jmeno, "chybí <title>")
    elif titulek in titulky:
        chyba(jmeno, f"titulek je stejný jako na {titulky[titulek]}")
    else:
        titulky[titulek] = jmeno
        if len(titulek) > 65:
            pozor(jmeno, f"titulek má {len(titulek)} znaků, Google ukáže asi 60")

    meta = {a.get("name") or a.get("property"): a.get("content", "") for t, a in r.tagy if t == "meta"}
    popis = meta.get("description", "")
    if not popis:
        chyba(jmeno, "chybí meta description")
    elif not 50 <= len(popis) <= 160:
        pozor(jmeno, f"meta description má {len(popis)} znaků (ideál 50–160)")

    h1 = [n for n in r.nadpisy if n[0] == 1]
    if len(h1) != 1:
        chyba(jmeno, f"stránka má mít právě jedno <h1>, má {len(h1)}")
    texty_nadpisu = [n[1] for n in r.nadpisy]
    for t in set(texty_nadpisu):
        if texty_nadpisu.count(t) > 1:
            chyba(jmeno, f"nadpis „{t}“ je tam víckrát")
    predchozi = 0
    for uroven, text in r.nadpisy:
        if uroven > predchozi + 1:
            pozor(jmeno, f"nadpis h{uroven} „{text}“ přeskakuje úroveň")
        predchozi = uroven
    emoji = re.compile("[\U0001F000-\U0001FAFF☀-➿]")
    for _, text in r.nadpisy:
        if emoji.search(text):
            chyba(jmeno, f"emoji v nadpisu „{text}“")

    odkazy = {t: a for t, a in r.tagy}
    if jmeno == "index.html":
        if not any(t == "link" and a.get("rel") == "canonical" for t, a in r.tagy):
            chyba(jmeno, "chybí <link rel=canonical>")
        for vlastnost in ("og:title", "og:description", "og:image", "og:url"):
            if not meta.get(vlastnost):
                chyba(jmeno, f"chybí {vlastnost}")
        if not r.ld_json:
            chyba(jmeno, "chybí strukturovaná data (application/ld+json)")
    for blok in r.ld_json:
        try:
            json.loads(blok)
        except json.JSONDecodeError as e:
            chyba(jmeno, f"strukturovaná data nejsou platný JSON: {e}")

    if not any(t == "link" and "icon" in (a.get("rel") or "") for t, a in r.tagy):
        chyba(jmeno, "chybí favicon")

    for tag, a in r.tagy:
        if tag == "img" and "alt" not in a:
            chyba(jmeno, f"obrázek {a.get('src')} nemá alt")
        if tag == "script" and a.get("type") != "application/ld+json":
            chyba(jmeno, "JavaScript není podle zadání povolený (jen HTML + CSS + Bootstrap)")
        for atr in ("href", "src"):
            url = a.get(atr)
            if not url or tag == "a" and atr == "href" and url.startswith(("mailto:", "tel:")):
                continue
            if tag == "link" and a.get("rel") == "canonical":
                continue
            if url.startswith(("http://", "https://", "//")):
                if tag != "a":
                    chyba(jmeno, f"cizí zdroj {url}, vše má být v repu")
                continue
            if url.startswith("#"):
                if url != "#" and url[1:] not in r.idcka:
                    chyba(jmeno, f"odkaz {url} vede na neexistující id")
                continue
            soubor = url.split("#", 1)[0].split("?", 1)[0]
            if soubor.startswith(PREFIX):
                soubor = soubor[len(PREFIX):]
            elif soubor.startswith("/"):
                chyba(jmeno, f"cesta {url} nemá předponu {PREFIX}")
                continue
            soubor = soubor.lstrip("./") or "index.html"
            plna = os.path.join(KOREN, soubor)
            if os.path.isdir(plna):
                plna = os.path.join(plna, "index.html")
            if not os.path.exists(plna):
                chyba(jmeno, f"odkaz {url} vede na soubor, který neexistuje")
            kotva = url.split("#", 1)[1] if "#" in url else None
            if kotva and soubor in ("", "index.html") and jmeno != "index.html":
                idcka = set(re.findall(r'\bid="([^"]+)"', open(os.path.join(KOREN, "index.html"), encoding="utf-8").read()))
                if kotva not in idcka:
                    chyba(jmeno, f"odkaz {url} vede na neexistující id v index.html")

    # česká typografie: jednopísmenná předložka/spojka na konci řádku
    text = " ".join(r.texty)
    for m in re.finditer(r"(?<![\w.])([vVsSzZkKoOuUaAiI]) (?=\w)", text):
        okoli = text[max(0, m.start() - 15):m.end() + 15].replace("\n", " ")
        pozor(jmeno, f"za „{m.group(1)}“ patří nezlomitelná mezera (&nbsp;): …{okoli.strip()}…")

    zkontroluj_zakazane(jmeno, zdroj)


# seznam „20 důvodů, proč web vypadá vibecoded“ – co se dá najít strojově
ZAKAZANE = [
    (r"—", "dlouhá pomlčka (em dash); v češtině pomlčka – (en dash) s mezerami"),
    (r"\bInter\b|Space Grotesk|Instrument Serif", "zakázané písmo (Inter / Space Grotesk / Instrument Serif)"),
    (r"background-clip\s*:\s*text", "text s přechodem (gradient hero text)"),
    (r"backdrop-filter", "glassmorphismus (backdrop-filter)"),
    (r"radial-gradient|conic-gradient", "barevný přechod (gradient) na pozadí"),
    (r"\b(grain|noise)\b", "zrno přes přechod (grain)"),
    (r"lucide|font-?awesome|bootstrap-icons", "knihovna ikon (Lucide apod.)"),
    (r"data-aos|animate__|IntersectionObserver", "animace při scrollování (fade-in on scroll)"),
    (r"btn-primary|btn-secondary", "nepřebarvené tlačítko Bootstrapu, použij .tlacitko"),
    (r'class="[^"]*\bcard\b', "nepřebarvená karta Bootstrapu"),
    (r"font-style\s*:\s*italic", "kurzíva jako ozdoba (serif italic accent)"),
    (r"#(?:6366f1|8b5cf6|7c3aed|a855f7|3b82f6)\b", "typická „AI“ fialová/modrá"),
]


def zkontroluj_zakazane(jmeno, zdroj):
    for vzor, popis in ZAKAZANE:
        for m in re.finditer(vzor, zdroj, flags=re.IGNORECASE if "Inter" not in vzor else 0):
            radek = zdroj.count("\n", 0, m.start()) + 1
            chyba(jmeno, f"řádek {radek}: {popis}")


def main():
    for soubor in POVINNE:
        if not os.path.exists(os.path.join(KOREN, soubor)):
            chyba(soubor, "soubor chybí")

    titulky = {}
    for stranka in STRANKY:
        zkontroluj_stranku(stranka, titulky)

    for slozka, _, soubory in os.walk(os.path.join(KOREN, "css")):
        for s in soubory:
            if s.endswith(".css"):
                zkontroluj_zakazane(os.path.relpath(os.path.join(slozka, s), KOREN),
                                    open(os.path.join(slozka, s), encoding="utf-8").read())

    for slozka, _, soubory in os.walk(KOREN):
        if ".git" in slozka:
            continue
        for s in soubory:
            cesta = os.path.relpath(os.path.join(slozka, s), KOREN)
            if s.endswith(".map"):
                chyba(cesta, "source mapa nemá být na produkci")
            if s.endswith((".css", ".js")) and "sourceMappingURL" in open(os.path.join(slozka, s), encoding="utf-8", errors="ignore").read():
                chyba(cesta, "odkaz na source mapu (sourceMappingURL)")

    sitemap = open(os.path.join(KOREN, "sitemap.xml"), encoding="utf-8").read()
    if "<loc>" not in sitemap:
        chyba("sitemap.xml", "neobsahuje žádnou adresu")

    for v in varovani:
        print("  varování  " + v)
    for c in chyby:
        print("  CHYBA     " + c)
    print(f"\n{len(chyby)} chyb, {len(varovani)} varování")
    sys.exit(1 if chyby else 0)


if __name__ == "__main__":
    main()
