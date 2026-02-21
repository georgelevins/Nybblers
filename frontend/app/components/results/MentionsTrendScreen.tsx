"use client";

import { useMemo, useState } from "react";
import { MONTHLY_TOPIC_MENTIONS } from "@/app/lib/resultsVisualData";
import styles from "@/app/redditdemand.module.css";
import LineChart from "./LineChart";

type MentionsTrendScreenProps = {
  query: string;
};

export default function MentionsTrendScreen({ query }: MentionsTrendScreenProps) {
  const maxWindow = MONTHLY_TOPIC_MENTIONS.length;
  const [windowSize, setWindowSize] = useState(Math.min(18, maxWindow));

  const filtered = useMemo(
    () => MONTHLY_TOPIC_MENTIONS.slice(-windowSize),
    [windowSize],
  );

  const totalMentions = filtered.reduce((sum, point) => sum + point.value, 0);
  const avgMentions = Math.round(totalMentions / filtered.length);
  const peakPoint = filtered.reduce((peak, point) =>
    point.value > peak.value ? point : peak,
  );

  const firstLabel = filtered[0]?.label ?? "";
  const lastLabel = filtered[filtered.length - 1]?.label ?? "";

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
        <div className={styles.metricPill}>
          <span>Peak Month</span>
          <strong>
            {peakPoint.label} ({peakPoint.value})
          </strong>
        </div>
      </div>

      <div className={styles.sliderWrap}>
        <label htmlFor="time-window" className={styles.sliderLabel}>
          Time Filter: Last {windowSize} months
        </label>
        <input
          id="time-window"
          type="range"
          min={6}
          max={maxWindow}
          step={1}
          value={windowSize}
          onChange={(event) => setWindowSize(Number(event.target.value))}
          className={styles.rangeInput}
        />
        <p className={styles.sliderRange}>
          Showing {firstLabel} to {lastLabel}
        </p>
      </div>

      <div className={styles.chartShell}>
        <LineChart
          points={filtered}
          xLabel="Time (months)"
          yLabel="Mentions"
        />
      </div>
    </section>
  );
}
