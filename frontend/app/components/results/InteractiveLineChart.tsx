"use client";

import { useRef, useState } from "react";
import type { TimePoint } from "@/app/lib/api";

type InteractiveLineChartProps = {
  points: TimePoint[];
  xLabel?: string;
  yLabel?: string;
};

export default function InteractiveLineChart({
  points,
  xLabel = "Time",
  yLabel = "Mentions",
}: InteractiveLineChartProps) {
  const width = 920;
  const height = 330;
  const padLeft = 52;
  const padRight = 22;
  const padTop = 24;
  const padBottom = 42;
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (points.length === 0) {
    return <p>No data points available.</p>;
  }

  const innerWidth = width - padLeft - padRight;
  const innerHeight = height - padTop - padBottom;
  const maxValue = Math.max(...points.map((point) => point.value), 1);
  const safeDenominator = Math.max(points.length - 1, 1);

  const xAt = (index: number) => padLeft + (index / safeDenominator) * innerWidth;
  const yAt = (value: number) => padTop + (1 - value / maxValue) * innerHeight;

  const linePath = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${xAt(index)} ${yAt(point.value)}`)
    .join(" ");
  const areaPath = `${linePath} L ${xAt(points.length - 1)} ${padTop + innerHeight} L ${xAt(0)} ${padTop + innerHeight} Z`;

  const yTicks = 4;
  const xTickEvery = Math.max(1, Math.floor(points.length / 7));

  const activePoint = hoverIndex !== null ? points[hoverIndex] : null;
  const activeX = hoverIndex !== null ? xAt(hoverIndex) : null;
  const activeY = activePoint ? yAt(activePoint.value) : null;

  function onMouseMove(event: React.MouseEvent<SVGRectElement>) {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    if (rect.width === 0) return;

    const svgX = ((event.clientX - rect.left) / rect.width) * width;
    const clamped = Math.min(padLeft + innerWidth, Math.max(padLeft, svgX));
    const progress = (clamped - padLeft) / innerWidth;
    const nextIndex = Math.round(progress * safeDenominator);
    setHoverIndex(nextIndex);
  }

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`${yLabel} by ${xLabel}`}
      onMouseLeave={() => setHoverIndex(null)}
    >
      {Array.from({ length: yTicks + 1 }).map((_, idx) => {
        const y = padTop + (innerHeight / yTicks) * idx;
        const value = Math.round(maxValue - (maxValue / yTicks) * idx);

        return (
          <g key={`grid-${idx}`}>
            <line x1={padLeft} y1={y} x2={width - padRight} y2={y} stroke="#f0d9c8" strokeWidth="1" />
            <text x={8} y={y + 4} fill="#995730" fontSize="11">
              {value}
            </text>
          </g>
        );
      })}

      <path d={areaPath} fill="#ffb882" opacity="0.28" />
      <path d={linePath} stroke="#e35900" strokeWidth="3" fill="none" />

      {points.map((point, index) => (
        <circle
          key={`${point.date}-${point.value}`}
          cx={xAt(index)}
          cy={yAt(point.value)}
          r={hoverIndex === index ? "4.4" : "3.2"}
          fill="#ffffff"
          stroke="#e35900"
          strokeWidth="1.6"
        />
      ))}

      {points.map((point, index) => {
        if (index % xTickEvery !== 0 && index !== points.length - 1) return null;
        return (
          <text key={`x-${point.date}`} x={xAt(index)} y={height - 14} textAnchor="middle" fill="#995730" fontSize="11">
            {point.label}
          </text>
        );
      })}

      <rect
        x={padLeft}
        y={padTop}
        width={innerWidth}
        height={innerHeight}
        fill="transparent"
        onMouseMove={onMouseMove}
        onMouseLeave={() => setHoverIndex(null)}
      />

      {activePoint && activeX !== null && activeY !== null && (
        <g>
          <line
            x1={activeX}
            y1={padTop}
            x2={activeX}
            y2={padTop + innerHeight}
            stroke="#d8773c"
            strokeDasharray="5 4"
            strokeWidth="1.2"
          />
          <circle cx={activeX} cy={activeY} r="4.9" fill="#fff" stroke="#e35900" strokeWidth="2" />

          {(() => {
            const tooltipWidth = 146;
            const tooltipHeight = 44;
            const tooltipX = activeX > width - padRight - tooltipWidth - 10
              ? activeX - tooltipWidth - 10
              : activeX + 10;
            const tooltipY = Math.max(padTop + 8, activeY - tooltipHeight - 8);
            return (
              <g>
                <rect
                  x={tooltipX}
                  y={tooltipY}
                  width={tooltipWidth}
                  height={tooltipHeight}
                  rx="8"
                  fill="#fff8f1"
                  stroke="#f0c6a6"
                />
                <text x={tooltipX + 10} y={tooltipY + 17} fill="#8d5031" fontSize="11" fontWeight="600">
                  {activePoint.label}
                </text>
                <text x={tooltipX + 10} y={tooltipY + 33} fill="#d04f00" fontSize="12" fontWeight="700">
                  {activePoint.value} mentions
                </text>
              </g>
            );
          })()}
        </g>
      )}

      <text x={width / 2} y={height - 2} fill="#7d482a" fontSize="12" textAnchor="middle">
        {xLabel}
      </text>
      <text x={16} y={16} fill="#7d482a" fontSize="12">
        {yLabel}
      </text>
    </svg>
  );
}
