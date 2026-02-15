import type { GraphNode, WorkflowEvent, RunMeta } from "../lib/schemas";

interface Props {
  nodes: GraphNode[];
  activeCount: number;
  completedCount: number;
  errorCount: number;
  totalEdges: number;
  events: WorkflowEvent[];
  selectedNode: string | null;
  isRunning: boolean;
  canBreak: boolean;
  targetProfile: string;
  runMeta: RunMeta;
  onStart: () => void;
  onStop: () => void;
  onBreak: () => void;
  onReset: () => void;
  onTargetChange: (profile: string) => void;
}

const STATUS_BADGE: Record<string, { color: string; label: string }> = {
  idle: { color: "#334455", label: "IDLE" },
  active: { color: "#ff69b4", label: "ACTIVE" },
  completed: { color: "#44ff88", label: "DONE" },
  error: { color: "#ff3333", label: "ERROR" },
};

const TYPE_LABELS: Record<string, string> = {
  http_request: "HTTP",
  shell_command: "Shell",
  regex_match: "Regex",
};

function timeAgo(ts: number): string {
  const diff = Math.floor((Date.now() - ts) / 1000);
  if (diff < 1) return "just now";
  if (diff < 60) return `${diff}s ago`;
  return `${Math.floor(diff / 60)}m ago`;
}

export function SystemPanel({
  nodes,
  activeCount,
  completedCount,
  errorCount,
  totalEdges,
  events,
  selectedNode,
  isRunning,
  canBreak,
  targetProfile,
  runMeta,
  onStart,
  onStop,
  onBreak,
  onReset,
  onTargetChange,
}: Props) {
  const selected = selectedNode ? nodes.find((n) => n.id === selectedNode) : null;
  const progress = nodes.length > 0 ? (completedCount / nodes.length) * 100 : 0;

  return (
    <div className="system-panel">
      {/* Controls */}
      <div className="panel-section">
        <div className="panel-title">CONTROLS</div>

        <div className="control-group">
          <label className="control-label">Target:</label>
          <select
            className="target-select"
            value={targetProfile}
            onChange={(e) => onTargetChange(e.target.value)}
            disabled={isRunning}
          >
            <option value="juice_shop">OWASP Juice Shop</option>
            <option value="nodegoat">OWASP NodeGoat</option>
            <option value="dvwa">DVWA</option>
          </select>
        </div>

        <div className="controls-row">
          {!isRunning ? (
            <button className="ctrl-btn start" onClick={onStart}>
              &#9654; RUN
            </button>
          ) : (
            <button className="ctrl-btn stop" onClick={onStop}>
              &#9632; STOP
            </button>
          )}
          {canBreak && (
            <button className="ctrl-btn break" onClick={onBreak}>
              &#9888; BREAK
            </button>
          )}
          <button className="ctrl-btn reset" onClick={onReset}>
            &#8635; RESET
          </button>
        </div>
      </div>

      {/* Compile Status (conditional) */}
      {runMeta.compileStatus && (
        <div className="panel-section">
          <div className="panel-title">COMPILE STATUS</div>
          <div className="state-value">{runMeta.compileStatus}</div>
        </div>
      )}

      {/* System State */}
      <div className="panel-section">
        <div className="panel-title">SYSTEM STATE</div>
        <div className="state-grid">
          <span className="state-label">Status:</span>
          <span className={`state-value ${isRunning ? "glow-green" : ""}`}>{runMeta.status}</span>

          <span className="state-label">Path:</span>
          <span className="state-value">{runMeta.path}</span>

          <span className="state-label">Nodes:</span>
          <span className="state-value">{nodes.length}</span>

          <span className="state-label">Edges:</span>
          <span className="state-value">{totalEdges}</span>

          <span className="state-label">Active:</span>
          <span className="state-value glow-pink">{activeCount}</span>

          <span className="state-label">Completed:</span>
          <span className="state-value glow-green">{completedCount}</span>

          <span className="state-label">Errors:</span>
          <span className={`state-value ${errorCount > 0 ? "glow-red" : ""}`}>{errorCount}</span>
        </div>

        {/* Progress bar */}
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
          {errorCount > 0 && (
            <div
              className="progress-error"
              style={{
                width: `${(errorCount / nodes.length) * 100}%`,
                left: `${progress}%`,
              }}
            />
          )}
        </div>
        <div className="progress-label">
          {completedCount}/{nodes.length} completed
        </div>
      </div>

      {/* Node Detail (if selected) */}
      {selected && (
        <div className="panel-section highlight">
          <div className="panel-title">NODE DETAIL</div>
          <div className="node-detail">
            <div className="node-detail-name">{selected.name}</div>
            <div className="node-detail-row">
              <span className="state-label">Type:</span>
              <span className="type-badge">{TYPE_LABELS[selected.type] || selected.type}</span>
            </div>
            <div className="node-detail-row">
              <span className="state-label">Phase:</span>
              <span className="state-value">{selected.group.toUpperCase()}</span>
            </div>
            <div className="node-detail-row">
              <span className="state-label">Status:</span>
              <span className="status-badge" style={{ background: STATUS_BADGE[selected.status]?.color }}>
                {STATUS_BADGE[selected.status]?.label}
              </span>
            </div>
            {selected.errorMsg && <div className="error-msg">{selected.errorMsg}</div>}
          </div>
        </div>
      )}

      {/* Node List */}
      <div className="panel-section">
        <div className="panel-title">NODES ({nodes.length})</div>
        <div className="node-list">
          {nodes.map((n) => (
            <div key={n.id} className={`node-row ${selectedNode === n.id ? "selected" : ""} ${n.status}`}>
              <span className="node-dot" style={{ background: STATUS_BADGE[n.status]?.color }} />
              <span className="node-name">{n.name}</span>
              <span className="node-status-mini">{STATUS_BADGE[n.status]?.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Event Feed */}
      <div className="panel-section">
        <div className="panel-title">EVENT LOG</div>
        <div className="event-feed">
          {events.length === 0 && <div className="event-empty">No events yet. Hit RUN.</div>}
          {events.map((evt, i) => (
            <div key={i} className={`event-row ${evt.type}`}>
              <span className="event-time">{timeAgo(evt.timestamp)}</span>
              <span className="event-msg">{evt.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
