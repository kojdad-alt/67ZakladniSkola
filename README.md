# 67ZakladniSkola

Školní projekt **„Vizitka školy“**: jednostránkový web smyšlené 67. základní školy Plzeň.
Jen HTML, CSS a Bootstrap 5.3.8, žádný JavaScript.

## Jak to otevřít

Web běží na GitHub Pages: **<https://kojdad-alt.github.io/67ZakladniSkola/>**

Po každém pushi do `main` se do pár minut aktualizuje sám.

Neexistující adresa ukáže stránku `404.html`.

## Spuštění u sebe

Stačí Git a Python 3 (nic dalšího se neinstaluje):

```bash
git clone https://github.com/kojdad-alt/67ZakladniSkola.git
cd 67ZakladniSkola
python3 nastroje/server.py
```

Pak otevřít <http://localhost:8067/67ZakladniSkola/>. Na Windows je místo `python3` příkaz `py`.
Server se chová jako GitHub Pages (stejná cesta, na neexistující adresy vrací stránku 404), ukončí se Ctrl+C.

Bez Pythonu jde otevřít i `index.html` dvojklikem, jen nefunguje stránka 404.

## Co kde je

| Soubor | Co v něm je |
|--------|-------------|
| `index.html` | celá stránka |
| `css/styl.css` | všechen vlastní vzhled; barvy a písma jen v `:root` nahoře |
| `404.html` | stránka „nenalezeno“ |
| `robots.txt` | pravidla pro roboty |
| `sitemap.xml` | mapa webu |
| `llms.txt` | shrnutí stránky pro jazykové modely |
| `nastroje/kontrola.py` | kontrola před commitem |
| `nastroje/server.py` | místní náhled |
| `AGENTS.md` | podrobná pravidla, vzhled, typografie, zdroje obsahu |

## Před commitem

```bash
python3 nastroje/kontrola.py
```

Musí skončit „0 chyb“. Hlídá zadání (žádný JavaScript), SEO (titulky, popisy, nadpisy, alt texty, odkazy, adresa
webu v sitemapě a llms.txt), přístupnost (`id`, `aria-labelledby`, kontrast barev ve světlém i tmavém tématu),
českou typografii a věci, podle kterých web vypadá „vibecoded“. Podrobnosti jsou v [AGENTS.md](AGENTS.md).

## Jak poslat změnu

Na `main` se nepushuje napřímo:

1. nová větev (`git switch -c jidelna-ceny`),
2. úprava, `python3 nastroje/kontrola.py`, kontrola v náhledu,
3. commit česky a krátce, co se změnilo („Jídelna: ceny na rok 2026/27“),
4. `git push` a pull request do `main`, po kontrole sloučit.

## Licence

Kód: MIT (viz `LICENSE`). Bootstrap: MIT. Písma Archivo a Playwrite CZ: SIL Open Font License (`fonty/`).
Škola, lidé i kontakty na webu jsou vymyšlené.
