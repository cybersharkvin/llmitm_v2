#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/reset-graph.sh
# Wipes all data and recreates schema. Online operation, no restart needed.

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Neo4j Reset ==="

# --- Step 1: Delete all nodes and relationships ---
echo ""
echo "Deleting all nodes and relationships..."
docker exec llmitm_neo4j cypher-shell -u neo4j -p password \
    "MATCH (n) DETACH DELETE n"
echo "All data deleted."

# --- Step 2: Drop all constraints and indexes ---
echo ""
echo "Dropping all constraints and indexes..."
docker exec llmitm_neo4j cypher-shell -u neo4j -p password \
    "CALL apoc.schema.assert({}, {})"
echo "All constraints and indexes dropped."

# --- Step 3: Recreate schema from source of truth ---
echo ""
echo "Recreating schema (setup_schema.py)..."
NEO4J_URI=bolt://localhost:7687 \
NEO4J_USERNAME=neo4j \
NEO4J_PASSWORD=password \
NEO4J_DATABASE=neo4j \
ANTHROPIC_API_KEY=dummy \
TARGET_URL=http://localhost:3000 \
    python3 -m llmitm_v2.repository.setup_schema

echo ""
echo "=== Reset complete ==="
