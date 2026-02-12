#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/export-snapshot.sh [name]
# Creates a binary dump (backups/<name>.dump) and Cypher export (snapshots/<name>.cypher)

NAME="${1:-latest}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUPS_DIR="$PROJECT_DIR/backups"
SNAPSHOTS_DIR="$PROJECT_DIR/snapshots"

mkdir -p "$BACKUPS_DIR" "$SNAPSHOTS_DIR"

echo "=== Neo4j Snapshot: $NAME ==="

# --- Step 1: Binary dump (requires Neo4j stopped) ---
echo ""
echo "Stopping Neo4j..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" stop neo4j

# Detect the data volume name dynamically
VOLUME_NAME=$(docker volume ls --filter "name=neo4j_data" -q | head -1)
if [ -z "$VOLUME_NAME" ]; then
    echo "ERROR: No neo4j_data volume found. Is Neo4j running via docker compose?"
    exit 1
fi
echo "Using volume: $VOLUME_NAME"

echo "Creating binary dump..."
docker run --rm \
    -v "$VOLUME_NAME:/data" \
    -v "$BACKUPS_DIR:/backups" \
    neo4j/neo4j-admin:5-community \
    neo4j-admin database dump neo4j --to-path=/backups --overwrite-destination=true

# Fix ownership (dump is created as neo4j UID 7474) and rename
docker run --rm -v "$BACKUPS_DIR:/backups" alpine chown -R "$(id -u):$(id -g)" /backups
if [ -f "$BACKUPS_DIR/neo4j.dump" ]; then
    mv "$BACKUPS_DIR/neo4j.dump" "$BACKUPS_DIR/$NAME.dump"
fi
echo "Binary dump: $BACKUPS_DIR/$NAME.dump ($(du -h "$BACKUPS_DIR/$NAME.dump" | cut -f1))"

# --- Step 2: Restart Neo4j ---
echo ""
echo "Starting Neo4j..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" start neo4j

# --- Step 3: Wait for healthcheck ---
echo "Waiting for Neo4j healthcheck..."
for i in $(seq 1 30); do
    if docker exec llmitm_neo4j cypher-shell -u neo4j -p password "RETURN 1" >/dev/null 2>&1; then
        echo "Neo4j is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: Neo4j did not become ready in 30 attempts."
        exit 1
    fi
    sleep 2
done

# --- Step 4: APOC Cypher export ---
echo ""
echo "Exporting Cypher snapshot..."
docker exec llmitm_neo4j cypher-shell -u neo4j -p password \
    "CALL apoc.export.cypher.all('/import/snapshots/$NAME.cypher', {format: 'cypher-shell'})" \
    2>/dev/null

# --- Step 5: Strip schema lines (setup_schema.py is source of truth) ---
if [ -f "$SNAPSHOTS_DIR/$NAME.cypher" ]; then
    sed -i '/^CREATE CONSTRAINT/d; /^CREATE INDEX/d; /^CREATE VECTOR INDEX/d; /^:schema/d' \
        "$SNAPSHOTS_DIR/$NAME.cypher"
    echo "Cypher export: $SNAPSHOTS_DIR/$NAME.cypher ($(du -h "$SNAPSHOTS_DIR/$NAME.cypher" | cut -f1))"
else
    echo "WARNING: Cypher export file not found. APOC export may have failed."
fi

# --- Step 6: Summary ---
echo ""
echo "=== Summary ==="
NODES=$(docker exec llmitm_neo4j cypher-shell -u neo4j -p password \
    "MATCH (n) RETURN count(n) AS count" 2>/dev/null | tail -1)
RELS=$(docker exec llmitm_neo4j cypher-shell -u neo4j -p password \
    "MATCH ()-[r]->() RETURN count(r) AS count" 2>/dev/null | tail -1)
echo "Nodes: $NODES"
echo "Relationships: $RELS"
echo "Binary dump: backups/$NAME.dump"
echo "Cypher export: snapshots/$NAME.cypher"
echo "Done."
