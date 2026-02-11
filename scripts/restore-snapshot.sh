#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/restore-snapshot.sh [name]
# Restores from a binary dump (backups/<name>.dump) and applies schema

NAME="${1:-latest}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUPS_DIR="$PROJECT_DIR/backups"
DUMP_FILE="$BACKUPS_DIR/$NAME.dump"

if [ ! -f "$DUMP_FILE" ]; then
    echo "ERROR: Dump file not found: $DUMP_FILE"
    echo "Available snapshots:"
    ls -1 "$BACKUPS_DIR"/*.dump 2>/dev/null || echo "  (none)"
    exit 1
fi

echo "=== Neo4j Restore: $NAME ==="

# --- Step 1: Stop Neo4j ---
echo ""
echo "Stopping Neo4j..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" stop neo4j

# Detect the data volume name dynamically
VOLUME_NAME=$(docker volume ls --filter "name=neo4j_data" -q | head -1)
if [ -z "$VOLUME_NAME" ]; then
    echo "ERROR: No neo4j_data volume found."
    exit 1
fi
echo "Using volume: $VOLUME_NAME"

# --- Step 2: Load binary dump ---
echo ""
echo "Loading binary dump..."

# Copy dump file to expected name for neo4j-admin
cp "$DUMP_FILE" "$BACKUPS_DIR/neo4j.dump"

docker run --rm \
    -v "$VOLUME_NAME:/data" \
    -v "$BACKUPS_DIR:/backups" \
    neo4j/neo4j-admin:5-community \
    neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true

# Clean up the copy
rm -f "$BACKUPS_DIR/neo4j.dump"

echo "Binary dump loaded."

# --- Step 3: Start Neo4j ---
echo ""
echo "Starting Neo4j..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" start neo4j

# --- Step 4: Wait for healthcheck ---
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

# --- Step 5: Apply schema (source of truth: setup_schema.py) ---
echo ""
echo "Applying schema (setup_schema.py)..."
NEO4J_URI=bolt://localhost:7687 \
NEO4J_USERNAME=neo4j \
NEO4J_PASSWORD=password \
NEO4J_DATABASE=neo4j \
ANTHROPIC_API_KEY=dummy \
TARGET_URL=http://localhost:3000 \
    python3 -m llmitm_v2.repository.setup_schema

# --- Step 6: Summary ---
echo ""
echo "=== Summary ==="
NODES=$(docker exec llmitm_neo4j cypher-shell -u neo4j -p password \
    "MATCH (n) RETURN count(n) AS count" 2>/dev/null | tail -1)
RELS=$(docker exec llmitm_neo4j cypher-shell -u neo4j -p password \
    "MATCH ()-[r]->() RETURN count(r) AS count" 2>/dev/null | tail -1)
echo "Nodes: $NODES"
echo "Relationships: $RELS"
echo "Restored from: backups/$NAME.dump"
echo "Done."
