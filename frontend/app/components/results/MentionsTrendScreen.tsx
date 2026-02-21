"use client";

import { useMemo, useState } from "react";
import styles from "@/app/redditdemand.module.css";
import LineChart from "./LineChart";
import type { TimePoint } from "@/app/lib/api";

type MentionsTrendScreenProps = {
  query: string;
  points: TimePoint[];
};

export default function MentionsTrendScreen({ query, points }: MentionsTrendScreenProps) {
  const maxWindow = points.length;
  const [windowSize, setWindowSize] = useState(Math.min(18, Math.max(1, maxWindow)));

  const filtered = useMemo(
    () => (maxWindow > 0 ? points.slice(-windowSize) : []),
    [points, windowSize, maxWindow],
  );

  const totalMentions = filtered.reduce((sum, p) => sum + p.value, 0);
  const avgMentions = filtered.length > 0 ? Math.round(totalMentions / filtered.length) : 0;
  const peakPoint = filtered.length > 0
    ? filtered.reduce((peak, p) => (p.value > peak.value ? p : peak))
    : null;

  const firstLabel = filtered[0]?.label ?? "";
  const lastLabel = filtered[filtered.length - 1]?.label ?? "";

  if (points.length === 0) {
    return (
      <section className={styles.visualCard}>
        <div className={styles.visualHeader}>
          <h2 className={styles.visualTitle}>Topic Mentions Over Time</h2>
          <p className={styles.visualSub}>
            No data found for <strong>{query}</strong> in the current dataset.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.visualCard}>
      <div className={styles.visualHeader}>
        <h2 className={styles.visualTitle}>Topic Mentions Over Time</h2>
        <p className={styles.visualSub}>
          Tracking how often people discussed <strong>{query}</strong> on Reddit.
        </p>
      </div>

      <div className={styles.metricsRow}>
        <div className={styles.metricPill}>
          <span>Total Mentions</span>
          <strong>{totalMentions}</strong>
        </div>
        <div className={styles.metricPill}>
          <span>Avg / Month</span>
          <strong>{avgMentions}</strong>
        </div>
        {peakPoint && (
          <div className={styles.metricPill}>
            <span>Peak Month</span>
            <strong>
              {peakPoint.label} ({peakPoint.value})
            </strong>
          </div>
        )}
      </div>

      {maxWindow > 1 && (
        <div className={styles.sliderWrap}>
          <label htmlFor="time-window" className={styles.sliderLabel}>
            Time Filter: Last {windowSize} months
          </label>
          <input
            id="time-window"
            type="range"
            min={1}
            max={maxWindow}
            step={1}
            value={windowSize}
            onChange={(e) => setWindowSize(Number(e.target.value))}
            className={styles.rangeInput}
          />
          <p className={styles.sliderRange}>
            Showing {firstLabel} to {lastLabel}
          </p>
        </div>
      )}

      <div className={styles.chartShell}>
        <LineChart points={filtered} xLabel="Time (months)" yLabel="Mentions" />
      </div>
    </section>
  );
}
