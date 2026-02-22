"use client";

import { useState } from "react";
import styles from "@/app/redditdemand.module.css";
import { draftReply, type ActiveThread } from "@/app/lib/api";

type Tab = "ai" | "manual";

function formatVelocity(v: number): string {
  if (v >= 1) return `${v.toFixed(1)}/hr`;
  return `${(v * 60).toFixed(0)}/min`;
}

export default function ReplyComposer({
  threads,
  query,
}: {
  threads: ActiveThread[];
  query: string;
}) {
  const [selected, setSelected] = useState<ActiveThread | null>(null);
  const [tab, setTab] = useState<Tab>("ai");
  const [businessIdea, setBusinessIdea] = useState(query);
  const [aiDraft, setAiDraft] = useState("");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  function selectThread(thread: ActiveThread) {
    setSelected(thread);
    setAiDraft("");
    setText("");
    setError(null);
  }

  async function handleAiDraft() {
    if (!selected || !businessIdea.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const draft = await draftReply(selected.title, selected.subreddit, businessIdea.trim());
      setAiDraft(draft);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate draft.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    const toCopy = tab === "ai" ? aiDraft : text;
    if (!toCopy.trim()) return;
    await navigator.clipboard.writeText(toCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <>
      {/* Thread list with selection */}
      <div className={styles.engageThreadList}>
        {threads.map((thread) => {
          const redditUrl = thread.url ?? `https://reddit.com/r/${thread.subreddit}/`;
          const isSelected = selected?.id === thread.id;
          return (
            <article
              key={thread.id}
              className={`${styles.engageThreadCard} ${isSelected ? styles.engageThreadCardSelected : ""}`.trim()}
            >
              <div className={styles.engageThreadHead}>
                <span className={styles.engageSubreddit}>r/{thread.subreddit}</span>
                <span className={styles.engageVelocityBadge}>
                  {thread.recent_comments} comments · {formatVelocity(thread.velocity)}
                </span>
              </div>
              <p className={styles.engageThreadTitle}>{thread.title}</p>
              <div className={styles.engageThreadMeta}>
                <span>~{thread.estimated_impressions.toLocaleString()} est. impressions</span>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  <a
                    href={redditUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.engageThreadLink}
                  >
                    View →
                  </a>
                  <button
                    type="button"
                    className={styles.engageSelectButton}
                    onClick={() => selectThread(thread)}
                  >
                    {isSelected ? "Selected ✓" : "Reply to this"}
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>

      {/* Reply Composer */}
      <div className={styles.engageComposer} style={{ marginTop: "1.5rem" }}>
        {selected ? (
          <p className={styles.engageBlockSub}>
            Replying to: <strong>r/{selected.subreddit}</strong> —{" "}
            {selected.title.slice(0, 80)}{selected.title.length > 80 ? "…" : ""}
          </p>
        ) : (
          <p className={styles.engageBlockSub}>Select a thread above to start composing.</p>
        )}

        <div className={styles.engageComposerTabs}>
          <button
            type="button"
            className={`${styles.engageComposerTab} ${tab === "ai" ? styles.engageComposerTabActive : ""}`.trim()}
            onClick={() => setTab("ai")}
          >
            AI Draft
          </button>
          <button
            type="button"
            className={`${styles.engageComposerTab} ${tab === "manual" ? styles.engageComposerTabActive : ""}`.trim()}
            onClick={() => setTab("manual")}
          >
            Write my own
          </button>
        </div>

        {tab === "ai" && (
          <>
            <label className={styles.engageBlockSub} style={{ display: "block", marginBottom: "0.25rem" }}>
              Your business idea or topic
            </label>
            <textarea
              className={styles.engageTextarea}
              rows={2}
              value={businessIdea}
              onChange={(e) => setBusinessIdea(e.target.value)}
              placeholder="e.g. invoicing software for freelancers"
              disabled={!selected || loading}
              style={{ marginBottom: "0.75rem" }}
            />
            <button
              type="button"
              className={styles.engagePostButton}
              style={{ alignSelf: "flex-start" }}
              disabled={!selected || !businessIdea.trim() || loading}
              onClick={handleAiDraft}
            >
              {loading ? "Generating…" : "Generate AI Draft"}
            </button>
            <label className={styles.engageBlockSub} style={{ display: "block", marginTop: "1rem", marginBottom: "0.25rem" }}>
              AI-generated reply
            </label>
            <textarea
              className={styles.engageTextarea}
              rows={5}
              value={aiDraft}
              onChange={(e) => setAiDraft(e.target.value)}
              placeholder="Your generated reply will appear here. You can edit it before copying."
              disabled={!selected || loading}
            />
          </>
        )}

        {tab === "manual" && (
          <textarea
            className={styles.engageTextarea}
            rows={5}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={!selected ? "Select a thread above to start composing…" : "Write your reply here…"}
            disabled={!selected}
          />
        )}

        {error && (
          <p style={{ color: "#c0392b", fontSize: "0.85rem", margin: 0 }}>{error}</p>
        )}

        <div className={styles.engageComposerActions}>
          <button
            type="button"
            className={styles.engagePostButton}
            disabled={loading || (tab === "ai" ? !aiDraft.trim() : !text.trim())}
            onClick={handleCopy}
          >
            {copied ? "Copied!" : "Copy Reply"}
          </button>
        </div>
      </div>
    </>
  );
}
