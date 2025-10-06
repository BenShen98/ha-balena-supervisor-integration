#!/usr/bin/env bash
# Install balena_docker resources into Home Assistant config directory

set -euo pipefail

SYMLINK=0
INSTALL_DIR=""

for arg in "$@"; do
  if [[ "$arg" == --symlink ]]; then
    SYMLINK=1
  elif [[ -z "$INSTALL_DIR" && "$arg" != --* ]]; then
    INSTALL_DIR="$arg"
  fi
done

if [[ -z "$INSTALL_DIR" ]]; then
  echo "Usage: $0 <config_dir>"
  exit 1
fi

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SRC_WWW="$SCRIPT_DIR/../www"
DEST_WWW="$INSTALL_DIR/www/balena_docker"
SRC_CC="$SCRIPT_DIR/../custom_components"
DEST_CC="$INSTALL_DIR/custom_components/balena_docker"

if [[ ! -d "$SRC_WWW" || ! -d "$SRC_CC" ]]; then
  echo "Source www or custom_components directory not found: $SRC_WWW, $SRC_CC"
  exit 1
fi

# Process WWW

## Remove any existing www/balena_docker
if [[ -e "$DEST_WWW" ]]; then
  chmod -R u+w "$DEST_WWW" 2>/dev/null || true
  rm -rf "$DEST_WWW"
fi

## Install www/balena_docker
mkdir -p "$DEST_WWW"
cp -r "$SRC_WWW/"* "$DEST_WWW"
find "$DEST_WWW" -type f -exec chmod 444 {} +

# Process custom_components

## Remove any existing balena_docker folder before install/symlink
if [[ -e "$DEST_CC" ]]; then
  # Assert DEST_CC does not have trailing slash
  if [[ "$DEST_CC" == */ ]]; then
    echo "Error: DEST_CC ($DEST_CC) must not have a trailing slash"
    exit 1
  fi
  rm -rf "$DEST_CC"
fi

## Install or symlink
if [[ "$SYMLINK" -eq 1 ]]; then
  mkdir -p "$(dirname "$DEST_CC")"
  ln -sfn "$SRC_CC" "$DEST_CC"
else
  mkdir -p "$DEST_CC"
  cp -r "$SRC_CC/"* "$DEST_CC"
  find "$DEST_CC" -type f -exec chmod 444 {} +
fi

# Ensure __init__.py exists in custom_components
INIT_FILE="$INSTALL_DIR/custom_components/__init__.py"
if [[ ! -f "$INIT_FILE" ]]; then
  touch "$INIT_FILE"
fi

echo "balena_docker resources installed to $INSTALL_DIR"
