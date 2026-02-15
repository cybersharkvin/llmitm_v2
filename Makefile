.PHONY: schema reset snapshot restore snapshot-baseline restore-baseline test run run-live break-graph fix-graph seed run-nodegoat run-dvwa break-graph-nodegoat break-graph-dvwa

NAME ?= latest
PYTHON ?= .venv/bin/python3

schema:
	NEO4J_URI=bolt://localhost:7687 \
	NEO4J_USERNAME=neo4j \
	NEO4J_PASSWORD=password \
	NEO4J_DATABASE=neo4j \
	ANTHROPIC_API_KEY=dummy \
	TARGET_URL=http://localhost:3000 \
	$(PYTHON) -m llmitm_v2.repository.setup_schema

reset:
	./scripts/reset-graph.sh

snapshot:
	./scripts/export-snapshot.sh $(NAME)

restore:
	./scripts/restore-snapshot.sh $(NAME)

snapshot-baseline:
	$(MAKE) snapshot NAME=phase5-baseline

restore-baseline:
	$(MAKE) restore NAME=phase5-baseline

test:
	$(PYTHON) -m pytest tests/

run:
	$(PYTHON) -m llmitm_v2

run-live:
	CAPTURE_MODE=live $(PYTHON) -m llmitm_v2

break-graph:
	./scripts/break-graph.sh

fix-graph:
	./scripts/fix-graph.sh

seed:
	$(PYTHON) scripts/seed-demo-graph.py

run-nodegoat:
	TARGET_PROFILE=nodegoat TRAFFIC_FILE=demo/nodegoat.mitm $(PYTHON) -m llmitm_v2

run-dvwa:
	TARGET_PROFILE=dvwa TRAFFIC_FILE=demo/dvwa.mitm $(PYTHON) -m llmitm_v2

break-graph-nodegoat:
	TARGET_PROFILE=nodegoat ./scripts/break-graph.sh

break-graph-dvwa:
	TARGET_PROFILE=dvwa ./scripts/break-graph.sh
