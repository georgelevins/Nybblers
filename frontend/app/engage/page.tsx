import Link from "next/link";
import styles from "../redditdemand.module.css";

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

  return (
    <main className={styles.page}>
      <header className={styles.topBar}>
        <div className={styles.topBarInner}>
          <Link href={`/results?q=${encodeURIComponent(query)}&screen=trend`} className={styles.topHomeButton}>
            ← Back to Results
          </Link>
        </div>
      </header>

      <section className={`${styles.shell} ${styles.section}`}>
        <h1 className={styles.resultsHeading}>Engagement Campaign: {query}</h1>
        <p className={styles.engagePageSub}>
          Find active threads and reply with a targeted message — manually or AI-assisted.
        </p>

        {/* Active Threads */}
        <div className={styles.engageBlock}>
          <h2 className={styles.engageBlockTitle}>Active Threads</h2>
          <p className={styles.engageBlockSub}>
            Threads with recent comment activity that match your topic will appear here.
          </p>
          <div className={styles.engagePlaceholderCard}>
            <span className={styles.engagePlaceholderLabel}>Thread detection coming soon</span>
            <p className={styles.engagePlaceholderText}>
              We&rsquo;ll surface posts with ≥3 comments in the last 24 hours that are semantically
              similar to <strong>{query}</strong>.
            </p>
          </div>
        </div>

        {/* Reply Composer */}
        <div className={styles.engageBlock}>
          <h2 className={styles.engageBlockTitle}>Reply Composer</h2>
          <p className={styles.engageBlockSub}>
            Choose a thread above, then draft your reply — or let the AI write one for you.
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
              placeholder="Select a thread above to generate an AI-drafted reply..."
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

        {/* Impression Estimate */}
        <div className={styles.engageBlock}>
          <h2 className={styles.engageBlockTitle}>Impression Estimate</h2>
          <p className={styles.engageBlockSub}>
            Estimated reach for your campaign based on post activity.
          </p>
          <div className={styles.engageStatRow}>
            <div className={styles.engageStat}>
              <span className={styles.engageStatValue}>—</span>
              <span className={styles.engageStatLabel}>Active threads</span>
            </div>
            <div className={styles.engageStat}>
              <span className={styles.engageStatValue}>—</span>
              <span className={styles.engageStatLabel}>Est. impressions</span>
            </div>
            <div className={styles.engageStat}>
              <span className={styles.engageStatValue}>—</span>
              <span className={styles.engageStatLabel}>Avg. thread velocity</span>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
