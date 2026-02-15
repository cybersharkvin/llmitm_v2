import { useState, useEffect, useCallback } from "react";
import { BrainGraph } from "./components/BrainGraph";
import { SystemPanel } from "./components/SystemPanel";
import { Legend } from "./components/Legend";
import { createSSEClient, type SSEEventType } from "./lib/sse-client";
import {
  emptyGraph,
  buildGraphFromRunStart,
  applyStepStart,
  applyStepResult,
  applyFailure,
  applyRepairStart,
} from "./lib/graph-builder";
import type { GraphData, WorkflowEvent, RunMeta } from "./lib/schemas";
import type {
  RunStartEvent,
  StepStartEvent,
  StepResultEvent,
  CompileIterEvent,
  CriticResultEvent,
  FailureEvent,
  RunEndEvent,
} from "./lib/schemas";
import "./App.css";

const INITIAL_META: RunMeta = { status: "IDLE", path: "-", compileStatus: "", fingerprintHash: "" };

export default function App() {
  const [graphData, setGraphData] = useState<GraphData>(emptyGraph());
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [runMeta, setRunMeta] = useState<RunMeta>(INITIAL_META);
  const [isRunning, setIsRunning] = useState(false);
  const [canBreak, setCanBreak] = useState(false);
  const [targetProfile, setTargetProfile] = useState<"juice_shop" | "nodegoat" | "dvwa">("juice_shop");
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const pushEvent = useCallback((msg: string, nodeId = "", nodeName = "") => {
    setEvents((prev) => [
      { timestamp: Date.now(), nodeId, nodeName, type: "status_change", from: "idle", to: "idle", message: msg },
      ...prev.slice(0, 49),
    ]);
  }, []);

  const handleEvent = useCallback(
    (eventType: SSEEventType, data: unknown) => {
      switch (eventType) {
        case "connected":
          pushEvent("Connected to monitor");
          break;

        case "compile_iter": {
          const e = data as CompileIterEvent;
          setRunMeta((m) => ({ ...m, status: "COMPILING", compileStatus: `Iteration ${e.iteration + 1}...` }));
          pushEvent(`Compiling — iteration ${e.iteration + 1}`);
          break;
        }

        case "critic_result": {
          const e = data as CriticResultEvent;
          setRunMeta((m) => ({ ...m, compileStatus: `Critic: ${e.exploits.join(", ")}` }));
          pushEvent(`Critic approved: ${e.exploits.join(", ")}`);
          break;
        }

        case "run_start": {
          const e = data as RunStartEvent;
          setGraphData(buildGraphFromRunStart(e));
          setRunMeta((m) => ({
            ...m,
            status: "EXECUTING",
            path: e.path,
            fingerprintHash: e.fingerprint_hash,
            compileStatus: "",
          }));
          pushEvent(`Run started (${e.path}, ${e.steps.length} steps)`);
          break;
        }

        case "step_start": {
          const e = data as StepStartEvent;
          setGraphData((prev) => applyStepStart(prev, e.order));
          pushEvent(`Step ${e.order} started`, `step_${e.order}`);
          break;
        }

        case "step_result": {
          const e = data as StepResultEvent;
          setGraphData((prev) => applyStepResult(prev, e.order, e.matched));
          pushEvent(`Step ${e.order} ${e.matched ? "completed" : "failed"}`, `step_${e.order}`);
          break;
        }

        case "failure": {
          const e = data as FailureEvent;
          setGraphData((prev) => applyFailure(prev, e.step, e.type));
          pushEvent(`Step ${e.step} failure: ${e.type}`, `step_${e.step}`);
          break;
        }

        case "repair_start": {
          setGraphData((prev) => applyRepairStart(prev));
          setRunMeta((m) => ({ ...m, status: "REPAIR" }));
          pushEvent("Self-repair initiated");
          break;
        }

        case "run_end": {
          const e = data as RunEndEvent;
          setRunMeta((m) => ({ ...m, status: "IDLE" }));
          setIsRunning(false);

          if (e.success && e.path === "warm_start" && !e.repaired) {
            setCanBreak(true);
          } else if (e.path === "repair") {
            setCanBreak(false);
          }

          pushEvent(`Run complete: ${e.success ? "SUCCESS" : "FAILED"}, ${e.findings_count} findings`);
          break;
        }
      }
    },
    [pushEvent],
  );

  useEffect(() => {
    const cleanup = createSSEClient("/api/events", handleEvent);
    return cleanup;
  }, [handleEvent]);

  // ── Control Handlers ──
  const handleStart = useCallback(async () => {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_profile: targetProfile,
        mode: "file",
        traffic_file: `demo/${targetProfile}.mitm`,
      }),
    });
    if (res.ok) {
      setIsRunning(true);
      setCanBreak(false);
      pushEvent("Orchestrator started");
    }
  }, [targetProfile, pushEvent]);

  const handleStop = useCallback(async () => {
    await fetch("/api/stop", { method: "POST" });
    setIsRunning(false);
    pushEvent("Orchestrator stopped");
  }, [pushEvent]);

  const handleBreak = useCallback(async () => {
    await fetch("/api/break", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_profile: targetProfile,
        mode: "file",
      }),
    });
    setCanBreak(false);
    pushEvent("Graph corrupted - next run will trigger repair");
  }, [targetProfile, pushEvent]);

  const handleResetClick = useCallback(() => {
    setShowResetConfirm(true);
  }, []);

  const handleResetConfirm = useCallback(async () => {
    setShowResetConfirm(false);
    await fetch("/api/reset", { method: "POST" });
    setGraphData(emptyGraph());
    setEvents([]);
    setSelectedNode(null);
    setRunMeta(INITIAL_META);
    setIsRunning(false);
    setCanBreak(false);
    pushEvent("Neo4j reset complete");
  }, [pushEvent]);

  const handleResetCancel = useCallback(() => {
    setShowResetConfirm(false);
  }, []);

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedNode((prev) => (prev === nodeId ? null : nodeId));
  }, []);

  const handleTargetChange = useCallback((profile: string) => {
    setTargetProfile(profile as "juice_shop" | "nodegoat" | "dvwa");
  }, []);

  // Derived counts
  const activeCount = graphData.nodes.filter((n) => n.status === "active").length;
  const completedCount = graphData.nodes.filter((n) => n.status === "completed").length;
  const errorCount = graphData.nodes.filter((n) => n.status === "error").length;

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1 className="app-title">LLMitM MONITOR</h1>
        </div>
        <div className="header-right">
          <span className={`status-dot ${runMeta.status === "IDLE" ? "idle" : "running"}`} />
          <span className="status-text">{runMeta.status}</span>
        </div>
      </header>

      <div className="subtitle-bar">
        Path: {runMeta.path} · Fingerprint: {runMeta.fingerprintHash.slice(0, 8) || "-"} ·{" "}
        {graphData.nodes.length} nodes
      </div>

      <div className="main-content">
        <div className="viz-container">
          <BrainGraph graphData={graphData} selectedNode={selectedNode} onNodeClick={handleNodeClick} />
          <Legend />
        </div>

        <SystemPanel
          nodes={graphData.nodes}
          activeCount={activeCount}
          completedCount={completedCount}
          errorCount={errorCount}
          totalEdges={graphData.links.length}
          events={events}
          selectedNode={selectedNode}
          isRunning={isRunning}
          canBreak={canBreak}
          targetProfile={targetProfile}
          runMeta={runMeta}
          onStart={handleStart}
          onStop={handleStop}
          onBreak={handleBreak}
          onReset={handleResetClick}
          onTargetChange={handleTargetChange}
        />
      </div>

      {/* Reset Confirmation Dialog */}
      {showResetConfirm && (
        <div className="dialog-overlay" onClick={handleResetCancel}>
          <div className="dialog-content" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-title">Reset Neo4j Database?</div>
            <div className="dialog-message">
              This will delete all ActionGraphs, Fingerprints, Findings, and repair history. This action
              cannot be undone.
            </div>
            <div className="dialog-actions">
              <button className="dialog-btn cancel" onClick={handleResetCancel}>
                Cancel
              </button>
              <button className="dialog-btn confirm" onClick={handleResetConfirm}>
                Reset Database
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
