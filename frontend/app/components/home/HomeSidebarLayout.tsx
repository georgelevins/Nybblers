"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import styles from "@/app/redditdemand.module.css";

type HomeSidebarLayoutProps = {
  children: React.ReactNode;
};

const HISTORY_KEY = "remand-query-history";
const SIDEBAR_WIDTH_KEY = "remand-sidebar-width";
const MIN_SIDEBAR_WIDTH = 220;
const MAX_SIDEBAR_WIDTH = 460;

function toResultsHref(query: string) {
  const params = new URLSearchParams();
  params.set("q", query);
  params.set("screen", "trend");
  return `/results?${params.toString()}`;
}

export default function HomeSidebarLayout({ children }: HomeSidebarLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    const raw = window.localStorage.getItem(HISTORY_KEY);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    const clean = parsed.filter((item) => item.trim().length > 0).slice(0, 20);
    const timer = window.setTimeout(() => {
      setHistory(clean);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

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
              {history.length === 0 ? (
                <p className={styles.sidebarEmpty}>No previous searches yet.</p>
              ) : (
                history.map((item) => (
                  <Link key={item} href={toResultsHref(item)} className={styles.sidebarHistoryItem}>
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

      <section className={`${styles.resultsMain} ${styles.homeMainContent}`}>
        {children}
      </section>
    </div>
  );
}
