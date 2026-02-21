import { TOP_RELEVANT_COMMENTS } from "@/app/lib/resultsVisualData";
import styles from "@/app/redditdemand.module.css";

type TopCommentsScreenProps = {
  query: string;
};

export default function TopCommentsScreen({ query }: TopCommentsScreenProps) {
  return (
    <section className={styles.visualCard}>
      <div className={styles.visualHeader}>
        <h2 className={styles.visualTitle}>Top 10 Most Relevant Reddit Mentions</h2>
        <p className={styles.visualSub}>
          Direct evidence for <strong>{query}</strong>: who said what, and where it was posted.
        </p>
      </div>

      <div className={styles.quoteList}>
        {TOP_RELEVANT_COMMENTS.map((item, index) => (
          <article key={`${item.username}-${item.url}`} className={styles.quoteCard}>
            <div className={styles.quoteHead}>
              <span className={styles.quoteRank}>#{index + 1}</span>
              <div className={styles.quoteMeta}>
                <span className={styles.subreddit}>{item.subreddit}</span>
                <span>u/{item.username}</span>
                <span className={styles.quoteType}>{item.kind}</span>
              </div>
              <span className={styles.relevanceBadge}>{item.relevance}% match</span>
            </div>

            <p className={styles.quoteText}>
              This user said: &ldquo;{item.quote}&rdquo;
            </p>

            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.quoteLink}
            >
              View on Reddit
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}
