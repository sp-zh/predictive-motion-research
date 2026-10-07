#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec /usr/bin/ssh -F "$ROOT/.transfer-private/ssh_config" "$@"
