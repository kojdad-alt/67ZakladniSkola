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
from urllib.parse import urlparse

KOREN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRANKY = ["index.html", "404.html"]
POVINNE = ["index.html", "404.html", "robots.txt", "sitemap.xml", "llms.txt", ".nojekyll",
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
        self.duplicitni_id = []
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
            if a["id"] in self.idcka:
                self.duplicitni_id.append(a["id"])
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

    # přístupnost: id jen jednou, aria-labelledby/describedby vedou na existující id, SVG má popis
    for i in sorted(set(r.duplicitni_id)):
        chyba(jmeno, f'id="{i}" je na stránce víckrát (odkazy #{i} a aria-labelledby pak míří jen na první)')
    for tag, a in r.tagy:
        for atr in ("aria-labelledby", "aria-describedby", "for"):
            for i in (a.get(atr) or "").split():
                if i not in r.idcka:
                    chyba(jmeno, f'<{tag} {atr}="{a[atr]}">: id „{i}“ na stránce není')
        if tag == "svg" and a.get("aria-hidden") != "true" and not (a.get("aria-labelledby") or a.get("aria-label")):
            chyba(jmeno, "<svg> bez popisu: buď aria-hidden=\"true\" (ozdoba), nebo aria-labelledby na <title> a <desc>")

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


def zkontroluj_adresu():
    """Adresa webu je na víc místech (AGENTS.md, „Adresa webu“). Všude musí začínat stejně jako canonical,
    aby se při přechodu na vlastní doménu nic nezapomnělo. Odkazy z llms.txt musí vést na existující oddíl."""
    index = open(os.path.join(KOREN, "index.html"), encoding="utf-8").read()
    m = re.search(r'<link rel="canonical" href="([^"]+)"', index)
    if not m:
        return  # chybějící canonical hlásí už zkontroluj_stranku
    adresa = m.group(1)
    if not adresa.endswith("/"):
        chyba("index.html", f"canonical {adresa} má končit lomítkem")
    if urlparse(adresa).path != PREFIX:
        chyba("nastroje/kontrola.py", f"PREFIX {PREFIX} neodpovídá cestě v canonical {adresa} "
                                      "(přepsat i 404.html a nastroje/server.py)")

    nalezene = [("index.html", u) for u in re.findall(r'<meta property="og:(?:url|image)" content="([^"]+)"', index)]

    def projdi(uzel):
        if isinstance(uzel, dict):
            for klic, hodnota in uzel.items():
                if klic in ("@id", "url", "logo", "image", "item") and isinstance(hodnota, str):
                    nalezene.append(("index.html (JSON-LD)", hodnota))
                else:
                    projdi(hodnota)
        elif isinstance(uzel, list):
            for hodnota in uzel:
                projdi(hodnota)

    for blok in re.findall(r'<script type="application/ld\+json">(.*?)</script>', index, re.S):
        try:
            projdi(json.loads(blok))
        except json.JSONDecodeError:
            pass  # neplatný JSON hlásí zkontroluj_stranku

    def precti(soubor):
        return open(os.path.join(KOREN, soubor), encoding="utf-8").read()

    lokace = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", precti("sitemap.xml"))
    nalezene += [("sitemap.xml", u) for u in lokace]
    nalezene += [("robots.txt", u) for u in re.findall(r"^Sitemap:\s*(\S+)", precti("robots.txt"), re.M)]
    llms = re.findall(r"\]\((https?://[^)\s]+)\)", precti("llms.txt"))
    nalezene += [("llms.txt", u) for u in llms]

    for soubor, url in nalezene:
        if not url.startswith(adresa):
            chyba(soubor, f"adresa {url} nezačíná na {adresa} (canonical v index.html)")
    if adresa not in lokace:
        chyba("sitemap.xml", f"chybí <loc>{adresa}</loc> (canonical úvodní stránky)")

    idcka = set(re.findall(r'\bid="([^"]+)"', index))
    for url in llms:
        kotva = url.split("#", 1)[1] if "#" in url else ""
        if kotva and kotva not in idcka:
            chyba("llms.txt", f"odkaz {url} vede na neexistující id v index.html")


# kontrast barevných tokenů z css/styl.css (WCAG 2.x): text aspoň 4,5 : 1, rámeček fokusu aspoň 3 : 1
KONTRAST = [
    # (barva, pozadí, minimum, kde se to potkává)
    ("inkoust", "zed", 4.5, "text na zdi"),
    ("inkoust-2", "zed", 4.5, "tlumený text, štítky, popisky"),
    ("inkoust", "zed-2", 4.5, "řádek pavilonu zvýrazněný přes :target"),
    ("inkoust-2", "zed-2", 4.5, "meta řádku pavilonu při :target"),
    ("inkoust", "papir", 4.5, "text v sešitu se zápisem"),
    ("inkoust-2", "papir", 4.5, "štítek v sešitu"),
    ("inkoust", "plan-pavilon", 4.5, "popisky v plánku"),
    ("propiska", "papir", 4.5, "vzkaz u zápisu"),
    ("propiska", "zed", 4.5, "prázdniny v kalendáři, rámeček fokusu"),
    ("odkaz", "zed", 4.5, "odkazy"),
    ("na-soklu", "sokl", 4.5, "čísla školy a patička na soklu"),
    ("na-horcici", "horcice", 4.5, "cedulky pavilonů, velká přestávka"),
    ("zed", "inkoust", 4.5, "tlačítka"),
    ("horcice", "sokl", 3.0, "rámeček fokusu na soklu"),
]


def jas(barva):
    h = barva.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    slozky = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    slozky = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in slozky]
    return 0.2126 * slozky[0] + 0.7152 * slozky[1] + 0.0722 * slozky[2]


def kontrast(a, b):
    sv, tm = sorted((jas(a), jas(b)), reverse=True)
    return (sv + 0.05) / (tm + 0.05)


def zkontroluj_kontrast():
    jmeno = "css/styl.css"
    css = open(os.path.join(KOREN, jmeno), encoding="utf-8").read()

    def tokeny(zacatek):
        if not zacatek:
            return {}
        blok = css[zacatek.end():css.index("}", zacatek.end())]
        return dict(re.findall(r"--([\w-]+)\s*:\s*(#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?)\b", blok))

    svetle = tokeny(re.search(r"^:root\s*\{", css, re.M))
    tmave = {**svetle, **tokeny(re.search(r"prefers-color-scheme:\s*dark\)\s*\{\s*:root\s*\{", css))}
    for tema, barvy in (("světlé", svetle), ("tmavé", tmave)):
        for popredi, pozadi, minimum, kde in KONTRAST:
            if popredi not in barvy or pozadi not in barvy:
                chyba(jmeno, f"{tema} téma: chybí token --{popredi} nebo --{pozadi} (#hex v :root)")
                continue
            k = kontrast(barvy[popredi], barvy[pozadi])
            if k < minimum:
                ma = f"{k:.2f}".replace(".", ",")
                ma_mit = f"{minimum:g}".replace(".", ",")
                chyba(jmeno, f"{tema} téma: --{popredi} na --{pozadi} má kontrast {ma} : 1, "
                             f"potřeba aspoň {ma_mit} : 1 ({kde})")


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

    zkontroluj_kontrast()
    zkontroluj_adresu()

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
