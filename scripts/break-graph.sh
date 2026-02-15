#!/usr/bin/env bash
set -euo pipefail

PROFILE="${TARGET_PROFILE:-juice_shop}"
case "$PROFILE" in
    juice_shop) ENDPOINT="/api/Users" ;;
    nodegoat)   ENDPOINT="/allocations" ;;
    dvwa)       ENDPOINT="/vulnerabilities" ;;
    *)          echo "Unknown profile: $PROFILE"; exit 1 ;;
esac

echo "=== Breaking ActionGraph: corrupting HTTP method on $ENDPOINT steps ==="
docker exec llmitm_neo4j cypher-shell -u neo4j -p password \
    "MATCH (ag:ActionGraph)-[:HAS_STEP]->(s:Step)
     WHERE s.parameters CONTAINS '$ENDPOINT'
     SET s.parameters = replace(s.parameters, '\"method\": \"GET\"', '\"method\": \"PATCH\"')
     SET s.command = replace(s.command, 'GET', 'PATCH')
     RETURN s.order, substring(s.command, 0, 80) AS command_preview"
echo "Steps corrupted (GET -> PATCH). Run 'make run' to trigger self-repair."
