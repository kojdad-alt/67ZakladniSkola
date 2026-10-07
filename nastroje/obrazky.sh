#!/usr/bin/env bash
# Vyrobí obrázky z předloh pomocí Google Chrome (headless):
#   img/og.png              1200×630  obrázek pro sdílení (z nastroje/og.html)
#   img/apple-touch-icon.png 180×180  ikona na plochu iPhonu (z img/favicon.svg)
#   img/favicon-32.png        32×32   záložní favicon pro starší prohlížeče
#   img/logo-512.png         512×512  logo do strukturovaných dat
# Spuštění z kořene repa:  ./nastroje/obrazky.sh
set -euo pipefail
cd "$(dirname "$0")/.."
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

foto() { # foto <soubor.html> <šířka> <výška> <výstup.png>
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --window-size="$2,$3" --screenshot="$4" "file://$PWD/$1" >/dev/null 2>&1
  echo "  $4 ($2×$3)"
}

ikona() { # ikona <velikost> <výstup.png> <pozadí pod rohy>
  cat > nastroje/.ikona.html <<HTML
<!doctype html><html><body style="margin:0;background:$3"><img src="../img/favicon.svg" width="$1" height="$1" style="display:block" alt=""></body></html>
HTML
  foto nastroje/.ikona.html "$1" "$1" "$2"
  rm -f nastroje/.ikona.html
}

echo "Vyrábím obrázky:"
foto nastroje/og.html 1200 630 img/og.png
ikona 180 img/apple-touch-icon.png "#e2ae38"
ikona 512 img/logo-512.png "#e2ae38"
ikona 32 img/favicon-32.png "#e2ae38"
