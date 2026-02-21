import styles from "@/app/redditdemand.module.css";
import type { TopMatch } from "@/app/lib/api";

type TopCommentsScreenProps = {
  query: string;
  matches: TopMatch[];
};

export default function TopCommentsScreen({ query, matches }: TopCommentsScreenProps) {
  if (matches.length === 0) {
    return (
      <section className={styles.visualCard}>
        <div className={styles.visualHeader}>
          <h2 className={styles.visualTitle}>Top Relevant Reddit Mentions</h2>
          <p className={styles.visualSub}>
            No matching discussions found for <strong>{query}</strong>.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.visualCard}>
      <div className={styles.visualHeader}>
        <h2 className={styles.visualTitle}>
          Top {matches.length} Most Relevant Reddit Mentions
        </h2>
        <p className={styles.visualSub}>
          Direct evidence for <strong>{query}</strong>: who said what, and where it was posted.
        </p>
      </div>

      <div className={styles.quoteList}>
        {matches.map((item, index) => {
          const relevancePct = Math.round(item.similarity * 100);
          const redditUrl = item.url
            ? item.url
            : `https://www.reddit.com/r/${item.subreddit}/`;
          return (
            <article key={item.id} className={styles.quoteCard}>
              <div className={styles.quoteHead}>
                <span className={styles.quoteRank}>#{index + 1}</span>
                <div className={styles.quoteMeta}>
                  <span className={styles.subreddit}>r/{item.subreddit}</span>
                  {item.author && <span>u/{item.author}</span>}
                  <span className={styles.quoteType}>{item.kind}</span>
                </div>
                <span className={styles.relevanceBadge}>{relevancePct}% match</span>
              </div>

              <p className={styles.quoteText}>
                &ldquo;{item.body.slice(0, 300)}{item.body.length > 300 ? "…" : ""}&rdquo;
              </p>

              <a
                href={redditUrl}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.quoteLink}
              >
                View on Reddit
              </a>
            </article>
          );
        })}
      </div>
    </section>
  );
}
