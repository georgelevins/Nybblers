"use client";

import { useMemo, useState } from "react";
import LineChart from "./LineChart";
import styles from "@/app/redditdemand.module.css";
import { getGrowthRate } from "@/app/lib/resultsVisualData";
import type { GrowthData } from "@/app/lib/api";

type Mode = "weekly" | "monthly";

type GrowthMomentumScreenProps = {
  query: string;
  data: GrowthData;
};

export default function GrowthMomentumScreen({ query, data }: GrowthMomentumScreenProps) {
  const [mode, setMode] = useState<Mode>("monthly");

  const points = mode === "monthly" ? data.monthly : data.weekly;

  const growth = useMemo(() => getGrowthRate(points), [points]);

  const first = points[0]?.value ?? 0;
  const latest = points[points.length - 1]?.value ?? 0;
  const delta = latest - first;

  if (data.monthly.length === 0 && data.weekly.length === 0) {
    return (
      <section className={styles.visualCard}>
        <div className={styles.visualHeader}>
          <h2 className={styles.visualTitle}>Growth Over Time</h2>
          <p className={styles.visualSub}>
            No growth data found for <strong>{query}</strong>.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.visualCard}>
      <div className={styles.visualHeader}>
        <h2 className={styles.visualTitle}>Growth Over Time (Momentum &gt; Raw Numbers)</h2>
        <p className={styles.visualSub}>
          Trend velocity for <strong>{query}</strong>.
        </p>
      </div>

      <div className={styles.segmentedControl}>
        <button
          type="button"
          className={`${styles.segmentButton} ${mode === "weekly" ? styles.segmentActive : ""}`.trim()}
          onClick={() => setMode("weekly")}
        >
          Weekly Mentions
        </button>
        <button
          type="button"
          className={`${styles.segmentButton} ${mode === "monthly" ? styles.segmentActive : ""}`.trim()}
          onClick={() => setMode("monthly")}
        >
          Monthly Mentions
        </button>
      </div>

      <div className={styles.metricsRow}>
        <div className={styles.metricPill}>
          <span>Growth Rate</span>
          <strong>{growth >= 0 ? "+" : ""}{growth.toFixed(1)}%</strong>
        </div>
        <div className={styles.metricPill}>
          <span>First vs Latest</span>
          <strong>
            {first} → {latest}
          </strong>
        </div>
        <div className={styles.metricPill}>
          <span>Net Momentum</span>
          <strong>{delta >= 0 ? "+" : ""}{delta}</strong>
        </div>
      </div>

      {points.length > 0 ? (
        <div className={styles.chartShell}>
          <LineChart
            points={points}
            xLabel={mode === "weekly" ? "Time (weeks)" : "Time (months)"}
            yLabel="Mentions"
          />
        </div>
      ) : (
        <p className={styles.agentSub}>No {mode} data available.</p>
      )}
    </section>
  );
}
