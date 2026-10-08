# AGENTS.md – pravidla pro práci na webu 67. ZŠ

Platí pro lidi i AI (Claude Code, Codex, Copilot…). `CLAUDE.md` sem jen odkazuje.

## Zadání

Školní projekt **„Vizitka školy“**: jedna stránka o smyšlené **67. základní škole Plzeň**.

- Povolené je jen **HTML + CSS + Bootstrap**. **Žádný JavaScript.** Jediný `<script>` na stránce je
  `application/ld+json`, což jsou strukturovaná data pro Google, ne kód.
- Škola, lidé, adresa, telefony i e-mail jsou **vymyšlené**. Na webu o tom je věta v patičce, nemazat ji.
- Web nesmí vypadat jako všechny školní weby se stejnou šablonou (modrá hlavička s logem, slider,
  sloupec „Aktuality“), ani jako „vibecoded“ web od AI (seznam níž).

## Struktura

```
index.html            jediná stránka webu
404.html              stránka „nenalezeno“ (cesty od /67ZakladniSkola/, protože se ukazuje na libovolné adrese)
css/styl.css          VŠECHEN vlastní vzhled; barvy a písma jen v :root (tokeny)
vendor/bootstrap-5.3.8/bootstrap.min.css   Bootstrap bez source map (neupravovat)
fonty/                písma Archivo a Playwrite CZ, oříznutá na češtinu (+ licence OFL)
img/                  favicon.svg, favicon-32.png, apple-touch-icon.png, logo-512.png, og.png
robots.txt, sitemap.xml, llms.txt
nastroje/server.py    místní náhled, chová se jako GitHub Pages
nastroje/kontrola.py  kontrola před commitem
nastroje/obrazky.sh   znovu vyrobí PNG obrázky (og.png, ikony) přes Google Chrome
nastroje/og.html      předloha obrázku pro sdílení
```

`1775-valorant-immortal-2.png` nahrál Matyáš a na webu se zatím nepoužívá. Je to ikona ze hry
Valorant (práva Riot Games), proto se nehodí jako logo školy.

## Náhled a kontrola

```bash
python3 nastroje/server.py       # pak http://localhost:8067/67ZakladniSkola/
python3 nastroje/kontrola.py     # před každým commitem, musí skončit „0 chyb“
```

Stačí i otevřít `index.html` dvojklikem. Neexistující adresy ukazují stránku 404 jen přes `nastroje/server.py`.
V Claude Code je v `.claude/launch.json` připravený náhled `web`.

Lighthouse (Google) bez instalace:

```bash
npx -y lighthouse@12 http://localhost:8067/67ZakladniSkola/ --view
```

Naposledy (8. 10. 2026, mobil): výkon 90, přístupnost 100, best practices 100, SEO 100.
Výkon místně snižuje jen chybějící komprese; GitHub Pages posílá gzip.

## Vzhled

Nápad: **pavilonová škola z roku 1967**. Stránka je jako procházka školou:

- **Světlé téma = chodba:** bílá zeď `--zed`, zelený olejový **sokl** s obkladem `--sokl` (pruh pod úvodem
  a patička), **hořčicové cedulky** pavilonů `--horcice`, text inkoustem `--inkoust`.
- **Tmavé téma = školní tabule** (`prefers-color-scheme: dark`): stejné tokeny, jiné hodnoty; křídově bílý text.
- **Červená = propiska paní učitelky** (`--propiska`): prázdniny v kalendáři, vzkaz u zápisu, rámeček fokusu.
- **Zápis** je stránka linkovaného sešitu s červeným okrajem. Řádkování je přesně `2rem`, okraje a mezery
  uvnitř `.sesit` drž v násobcích `2rem`, jinak text ujede z linek.
- **Plánek areálu** v úvodu je ručně kreslené SVG; pavilony jsou odkazy na řádky v oddílu Pavilony
  (zvýrazní je `:target`, bez JavaScriptu).

Písma:

- **Archivo** (proměnná šířka 75–125 % a tloušťka 400–800). Nadpisy jsou rozšířené (`font-stretch: 115–125%`),
  štítky úzké verzálky (`.stitek`, 75 %).
- **Playwrite CZ** je české školní psací písmo, jak ho píšou prvňáci. Jen na vzkaz u zápisu, nikde jinde.

Bootstrap používáme na mřížku (`container`, `row`, `col-*`, `g-*`), utility (`d-flex`, `gap-*`…),
`.btn` (přebarvené přes `--bs-btn-*` ve třídě `.tlacitko`), `.table` (`.rozvrh`) a `.breadcrumb`.
Nepřebarvené komponenty (`btn-primary`, `card`…) nepoužívat, vypadají jako každý jiný web.

## Zakázané (web by vypadal „vibecoded“)

Kontroluje to i `nastroje/kontrola.py`.

1. Fialovo-modrý přechod (gradient), přechod přes nadpis, zrno přes přechod.
2. Emoji v nadpisech.
3. Písma Inter, Space Grotesk, Instrument Serif; ozdobná patková kurzíva.
4. Karty s barevným okrajem, glassmorphismus (`backdrop-filter`), tři ikonové boxy v řadě.
5. Štítek („badge“) nad hlavním nadpisem.
6. Knihovny ikon (Lucide apod.). Když je ikona potřeba, nakreslit vlastní SVG.
7. Animace při scrollování, záře za kurzorem, tlačítka, která při najetí jen zprůhlední.
8. Tmavý režim s nízkým kontrastem. Kontrast textu drž aspoň 4,5 : 1 (teď 6–15 : 1).
9. Nekonzistentní mezery: používat jen `--m1` až `--m6` a Bootstrap `g-*`/`gap-*`.
10. Dlouhá pomlčka „—“ (em dash). V češtině se píše „–“ (en dash) s mezerami, rozsahy bez mezer: `1.–5. ročník`.
11. Obecné reklamní fráze („moderní škola s rodinnou atmosférou“). Psát konkrétně: čísla, časy, místa.

## SEO seznam (hotovo, udržovat)

- Jedinečný `<title>` a `meta description` na každé stránce, právě jedno `<h1>`, nadpisy bez přeskakování úrovní.
- `alt` u obrázků, SVG s `<title>` a `<desc>`.
- `canonical`, Open Graph (`og:*`, obrázek `img/og.png` 1200×630), favicon (SVG + PNG + apple-touch-icon).
- Strukturovaná data JSON-LD: `ElementarySchool`, `WebSite`, `WebPage` s drobečky, `Event` (zápis).
- Vlastní `404.html` s drobečkovou navigací, `robots.txt`, `sitemap.xml`, `llms.txt`.
- Žádné source mapy, žádný JavaScript, žádné cizí zdroje (písma i Bootstrap jsou v repu).
- Žádný zástupný text (lorem ipsum, „Text sem“).

### Adresa webu

Všude je `https://kojdad-alt.github.io/67ZakladniSkola/`. GitHub Pages u soukromého repa potřebuje placený
účet nebo veřejné repo. Při změně adresy (vlastní doména) přepsat:
`index.html` (canonical, og:url, og:image, JSON-LD), `sitemap.xml`, `robots.txt`, `llms.txt`,
a v `404.html` a `nastroje/server.py` předponu `/67ZakladniSkola/`.
`robots.txt` funguje jen v kořeni domény, tedy až s vlastní doménou.

## Česká typografie

- Za jednopísmennými předložkami a spojkami (k, s, v, z, o, u, a, i) patří `&nbsp;`. Kontrola je hlídá.
- Data: `1.&nbsp;9.&nbsp;2026`, jednotky: `24&nbsp;×&nbsp;12&nbsp;m`, `38&nbsp;Kč`, `45&nbsp;minut`.
- Časy bez nul na začátku: `7:40`, rozsahy pomlčkou bez mezer: `11:40–17:00`.
- Uvozovky „takhle“.

## Obsah a zdroje

- Termíny prázdnin 2026/27: MŠMT, Organizace školního roku 2026/2027; jarní prázdniny pro okres Plzeň-město
  22.–28. 2. 2027.
- Zápis do 1. třídy podle školského zákona (561/2004 Sb., § 36–37): 1.–30. dubna, odklad s doporučením
  školského poradenského zařízení a lékaře nebo klinického psychologa.
- Alergeny 1–14 podle nařízení EU č. 1169/2011, ceny obědů podle věkových skupin (vyhláška 107/2005 Sb.).

## Úprava písem

Písma jsou z repozitáře google/fonts, oříznutá na české znaky (Python `fonttools`):

```bash
python3 -m fontTools.varLib.instancer "Archivo[wdth,wght].ttf" wght=400:800 wdth=75:125 -o Archivo-ltd.ttf
python3 -m fontTools.subset Archivo-ltd.ttf --unicodes="U+0020-007E,U+00A0-00FF,U+010C-010F,U+011A-011B,U+0139-013A,U+013D-013E,U+0147-0148,U+0154-0155,U+0158-0161,U+0164-0165,U+016E-016F,U+017D-017E,U+2009,U+2013-2014,U+2018-201E,U+2022,U+2026,U+202F,U+20AC,U+2192" --layout-features='kern,liga,calt,ccmp,locl,mark,mkmk,tnum,lnum,case' --flavor=woff2 --output-file=fonty/archivo-cz.woff2
```

Logo „67“ ve favicon.svg a v hlavičce je převedené na křivky (Archivo 800, šířka 125 %), takže nepotřebuje písmo.

## Git

- Na `main` nepushovat napřímo: větev, pull request, sloučit po kontrole.
- Commity česky, krátce, co se změnilo („Jídelna: ceny na rok 2026/27“).
