"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import styles from "../../landing.module.css";

type Point = {
  label: string;
  mentions: number;
};

const DATA: Point[] = [
  { label: "Jan", mentions: 41 },
  { label: "Feb", mentions: 45 },
  { label: "Mar", mentions: 48 },
  { label: "Apr", mentions: 56 },
  { label: "May", mentions: 63 },
  { label: "Jun", mentions: 66 },
  { label: "Jul", mentions: 74 },
  { label: "Aug", mentions: 83 },
  { label: "Sep", mentions: 95 },
  { label: "Oct", mentions: 108 },
];

export default function LandingGrowthChart() {
  const width = 680;
  const height = 280;
  const left = 60;
  const right = 40;
  const top = 32;
  const bottom = 52;
  const innerWidth = width - left - right;
  const innerHeight = height - top - bottom;

  const max = Math.max(...DATA.map((d) => d.mentions), 1);
  const min = Math.min(...DATA.map((d) => d.mentions), 0);
  const range = Math.max(max - min, 1);
  const stepX = innerWidth / Math.max(DATA.length - 1, 1);

  const points = useMemo(
    () =>
      DATA.map((d, i) => {
        const x = left + i * stepX;
        const y = top + (1 - (d.mentions - min) / range) * innerHeight;
        return { ...d, x, y };
      }),
    [innerHeight, left, min, range, stepX, top],
  );

  const polylinePoints = points.map((p) => `${p.x},${p.y}`).join(" ");
  const areaPoints = `${left},${top + innerHeight} ${polylinePoints} ${left + innerWidth},${top + innerHeight}`;

  const [hovered, setHovered] = useState<number | null>(null);
  const [draw, setDraw] = useState(false);
  const pathRef = useRef<SVGPolylineElement | null>(null);
  const [pathLength, setPathLength] = useState(0);

  useEffect(() => {
    const node = pathRef.current;
    if (!node) return;
    setPathLength(node.getTotalLength());
  }, [polylinePoints]);

  // automatically start drawing once we've measured the path length
  useEffect(() => {
    if (pathLength > 0) {
      // give React a tick so that the initial value (draw=false) is applied and
      // the transition can animate from full offset to zero
      const id = setTimeout(() => setDraw(true), 40);
      return () => clearTimeout(id);
    }
  }, [pathLength]);

  function handleMouseMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const xPx = e.clientX - rect.left;
    const x = (xPx / rect.width) * width;
    let nearest = 0;
    let diff = Infinity;
    points.forEach((p, i) => {
      const d = Math.abs(p.x - x);
      if (d < diff) {
        diff = d;
        nearest = i;
      }
    });
    setHovered(nearest);
  }

  const hoveredPoint = hovered !== null ? points[hovered] : null;

  return (
    <div className={styles.chartInteractiveWrap}>
      <svg
        className={styles.chart}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Growth momentum sample chart"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHovered(null)}
      >
        <line x1={left} y1={top} x2={left} y2={top + innerHeight} stroke="#efcfb8" strokeWidth="1" />
        <line x1={left} y1={top + innerHeight} x2={left + innerWidth} y2={top + innerHeight} stroke="#efcfb8" strokeWidth="1" />
        <line x1={left} y1={top + innerHeight * 0.75} x2={left + innerWidth} y2={top + innerHeight * 0.75} stroke="#f4dcc9" strokeWidth="1" />
        <line x1={left} y1={top + innerHeight * 0.5} x2={left + innerWidth} y2={top + innerHeight * 0.5} stroke="#f4dcc9" strokeWidth="1" />
        <line x1={left} y1={top + innerHeight * 0.25} x2={left + innerWidth} y2={top + innerHeight * 0.25} stroke="#f4dcc9" strokeWidth="1" />

        <polygon points={areaPoints} fill="#ff9f62" opacity="0.16" />

        <polyline
          ref={pathRef}
          points={polylinePoints}
          fill="none"
          stroke="#e35900"
          strokeWidth="4"
          strokeLinejoin="round"
          strokeLinecap="round"
          style={{
            strokeDasharray: pathLength || undefined,
            strokeDashoffset: draw ? 0 : pathLength || 0,
            transition: "stroke-dashoffset 1.6s cubic-bezier(0.2, 0.8, 0.2, 1)",
          }}
        />

        {points.map((point, index) => (
          <g key={point.label}>
            <circle
              cx={point.x}
              cy={point.y}
              r={hovered === index ? 5.2 : 4}
              fill="#fff"
              stroke="#e35900"
              strokeWidth="2"
              style={{
                opacity: draw ? 1 : 0,
                transition: `opacity 0.35s ease ${0.65 + index * 0.05}s, r 0.15s ease`,
              }}
            />
            <circle
              cx={point.x}
              cy={point.y}
              r={10}
              fill="transparent"
              onMouseEnter={() => setHovered(index)}
            />
          </g>
        ))}

        {points.map((point) => (
          <text key={`${point.label}-label`} x={point.x} y={height - 16} fill="#9a5d3a" fontSize="12" textAnchor="middle">
            {point.label}
          </text>
        ))}

        {hoveredPoint && (
          <g>
            <line
              x1={hoveredPoint.x}
              y1={top}
              x2={hoveredPoint.x}
              y2={top + innerHeight}
              stroke="#d98858"
              strokeDasharray="5 4"
              strokeWidth="1"
            />
            <rect x={hoveredPoint.x - 52} y={hoveredPoint.y - 46} width="104" height="36" rx="8" fill="#fff8f1" stroke="#e6b088" />
            <text x={hoveredPoint.x} y={hoveredPoint.y - 30} fill="#8b4f2f" fontSize="11" textAnchor="middle">
              {hoveredPoint.label}
            </text>
            <text x={hoveredPoint.x} y={hoveredPoint.y - 16} fill="#d04f00" fontSize="11" textAnchor="middle" fontWeight="700">
              {hoveredPoint.mentions} mentions
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}
