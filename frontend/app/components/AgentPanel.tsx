"use client";

import { useState } from "react";
import {
  runAgent,
  type AgentAction,
  type AgentResponse,
  type IdeaCard,
  type EvidenceItem,
  type RetrievalMatch,
} from "../lib/api";
import styles from "../redditdemand.module.css";

const AGENT_OPTIONS: { action: AgentAction; label: string }[] = [
  { action: "enhance_idea", label: "AI Enhance" },
];

type AgentPanelProps = {
  /** Pre-fill the idea input (e.g. from the search query on the results page). */
  initialIdea?: string;
  /** Real Reddit matches from the search — passed to the agent as retrieval context. */
  retrievalMatches?: RetrievalMatch[];
};

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
          ),
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
  const { idea_card, outputs, evidence } = data;
  const rationale = typeof outputs?.rationale === "string" ? outputs.rationale : null;
  const enhanceSuggested = outputs?.suggested === true;
  const enhanceError = typeof outputs?.enhance_error === "string";
  const enhancedIdeaText = typeof outputs?.enhanced_idea_text === "string" ? (outputs.enhanced_idea_text as string) : null;
  const originalTraction = typeof outputs?.original_traction === "number" ? (outputs.original_traction as number) : null;
  const enhancedTraction = typeof outputs?.enhanced_traction === "number" ? (outputs.enhanced_traction as number) : null;

  return (
    <div className={styles.agentResult}>
      {enhanceError && <p className={styles.agentError}>{outputs.enhance_error as string}</p>}
      {enhanceSuggested && enhancedIdeaText && (
        <div className={styles.agentListBlock}>
          <span className={styles.agentListLabel}>Suggested idea (more Reddit traction)</span>
          <p className={styles.agentRationale}>{enhancedIdeaText}</p>
        </div>
      )}
      {!enhanceSuggested && !enhanceError && enhancedIdeaText && (
        <p className={styles.agentRationale}>
          We tested an enhanced variant but it didn’t get better traction than your idea. Your idea is strong as-is.
        </p>
      )}
      {enhancedIdeaText && !enhanceSuggested && !enhanceError && (
        <p className={styles.agentRationale} style={{ marginTop: "0.5rem" }}><strong>Enhanced variant (not suggested):</strong> {enhancedIdeaText}</p>
      )}
      {originalTraction !== null && enhancedTraction !== null && (
        <p className={styles.agentRationale} style={{ marginTop: "0.5rem", fontSize: "0.9em" }}>
          Your idea traction: <strong>{originalTraction.toFixed(1)}</strong> · Enhanced traction: <strong>{enhancedTraction.toFixed(1)}</strong>
        </p>
      )}
      {rationale && <p className={styles.agentRationale}>{rationale}</p>}
      {(idea_card?.problem || idea_card?.solution) && (
        <IdeaCardBlock card={idea_card} />
      )}
      <EvidenceList items={evidence} />
    </div>
  );
}

export default function AgentPanel({
  initialIdea = "",
  retrievalMatches,
}: AgentPanelProps) {
  const [idea, setIdea] = useState(initialIdea);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const hasContext = retrievalMatches && retrievalMatches.length > 0;

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
      const data = await runAgent(action, text, retrievalMatches);
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
        AI-enhance your idea: we brainstorm a better variant and test both against Reddit demand—only suggest it if it gets more traction.
        {hasContext && (
          <> Using <strong>{retrievalMatches.length}</strong> real Reddit posts as context.</>
        )}
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
