"use client";

import * as React from "react";
import { motion } from "motion/react";
import { NetworkGraph, type ColorMode } from "@/components/graph/network-graph";
import { FilterRail } from "@/components/explorer/filter-rail";
import { DetailPanel } from "@/components/explorer/detail-panel";
import { getGraph } from "@/lib/data";
import type { ConceptCategory, GraphData, GraphNode, Period } from "@/lib/types";

export default function ExplorerPage() {
  const [period, setPeriod] = React.useState<Period>("Q1");
  const [cache, setCache] = React.useState<Partial<Record<Period, GraphData>>>({});
  const [loading, setLoading] = React.useState(true);

  const [industry, setIndustry] = React.useState("all");
  const [category, setCategory] = React.useState<ConceptCategory | "all">("all");
  const [customFilter, setCustomFilter] = React.useState<"all" | "custom" | "standard">("all");
  const [search, setSearch] = React.useState("");
  const [colorBy, setColorBy] = React.useState<ColorMode>("category");
  const [selectedId, setSelectedId] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (cache[period]) {
      setLoading(false);
      return;
    }
    setLoading(true);
    getGraph(period).then((g) => {
      setCache((prev) => ({ ...prev, [period]: g }));
      setLoading(false);
    });
  }, [period, cache]);

  const raw = cache[period];

  const industries = React.useMemo(() => {
    if (!raw) return [];
    const set = new Set<string>();
    for (const n of raw.nodes) if (n.industry) set.add(n.industry);
    return [...set].sort();
  }, [raw]);

  const filtered = React.useMemo<GraphData | null>(() => {
    if (!raw) return null;
    const nodes = raw.nodes.filter((n) => {
      if (industry !== "all" && n.industry !== industry) return false;
      if (category !== "all" && n.category !== category) return false;
      if (customFilter === "custom" && !n.isCustom) return false;
      if (customFilter === "standard" && n.isCustom) return false;
      return true;
    });
    const keep = new Set(nodes.map((n) => n.id));
    const edges = raw.edges.filter(
      (e) => keep.has(e.source as string) && keep.has(e.target as string)
    );
    return { ...raw, nodes, edges, nodeCount: nodes.length, edgeCount: edges.length };
  }, [raw, industry, category, customFilter]);

  const highlightIds = React.useMemo(() => {
    if (!filtered || !search.trim()) return null;
    const q = search.trim().toLowerCase();
    const set = new Set<string>();
    for (const n of filtered.nodes) {
      if (n.id.toLowerCase().includes(q) || n.label.toLowerCase().includes(q)) set.add(n.id);
    }
    return set;
  }, [filtered, search]);

  const selectedNode: GraphNode | null = React.useMemo(() => {
    if (!raw || !selectedId) return null;
    return raw.nodes.find((n) => n.id === selectedId) ?? null;
  }, [raw, selectedId]);

  // Stable identity so NetworkGraph's zoom/click effect doesn't re-attach
  // on every Explorer re-render (e.g. each search keystroke).
  const handleSelect = React.useCallback((n: GraphNode | null) => {
    setSelectedId(n?.id ?? null);
  }, []);

  const handlePeriodChange = React.useCallback((p: Period) => {
    setPeriod(p);
  }, []);

  return (
    <div className="pt-20">
      <div className="mx-auto flex h-[calc(100vh-5rem)] max-w-[1600px] flex-col lg:flex-row">
        <aside className="border-b border-border/60 lg:w-72 lg:shrink-0 lg:border-b-0 lg:border-r">
          {raw && filtered && (
            <FilterRail
              period={period}
              onPeriodChange={handlePeriodChange}
              industries={industries}
              industry={industry}
              onIndustryChange={setIndustry}
              category={category}
              onCategoryChange={setCategory}
              customFilter={customFilter}
              onCustomFilterChange={setCustomFilter}
              search={search}
              onSearchChange={setSearch}
              colorBy={colorBy}
              onColorByChange={setColorBy}
              nodeCount={filtered.nodeCount}
              edgeCount={filtered.edgeCount}
            />
          )}
        </aside>

        <main className="relative min-h-[50vh] flex-1 bg-secondary/30">
          {loading || !filtered ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-sm text-muted-foreground">
              <div className="flex gap-1.5">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    className="h-2 w-2 rounded-full bg-primary"
                    animate={{ opacity: [0.25, 1, 0.25], scale: [0.8, 1, 0.8] }}
                    transition={{ duration: 1, repeat: Infinity, delay: i * 0.15, ease: "easeInOut" }}
                  />
                ))}
              </div>
              Loading {period} concept network…
            </div>
          ) : (
            <NetworkGraph
              data={filtered}
              colorBy={colorBy}
              selectedId={selectedId}
              onSelect={handleSelect}
              highlightIds={highlightIds}
            />
          )}
        </main>

        <aside className="border-t border-border/60 lg:w-80 lg:shrink-0 lg:border-l lg:border-t-0">
          {raw && (
            <DetailPanel
              node={selectedNode}
              data={raw}
              onSelectNeighbor={(id) => setSelectedId(id)}
            />
          )}
        </aside>
      </div>
    </div>
  );
}
