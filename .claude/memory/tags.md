# Code Architecture Overview

## Plugin Architecture

### Abstract Base Classes

### Concrete Implementations
- **ActionGraph** extends `BaseModel` (`llmitm_v2/models/action_graph.py:11`)
- **CompilationContext** extends `BaseModel` (`llmitm_v2/models/context.py:49`)
- **CriticFeedback** extends `BaseModel` (`llmitm_v2/models/critic.py:10`)
- **ExecutionContext** extends `BaseModel` (`llmitm_v2/models/context.py:11`)
- **FailureType** extends `str, Enum` (`llmitm_v2/constants.py:26`)
- **Finding** extends `BaseModel` (`llmitm_v2/models/finding.py:9`)
- **Fingerprint** extends `BaseModel` (`llmitm_v2/models/fingerprint.py:9`)
- **RepairContext** extends `BaseModel` (`llmitm_v2/models/context.py:64`)
- **RepairDiagnosis** extends `BaseModel` (`llmitm_v2/models/critic.py:21`)
- **Settings** extends `BaseSettings` (`llmitm_v2/config.py:6`)
- **Step** extends `BaseModel` (`llmitm_v2/models/step.py:10`)
- **StepPhase** extends `str, Enum` (`llmitm_v2/constants.py:6`)
- **StepResult** extends `BaseModel` (`llmitm_v2/models/context.py:28`)
- **StepType** extends `str, Enum` (`llmitm_v2/constants.py:16`)

### Factory Functions

## All Classes
- **ActionGraph** (`llmitm_v2/models/action_graph.py:11`)
- **CompilationContext** (`llmitm_v2/models/context.py:49`)
- **CriticFeedback** (`llmitm_v2/models/critic.py:10`)
- **ExecutionContext** (`llmitm_v2/models/context.py:11`)
- **FailureType** (`llmitm_v2/constants.py:26`)
- **Finding** (`llmitm_v2/models/finding.py:9`)
- **Fingerprint** (`llmitm_v2/models/fingerprint.py:9`)
- **GraphRepository** (`llmitm_v2/repository/graph_repository.py:11`)
- **RepairContext** (`llmitm_v2/models/context.py:64`)
- **RepairDiagnosis** (`llmitm_v2/models/critic.py:21`)
- **Settings** (`llmitm_v2/config.py:6`)
- **Step** (`llmitm_v2/models/step.py:10`)
- **StepPhase** (`llmitm_v2/constants.py:6`)
- **StepResult** (`llmitm_v2/models/context.py:28`)
- **StepType** (`llmitm_v2/constants.py:16`)

## All Functions
- **setup_schema**() (`llmitm_v2/repository/setup_schema.py:8`)
- **tx_func**(tx: Session) (`llmitm_v2/repository/graph_repository.py:89`)
- **tx_func**(tx: Session) (`llmitm_v2/repository/graph_repository.py:133`)
- **tx_func**(tx: Session) (`llmitm_v2/repository/graph_repository.py:265`)
- **tx_func**(tx: Session) (`llmitm_v2/repository/graph_repository.py:30`)
- **tx_func**(tx: Session) (`llmitm_v2/repository/graph_repository.py:309`)
- **tx_func**(tx: Session) (`llmitm_v2/repository/graph_repository.py:422`)
- **tx_func**(tx: Session) (`llmitm_v2/repository/graph_repository.py:218`)
- **tx_func**(tx: Session) (`llmitm_v2/repository/graph_repository.py:63`)

## All Methods
- **__init__**(self, driver: Driver) (`llmitm_v2/repository/graph_repository.py:14`)
- **compute_hash**(self) (`llmitm_v2/models/fingerprint.py:32`)
- **ensure_hash**(self) (`llmitm_v2/models/fingerprint.py:41`)
- **ensure_id**(self) (`llmitm_v2/models/action_graph.py:36`)
- **ensure_id**(self) (`llmitm_v2/models/finding.py:32`)
- **find_similar_fingerprints**( self, embedding: List[float], top_k: int = 5, ) (`llmitm_v2/repository/graph_repository.py:74`)
- **get_action_graph_with_steps**( self, fingerprint_hash: str, ) (`llmitm_v2/repository/graph_repository.py:203`)
- **get_fingerprint_by_hash**(self, hash_value: str) (`llmitm_v2/repository/graph_repository.py:53`)
- **increment_execution_count**( self, action_graph_id: str, succeeded: bool, ) (`llmitm_v2/repository/graph_repository.py:410`)
- **repair_step_chain**( self, action_graph_id: str, failed_step_order: int, new_steps: List[Step], ) (`llmitm_v2/repository/graph_repository.py:292`)
- **save_action_graph**( self, fingerprint_hash: str, action_graph: ActionGraph, ) (`llmitm_v2/repository/graph_repository.py:111`)
- **save_finding**( self, action_graph_id: str, finding: Finding, ) (`llmitm_v2/repository/graph_repository.py:252`)
- **save_fingerprint**(self, fingerprint: Fingerprint) (`llmitm_v2/repository/graph_repository.py:22`)
- **success_rate**(self) (`llmitm_v2/models/action_graph.py:41`)
