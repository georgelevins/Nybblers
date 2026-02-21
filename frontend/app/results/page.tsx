import Link from "next/link";
import CopyContextButton from "../components/CopyContextButton";
import ViewTabs from "../components/ViewTabs";
import styles from "../redditdemand.module.css";
import { getThreads, type ResultsView } from "../lib/redditDemandData";

type SearchParamsInput = Record<string, string | string[] | undefined>;

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return value ?? "";
}

function resolveView(value: string): ResultsView {
  return value === "opportunity" ? "opportunity" : "demand";
}

export default async function ResultsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParamsInput>;
}) {
  const params = await searchParams;
  const query = firstParam(params.q).trim();
  const view = resolveView(firstParam(params.view));
  const threads = getThreads(view);

  return (
    <main className={styles.page}>
      <header className={styles.topBar}>
        <div className={styles.topBarInner}>
          {/* home button sits to the left of the search box */}
          <Link href="/home" className={styles.topHomeButton}>
            Home
          </Link>
          <form action="/results" className={`${styles.searchForm} ${styles.compactSearch}`}>
            <input
              className={styles.searchInput}
              name="q"
              defaultValue={query}
              placeholder="Search demand..."
              aria-label="Search demand"
            />
            <input type="hidden" name="view" value={view} />
            <button type="submit" className={styles.searchButton}>
              Search
            </button>
          </form>
        </div>
      </header>

      <section className={`${styles.shell} ${styles.section}`}>
        <ViewTabs
          active={view}
          query={query}
          className={styles.tabs}
          tabClassName={styles.tab}
          activeClassName={styles.tabActive}
        />

        <p className={styles.resultsCount}>
          {threads.length} threads matched · sorted by{" "}
          {view === "opportunity" ? "heat score" : "relevance"}
        </p>

        <div className={styles.cards}>
          {threads.map((thread) => (
            <article key={thread.title} className={styles.card}>
              <h2 className={styles.cardTitle}>{thread.title}</h2>
              <div className={styles.meta}>
                <span className={styles.subreddit}>{thread.subreddit}</span>
                <span>{thread.age}</span>
                <span>{thread.comments} comments</span>
                {thread.ranksOnGoogle ? (
                  <span className={`${styles.badge} ${styles.badgeGoogle}`}>Ranks on Google</span>
                ) : null}
                {thread.active ? (
                  <span className={`${styles.badge} ${styles.badgeActive}`}>Active</span>
                ) : null}
              </div>
              <p className={styles.snippet}>{thread.snippet}</p>
              <div className={styles.cardFooter}>
                <div className={styles.heatRow}>
                  <span>Heat</span>
                  <span className={styles.heatTrack}>
                    <span
                      className={styles.heatFill}
                      style={{ width: `${thread.heat}%`, display: "block" }}
                    />
                  </span>
                  <span className={styles.heatValue}>{thread.heat}</span>
                </div>

                <div className={styles.actions}>
                  {view === "opportunity" ? (
                    <CopyContextButton
                      className={styles.ghostButton}
                      title={thread.title}
                      summary={thread.summary}
                    />
                  ) : null}
                  <Link
                    href={thread.url}
                    className={styles.ghostButton}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View thread
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
