"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type CSSProperties } from "react";
import styles from "@/app/redditdemand.module.css";
import InteractiveLineChart from "./InteractiveLineChart";
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

type ScoreFactor = {
  key: "growth" | "intent" | "evergreen" | "engagement";
  label: string;
  value: number;
  weight: number;
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

function clampScore(value: number): number {
  return Math.max(0, Math.min(100, value));
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
  const [momentumWindow, setMomentumWindow] = useState<number | null>(null);

  const minMomentumWindow = Math.min(4, Math.max(1, momentumPoints.length));
  const defaultMomentumWindow = Math.min(18, Math.max(1, momentumPoints.length));
  const selectedMomentumWindow = momentumWindow ?? defaultMomentumWindow;
  const effectiveMomentumWindow = Math.min(
    Math.max(minMomentumWindow, selectedMomentumWindow),
    Math.max(1, momentumPoints.length),
  );
  const filteredMomentumPoints = momentumPoints.slice(-effectiveMomentumWindow);
  const filteredMomentumGrowth = getGrowthRate(filteredMomentumPoints);
  const momentumStartLabel = filteredMomentumPoints[0]?.label ?? "";
  const momentumEndLabel =
    filteredMomentumPoints[filteredMomentumPoints.length - 1]?.label ?? "";
  const trendGrowthRate = getGrowthRate(trendPoints);

  const intentPercent = clampScore(
    feedbackMatches.length > 0
      ? (feedbackMatches.reduce((sum, item) => sum + item.similarity, 0) / feedbackMatches.length) * 100
      : 0,
  );

  const evergreenRatio = trendPoints.length > 1
    ? trendPoints
      .slice(1)
      .reduce(
        (count, point, index) =>
          point.value >= trendPoints[index].value ? count + 1 : count,
        0,
      ) / (trendPoints.length - 1)
    : 0;
  const evergreenPosts = feedbackMatches.length > 0
    ? feedbackMatches.filter((item) => item.kind === "post").length / feedbackMatches.length
    : 0;
  const evergreenPercent = clampScore((evergreenRatio * 100) * 0.65 + (evergreenPosts * 100) * 0.35);

  const averageMentions = trendPoints.length > 0 ? trendTotal / trendPoints.length : 0;
  const engagementVolume = clampScore((averageMentions / 120) * 100);
  const engagementBreadth = clampScore((subredditStats.length / 6) * 100);
  const engagementPercent = clampScore((engagementVolume * 0.7) + (engagementBreadth * 0.3));

  const growthPercent = clampScore((trendGrowthRate / 160) * 100);

  const scoreFactors: ScoreFactor[] = [
    { key: "growth", label: "Growth rate", value: growthPercent, weight: 0.35 },
    { key: "intent", label: "Intent %", value: intentPercent, weight: 0.3 },
    { key: "evergreen", label: "Evergreen threads", value: evergreenPercent, weight: 0.2 },
    { key: "engagement", label: "Engagement", value: engagementPercent, weight: 0.15 },
  ];

  const opportunityScore = Math.round(
    scoreFactors.reduce((sum, factor) => sum + (factor.value * factor.weight), 0),
  );

  const hasExpandedCard = expandedCard !== null;

  const layoutStyle = {
    gridTemplateColumns: collapsed
      ? "0px minmax(0, 1fr)"
      : `${sidebarWidth}px minmax(0, 1fr)`,
    ["--expanded-left" as string]: collapsed ? "0.95rem" : `${sidebarWidth + 14}px`,
  } as CSSProperties;

  function cardClass(cardId: CardId) {
    return `${styles.resultsDataCard} ${
      expandedCard === cardId ? styles.resultsDataCardExpanded : ""
    } ${
      hasExpandedCard && expandedCard !== cardId ? styles.resultsDataCardMinimized : ""
    }`.trim();
  }

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

        <div className={styles.resultsPanelsViewport}>
          <div
            className={`${styles.resultsPanelsGrid} ${hasExpandedCard ? styles.resultsPanelsGridHasExpanded : ""}`.trim()}
          >
            <article className={cardClass("trend")}>
              <div className={styles.resultsDataCardHead}>
                <h2 className={styles.resultsDataCardTitle}>Buyer Readiness Score</h2>
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
                Opportunity Score: <strong>{opportunityScore}/100</strong>
              </p>
              {expandedCard === "trend" && (
                <p className={styles.resultsDataCardDescription}>
                  Composite score for buyer readiness based on growth rate, intent %, evergreen threads, and
                  engagement.
                </p>
              )}

              <div className={styles.readinessLayout}>
                <div className={styles.readinessGaugeWrap}>
                  <div
                    className={styles.readinessGauge}
                    style={{
                      background: `conic-gradient(#e35900 ${(opportunityScore / 100) * 360}deg, #f4dcc7 0deg)`,
                    }}
                    aria-label={`Opportunity score ${opportunityScore} out of 100`}
                  >
                    <div className={styles.readinessGaugeInner}>
                      <span className={styles.readinessGaugeValue}>{opportunityScore}</span>
                      <span className={styles.readinessGaugeOutOf}>/100</span>
                    </div>
                  </div>
                  <p className={styles.readinessGaugeLabel}>Buyer Readiness Meter</p>
                </div>

                <div className={styles.readinessFactors}>
                  {scoreFactors.map((factor) => (
                    <div key={factor.key} className={styles.readinessFactorRow}>
                      <div className={styles.readinessFactorHead}>
                        <span>{factor.label}</span>
                        <span>{Math.round(factor.value)}%</span>
                      </div>
                      <div className={styles.readinessFactorTrack}>
                        <div
                          className={styles.readinessFactorFill}
                          style={{ width: `${Math.max(6, factor.value)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {expandedCard === "trend" && (
                <div className={styles.readinessExpandedNote}>
                  <p>
                    This score estimates how likely people in this market are to actively look for — and
                    pay for — a solution like yours.
                  </p>
                  <p>Weighted to prioritize buying signals.</p>
                  <p>A high score means:</p>
                  <ul>
                    <li>Strong, growing demand</li>
                    <li>Frequent buying-intent discussions</li>
                    <li>Long-lasting discovery via search</li>
                    <li>Consistent community engagement</li>
                  </ul>
                  <p>Scores above 75 indicate strong early-market opportunities.</p>
                </div>
              )}
            </article>

            <article className={cardClass("subreddits")}>
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

            <article className={cardClass("feedback")}>
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

            <article className={cardClass("momentum")}>
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
                Growth rate: <strong>{filteredMomentumGrowth >= 0 ? "+" : ""}{filteredMomentumGrowth.toFixed(1)}%</strong>
              </p>
              {expandedCard === "momentum" && (
                <p className={styles.resultsDataCardDescription}>
                  Momentum highlights acceleration, not just volume. Rising slope indicates growing market urgency.
                </p>
              )}
              {momentumPoints.length > 1 && (
                <div className={styles.sliderWrap}>
                  <label htmlFor="momentum-window" className={styles.sliderLabel}>
                    Time Filter: Last {effectiveMomentumWindow} periods
                  </label>
                  <input
                    id="momentum-window"
                    type="range"
                    min={minMomentumWindow}
                    max={momentumPoints.length}
                    step={1}
                    value={effectiveMomentumWindow}
                    onChange={(event) => setMomentumWindow(Number(event.target.value))}
                    className={styles.rangeInput}
                  />
                  <p className={styles.sliderRange}>
                    Showing {momentumStartLabel} to {momentumEndLabel}
                  </p>
                </div>
              )}
              <div className={styles.chartShell}>
                <InteractiveLineChart
                  points={filteredMomentumPoints}
                  xLabel="Time"
                  yLabel="Momentum"
                />
              </div>
            </article>
          </div>
        </div>
      </section>
    </div>
  );
}
