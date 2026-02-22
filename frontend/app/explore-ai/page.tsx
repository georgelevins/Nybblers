"use client";

import { useCallback, useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import styles from "../redditdemand.module.css";
import {
  runAgent,
  getTopMatches,
  topMatchesToRetrievalMatches,
  type AgentResponse,
  type IdeaCard,
  type EvidenceItem,
} from "../lib/api";

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
  const wellOptimisedMessage =
    typeof outputs?.well_optimised_message === "string" ? (outputs.well_optimised_message as string) : null;
  const enhancedIdeaText =
    typeof outputs?.enhanced_idea_text === "string" ? (outputs.enhanced_idea_text as string) : null;
  const originalTraction =
    typeof outputs?.original_traction === "number" ? (outputs.original_traction as number) : null;
  const enhancedTraction =
    typeof outputs?.enhanced_traction === "number" ? (outputs.enhanced_traction as number) : null;
  const dbUsed = outputs?.db_used === true;

  return (
    <div className={styles.agentResult}>
      {enhanceError && <p className={styles.agentError}>{outputs.enhance_error as string}</p>}
      {enhanceSuggested && enhancedIdeaText && (
        <div className={styles.agentListBlock}>
          <span className={styles.agentListLabel}>New idea (from Remand + AI)</span>
          <p className={styles.agentRationale}>{enhancedIdeaText}</p>
        </div>
      )}
      {wellOptimisedMessage && (
        <p className={styles.agentRationale}>{wellOptimisedMessage}</p>
      )}
      {!enhanceSuggested && !enhanceError && !wellOptimisedMessage && enhancedIdeaText && (
        <p className={styles.agentRationale}>
          We tested an enhanced variant but it didn’t get better traction than your idea. Your idea is strong as-is.
        </p>
      )}
      {enhancedIdeaText && !enhanceSuggested && !enhanceError && !wellOptimisedMessage && (
        <p className={styles.agentRationale} style={{ marginTop: "0.5rem" }}>
          <strong>Enhanced variant (not suggested):</strong> {enhancedIdeaText}
        </p>
      )}
      {originalTraction !== null && (
        <p className={styles.agentRationale} style={{ marginTop: "0.5rem", fontSize: "0.9em" }}>
          Your idea traction: <strong>{originalTraction.toFixed(1)}</strong>
          {enhancedTraction !== null && (
            <>
              {" "}
              · Enhanced traction: <strong>{enhancedTraction.toFixed(1)}</strong>
            </>
          )}
        </p>
      )}
      {rationale && <p className={styles.agentRationale}>{rationale}</p>}
      {!dbUsed && (
        <p className={styles.agentRationale} style={{ marginTop: "0.5rem", fontSize: "0.85em", opacity: 0.9 }}>
          Referenced Remand-style context; traction comparison uses DB when connected.
        </p>
      )}
      {(idea_card?.problem || idea_card?.solution) && <IdeaCardBlock card={idea_card} />}
      <EvidenceList items={evidence} />
    </div>
  );
}

function EnhanceIdeaContent() {
  const searchParams = useSearchParams();
  const q = searchParams.get("q")?.trim() ?? "";

  const [idea, setIdea] = useState(q);
  const [loading, setLoading] = useState(!!q);
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hasRun, setHasRun] = useState(false);

  const runEnhance = useCallback(async (ideaText: string) => {
    const text = ideaText.trim();
    if (!text) {
      setError("Enter an idea first.");
      return;
    }
    setError(null);
    setResult(null);
    setLoading(true);
    setHasRun(true);
    try {
      let retrievalMatches: ReturnType<typeof topMatchesToRetrievalMatches> = [];
      try {
        const matches = await getTopMatches(text, 15);
        retrievalMatches = topMatchesToRetrievalMatches(matches);
      } catch {
        // Search/DB may be unavailable; agent will use context or mock
      }
      const data = await runAgent("enhance_idea", text, retrievalMatches);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }, []);

  // When landing with ?q=, run once on mount
  useEffect(() => {
    if (!q || hasRun) return;
    runEnhance(q);
  }, [q, hasRun, runEnhance]);

  // Sync idea field when q changes (e.g. user came from results)
  useEffect(() => {
    if (q) setIdea(q);
  }, [q]);

  return (
    <main className={styles.page}>
      <section className={styles.blankAiPage}>
        <div className={styles.enhanceAiWrap}>
          <h1 className={styles.blankAiTitle}>Enhance idea with AI</h1>
          <p className={styles.blankAiSub}>
            We use the Remand demand signal (and DB when connected) to refine your idea and suggest a stronger variant.
          </p>

          {!q && (
            <div className={styles.agentForm} style={{ marginTop: "1.25rem", maxWidth: "32rem", marginLeft: "auto", marginRight: "auto" }}>
              <input
                className={styles.agentInput}
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                placeholder="e.g. Tool for freelancers to track time"
                aria-label="Your idea"
                disabled={loading}
              />
              <div className={styles.agentButtons} style={{ marginTop: "0.75rem" }}>
                <button
                  type="button"
                  className={styles.agentButton}
                  onClick={() => runEnhance(idea)}
                  disabled={loading}
                >
                  Enhance idea
                </button>
              </div>
            </div>
          )}

          {loading && (
            <div className={styles.enhanceAiLoading} aria-live="polite">
              <span className={styles.enhanceAiSpinner} aria-hidden />
              <p>AI is refining your idea against Remand demand…</p>
            </div>
          )}

          {error && <p className={styles.agentError} style={{ marginTop: "1rem" }}>{error}</p>}
          {result && !loading && (
            <div className={styles.enhanceAiResult}>
              <ResultView data={result} />
            </div>
          )}

          <p style={{ marginTop: "2rem", fontSize: "0.9rem" }}>
            <Link
              href={q ? `/results?q=${encodeURIComponent(q)}` : "/results"}
              className={styles.exploreAiLink}
            >
              ← Back to results
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}

export default function EnhanceIdeaPage() {
  return (
    <Suspense
      fallback={
        <main className={styles.page}>
          <section className={styles.blankAiPage}>
            <h1 className={styles.blankAiTitle}>Enhance idea with AI</h1>
            <p className={styles.blankAiSub}>Loading…</p>
          </section>
        </main>
      }
    >
      <EnhanceIdeaContent />
    </Suspense>
  );
}
