import Link from "next/link";
import HomeSidebarLayout from "../components/home/HomeSidebarLayout";
import SkipProfileModal from "../components/SkipProfileModal";
import styles from "../redditdemand.module.css";
import { EXAMPLE_SEARCHES } from "../lib/redditDemandData";

type SearchParamsInput = Record<string, string | string[] | undefined>;

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return value ?? "";
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<SearchParamsInput>;
}) {
  const params = await searchParams;
  const skippedRaw = firstParam(params.skipped).trim().toLowerCase();
  const showSkippedModal = skippedRaw === "1" || skippedRaw === "true";

  return (
    <main className={styles.page}>
      {showSkippedModal ? <SkipProfileModal /> : null}

      <HomeSidebarLayout>
        <section className={styles.homeWrap}>
          <h1 className={styles.wordmark}>Remand</h1>
          <p className={styles.tagline}>Signal from the Noise</p>

          <form action="/results" className={styles.searchForm}>
            <input
              className={styles.searchInput}
              name="q"
              placeholder="e.g. invoicing software for freelancers..."
              aria-label="Search Reddit demand"
              autoComplete="off"
            />
            <input type="hidden" name="screen" value="trend" />
            <button className={styles.searchButton} type="submit">
              Search
            </button>
          </form>

          <div className={styles.examples}>
            {EXAMPLE_SEARCHES.map((example) => (
              <Link
                key={example}
                href={`/results?q=${encodeURIComponent(example)}&screen=trend`}
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
      </HomeSidebarLayout>
    </main>
  );
}
