"use client";

import * as d3 from "d3";
import * as React from "react";
import { motion } from "motion/react";

export interface BarDatum {
  group: string;
  mean: number;
  n: number;
}

interface BarChartProps {
  data: BarDatum[];
  height?: number;
  color?: string;
  valueFormat?: (v: number) => string;
  /** Groups with n below this render at reduced opacity — small-n caution, per findings.md. */
  smallN?: number;
  className?: string;
}

/** Horizontal bar chart — drift-by-industry / by-size / by-complexity. */
export function BarChart({
  data,
  height = 22,
  color = "#0f7a82",
  valueFormat = (v) => v.toFixed(3),
  smallN = 20,
  className,
}: BarChartProps) {
  const [hovered, setHovered] = React.useState<string | null>(null);
  const sorted = [...data].sort((a, b) => b.mean - a.mean);
  const max = d3.max(sorted, (d) => d.mean) ?? 1;
  const scale = d3.scaleLinear().domain([0, max]).range([0, 100]);

  return (
    <div className={className}>
      <div className="flex flex-col gap-2.5">
        {sorted.map((d) => {
          const isHovered = hovered === d.group;
          return (
            <div
              key={d.group}
              style={{ opacity: d.n < smallN ? 0.55 : 1 }}
              onMouseEnter={() => setHovered(d.group)}
              onMouseLeave={() => setHovered((prev) => (prev === d.group ? null : prev))}
            >
              <div className="mb-1 flex items-baseline justify-between gap-2 text-xs">
                <span className={isHovered ? "truncate font-semibold text-foreground" : "truncate font-medium text-foreground"}>
                  {d.group}
                </span>
                <span className="shrink-0 font-mono text-muted-foreground">
                  {valueFormat(d.mean)} <span className="text-muted-foreground/70">n={d.n}</span>
                </span>
              </div>
              <div className="w-full overflow-hidden rounded-full bg-muted" style={{ height }}>
                <motion.div
                  className="rounded-full"
                  initial={{ width: 0 }}
                  whileInView={{ width: `${scale(d.mean)}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                  style={{
                    height,
                    backgroundColor: color,
                    filter: isHovered ? "brightness(1.15)" : "none",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
