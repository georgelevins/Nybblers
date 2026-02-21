import Link from "next/link";
import GrowthMomentumScreen from "../components/results/GrowthMomentumScreen";
import MentionsTrendScreen from "../components/results/MentionsTrendScreen";
import SubredditUsersScreen from "../components/results/SubredditUsersScreen";
import TopCommentsScreen from "../components/results/TopCommentsScreen";
import AgentPanel from "../components/AgentPanel";
import styles from "../redditdemand.module.css";
import {
  getMentionsTrend,
  getUsersBySubreddit,
  getTopMatches,
  getGrowthMomentum,
  matchesToRetrieval,
  type TimePoint,
  type TopMatch,
  type GrowthData,
} from "../lib/api";

type SearchParamsInput = Record<string, string | string[] | undefined>;
type ResultsScreen = "trend" | "users" | "growth" | "quotes";

function firstParam(value: string | string[] | undefined): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return value ?? "";
}

function resolveScreen(value: string): ResultsScreen {
  if (value === "users") return "users";
  if (value === "growth") return "growth";
  if (value === "quotes") return "quotes";
  return "trend";
}

function screenHref(query: string, screen: ResultsScreen) {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  params.set("screen", screen);
  return `/results?${params.toString()}`;
}

async function fetchAnalytics(query: string): Promise<{
  points: TimePoint[];
  subreddits: Record<string, string[]>;
  topMatches: TopMatch[];
  growthData: GrowthData;
}> {
  const [points, subreddits, topMatches, growthData] = await Promise.allSettled([
    getMentionsTrend(query),
    getUsersBySubreddit(query),
    getTopMatches(query, 10),
    getGrowthMomentum(query),
  ]);

  return {
    points: points.status === "fulfilled" ? points.value : [],
    subreddits: subreddits.status === "fulfilled" ? subreddits.value : {},
    topMatches: topMatches.status === "fulfilled" ? topMatches.value : [],
    growthData:
      growthData.status === "fulfilled"
        ? growthData.value
        : { weekly: [], monthly: [] },
  };
}

export default async function ResultsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParamsInput>;
}) {
  const params = await searchParams;
  const query = firstParam(params.q).trim() || "micro saas ideas";
  const screen = resolveScreen(firstParam(params.screen));

  const { points, subreddits, topMatches, growthData } = await fetchAnalytics(query);
  const retrievalMatches = matchesToRetrieval(topMatches);

  return (
    <main className={styles.page}>
      <header className={styles.topBar}>
        <div className={styles.topBarInner}>
          <form action="/results" className={`${styles.searchForm} ${styles.compactSearch}`}>
            <input
              className={styles.searchInput}
              name="q"
              defaultValue={query}
              placeholder="Search demand..."
              aria-label="Search demand"
            />
            <input type="hidden" name="screen" value={screen} />
            <button type="submit" className={styles.searchButton}>
              Search
            </button>
          </form>
          <Link href="/home" className={styles.topHomeButton}>
            Home
          </Link>
        </div>
      </header>

      <section className={`${styles.shell} ${styles.section}`}>
        <h1 className={styles.resultsHeading}>Analytics View: {query}</h1>

        <div className={styles.tabs}>
          <Link
            href={screenHref(query, "trend")}
            className={`${styles.tab} ${screen === "trend" ? styles.tabActive : ""}`.trim()}
          >
            1. Topic Mentions
          </Link>
          <Link
            href={screenHref(query, "users")}
            className={`${styles.tab} ${screen === "users" ? styles.tabActive : ""}`.trim()}
          >
            2. Users by Subreddit
          </Link>
          <Link
            href={screenHref(query, "growth")}
            className={`${styles.tab} ${screen === "growth" ? styles.tabActive : ""}`.trim()}
          >
            3. Growth Momentum
          </Link>
          <Link
            href={screenHref(query, "quotes")}
            className={`${styles.tab} ${screen === "quotes" ? styles.tabActive : ""}`.trim()}
          >
            4. Top Comments
          </Link>
        </div>

        {screen === "trend" && <MentionsTrendScreen query={query} points={points} />}
        {screen === "users" && <SubredditUsersScreen query={query} subreddits={subreddits} />}
        {screen === "growth" && <GrowthMomentumScreen query={query} data={growthData} />}
        {screen === "quotes" && <TopCommentsScreen query={query} matches={topMatches} />}

        <AgentPanel
          initialIdea={query}
          retrievalMatches={retrievalMatches}
        />
      </section>
    </main>
  );
}
