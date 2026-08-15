"use client";

import * as d3 from "d3";
import * as React from "react";

interface SparklineProps {
  values: (number | null | undefined)[];
  width?: number;
  height?: number;
  color?: string;
  className?: string;
}

/** Small trend line for KPI cards — e.g. a metric's Q1→Q2 and Q2→Q3 values. */
export function Sparkline({ values, width = 96, height = 28, color = "#0f7a82", className }: SparklineProps) {
  const clean = values.filter((v): v is number => v !== null && v !== undefined);
  if (clean.length < 2) return null;

  const x = d3.scaleLinear().domain([0, clean.length - 1]).range([2, width - 2]);
  const [ymin, ymax] = d3.extent(clean) as [number, number];
  const pad = (ymax - ymin) * 0.2 || 1;
  const y = d3.scaleLinear().domain([ymin - pad, ymax + pad]).range([height - 4, 4]);

  const line = d3.line<number>().x((_, i) => x(i)).y((v) => y(v)).curve(d3.curveMonotoneX);
  const path = line(clean) ?? "";

  return (
    <svg width={width} height={height} className={className} aria-hidden>
      <path d={path} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" />
      {clean.map((v, i) => (
        <circle key={i} cx={x(i)} cy={y(v)} r={i === clean.length - 1 ? 2.5 : 1.75} fill={color} />
      ))}
    </svg>
  );
}
