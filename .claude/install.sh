#!/usr/bin/env bash
# Install the Portuguese property buyer skills, agent and commands into
# ~/.claude so they are available in every session, not only inside this repo.
#
# Symlinks by default so edits here stay live; pass --copy for standalone copies.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CLAUDE_HOME:-$HOME/.claude}"
MODE="link"
[[ "${1:-}" == "--copy" ]] && MODE="copy"

install_one() {
  local kind="$1" name="$2"
  mkdir -p "$DEST/$kind"
  local target="$DEST/$kind/$name"
  if [[ -e "$target" || -L "$target" ]]; then
    echo "  skip   $kind/$name (already present — remove it first to reinstall)"
    return
  fi
  if [[ "$MODE" == "link" ]]; then
    ln -s "$SRC/$kind/$name" "$target"
    echo "  link   $kind/$name"
  else
    cp -r "$SRC/$kind/$name" "$target"
    echo "  copy   $kind/$name"
  fi
}

echo "Installing into $DEST ($MODE)"
for skill in pt-property-market-scan pt-property-tracker pt-property-due-diligence; do
  install_one skills "$skill"
done
install_one agents property-scout-pt.md
for cmd in property-scan.md property-dd.md; do
  install_one commands "$cmd"
done

WS="${PROPERTY_WORKSPACE:-$HOME/property-portugal}"
mkdir -p "$WS"/{notes,digests,dd}
if [[ ! -f "$WS/profile.yaml" ]]; then
  cp "$SRC/skills/pt-property-market-scan/references/profile-template.yaml" \
     "$WS/profile.yaml"
  echo "  seed   $WS/profile.yaml — fill in your strategy"
else
  echo "  keep   $WS/profile.yaml (already exists)"
fi

cat <<EOF

Done. Next:

  export PROPERTY_WORKSPACE="$WS"     # add this to your shell profile
  \$EDITOR "$WS/profile.yaml"          # or just run /property-scan and answer

Then run /property-scan daily. Optional extras:
  pip install pyyaml openpyxl
EOF
