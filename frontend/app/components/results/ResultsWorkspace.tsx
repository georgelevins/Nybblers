"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import styles from "@/app/redditdemand.module.css";
import LineChart from "./LineChart";
import type { GrowthData, TimePoint, TopMatch } from "@/app/lib/api";
import {
  MONTHLY_TOPIC_MENTIONS,
  TOP_RELEVANT_COMMENTS,
  USERS_BY_SUBREDDIT,
  getGrowthRate,
} from "@/app/lib/resultsVisualData";

type CardId = "trend" | "subreddits" | "feedback" | "momentum";

type ResultsWorkspaceProps = {
  query: string;
  points: TimePoint[];
  subreddits: Record<string, string[]>;
  topMatches: TopMatch[];
  growthData: GrowthData;
};

type SubredditStat = {
  name: string;
  mentions: number;
};

const HISTORY_KEY = "remand-query-history";
const SIDEBAR_WIDTH_KEY = "remand-sidebar-width";
const MIN_SIDEBAR_WIDTH = 220;
const MAX_SIDEBAR_WIDTH = 460;

const FALLBACK_MATCHES: TopMatch[] = TOP_RELEVANT_COMMENTS.map((item, index) => ({
  id: `fallback-${index + 1}`,
  subreddit: item.subreddit.replace(/^r\//i, ""),
  author: item.username,
  body: item.quote,
  score: 100 - index,
  url: item.url,
  similarity: item.relevance / 100,
  kind: item.kind,
}));

function resultsHref(query: string) {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  return `/results?${params.toString()}`;
}

function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

function normalizeSubredditStats(source: Record<string, string[]>): SubredditStat[] {
  return Object.entries(source)
    .map(([name, users]) => ({
      name: name.replace(/^r\//i, ""),
      mentions: users.length,
    }))
    .sort((a, b) => b.mentions - a.mentions);
}

export default function ResultsWorkspace({
  query,
  points,
  subreddits,
  topMatches,
  growthData,
}: ResultsWorkspaceProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [isResizing, setIsResizing] = useState(false);
  const [expandedCard, setExpandedCard] = useState<CardId | null>(null);

  useEffect(() => {
    const raw = window.localStorage.getItem(HISTORY_KEY);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    const unique = [query, ...parsed.filter((item) => item.toLowerCase() !== query.toLowerCase())]
      .filter((item) => item.trim().length > 0)
      .slice(0, 20);
    window.localStorage.setItem(HISTORY_KEY, JSON.stringify(unique));
    const timer = window.setTimeout(() => {
      setHistory(unique);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    const raw = window.localStorage.getItem(SIDEBAR_WIDTH_KEY);
    if (!raw) return;
    const value = Number(raw);
    if (!Number.isFinite(value)) return;
    const timer = window.setTimeout(() => {
      setSidebarWidth(Math.min(MAX_SIDEBAR_WIDTH, Math.max(MIN_SIDEBAR_WIDTH, value)));
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!isResizing) return;

    function handleMove(event: MouseEvent) {
      const nextWidth = Math.min(
        MAX_SIDEBAR_WIDTH,
        Math.max(MIN_SIDEBAR_WIDTH, event.clientX),
      );
      setSidebarWidth(nextWidth);
    }

    function handleUp() {
      setIsResizing(false);
    }

    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleUp);
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";

    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseup", handleUp);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
    };
  }, [isResizing]);

  useEffect(() => {
    window.localStorage.setItem(SIDEBAR_WIDTH_KEY, String(sidebarWidth));
  }, [sidebarWidth]);

  const sidebarHistory = useMemo(
    () => history.filter((item) => item.toLowerCase() !== query.toLowerCase()),
    [history, query],
  );

  const trendPoints = points.length > 0 ? points : MONTHLY_TOPIC_MENTIONS;
  const momentumPoints =
    growthData.monthly.length > 0
      ? growthData.monthly
      : growthData.weekly.length > 0
        ? growthData.weekly
        : MONTHLY_TOPIC_MENTIONS;

  const feedbackMatches = (topMatches.length > 0 ? topMatches : FALLBACK_MATCHES).slice(0, 10);

  const subredditStats = useMemo(
    () =>
      normalizeSubredditStats(
        Object.keys(subreddits).length > 0 ? subreddits : USERS_BY_SUBREDDIT,
      ),
    [subreddits],
  );

  const totalSubredditMentions = subredditStats.reduce((sum, item) => sum + item.mentions, 0);
  const maxSubredditMentions = subredditStats[0]?.mentions ?? 1;

  const trendTotal = trendPoints.reduce((sum, item) => sum + item.value, 0);
  const momentumGrowth = getGrowthRate(momentumPoints);

  const layoutStyle = {
    gridTemplateColumns: collapsed
      ? "0px minmax(0, 1fr)"
      : `${sidebarWidth}px minmax(0, 1fr)`,
  };

  return (
    <div
      className={`${styles.resultsWorkspace} ${collapsed ? styles.resultsWorkspaceCollapsed : ""}`.trim()}
      style={layoutStyle}
    >
      <aside
        className={`${styles.resultsSidebar} ${collapsed ? styles.resultsSidebarCollapsed : ""}`.trim()}
      >
        <Link href="/home" className={styles.sidebarBrand}>
          Remand
        </Link>
        <button
          type="button"
          className={styles.sidebarToggle}
          onClick={() => setCollapsed(true)}
        >
          Collapse sidebar
        </button>

        {!collapsed && (
          <>
            <p className={styles.sidebarLabel}>Search History</p>
            <div className={styles.sidebarHistory}>
              {sidebarHistory.length === 0 ? (
                <p className={styles.sidebarEmpty}>No previous searches yet.</p>
              ) : (
                sidebarHistory.map((item) => (
                  <Link
                    key={item}
                    href={resultsHref(item)}
                    className={styles.sidebarHistoryItem}
                  >
                    {item}
                  </Link>
                ))
              )}
            </div>
          </>
        )}
        {!collapsed && (
          <button
            type="button"
            aria-label="Resize sidebar"
            className={styles.sidebarResizer}
            onMouseDown={(event) => {
              event.preventDefault();
              setIsResizing(true);
            }}
          />
        )}
      </aside>

      {collapsed && (
        <button
          type="button"
          className={styles.sidebarOpenButton}
          onClick={() => setCollapsed(false)}
        >
          Open sidebar
        </button>
      )}

      <section className={styles.resultsMain}>
        <div className={styles.resultsToolbar}>
          <h1 className={styles.resultsReportTitle}>
            Report: <span>{query}</span>
          </h1>

          <form action="/results" className={styles.resultsMiniSearch}>
            <input
              className={styles.resultsMiniInput}
              name="q"
              defaultValue={query}
              aria-label="Search demand"
              placeholder="Search..."
            />
            <button type="submit" className={styles.resultsMiniButton}>
              Search
            </button>
          </form>

          <Link href="/explore-ai" className={styles.exploreAiLink}>
            Explore with AI
          </Link>
        </div>

        <div className={styles.engageCta}>
          <p className={styles.engageCtaText}>
            Some of these posts may still be active.{" "}
            <a href={`/engage?q=${encodeURIComponent(query)}`} className={styles.engageLink}>
              Run an engagement campaign →
            </a>
          </p>
        </div>

        <div className={styles.resultsPanelsViewport}>
          <div className={styles.resultsPanelsGrid}>
            <article
              className={`${styles.resultsDataCard} ${expandedCard === "trend" ? styles.resultsDataCardExpanded : ""}`.trim()}
            >
              <div className={styles.resultsDataCardHead}>
                <h2 className={styles.resultsDataCardTitle}>Graph Trend</h2>
                <button
                  type="button"
                  className={styles.resultsDataCardToggle}
                  onClick={() =>
                    setExpandedCard((current) => (current === "trend" ? null : "trend"))
                  }
                  aria-label={expandedCard === "trend" ? "Collapse graph trend" : "Expand graph trend"}
                >
                  {expandedCard === "trend" ? "-" : "+"}
                </button>
              </div>
              <p className={styles.resultsDataCardMeta}>
                Total mentions in timeline: <strong>{trendTotal}</strong>
              </p>
              {expandedCard === "trend" && (
                <p className={styles.resultsDataCardDescription}>
                  This trend line shows how frequently the topic appears in Reddit conversations over time.
                  Use this to spot sustained demand versus one-off spikes.
                </p>
              )}
              <div className={styles.chartShell}>
                <LineChart points={trendPoints} xLabel="Time" yLabel="Mentions" />
              </div>
            </article>

            <article
              className={`${styles.resultsDataCard} ${expandedCard === "subreddits" ? styles.resultsDataCardExpanded : ""}`.trim()}
            >
              <div className={styles.resultsDataCardHead}>
                <h2 className={styles.resultsDataCardTitle}>Mentions by Subreddit</h2>
                <button
                  type="button"
                  className={styles.resultsDataCardToggle}
                  onClick={() =>
                    setExpandedCard((current) => (current === "subreddits" ? null : "subreddits"))
                  }
                  aria-label={expandedCard === "subreddits" ? "Collapse subreddit chart" : "Expand subreddit chart"}
                >
                  {expandedCard === "subreddits" ? "-" : "+"}
                </button>
              </div>
              <p className={styles.resultsDataCardMeta}>
                Total tracked subreddit mentions: <strong>{totalSubredditMentions}</strong>
              </p>
              {expandedCard === "subreddits" && (
                <p className={styles.resultsDataCardDescription}>
                  Bars are scaled to the largest subreddit, so you can compare where this conversation is concentrated.
                </p>
              )}
              <div className={styles.subredditBars}>
                {subredditStats.map((item) => {
                  const widthPct = (item.mentions / maxSubredditMentions) * 100;
                  const share = totalSubredditMentions > 0
                    ? (item.mentions / totalSubredditMentions) * 100
                    : 0;
                  return (
                    <div key={item.name} className={styles.subredditBarRow}>
                      <span className={styles.subredditBarLabel}>r/{item.name}</span>
                      <div className={styles.subredditBarTrack}>
                        <div
                          className={styles.subredditBarFill}
                          style={{ width: `${Math.max(widthPct, 6)}%` }}
                        />
                      </div>
                      <span className={styles.subredditBarValue}>
                        {item.mentions} ({formatPercent(share)})
                      </span>
                    </div>
                  );
                })}
              </div>
            </article>

            <article
              className={`${styles.resultsDataCard} ${expandedCard === "feedback" ? styles.resultsDataCardExpanded : ""}`.trim()}
            >
              <div className={styles.resultsDataCardHead}>
                <h2 className={styles.resultsDataCardTitle}>Best Feedback</h2>
                <button
                  type="button"
                  className={styles.resultsDataCardToggle}
                  onClick={() =>
                    setExpandedCard((current) => (current === "feedback" ? null : "feedback"))
                  }
                  aria-label={expandedCard === "feedback" ? "Collapse feedback list" : "Expand feedback list"}
                >
                  {expandedCard === "feedback" ? "-" : "+"}
                </button>
              </div>
              <p className={styles.resultsDataCardMeta}>
                Top {feedbackMatches.length} most relevant comments and posts.
              </p>
              {expandedCard === "feedback" && (
                <p className={styles.resultsDataCardDescription}>
                  These are the strongest signal quotes for your query, each linked to the original Reddit source.
                </p>
              )}
              <ol
                className={`${styles.feedbackList} ${expandedCard === "feedback" ? styles.feedbackListExpanded : ""}`.trim()}
              >
                {feedbackMatches.map((item, index) => {
                  const redditUrl = item.url || `https://www.reddit.com/r/${item.subreddit}/`;
                  const subreddit = item.subreddit.replace(/^r\//i, "");
                  const snippet = item.body.slice(0, 170);
                  return (
                    <li key={item.id} className={styles.feedbackItem}>
                      <div className={styles.feedbackItemHead}>
                        <span className={styles.feedbackRank}>#{index + 1}</span>
                        <span className={styles.feedbackMeta}>r/{subreddit}</span>
                        {item.author ? <span className={styles.feedbackMeta}>u/{item.author}</span> : null}
                      </div>
                      <p className={styles.feedbackQuote}>
                        &ldquo;{snippet}{item.body.length > 170 ? "..." : ""}&rdquo;
                      </p>
                      <a
                        href={redditUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.feedbackLink}
                      >
                        View post or comment
                      </a>
                    </li>
                  );
                })}
              </ol>
            </article>

            <article
              className={`${styles.resultsDataCard} ${expandedCard === "momentum" ? styles.resultsDataCardExpanded : ""}`.trim()}
            >
              <div className={styles.resultsDataCardHead}>
                <h2 className={styles.resultsDataCardTitle}>Growth Momentum</h2>
                <button
                  type="button"
                  className={styles.resultsDataCardToggle}
                  onClick={() =>
                    setExpandedCard((current) => (current === "momentum" ? null : "momentum"))
                  }
                  aria-label={expandedCard === "momentum" ? "Collapse growth momentum" : "Expand growth momentum"}
                >
                  {expandedCard === "momentum" ? "-" : "+"}
                </button>
              </div>
              <p className={styles.resultsDataCardMeta}>
                Growth rate: <strong>{momentumGrowth >= 0 ? "+" : ""}{momentumGrowth.toFixed(1)}%</strong>
              </p>
              {expandedCard === "momentum" && (
                <p className={styles.resultsDataCardDescription}>
                  Momentum highlights acceleration, not just volume. Rising slope indicates growing market urgency.
                </p>
              )}
              <div className={styles.chartShell}>
                <LineChart points={momentumPoints} xLabel="Time" yLabel="Momentum" />
              </div>
            </article>
          </div>
        </div>
      </section>
    </div>
  );
}
