.PHONY: up down schema reset snapshot restore snapshot-baseline restore-baseline test run run-live break-graph fix-graph seed run-nodegoat run-dvwa break-graph-nodegoat break-graph-dvwa monitor monitor-stop monitor-logs

NAME ?= latest
PYTHON ?= .venv/bin/python3

up:
	docker compose up -d
	@echo "Waiting for Neo4j healthcheck..."
	@for i in $$(seq 1 30); do \
		docker exec llmitm_neo4j cypher-shell -u neo4j -p password "RETURN 1" >/dev/null 2>&1 && break; \
		sleep 2; \
	done
	@echo "Neo4j is ready."

down:
	docker compose down

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

monitor:
	@mkdir -p logs
	@echo "🚀 Starting LLMitM Monitor..."
	@echo ""
	@echo "Starting Flask SSE backend..."
	@MONITOR=true $(PYTHON) -m llmitm_v2 > logs/orchestrator.log 2>&1 &
	@echo $$! > logs/orchestrator.pid
	@sleep 2
	@echo "Starting Vite frontend..."
	@cd frontend && npm run dev > ../logs/frontend.log 2>&1 &
	@echo $$! > logs/frontend.pid
	@sleep 4
	@echo ""
	@echo "✅ Monitor ready!"
	@echo ""
	@echo "   🌐 Frontend:  http://localhost:5173"
	@echo "   🔌 Backend:   http://localhost:5001/health"
	@echo ""
	@echo "📋 Commands:"
	@echo "   make monitor-logs  - View logs"
	@echo "   make monitor-stop  - Stop monitor"
	@echo ""
	@xdg-open http://localhost:5173 2>/dev/null || open http://localhost:5173 2>/dev/null || true

monitor-stop:
	@echo "🛑 Stopping monitor..."
	@-[ -f logs/orchestrator.pid ] && kill $$(cat logs/orchestrator.pid) 2>/dev/null || true
	@-[ -f logs/frontend.pid ] && kill $$(cat logs/frontend.pid) 2>/dev/null || true
	@-pkill -f "vite" 2>/dev/null || true
	@-pkill -f "llmitm_v2.*MONITOR" 2>/dev/null || true
	@-rm -f logs/*.pid
	@echo "✅ Monitor stopped"

monitor-logs:
	@echo "📊 Orchestrator logs (Ctrl+C to exit):"
	@echo "========================================"
	@tail -f logs/orchestrator.log logs/frontend.log 2>/dev/null || echo "No logs yet. Run 'make monitor' first."
