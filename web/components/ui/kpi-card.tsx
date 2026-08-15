"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { Sparkline } from "@/components/charts/sparkline";
import { AnimatedNumber } from "@/components/motion/animated-number";
import { cn } from "@/lib/utils";

// A plain function prop can't cross the Server->Client boundary (KpiCard
// renders AnimatedNumber, which needs hooks), so formatting is selected
// by key instead of passed as a closure.
export type FormatKind = "decimal" | "percent" | "pvalue" | "integer";

const FORMATTERS: Record<FormatKind, (v: number) => string> = {
  decimal: (v) => v.toFixed(3),
  percent: (v) => `${(v * 100).toFixed(1)}%`,
  pvalue: (v) => `p=${v.toFixed(4)}`,
  integer: (v) => String(Math.round(v)),
};

interface KpiCardProps {
  label: string;
  sublabel?: string;
  q1q2: number | null;
  q2q3: number | null;
  format?: FormatKind;
  hero?: boolean;
  decelerating?: boolean | null;
  className?: string;
}

export function KpiCard({
  label,
  sublabel,
  q1q2,
  q2q3,
  format = "decimal",
  hero = false,
  decelerating,
  className,
}: KpiCardProps) {
  const fmt = FORMATTERS[format];
  const headline = q2q3 !== null ? q2q3 : q1q2;

  return (
    <Card
      variant={hero ? "tinted" : "default"}
      interactive
      className={cn("flex flex-col justify-between gap-5 p-6", hero && "sm:p-8", className)}
    >
      <div>
        <div className={cn("font-medium text-foreground", hero ? "text-base" : "text-sm")}>{label}</div>
        {sublabel && <div className="mt-0.5 text-xs text-muted-foreground">{sublabel}</div>}
      </div>
      <div className="flex items-end justify-between gap-3">
        <div>
          <div
            className={cn(
              "font-display font-semibold tabular-nums text-foreground",
              hero ? "text-4xl sm:text-5xl" : "text-3xl"
            )}
          >
            {headline !== null ? <AnimatedNumber value={headline} format={fmt} /> : "—"}
          </div>
          <div className="mt-2 text-[11px] text-muted-foreground">
            {q1q2 !== null && q2q3 !== null ? (
              <>
                {fmt(q1q2)} → {fmt(q2q3)}
                {decelerating !== null && decelerating !== undefined && (
                  <span className={cn("ml-1.5 font-medium", decelerating ? "text-primary" : "text-amber-600 dark:text-amber-400")}>
                    {decelerating ? "↓ decelerating" : "↑ accelerating"}
                  </span>
                )}
              </>
            ) : (
              "Q1 → Q2 → Q3"
            )}
          </div>
        </div>
        <Sparkline
          values={[q1q2, q2q3]}
          width={hero ? 128 : 88}
          height={hero ? 36 : 26}
          color={hero ? "#0f7a82" : "currentColor"}
          className={hero ? "" : "text-muted-foreground/70"}
        />
      </div>
    </Card>
  );
}
