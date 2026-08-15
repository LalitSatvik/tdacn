"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { motion } from "motion/react";
import type { ConceptCategory, Period } from "@/lib/types";
import { cn } from "@/lib/utils";
import { CATEGORY_COLORS } from "@/components/graph/network-graph";

const CATEGORY_LABELS: Record<ConceptCategory | "all", string> = {
  all: "All",
  accounting_fact: "Core / fact",
  abstract_header: "Abstract header",
  dimensional: "Dimensional",
  dei: "DEI (cover page)",
};

interface FilterRailProps {
  period: Period;
  onPeriodChange: (p: Period) => void;
  industries: string[];
  industry: string;
  onIndustryChange: (v: string) => void;
  category: ConceptCategory | "all";
  onCategoryChange: (v: ConceptCategory | "all") => void;
  customFilter: "all" | "custom" | "standard";
  onCustomFilterChange: (v: "all" | "custom" | "standard") => void;
  search: string;
  onSearchChange: (v: string) => void;
  colorBy: "category" | "drift" | "layer";
  onColorByChange: (v: "category" | "drift" | "layer") => void;
  nodeCount: number;
  edgeCount: number;
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <div className="mb-2 text-xs font-medium text-foreground">{children}</div>;
}

function Pill({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-full px-3 py-1.5 text-left text-xs font-medium transition-colors",
        active
          ? "bg-primary text-primary-foreground"
          : "bg-secondary text-foreground/70 hover:bg-secondary/70"
      )}
    >
      {children}
    </button>
  );
}

export function FilterRail(props: FilterRailProps) {
  const {
    period,
    onPeriodChange,
    industries,
    industry,
    onIndustryChange,
    category,
    onCategoryChange,
    customFilter,
    onCustomFilterChange,
    search,
    onSearchChange,
    colorBy,
    onColorByChange,
    nodeCount,
    edgeCount,
  } = props;

  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="flex h-full flex-col gap-6 overflow-y-auto p-5"
    >
      <div>
        <FieldLabel>Period</FieldLabel>
        <div className="flex gap-1 rounded-full bg-secondary p-1">
          {(["Q1", "Q2", "Q3"] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => onPeriodChange(p)}
              className={cn(
                "relative flex-1 rounded-full py-1.5 text-xs font-semibold transition-colors",
                period === p ? "text-primary-foreground" : "text-foreground/60"
              )}
            >
              {period === p && (
                <motion.span
                  layoutId="period-active-pill"
                  transition={{ type: "spring", stiffness: 420, damping: 34 }}
                  className="absolute inset-0 rounded-full bg-primary"
                />
              )}
              <span className="relative z-10">{p}</span>
            </button>
          ))}
        </div>
      </div>

      <div>
        <FieldLabel>Search concept</FieldLabel>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="e.g. OperatingLeaseLiability"
            className="w-full rounded-full border border-border bg-card py-2 pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground transition-shadow focus:outline-none focus:ring-2 focus:ring-ring/40"
          />
        </div>
      </div>

      <div>
        <FieldLabel>Concept category</FieldLabel>
        <div className="flex flex-col gap-1.5">
          {(Object.keys(CATEGORY_LABELS) as (ConceptCategory | "all")[]).map((c) => (
            <button
              key={c}
              onClick={() => onCategoryChange(c)}
              className={cn(
                "flex items-center gap-2 rounded-full px-3 py-1.5 text-left text-xs font-medium transition-colors",
                category === c
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-foreground/70 hover:bg-secondary/70"
              )}
            >
              {c !== "all" && (
                <span
                  className="h-2 w-2 shrink-0 rounded-full"
                  style={{ backgroundColor: CATEGORY_COLORS[c] }}
                />
              )}
              {CATEGORY_LABELS[c]}
            </button>
          ))}
        </div>
      </div>

      <div>
        <FieldLabel>Tag origin</FieldLabel>
        <div className="flex gap-1.5">
          <Pill active={customFilter === "all"} onClick={() => onCustomFilterChange("all")}>
            All
          </Pill>
          <Pill active={customFilter === "standard"} onClick={() => onCustomFilterChange("standard")}>
            Standard
          </Pill>
          <Pill active={customFilter === "custom"} onClick={() => onCustomFilterChange("custom")}>
            Custom
          </Pill>
        </div>
      </div>

      <div>
        <FieldLabel>Industry</FieldLabel>
        <select
          value={industry}
          onChange={(e) => onIndustryChange(e.target.value)}
          className="w-full rounded-full border border-border bg-card px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-ring/40"
        >
          <option value="all">All industries</option>
          {industries.map((i) => (
            <option key={i} value={i}>
              {i}
            </option>
          ))}
        </select>
      </div>

      <div>
        <FieldLabel>Color nodes by</FieldLabel>
        <div className="flex flex-col gap-1.5">
          {(["category", "drift", "layer"] as const).map((c) => (
            <Pill key={c} active={colorBy === c} onClick={() => onColorByChange(c)}>
              {c === "category" ? "Concept category" : c === "drift" ? "Drift into next quarter" : "Edge layer"}
            </Pill>
          ))}
        </div>
      </div>

      <div className="mt-auto rounded-2xl bg-secondary/60 p-3 text-[11px] text-muted-foreground">
        Showing <span className="font-mono text-foreground">{nodeCount.toLocaleString()}</span>{" "}
        concepts,{" "}
        <span className="font-mono text-foreground">{edgeCount.toLocaleString()}</span> edges.
      </div>
    </motion.div>
  );
}
