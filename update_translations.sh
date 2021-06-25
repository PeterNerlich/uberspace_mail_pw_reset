#!/bin/bash

SCRIPT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

CDIR=$(git rev-parse --show-toplevel)

if [ $(which pybabel &>/dev/null; echo $?) == 0 ]; then
  BABEL='pybabel'
else
  BABEL="$CDIR/bin/pybabel"
fi

"$BABEL" extract -F babel.cfg -k 'lazy_gettext _l' -o strings.pot .
"$BABEL" update -i strings.pot -d translations

"$BABEL" compile -d translations
