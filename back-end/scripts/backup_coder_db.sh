#!/usr/bin/env bash
set -euo pipefail

# Nightly backup script for Coder Postgres.
# Adjust container name (coder-postgres), db name/user if yours differ.

ts=$(date +%F-%H%M)
mkdir -p /var/backups
docker exec -i coder-postgres pg_dump -U coder coder | gzip > /var/backups/coder-$ts.sql.gz
find /var/backups -name 'coder-*.sql.gz' -mtime +14 -delete

echo "Backup complete: /var/backups/coder-$ts.sql.gz"

