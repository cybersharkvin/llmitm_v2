export function Legend() {
  return (
    <div className="legend-panel">
      <div className="legend-title">LEGEND</div>

      <div className="legend-section">
        <div className="legend-section-title">STATUS (GLOW INTENSITY)</div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#fff0e8", boxShadow: "0 0 3px #ff88aa" }} />
          <span>Idle (dim)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot pulse-dot" style={{ background: "#fff0e8", boxShadow: "0 0 10px #ff69b4" }} />
          <span>Active (bright)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#fff0e8", boxShadow: "0 0 6px #ff88aa" }} />
          <span>Completed</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#fff0e8", boxShadow: "0 0 8px #ff3333" }} />
          <span>Error</span>
        </div>
      </div>

      <div className="legend-section">
        <div className="legend-section-title">SPIKE COLORS</div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#ff69b4" }} />
          <span>Pink</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#44ff88" }} />
          <span>Green</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#66ccff" }} />
          <span>Cyan</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#cc66ff" }} />
          <span>Purple</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#ffaa00" }} />
          <span>Amber</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#00cccc" }} />
          <span>Teal</span>
        </div>
      </div>

      <div className="legend-section">
        <div className="legend-section-title">CONNECTION FLOW</div>
        <div className="legend-item">
          <span className="legend-line" style={{ background: "#00ccaa" }} />
          <span>Data Flow</span>
        </div>
        <div className="legend-item">
          <span className="legend-line" style={{ background: "#ff4488" }} />
          <span>Feedback</span>
        </div>
      </div>

      <div className="legend-hint">Click nodes to inspect</div>
    </div>
  );
}
