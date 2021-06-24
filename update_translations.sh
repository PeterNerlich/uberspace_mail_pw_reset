
#!/bin/bash

CDIR=$(git rev-parse --show-toplevel)

if [ $(which pybabel &>/dev/null; echo $?) == 0 ]; then
  BABEL='pybabel'
else
  BABEL="$CDIR/bin/pybabel"
fi

cd "$CDIR"
"$BABEL" extract -F babel.cfg -k 'lazy_gettext _l' -o strings.pot .
"$BABEL" update -i strings.pot -d po

"$BABEL" compile -d po
