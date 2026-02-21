import Link from "next/link";
import ViewTabs from "../components/ViewTabs";
import styles from "../redditdemand.module.css";
import { DEFAULT_ALERTS } from "../lib/redditDemandData";

type SearchParamsInput = Record<string, string | string[] | undefined>;

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return value ?? "";
}

export default async function AlertsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParamsInput>;
}) {
  const params = await searchParams;
  const query = firstParam(params.q).trim();
  const watched = firstParam(params.watch).trim();

  const alerts = [...DEFAULT_ALERTS];
  if (watched) {
    alerts.unshift({
      query: watched,
      detail: "Daily digest · all subreddits",
    });
  }

  return (
    <main className={styles.page}>
      <header className={styles.topBar}>
        <div className={styles.topBarInner}>
          {/* home button to left of search, same adjustment as results page */}
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
            <input type="hidden" name="screen" value="trend" />
            <button type="submit" className={styles.searchButton}>
              Search
            </button>
          </form>
        </div>
      </header>

      <section className={`${styles.shell} ${styles.section}`}>
        <ViewTabs
          active="alerts"
          query={query}
          className={styles.tabs}
          tabClassName={styles.tab}
          activeClassName={styles.tabActive}
        />

        <div className={styles.alertsCard}>
          <h1 className={styles.alertsHeading}>Alerts</h1>
          <p className={styles.alertsSub}>
            Save a query and get notified when new Reddit posts match it.
          </p>

          <form action="/alerts" className={styles.alertForm}>
            <input type="hidden" name="q" value={query} />
            <input
              className={styles.textInput}
              name="watch"
              defaultValue={query}
              placeholder="Search query to watch..."
              aria-label="Search query to watch"
            />
            <div className={styles.row}>
              <input
                className={styles.textInput}
                name="email"
                placeholder="Your email..."
                aria-label="Your email"
              />
              <select
                className={`${styles.textInput} ${styles.selectInput}`}
                name="frequency"
                defaultValue="Daily"
                aria-label="Alert frequency"
              >
                <option>Daily</option>
                <option>Instant</option>
                <option>Weekly</option>
              </select>
              <button className={styles.saveButton} type="submit">
                Save
              </button>
            </div>
          </form>

          <p className={styles.savedLabel}>Active Alerts</p>
          <div className={styles.alertList}>
            {alerts.map((alert) => (
              <article key={`${alert.query}-${alert.detail}`} className={styles.alertItem}>
                <div>
                  <h2 className={styles.alertTitle}>{alert.query}</h2>
                  <p className={styles.alertDetail}>{alert.detail}</p>
                </div>
                <span className={styles.liveDot} />
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
