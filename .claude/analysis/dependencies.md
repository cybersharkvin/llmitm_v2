# Internal Dependencies Analysis

## 1. Import Graph

### 1.1 File-by-File Imports

#### llmitm_v2/__init__.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.fingerprinter import Fingerprinter` | internal |

#### llmitm_v2/__main__.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.config import Settings` | internal |
| `from llmitm_v2.target_profiles import get_active_profile` | internal |
| `from llmitm_v2.orchestrator import Orchestrator` | internal |
| `from llmitm_v2.repository import GraphRepository` | internal |
| `from llmitm_v2.repository.setup_schema import setup_schema` | internal |
| `from llmitm_v2.orchestrator.agents import set_token_budget` | internal (conditional) |
| `from llmitm_v2.debug_logger import init_debug_logging, write_summary` | internal (conditional) |

#### llmitm_v2/config.py

| Imports | Type |
|---------|------|
| *(no internal imports)* | — |

#### llmitm_v2/constants.py

| Imports | Type |
|---------|------|
| *(no internal imports)* | — |

#### llmitm_v2/debug_logger.py

| Imports | Type |
|---------|------|
| *(no internal imports)* | — |

#### llmitm_v2/fingerprinter.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.models import Fingerprint` | internal |

#### llmitm_v2/target_profiles.py

| Imports | Type |
|---------|------|
| *(no internal imports)* | — |

#### llmitm_v2/models/__init__.py (re-export facade)

| Imports | Type |
|---------|------|
| `from llmitm_v2.models.action_graph import ActionGraph` | internal |
| `from llmitm_v2.models.context import ExecutionContext, ExecutionResult, OrchestratorResult, StepResult` | internal |
| `from llmitm_v2.models.critic import CriticFeedback, RepairDiagnosis` | internal |
| `from llmitm_v2.models.finding import Finding` | internal |
| `from llmitm_v2.models.fingerprint import Fingerprint` | internal |
| `from llmitm_v2.models.recon import AttackOpportunity, AttackPlan, ExploitTool, ReconTool` | internal |
| `from llmitm_v2.models.step import Step` | internal |

#### llmitm_v2/models/action_graph.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.models.step import Step` | internal |

#### llmitm_v2/models/context.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.models.finding import Finding` | internal |
| `from llmitm_v2.models.fingerprint import Fingerprint` | internal |

#### llmitm_v2/models/critic.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.constants import FailureType` | internal |

#### llmitm_v2/models/finding.py

| Imports | Type |
|---------|------|
| *(no internal imports)* | — |

#### llmitm_v2/models/fingerprint.py

| Imports | Type |
|---------|------|
| *(no internal imports)* | — |

#### llmitm_v2/models/recon.py

| Imports | Type |
|---------|------|
| *(no internal imports)* | — |

#### llmitm_v2/models/step.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.constants import StepPhase, StepType` | internal |

#### llmitm_v2/handlers/__init__.py (re-export facade)

| Imports | Type |
|---------|------|
| `from llmitm_v2.handlers.base import StepHandler` | internal |
| `from llmitm_v2.handlers.http_request_handler import HTTPRequestHandler` | internal |
| `from llmitm_v2.handlers.regex_match_handler import RegexMatchHandler` | internal |
| `from llmitm_v2.handlers.registry import HANDLER_REGISTRY, get_handler` | internal |
| `from llmitm_v2.handlers.shell_command_handler import ShellCommandHandler` | internal |

#### llmitm_v2/handlers/base.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.models.context import ExecutionContext, StepResult` | internal |
| `from llmitm_v2.models.step import Step` | internal |

#### llmitm_v2/handlers/http_request_handler.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.handlers.base import StepHandler` | internal |
| `from llmitm_v2.models.context import ExecutionContext, StepResult` | internal |
| `from llmitm_v2.models.step import Step` | internal |

#### llmitm_v2/handlers/regex_match_handler.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.handlers.base import StepHandler` | internal |
| `from llmitm_v2.models.context import ExecutionContext, StepResult` | internal |
| `from llmitm_v2.models.step import Step` | internal |

#### llmitm_v2/handlers/shell_command_handler.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.handlers.base import StepHandler` | internal |
| `from llmitm_v2.models.context import ExecutionContext, StepResult` | internal |
| `from llmitm_v2.models.step import Step` | internal |

#### llmitm_v2/handlers/registry.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.constants import StepType` | internal |
| `from llmitm_v2.handlers.base import StepHandler` | internal |
| `from llmitm_v2.handlers.http_request_handler import HTTPRequestHandler` | internal |
| `from llmitm_v2.handlers.regex_match_handler import RegexMatchHandler` | internal |
| `from llmitm_v2.handlers.shell_command_handler import ShellCommandHandler` | internal |

#### llmitm_v2/repository/__init__.py (re-export facade)

| Imports | Type |
|---------|------|
| `from llmitm_v2.repository.graph_repository import GraphRepository` | internal |

#### llmitm_v2/repository/graph_repository.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.models import ActionGraph, Finding, Fingerprint, Step` | internal |

#### llmitm_v2/repository/setup_schema.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.config import Settings` | internal |

#### llmitm_v2/tools/__init__.py (re-export facade)

| Imports | Type |
|---------|------|
| `from llmitm_v2.tools.graph_tools import GraphTools` | internal |

#### llmitm_v2/tools/exploit_tools.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.constants import StepPhase, StepType` | internal |
| `from llmitm_v2.models.step import Step` | internal |
| `from llmitm_v2.target_profiles import TargetProfile` | internal |

#### llmitm_v2/tools/graph_tools.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.repository import GraphRepository` | internal |

#### llmitm_v2/tools/recon_tools.py

| Imports | Type |
|---------|------|
| *(no internal imports)* | — |

#### llmitm_v2/orchestrator/__init__.py (re-export facade)

| Imports | Type |
|---------|------|
| `from llmitm_v2.orchestrator.agents import create_attack_critic, create_recon_agent` | internal |
| `from llmitm_v2.orchestrator.context import assemble_recon_context, assemble_repair_context` | internal |
| `from llmitm_v2.orchestrator.failure_classifier import classify_failure` | internal |
| `from llmitm_v2.orchestrator.orchestrator import Orchestrator` | internal |

#### llmitm_v2/orchestrator/agents.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.debug_logger import ToolCallRecord, log_api_call` | internal |
| `from llmitm_v2.tools.recon_tools import TOOL_HANDLERS, TOOL_SCHEMAS` | internal (conditional) |

#### llmitm_v2/orchestrator/context.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.models import Step` | internal |

#### llmitm_v2/orchestrator/failure_classifier.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.constants import FailureType` | internal |

#### llmitm_v2/orchestrator/orchestrator.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.config import Settings` | internal |
| `from llmitm_v2.constants import FailureType, StepPhase` | internal |
| `from llmitm_v2.debug_logger import log_event` | internal |
| `from llmitm_v2.handlers.registry import get_handler` | internal |
| `from llmitm_v2.models import ActionGraph, ExecutionContext, ExecutionResult, Finding, Fingerprint, OrchestratorResult, Step, StepResult` | internal |
| `from llmitm_v2.models.recon import AttackPlan` | internal |
| `from llmitm_v2.orchestrator.agents import create_attack_critic, create_recon_agent` | internal |
| `from llmitm_v2.orchestrator.context import assemble_recon_context, assemble_repair_context` | internal |
| `from llmitm_v2.orchestrator.failure_classifier import classify_failure` | internal |
| `from llmitm_v2.repository import GraphRepository` | internal |
| `from llmitm_v2.target_profiles import TargetProfile, get_active_profile` | internal |
| `from llmitm_v2.tools.exploit_tools import EXPLOIT_STEP_GENERATORS` | internal |

#### llmitm_v2/capture/__init__.py

*(empty)*

#### llmitm_v2/capture/addon.py

| Imports | Type |
|---------|------|
| *(no internal imports)* | — |

#### llmitm_v2/capture/launcher.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.fingerprinter import Fingerprinter` | internal |
| `from llmitm_v2.models.fingerprint import Fingerprint` | internal |

#### llmitm_v2/hooks/__init__.py

*(empty — dead code)*

#### tests/test_fingerprinter.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.fingerprinter import Fingerprinter` | internal |

#### tests/test_graph_repository.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.constants import StepPhase, StepType` | internal |
| `from llmitm_v2.models import ActionGraph, Finding, Fingerprint, Step` | internal |

#### tests/test_handlers.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.constants import StepPhase, StepType` | internal |
| `from llmitm_v2.handlers import HANDLER_REGISTRY, HTTPRequestHandler, RegexMatchHandler, ShellCommandHandler, get_handler` | internal |
| `from llmitm_v2.models import ExecutionContext, Fingerprint, Step, StepResult` | internal |

#### tests/test_models.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.constants import StepPhase, StepType` | internal |
| `from llmitm_v2.models import ActionGraph, CriticFeedback, ExecutionContext, ExecutionResult, Finding, Fingerprint, OrchestratorResult, RepairDiagnosis, Step, StepResult` | internal |

#### tests/test_orchestrator.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.constants import FailureType, StepPhase, StepType` | internal |
| `from llmitm_v2.models import Fingerprint, Step` | internal |
| `from llmitm_v2.orchestrator import assemble_recon_context, assemble_repair_context, classify_failure, create_attack_critic, create_recon_agent` | internal |
| `from llmitm_v2.repository import GraphRepository` | internal (conditional) |

#### tests/test_orchestrator_main.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.constants import StepPhase, StepType` | internal |
| `from llmitm_v2.models import ActionGraph, ExecutionContext, Fingerprint, OrchestratorResult, Step` | internal |
| `from llmitm_v2.orchestrator.orchestrator import Orchestrator` | internal |
| `from llmitm_v2.repository import GraphRepository` | internal (conditional) |

#### tests/test_recon_models.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.models.recon import AttackOpportunity, AttackPlan` | internal |

#### tests/test_target_profiles.py

| Imports | Type |
|---------|------|
| `from llmitm_v2.target_profiles import TARGET_PROFILES, get_active_profile` | internal |
| `from llmitm_v2.tools.exploit_tools import auth_strip_steps, idor_walk_steps, namespace_probe_steps, role_tamper_steps, token_swap_steps` | internal |

---

## 2. Dependency Hotspots

### 2.1 Most Imported Modules

| Module | Import Count | Imported By |
|--------|-------------|-------------|
| `constants` | 9 | models/step, models/critic, handlers/registry, orchestrator/orchestrator, orchestrator/failure_classifier, tools/exploit_tools, + 5 test files |
| `models` (package) | 8 | fingerprinter, handlers/base + 3 impls, orchestrator/orchestrator, repository/graph_repository, capture/launcher, + 6 test files |
| `handlers.base.StepHandler` | 4 | http_request_handler, regex_match_handler, shell_command_handler, registry |
| `config.Settings` | 3 | __main__, orchestrator/orchestrator, repository/setup_schema |
| `target_profiles` | 3 | __main__, orchestrator/orchestrator, tools/exploit_tools |
| `debug_logger` | 3 | __main__, orchestrator/agents, orchestrator/orchestrator |
| `repository.GraphRepository` | 3 | orchestrator/orchestrator, tools/graph_tools, + tests (conditional) |

### 2.2 Import Distribution

| Range | Files | Count |
|-------|-------|-------|
| 0 imports (leaf) | config, constants, debug_logger, target_profiles, models/finding, models/fingerprint, models/recon, tools/recon_tools, capture/addon, capture/__init__, hooks/__init__ | 11 |
| 1–2 imports | fingerprinter, models/action_graph, models/context, models/critic, models/step, orchestrator/context, orchestrator/failure_classifier, tools/graph_tools, capture/launcher | 9 |
| 3–5 imports | handlers/base, http_request_handler, regex_match_handler, shell_command_handler, tools/exploit_tools, orchestrator/agents, repository/graph_repository | 7 |
| 6+ imports | __main__ (7), orchestrator/orchestrator (12) | 2 |

---

## 3. Circular Dependencies

### 3.1 Detected Cycles

**None found.** All dependencies flow strictly downward through the layer hierarchy. The dependency graph is a DAG.

---

## 4. Import Patterns

### 4.1 Re-exports (Barrel Files)

| File | Exports | Purpose |
|------|---------|---------|
| `llmitm_v2/__init__.py` | `Fingerprinter` | Public API |
| `models/__init__.py` | 12 symbols from 7 submodules | Unified model namespace |
| `handlers/__init__.py` | 6 symbols from 5 submodules | Handler ABC + impls + registry |
| `repository/__init__.py` | `GraphRepository` | Persistence entry point |
| `tools/__init__.py` | `GraphTools` | Vector search facade |
| `orchestrator/__init__.py` | 6 symbols from 4 submodules | Agent factories + context + classifier + orchestrator |

### 4.2 Type-Only Imports

None found. All imports are used at runtime.

### 4.3 Conditional / Dynamic Imports

| Import | Location | Trigger |
|--------|----------|---------|
| `set_token_budget` | `__main__.py` | `settings.max_token_budget` is set |
| `init_debug_logging, write_summary` | `__main__.py` | `settings.debug_mode_enabled` |
| `TOOL_HANDLERS, TOOL_SCHEMAS` | `orchestrator/agents.py` | Inside `create_recon_agent()` function body |

### 4.4 Dead Modules (Zero Importers)

| Module | Status |
|--------|--------|
| `hooks/__init__.py` | Dead code — no imports, no functionality |
| `capture/addon.py` | Used by mitmproxy runtime, not imported by project code |

---

## 5. Architecture Insights

### 5.1 Layer Dependencies

```
┌───────────────────────────────────────────────────────────────┐
│  CLI Layer                                                     │
│    __main__.py                                                 │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             v
┌───────────────────────────────────────────────────────────────┐
│  Orchestrator Layer                                            │
│    orchestrator.py, agents.py, context.py, failure_classifier  │
└───┬──────────┬──────────┬──────────┬─────────────────────────┘
    │          │          │          │
    v          v          v          v
┌────────┐ ┌────────┐ ┌────────┐ ┌────────────────────────────┐
│Handlers│ │Reposit.│ │ Tools  │ │ Fingerprinter / Capture    │
│base    │ │graph_  │ │graph_  │ │ fingerprinter.py           │
│http    │ │reposit.│ │tools   │ │ capture/launcher.py        │
│regex   │ │setup_  │ │exploit │ │                            │
│shell   │ │schema  │ │recon   │ │                            │
│registry│ │        │ │tools   │ │                            │
└───┬────┘ └───┬────┘ └───┬────┘ └──────────┬─────────────────┘
    │          │          │                  │
    v          v          v                  v
┌───────────────────────────────────────────────────────────────┐
│  Models Layer                                                  │
│    step, fingerprint, action_graph, context, finding, critic,  │
│    recon                                                       │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             v
┌───────────────────────────────────────────────────────────────┐
│  Foundation Layer (zero internal imports)                       │
│    config.py, constants.py, debug_logger.py, target_profiles   │
└───────────────────────────────────────────────────────────────┘
```

No upward arrows exist. Dependencies flow strictly top-to-bottom.

### 5.2 Coupling Analysis

| Module | Afferent (Ca) | Efferent (Ce) | Instability (Ce/(Ca+Ce)) |
|--------|--------------|--------------|--------------------------|
| constants.py | 9 | 0 | 0.00 (maximally stable) |
| models/ (aggregate) | 15 | 2 | 0.12 |
| config.py | 3 | 0 | 0.00 |
| target_profiles.py | 3 | 0 | 0.00 |
| debug_logger.py | 3 | 0 | 0.00 |
| handlers/base.py | 4 | 2 | 0.33 |
| handlers/registry.py | 2 | 5 | 0.71 |
| repository/graph_repository.py | 3 | 4 | 0.57 |
| tools/exploit_tools.py | 2 | 3 | 0.60 |
| tools/graph_tools.py | 2 | 1 | 0.33 |
| orchestrator/orchestrator.py | 2 | 12 | 0.86 (coordinator) |
| __main__.py | 0 | 7 | 1.00 (entry point) |

### 5.3 Module Boundaries

| Boundary | Clean? | Notes |
|----------|--------|-------|
| Handlers → Models only | Yes | All handlers depend on StepHandler ABC + ExecutionContext + Step. Zero cross-handler imports |
| Repository → Models only | Yes | GraphRepository imports only DTOs. No business logic in repository layer |
| Models → Constants only | Yes | Models import enums from constants. No reverse dependencies |
| Tools → Models + Constants + target_profiles | Yes | No upward imports to orchestrator or handlers |
| Orchestrator → all mid-tier layers | Yes | Expected for coordinator. High efferent coupling by design |
| orchestrator/agents → tools/recon_tools | Marginal | Conditional import inside factory function. Could use DI instead |

---

## Summary

### Dependency Metrics

| Metric | Value |
|--------|-------|
| Source modules | 29 |
| Leaf modules (zero internal imports) | 11 (38%) |
| Circular dependencies | 0 |
| Max efferent coupling | 12 (orchestrator.py) |
| Max afferent coupling | 9 (constants.py) |
| Re-export facades | 6 |
| Conditional imports | 3 |

### Architecture Assessment

**Coupling**: Well-decoupled. High coupling concentrated in the orchestrator coordinator (by design). Foundation and model layers are maximally stable (I = 0.00–0.12).

**Cohesion**: Strong. Related code is grouped into coherent packages. No cross-package leakage.

### Recommendations

1. Delete `hooks/__init__.py` — dead code, zero importers
2. Consider dependency injection for tool registries (`EXPLOIT_STEP_GENERATORS`, `TOOL_HANDLERS`) to improve testability
3. Post-hackathon: split `orchestrator.py` (12 efferent imports) into compilation, execution, and repair sub-coordinators
