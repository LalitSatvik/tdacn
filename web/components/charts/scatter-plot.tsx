"use client";

import * as d3 from "d3";
import * as React from "react";

export interface ScatterDatum {
  id: string;
  x: number;
  y: number;
}

interface ScatterPlotProps {
  data: ScatterDatum[];
  xLabel: string;
  yLabel: string;
  width?: number;
  height?: number;
  color?: string;
  className?: string;
}

// General-purpose format (2 significant digits, no trailing zeros) so
// small-magnitude axes like PageRank (~0.0002) don't all round to "0.00".
const tickFormat = d3.format(".2~g");

const MARGIN = { top: 12, right: 16, bottom: 32, left: 44 };

/** Centrality vs. drift scatter — one point per concept, hoverable. */
export function ScatterPlot({
  data,
  xLabel,
  yLabel,
  width = 480,
  height = 280,
  color = "#0f7a82",
  className,
}: ScatterPlotProps) {
  const [hovered, setHovered] = React.useState<ScatterDatum | null>(null);
  const innerW = width - MARGIN.left - MARGIN.right;
  const innerH = height - MARGIN.top - MARGIN.bottom;

  const x = d3
    .scaleLinear()
    .domain(d3.extent(data, (d) => d.x) as [number, number])
    .nice()
    .range([0, innerW]);
  const y = d3
    .scaleLinear()
    .domain(d3.extent(data, (d) => d.y) as [number, number])
    .nice()
    .range([innerH, 0]);

  return (
    <div className={className} style={{ position: "relative" }}>
      <svg width="100%" viewBox={`0 0 ${width} ${height}`}>
        <g transform={`translate(${MARGIN.left},${MARGIN.top})`}>
          {y.ticks(4).map((t) => (
            <g key={t}>
              <line x1={0} x2={innerW} y1={y(t)} y2={y(t)} stroke="var(--border)" strokeWidth={1} />
              <text x={-8} y={y(t)} textAnchor="end" dominantBaseline="middle" className="fill-muted-foreground text-[10px]">
                {tickFormat(t)}
              </text>
            </g>
          ))}
          {x.ticks(4).map((t) => (
            <text key={t} x={x(t)} y={innerH + 18} textAnchor="middle" className="fill-muted-foreground text-[10px]">
              {tickFormat(t)}
            </text>
          ))}
          {data.map((d) => {
            const isHovered = hovered?.id === d.id;
            return (
              <circle
                key={d.id}
                cx={x(d.x)}
                cy={y(d.y)}
                r={isHovered ? 5 : 2.5}
                fill={color}
                fillOpacity={isHovered ? 0.95 : 0.45}
                stroke={isHovered ? "var(--card)" : "none"}
                strokeWidth={1.5}
                className="cursor-pointer transition-[r,fill-opacity] duration-100"
                onMouseEnter={() => setHovered(d)}
                onMouseLeave={() => setHovered((prev) => (prev?.id === d.id ? null : prev))}
              />
            );
          })}
          <text x={innerW / 2} y={innerH + 30} textAnchor="middle" className="fill-foreground text-[11px] font-medium">
            {xLabel}
          </text>
          <text
            x={-innerH / 2}
            y={-32}
            textAnchor="middle"
            transform="rotate(-90)"
            className="fill-foreground text-[11px] font-medium"
          >
            {yLabel}
          </text>
        </g>
      </svg>
      {hovered && (
        <div
          className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-lg border border-border bg-card px-2.5 py-1.5 text-[11px] shadow-lg"
          style={{
            left: `${((MARGIN.left + x(hovered.x)) / width) * 100}%`,
            top: `${((MARGIN.top + y(hovered.y)) / height) * 100}%`,
            marginTop: -8,
          }}
        >
          <div className="font-mono font-medium text-foreground">{hovered.id}</div>
          <div className="text-muted-foreground">
            {xLabel}: {tickFormat(hovered.x)} · {yLabel}: {tickFormat(hovered.y)}
          </div>
        </div>
      )}
    </div>
  );
}
