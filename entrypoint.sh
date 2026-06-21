#!/bin/sh
set -e

# The host directory bind-mounted at $APP_DATA_DIR may be owned by root
# (Docker creates it that way the first time it's mounted, or it may have
# been created manually). Fix ownership every startup, before dropping to
# the unprivileged 'appuser', so SQLite writes actually persist to disk
# instead of silently failing.
mkdir -p "$APP_DATA_DIR"
chown -R appuser:appuser "$APP_DATA_DIR"

exec gosu appuser streamlit run app.py