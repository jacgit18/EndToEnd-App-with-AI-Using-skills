#!/usr/bin/env bash
# Dump the Postgres database to a compressed file and prune old dumps.
#
#   scripts/backup-db.sh                       # prod stack, keep 14, ./backups
#   COMPOSE_FILE=compose.yaml scripts/backup-db.sh   # dev stack
#   KEEP=30 BACKUP_DIR=/mnt/usb/finance scripts/backup-db.sh
#
# Schedule it (crontab -e), e.g. every night at 02:30:
#   30 2 * * * cd /path/to/finance-dashboard && scripts/backup-db.sh >> backups/backup.log 2>&1
#
# What this does NOT cover — read before trusting it:
#  * Same machine. A dump next to the database it protects dies with the disk.
#    Free off-box options: copy BACKUP_DIR to a USB drive / another computer
#    (rsync), or to Backblaze B2 (first 10 GB free) with `rclone`. Serious
#    version: a managed Postgres with point-in-time restore (Neon, Supabase,
#    RDS — paid tiers) or a VPS provider's snapshot add-on (~20% of the VPS
#    price), so restoring doesn't depend on a cron job you wrote.
#  * Secrets. Per ADR-0014 the dump holds data only; back up backend/.env.prod
#    separately (a password manager works). Without it, a restored database
#    can't be logged into.
#  * Untested backups are hopes. Try a restore once (see docs/deploy.md).

set -euo pipefail

cd "$(dirname "$0")/.."   # finance-dashboard/, wherever this is called from

COMPOSE_FILE="${COMPOSE_FILE:-compose.prod.yaml}"
BACKUP_DIR="${BACKUP_DIR:-backups}"
KEEP="${KEEP:-14}"

mkdir -p "$BACKUP_DIR"
stamp="$(date +%Y%m%d-%H%M%S)"
final="$BACKUP_DIR/finance-$stamp.sql.gz"
partial="$final.partial"

# Dump to a .partial file and rename only on success, so a failed run (db down,
# disk full) never leaves a file that looks like a good backup. `-T` = no TTY,
# required when the command runs under cron. pg_dump runs *inside* the db
# container, so the password never leaves it and the db needs no published port.
if ! docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U finance --no-owner finance \
    | gzip > "$partial"; then
  rm -f "$partial"
  echo "backup FAILED ($stamp)" >&2
  exit 1
fi
mv "$partial" "$final"
echo "backup ok: $final ($(du -h "$final" | cut -f1))"

# Keep the newest $KEEP dumps. Names sort by timestamp, so `ls` order is age order.
# shellcheck disable=SC2012
ls -1 "$BACKUP_DIR"/finance-*.sql.gz | head -n "-$KEEP" | while read -r old; do
  rm -f "$old"
  echo "pruned: $old"
done
