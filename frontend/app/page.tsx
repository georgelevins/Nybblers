import Link from "next/link";
import styles from "./redditdemand.module.css";
import { EXAMPLE_SEARCHES } from "./lib/redditDemandData";

export default function Home() {
  return (
    <main className={`${styles.page} ${styles.homePage}`}>
      <section className={styles.homeWrap}>
        <h1 className={styles.wordmark}>RedditDemand</h1>
        <p className={styles.tagline}>Signal from the Noise</p>

        <form action="/results" className={styles.searchForm}>
          <input
            className={styles.searchInput}
            name="q"
            placeholder="e.g. invoicing software for freelancers..."
            aria-label="Search Reddit demand"
            autoComplete="off"
          />
          <input type="hidden" name="view" value="demand" />
          <button className={styles.searchButton} type="submit">
            Search
          </button>
        </form>

        <div className={styles.examples}>
          {EXAMPLE_SEARCHES.map((example) => (
            <Link
              key={example}
              href={`/results?q=${encodeURIComponent(example)}&view=demand`}
              className={styles.examplePill}
            >
              {example}
            </Link>
          ))}
        </div>

        <p className={styles.ticker}>
          23 million comments indexed across 28 subreddits
        </p>
      </section>
    </main>
  );
}
