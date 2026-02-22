"use client";

import { useRef, useState } from "react";

export type SaturationPoint = {
  date: string;
  label: string;
  needs: number;
  tools: number;
};

type MarketSaturationChartProps = {
  points: SaturationPoint[];
  xLabel?: string;
  yLabel?: string;
};

export default function MarketSaturationChart({
  points,
  xLabel = "Time",
  yLabel = "Mentions",
}: MarketSaturationChartProps) {
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
  const maxValue = Math.max(...points.flatMap((point) => [point.needs, point.tools]), 1);
  const safeDenominator = Math.max(points.length - 1, 1);

  const xAt = (index: number) => padLeft + (index / safeDenominator) * innerWidth;
  const yAt = (value: number) => padTop + (1 - value / maxValue) * innerHeight;

  const needsPath = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${xAt(index)} ${yAt(point.needs)}`)
    .join(" ");

  const toolsPath = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${xAt(index)} ${yAt(point.tools)}`)
    .join(" ");

  const yTicks = 4;
  const xTickEvery = Math.max(1, Math.floor(points.length / 7));

  const activePoint = hoverIndex !== null ? points[hoverIndex] : null;
  const activeX = hoverIndex !== null ? xAt(hoverIndex) : null;

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
      aria-label="Need/problem mentions versus existing-tool mentions"
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

      <path d={needsPath} stroke="#e35900" strokeWidth="3" fill="none" />
      <path d={toolsPath} stroke="#8f5a3a" strokeWidth="3" fill="none" />

      {points.map((point, index) => (
        <g key={`${point.date}-${point.needs}-${point.tools}`}>
          <circle
            cx={xAt(index)}
            cy={yAt(point.needs)}
            r={hoverIndex === index ? "4.2" : "3"}
            fill="#fff"
            stroke="#e35900"
            strokeWidth="1.6"
          />
          <circle
            cx={xAt(index)}
            cy={yAt(point.tools)}
            r={hoverIndex === index ? "4.2" : "3"}
            fill="#fff"
            stroke="#8f5a3a"
            strokeWidth="1.6"
          />
        </g>
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

      {activePoint && activeX !== null && (
        <g>
          <line
            x1={activeX}
            y1={padTop}
            x2={activeX}
            y2={padTop + innerHeight}
            stroke="#d39a79"
            strokeDasharray="5 4"
            strokeWidth="1.1"
          />

          {(() => {
            const tooltipWidth = 176;
            const tooltipHeight = 58;
            const tooltipX = activeX > width - padRight - tooltipWidth - 10
              ? activeX - tooltipWidth - 10
              : activeX + 10;
            const tooltipY = Math.max(padTop + 8, Math.min(yAt(activePoint.needs), yAt(activePoint.tools)) - tooltipHeight - 8);
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
                <text x={tooltipX + 10} y={tooltipY + 16} fill="#8d5031" fontSize="11" fontWeight="600">
                  {activePoint.label}
                </text>
                <text x={tooltipX + 10} y={tooltipY + 32} fill="#e35900" fontSize="11" fontWeight="700">
                  Need/problem: {activePoint.needs}
                </text>
                <text x={tooltipX + 10} y={tooltipY + 47} fill="#8f5a3a" fontSize="11" fontWeight="700">
                  Existing tools: {activePoint.tools}
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
