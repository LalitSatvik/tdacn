"use client";

import * as React from "react";
import { AnimatePresence, motion } from "motion/react";
import type { GraphData, GraphNode } from "@/lib/types";
import { CATEGORY_COLORS } from "@/components/graph/network-graph";
import { cn } from "@/lib/utils";

interface DetailPanelProps {
  node: GraphNode | null;
  data: GraphData;
  onSelectNeighbor: (id: string) => void;
}

export function DetailPanel({ node, data, onSelectNeighbor }: DetailPanelProps) {
  // Hooks must run unconditionally on every render, so this is computed
  // before the "nothing selected" early return below.
  const neighbors = React.useMemo(() => {
    if (!node) return [];
    const rows: { id: string; weight: number }[] = [];
    for (const e of data.edges) {
      if (e.source === node.id) rows.push({ id: e.target as string, weight: e.weight });
      else if (e.target === node.id) rows.push({ id: e.source as string, weight: e.weight });
    }
    return rows.sort((a, b) => b.weight - a.weight).slice(0, 10);
  }, [data, node]);

  return (
    <AnimatePresence mode="wait">
      {!node ? (
        <motion.div
          key="empty"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="flex h-full flex-col items-center justify-center p-8 text-center"
        >
          <div className="text-sm font-medium text-foreground">No concept selected</div>
          <p className="mt-2 max-w-[220px] text-xs text-muted-foreground">
            Click any node in the network, or search for a concept in the left panel.
          </p>
        </motion.div>
      ) : (
        <motion.div
          key={node.id}
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -8 }}
          transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
          className="flex h-full flex-col gap-6 overflow-y-auto p-5"
        >
          <div>
            <div className="flex items-center gap-2">
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: CATEGORY_COLORS[node.category] }}
              />
              <span className="text-xs font-medium text-muted-foreground">
                {node.category.replace("_", " ")}
              </span>
            </div>
            <h3 className="font-mono mt-2 break-words text-lg font-semibold text-foreground">
              {node.label}
            </h3>
            {node.isCustom && (
              <span className="mt-2 inline-block rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-700 dark:text-amber-400">
                Custom / company-specific tag
              </span>
            )}
          </div>

          <dl className="grid grid-cols-2 gap-3 text-xs">
            <Stat label="PageRank" value={node.pagerank.toFixed(4)} />
            <Stat label="Weighted degree" value={node.degree.toFixed(1)} />
            <Stat
              label="Drift → next quarter"
              value={node.driftNext !== null ? node.driftNext.toFixed(3) : "n/a (last period)"}
            />
            <Stat label="Industry" value={node.industry ?? "—"} />
            <Stat label="Filer size" value={node.sizeClass ?? "—"} />
            <Stat label="Mean complexity" value={node.complexity !== null ? node.complexity.toFixed(1) : "—"} />
          </dl>

          <div>
            <div className="mb-2 text-xs font-medium text-foreground">Strongest connections</div>
            <div className="flex flex-col gap-1">
              {neighbors.map((n) => (
                <button
                  key={n.id}
                  onClick={() => onSelectNeighbor(n.id)}
                  className="flex items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-left text-xs transition-colors hover:bg-secondary"
                >
                  <span className="truncate font-mono text-foreground">{n.id}</span>
                  <span className="shrink-0 text-muted-foreground">{n.weight.toFixed(2)}</span>
                </button>
              ))}
              {neighbors.length === 0 && (
                <div className="text-xs text-muted-foreground">No surviving edges after sparsification.</div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className={cn("rounded-xl bg-secondary/60 p-2.5")}>
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-0.5 truncate font-medium text-foreground">{value}</div>
    </div>
  );
}
