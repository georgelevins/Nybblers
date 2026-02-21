"use client";

import { useState } from "react";
import {
  runAgent,
  type AgentAction,
  type AgentResponse,
  type IdeaCard,
  type EvidenceItem,
} from "../lib/api";
import styles from "../redditdemand.module.css";

const AGENT_OPTIONS: { action: AgentAction; label: string }[] = [
  { action: "flesh_out_idea", label: "Flesh out" },
  { action: "refine_idea", label: "Refine" },
  { action: "rank_idea", label: "Rank" },
];

function IdeaCardBlock({ card }: { card: IdeaCard }) {
  const fields = [
    { key: "problem", label: "Problem", value: card.problem },
    { key: "customer", label: "Customer", value: card.customer },
    { key: "solution", label: "Solution", value: card.solution },
    { key: "differentiator", label: "Differentiator", value: card.differentiator },
    { key: "monetization", label: "Monetization", value: card.monetization },
  ] as const;
  return (
    <div className={styles.agentCardBlock}>
      {fields.map(
        (f) =>
          f.value && (
            <div key={f.key} className={styles.agentField}>
              <span className={styles.agentFieldLabel}>{f.label}</span>
              <span className={styles.agentFieldValue}>{f.value}</span>
            </div>
          )
      )}
    </div>
  );
}

function EvidenceList({ items }: { items: EvidenceItem[] }) {
  if (!items.length) return null;
  return (
    <div className={styles.agentEvidence}>
      <span className={styles.agentEvidenceTitle}>Evidence (Reddit data)</span>
      <ul className={styles.agentEvidenceList}>
        {items.map((e, i) => (
          <li key={i} className={styles.agentEvidenceItem}>
            <blockquote className={styles.agentQuote}>{e.quote}</blockquote>
            <span className={styles.agentWhy}>{e.why_it_matters}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ResultView({ data }: { data: AgentResponse }) {
  const { idea_card, outputs, evidence, action } = data;
  const rating = typeof outputs?.rating === "number" ? outputs.rating : null;
  const rationale = typeof outputs?.rationale === "string" ? outputs.rationale : null;
  const strengths = Array.isArray(outputs?.strengths) ? (outputs.strengths as string[]) : [];
  const weaknesses = Array.isArray(outputs?.weaknesses) ? (outputs.weaknesses as string[]) : [];

  return (
    <div className={styles.agentResult}>
      {action === "rank_idea" && rating !== null && (
        <div className={styles.agentRatingRow}>
          <span className={styles.agentRatingLabel}>Rating</span>
          <span className={styles.agentRatingValue}>{rating}/10</span>
        </div>
      )}
      {rationale && <p className={styles.agentRationale}>{rationale}</p>}
      {strengths.length > 0 && (
        <div className={styles.agentListBlock}>
          <span className={styles.agentListLabel}>Strengths</span>
          <ul className={styles.agentList}>
            {strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}
      {weaknesses.length > 0 && (
        <div className={styles.agentListBlock}>
          <span className={styles.agentListLabel}>Weaknesses</span>
          <ul className={styles.agentList}>
            {weaknesses.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
      {(idea_card?.problem || idea_card?.solution) && (
        <IdeaCardBlock card={idea_card} />
      )}
      <EvidenceList items={evidence} />
    </div>
  );
}

export default function AgentPanel() {
  const [idea, setIdea] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleRun(action: AgentAction) {
    const text = idea.trim();
    if (!text) {
      setError("Enter an idea first.");
      return;
    }
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data = await runAgent(action, text);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className={styles.agentSection}>
      <h2 className={styles.agentHeading}>Validate with AI</h2>
      <p className={styles.agentSub}>
        Flesh out, refine, or rank your idea using Reddit demand data.
      </p>
      <div className={styles.agentForm}>
        <input
          className={styles.agentInput}
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          placeholder="e.g. Duolingo for card games"
          aria-label="Your idea"
          disabled={loading}
        />
        <div className={styles.agentButtons}>
          {AGENT_OPTIONS.map(({ action, label }) => (
            <button
              key={action}
              type="button"
              className={styles.agentButton}
              onClick={() => handleRun(action)}
              disabled={loading}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      {loading && <p className={styles.agentStatus}>Running…</p>}
      {error && <p className={styles.agentError}>{error}</p>}
      {result && !loading && <ResultView data={result} />}
    </section>
  );
}
