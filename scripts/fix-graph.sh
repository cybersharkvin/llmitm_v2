#!/usr/bin/env bash
set -euo pipefail
echo "=== Restoring ActionGraph Step 6 ==="
docker exec llmitm_neo4j cypher-shell -u neo4j -p password \
    "MATCH (s:Step {order: 6})
     SET s.command = replace(s.command, '/api/Users/1/bogus-subpath', '/api/Users/1')
     RETURN s.order, substring(s.command, 0, 80) AS command_preview"
echo "Step 6 restored."
