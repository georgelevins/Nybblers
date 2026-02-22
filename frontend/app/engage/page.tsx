import Link from "next/link";
import styles from "../redditdemand.module.css";
import { getActiveThreads } from "../lib/api";
import ReplyComposer from "../components/engage/ReplyComposer";

type SearchParamsInput = Record<string, string | string[] | undefined>;

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return value ?? "";
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
            href={`/results?q=${encodeURIComponent(query)}`}
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

        {/* Estimated Reach */}
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

        {/* Active Threads + Reply Composer */}
        <div className={styles.engageBlock}>
          <h2 className={styles.engageBlockTitle}>Active Threads</h2>
          <p className={styles.engageBlockSub}>
            Posts about <strong>{query}</strong> with recent comment activity — ranked by velocity.
            Select one to compose a reply.
          </p>

          {noDb && (
            <div className={styles.engagePlaceholderCard}>
              <span className={styles.engagePlaceholderLabel}>No database connected</span>
              <p className={styles.engagePlaceholderText}>
                Set <code>DATABASE_URL</code> and ingest data to see active threads.
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

          {hasData && (
            <ReplyComposer threads={data.threads} query={query} />
          )}
        </div>

        {/* Reply Composer heading (shown when no data) */}
        {!hasData && (
          <div className={styles.engageBlock}>
            <h2 className={styles.engageBlockTitle}>Reply Composer</h2>
            <p className={styles.engageBlockSub}>
              There are no active threads at the moment. Try a different search or check back later.
            </p>
            <div className={styles.engageComposer}>
              <textarea
                className={styles.engageTextarea}
                rows={5}
                placeholder="No active threads to reply to yet."
                disabled
              />
              <div className={styles.engageComposerActions}>
                <button className={styles.engagePostButton} disabled>
                  Copy Reply
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
