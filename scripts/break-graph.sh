#!/usr/bin/env bash
set -euo pipefail
echo "=== Breaking ActionGraph Step 6 ==="
docker exec llmitm_neo4j cypher-shell -u neo4j -p password \
    "MATCH (s:Step {order: 6})
     SET s.command = replace(s.command, '/api/Users/1', '/api/Users/1/bogus-subpath')
     RETURN s.order, substring(s.command, 0, 80) AS command_preview"
echo "Step 6 corrupted. Run 'make run' to trigger self-repair."
