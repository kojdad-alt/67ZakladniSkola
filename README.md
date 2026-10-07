# 67ZakladniSkola

Školní projekt **„Vizitka školy“**: jednostránkový web smyšlené 67. základní školy Plzeň.
Jen HTML, CSS a Bootstrap 5.3.8, žádný JavaScript.

## Jak to otevřít

Dvojklikem na `index.html`, nebo přes místní server, který se chová jako GitHub Pages:

```bash
python3 nastroje/server.py
```

a pak <http://localhost:8067/67ZakladniSkola/>.

## Před commitem

```bash
python3 nastroje/kontrola.py
```

Hlídá zadání (žádný JavaScript), SEO (titulky, popisy, nadpisy, alt texty, odkazy) a věci, podle kterých
web vypadá „vibecoded“. Podrobná pravidla, vzhled a struktura jsou v [AGENTS.md](AGENTS.md).

## Licence

Kód: MIT (viz `LICENSE`). Bootstrap: MIT. Písma Archivo a Playwrite CZ: SIL Open Font License (`fonty/`).
Škola, lidé i kontakty na webu jsou vymyšlené.
