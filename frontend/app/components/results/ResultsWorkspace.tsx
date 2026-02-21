"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import styles from "@/app/redditdemand.module.css";

type ResultsScreen = "trend" | "users" | "growth" | "quotes";

type ResultsWorkspaceProps = {
  query: string;
  screen: ResultsScreen;
  children: React.ReactNode;
};

const HISTORY_KEY = "remand-query-history";
const SIDEBAR_WIDTH_KEY = "remand-sidebar-width";
const MIN_SIDEBAR_WIDTH = 220;
const MAX_SIDEBAR_WIDTH = 460;

function screenHref(query: string, screen: ResultsScreen) {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  params.set("screen", screen);
  return `/results?${params.toString()}`;
}

export default function ResultsWorkspace({
  query,
  screen,
  children,
}: ResultsWorkspaceProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [isResizing, setIsResizing] = useState(false);

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
                    href={screenHref(item, "trend")}
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
            <input type="hidden" name="screen" value={screen} />
            <button type="submit" className={styles.resultsMiniButton}>
              Search
            </button>
          </form>

          <Link href="/explore-ai" className={styles.exploreAiLink}>
            Explore with AI
          </Link>
        </div>

        <div className={styles.resultsTopTabs}>
          <Link
            href={screenHref(query, "trend")}
            className={`${styles.resultsTab} ${screen === "trend" ? styles.resultsTabActive : ""}`.trim()}
          >
            Topic Mentions
          </Link>
          <Link
            href={screenHref(query, "growth")}
            className={`${styles.resultsTab} ${screen === "growth" ? styles.resultsTabActive : ""}`.trim()}
          >
            Growth Momentum
          </Link>
          <Link
            href={screenHref(query, "quotes")}
            className={`${styles.resultsTab} ${screen === "quotes" ? styles.resultsTabActive : ""}`.trim()}
          >
            Top Comments
          </Link>
        </div>

        <div>{children}</div>
      </section>

      <Link
        href={screenHref(query, "users")}
        className={`${styles.connectMarketButton} ${screen === "users" ? styles.connectMarketButtonActive : ""}`.trim()}
      >
        Connect with your market
      </Link>
    </div>
  );
}
