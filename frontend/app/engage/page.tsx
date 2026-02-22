import Link from "next/link";
import styles from "../redditdemand.module.css";
import { getActiveThreads, type ActiveThread } from "../lib/api";

type SearchParamsInput = Record<string, string | string[] | undefined>;

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return value ?? "";
}

function formatVelocity(v: number): string {
  if (v >= 1) return `${v.toFixed(1)}/hr`;
  return `${(v * 60).toFixed(0)}/min`;
}

function ThreadCard({ thread }: { thread: ActiveThread }) {
  const redditUrl = thread.url ?? `https://reddit.com/r/${thread.subreddit}/`;
  return (
    <article className={styles.engageThreadCard}>
      <div className={styles.engageThreadHead}>
        <span className={styles.engageSubreddit}>r/{thread.subreddit}</span>
        <span className={styles.engageVelocityBadge}>
          {thread.recent_comments} comments · {formatVelocity(thread.velocity)}
        </span>
      </div>
      <p className={styles.engageThreadTitle}>{thread.title}</p>
      <div className={styles.engageThreadMeta}>
        <span>~{thread.estimated_impressions.toLocaleString()} est. impressions</span>
        <a
          href={redditUrl}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.engageThreadLink}
        >
          View on Reddit →
        </a>
      </div>
    </article>
  );
}

export default async function EngagePage({
  searchParams,
}: {
  searchParams: Promise<SearchParamsInput>;
}) {
  const params = await searchParams;
  const query = firstParam(params.q).trim() || "your topic";

  const data = await getActiveThreads(query, 24, 3, 20).catch(() => null);

  const hasData = data !== null && data.active_count > 0;
  const noDb = data === null;

  return (
    <main className={styles.page}>
      <header className={styles.topBar}>
        <div className={styles.topBarInner}>
          <Link
            href={`/results?q=${encodeURIComponent(query)}&screen=trend`}
            className={styles.topHomeButton}
          >
            ← Back to Results
          </Link>
        </div>
      </header>

      <section className={`${styles.shell} ${styles.section}`}>
        <h1 className={styles.resultsHeading}>Engagement Campaign: {query}</h1>
        <p className={styles.engagePageSub}>
          Reply to active threads and reach people already discussing this topic.
        </p>

        {/* Impression Estimate */}
        <div className={styles.engageBlock}>
          <h2 className={styles.engageBlockTitle}>Estimated Reach</h2>
          <div className={styles.engageStatRow}>
            <div className={styles.engageStat}>
              <span className={styles.engageStatValue}>
                {noDb ? "—" : data.active_count}
              </span>
              <span className={styles.engageStatLabel}>Active threads</span>
            </div>
            <div className={styles.engageStat}>
              <span className={styles.engageStatValue}>
                {noDb ? "—" : `~${data.total_estimated_impressions.toLocaleString()}`}
              </span>
              <span className={styles.engageStatLabel}>Est. impressions</span>
            </div>
            <div className={styles.engageStat}>
              <span className={styles.engageStatValue}>
                {noDb || !hasData ? "—" : `${data.window_hours}h`}
              </span>
              <span className={styles.engageStatLabel}>Activity window</span>
            </div>
          </div>
          {noDb && (
            <p className={styles.engagePlaceholderText} style={{ marginTop: "0.75rem" }}>
              Connect a database to see live reach estimates.
            </p>
          )}
        </div>

        {/* Active Threads */}
        <div className={styles.engageBlock}>
          <h2 className={styles.engageBlockTitle}>Active Threads</h2>
          <p className={styles.engageBlockSub}>
            Posts about <strong>{query}</strong> with recent comment activity — ranked by velocity.
          </p>

          {noDb && (
            <div className={styles.engagePlaceholderCard}>
              <span className={styles.engagePlaceholderLabel}>No database connected</span>
              <p className={styles.engagePlaceholderText}>
                Set <code>DATABASE_URL</code> and ingest the ZST data to see active threads.
              </p>
            </div>
          )}

          {!noDb && !hasData && (
            <div className={styles.engagePlaceholderCard}>
              <span className={styles.engagePlaceholderLabel}>No active threads found</span>
              <p className={styles.engagePlaceholderText}>
                No posts had recent comment activity. Try a broader query.
              </p>
            </div>
          )}

          {data !== null && data.active_count > 0 && (
            <div className={styles.engageThreadList}>
              {data.threads.map((thread) => (
                <ThreadCard key={thread.id} thread={thread} />
              ))}
            </div>
          )}
        </div>

        {/* Reply Composer */}
        <div className={styles.engageBlock}>
          <h2 className={styles.engageBlockTitle}>Reply Composer</h2>
          <p className={styles.engageBlockSub}>
            Select a thread above, then draft your reply — or let AI write one for you.
          </p>

          <div className={styles.engageComposer}>
            <div className={styles.engageComposerTabs}>
              <span className={`${styles.engageComposerTab} ${styles.engageComposerTabActive}`}>
                AI Draft
              </span>
              <span className={styles.engageComposerTab}>Write my own</span>
            </div>
            <textarea
              className={styles.engageTextarea}
              rows={5}
              placeholder={
                hasData
                  ? "Select a thread above to generate an AI-drafted reply…"
                  : "No active threads to reply to yet."
              }
              disabled
            />
            <div className={styles.engageComposerActions}>
              <button className={styles.engagePostButton} disabled>
                Post Reply
              </button>
              <span className={styles.engagePostNote}>
                Reddit API integration coming soon
              </span>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
