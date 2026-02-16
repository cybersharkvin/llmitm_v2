import { useState } from "react";
import type { AttackPlan, AttackOpportunity as AttackOpp } from "../lib/schemas";

interface CompilePanelProps {
  reconPlan: AttackPlan | null;
  criticPlan: AttackPlan | null;
  isCompiling: boolean;
  collapsed: boolean;
  onToggle: () => void;
}

type Tab = "recon" | "critic";

function OpportunityCard({ opp, index }: { opp: AttackOpp; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="opp-card">
      <div className="opp-header" onClick={() => setExpanded(!expanded)}>
        <span className="opp-index">#{index + 1}</span>
        <span className="opp-title">{opp.opportunity}</span>
        <span className="opp-expand">{expanded ? "\u25B2" : "\u25BC"}</span>
      </div>
      <div className="opp-flow">
        <span className="opp-tag recon">{opp.recon_tool_used}</span>
        <span className="opp-arrow">{"\u2192"}</span>
        <span className="opp-tag exploit">{opp.recommended_exploit}</span>
        <code className="opp-target">{opp.exploit_target}</code>
      </div>
      {expanded && (
        <div className="opp-details">
          <div className="opp-field">
            <span className="opp-label">Observation</span>
            <span className="opp-value">{opp.observation}</span>
          </div>
          <div className="opp-field">
            <span className="opp-label">Suspected Gap</span>
            <span className="opp-value">{opp.suspected_gap}</span>
          </div>
          <div className="opp-field">
            <span className="opp-label">Reasoning</span>
            <span className="opp-value">{opp.exploit_reasoning}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export function CompilePanel({ reconPlan, criticPlan, isCompiling, collapsed, onToggle }: CompilePanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("recon");

  const hasPlan = reconPlan || criticPlan;
  if (!hasPlan && !isCompiling) return null;

  if (collapsed) {
    return (
      <div className="compile-panel-tab" onClick={onToggle}>
        <span className="compile-panel-tab-label">Plan</span>
      </div>
    );
  }

  const plan = activeTab === "recon" ? reconPlan : criticPlan;
  const hasRecon = reconPlan !== null;
  const hasCritic = criticPlan !== null;

  return (
    <div className="compile-panel">
      <div className="compile-panel-header" onClick={onToggle}>
        <span className="compile-panel-title">
          {isCompiling ? "\u25C9 Compilation" : "\u25CB Compilation Plan"}
        </span>
        <span className="compile-panel-toggle">{"\u25C0"}</span>
      </div>
      <div className="compile-panel-body">
        <div className="compile-tabs">
          <button
            className={`compile-tab ${activeTab === "recon" ? "active" : ""}`}
            disabled={!hasRecon}
            onClick={() => setActiveTab("recon")}
          >
            Recon Plan {hasRecon ? `(${reconPlan!.attack_plan.length})` : ""}
          </button>
          <button
            className={`compile-tab ${activeTab === "critic" ? "active" : ""}`}
            disabled={!hasCritic}
            onClick={() => setActiveTab("critic")}
          >
            Critic Refined {hasCritic ? `(${criticPlan!.attack_plan.length})` : ""}
          </button>
        </div>
        <div className="compile-content">
          {plan ? (
            plan.attack_plan.map((opp, i) => (
              <OpportunityCard key={i} opp={opp} index={i} />
            ))
          ) : (
            <div className="compile-waiting">
              {isCompiling ? "Waiting for agent output..." : "No plan available"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
