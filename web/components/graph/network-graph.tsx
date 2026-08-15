"use client";

import * as React from "react";
import * as d3 from "d3";
import type { GraphData, GraphEdge, GraphNode } from "@/lib/types";
import { cn } from "@/lib/utils";

export const CATEGORY_COLORS: Record<string, string> = {
  accounting_fact: "#0f7a82", // teal — the site accent, used here because this
  // is the largest/most important category, not decoration
  abstract_header: "#9a9178",
  dimensional: "#c17a4a",
  dei: "#5b7c99",
};

export const LAYER_COLORS: Record<string, string> = {
  structural: "#0f7a82",
  co_reporting: "#c9a24b",
};

export type ColorMode = "category" | "drift" | "layer";

interface NetworkGraphProps {
  data: GraphData;
  colorBy?: ColorMode;
  selectedId?: string | null;
  onSelect?: (node: GraphNode | null) => void;
  highlightIds?: Set<string> | null;
  minWeight?: number;
  /** Decorative mode: no pan/zoom/click, gentle constant slow drift for a hero backdrop. */
  interactive?: boolean;
  className?: string;
}

const NODE_PX = [2, 9] as const; // constant on-screen radius range, px
const EDGE_ALPHA = 0.16;

export function NetworkGraph({
  data,
  colorBy = "category",
  selectedId = null,
  onSelect,
  highlightIds = null,
  minWeight = 0,
  interactive = true,
  className,
}: NetworkGraphProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const canvasRef = React.useRef<HTMLCanvasElement>(null);
  const tooltipRef = React.useRef<HTMLDivElement>(null);
  const transformRef = React.useRef<d3.ZoomTransform>(d3.zoomIdentity);
  const sizeRef = React.useRef({ width: 0, height: 0, dpr: 1 });
  const rafRef = React.useRef<number | null>(null);
  const [hoveredNode, setHoveredNode] = React.useState<GraphNode | null>(null);
  // Resolved from CSS custom properties so edges/selection ring stay
  // legible against either theme's background without hardcoding a color.
  const themeRef = React.useRef({ edge: "#6b6656", ring: "#16160f" });

  const nodesById = React.useMemo(() => {
    const map = new Map<string, GraphNode>();
    for (const n of data.nodes) map.set(n.id, n);
    return map;
  }, [data]);

  const quadtree = React.useMemo(
    () =>
      d3
        .quadtree<GraphNode>()
        .x((d) => d.x)
        .y((d) => d.y)
        .addAll(data.nodes),
    [data]
  );

  const radiusScale = React.useMemo(() => {
    const max = d3.max(data.nodes, (d) => d.pagerank) ?? 1;
    return d3.scaleSqrt().domain([0, max]).range(NODE_PX);
  }, [data]);

  const driftScale = React.useMemo(() => {
    const max = d3.max(data.nodes, (d) => d.driftNext ?? 0) ?? 1;
    return d3.scaleSequential(d3.interpolateViridis).domain([0, max || 1]);
  }, [data]);

  const filteredEdges = React.useMemo<GraphEdge[]>(
    () => (minWeight > 0 ? data.edges.filter((e) => e.weight >= minWeight) : data.edges),
    [data, minWeight]
  );

  const nodeColor = React.useCallback(
    (node: GraphNode) => {
      if (colorBy === "drift") return driftScale(node.driftNext ?? 0);
      return CATEGORY_COLORS[node.category] ?? "#8b8574";
    },
    [colorBy, driftScale]
  );

  const draw = React.useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const { width, height, dpr } = sizeRef.current;
    const t = transformRef.current;

    ctx.save();
    ctx.clearRect(0, 0, width * dpr, height * dpr);
    ctx.scale(dpr, dpr);
    ctx.translate(t.x, t.y);
    ctx.scale(t.k, t.k);

    const dimmed = highlightIds && highlightIds.size > 0;

    // edges, batched per layer color into one path each for speed
    const groups: Record<string, GraphEdge[]> = { structural: [], co_reporting: [] };
    for (const e of filteredEdges) groups[e.layer]?.push(e);

    for (const [layer, edges] of Object.entries(groups)) {
      ctx.beginPath();
      for (const e of edges) {
        const s = nodesById.get(e.source as string);
        const tgt = nodesById.get(e.target as string);
        if (!s || !tgt) continue;
        if (dimmed && !highlightIds!.has(s.id) && !highlightIds!.has(tgt.id)) continue;
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(tgt.x, tgt.y);
      }
      ctx.strokeStyle = colorBy === "layer" ? LAYER_COLORS[layer] : themeRef.current.edge;
      ctx.globalAlpha = dimmed ? EDGE_ALPHA * 0.4 : EDGE_ALPHA;
      ctx.lineWidth = 1 / t.k;
      ctx.stroke();
    }

    // nodes
    ctx.globalAlpha = 1;
    for (const n of data.nodes) {
      const isDimmed = dimmed && !highlightIds!.has(n.id);
      const isSelected = n.id === selectedId;
      const r = (isSelected ? radiusScale(n.pagerank) * 1.6 : radiusScale(n.pagerank)) / t.k;
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fillStyle = nodeColor(n);
      ctx.globalAlpha = isDimmed ? 0.15 : n.isCustom ? 0.55 : 0.92;
      ctx.fill();
      if (isSelected) {
        ctx.lineWidth = 1.5 / t.k;
        ctx.strokeStyle = themeRef.current.ring;
        ctx.globalAlpha = 1;
        ctx.stroke();
      }
    }

    ctx.restore();
  }, [data, filteredEdges, nodesById, radiusScale, nodeColor, colorBy, highlightIds, selectedId]);

  const requestDraw = React.useCallback(() => {
    if (rafRef.current !== null) return;
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null;
      draw();
    });
  }, [draw]);

  // keep edge/selection colors in sync with the active theme
  React.useEffect(() => {
    const readThemeColors = () => {
      const style = getComputedStyle(document.documentElement);
      themeRef.current = {
        edge: style.getPropertyValue("--muted-foreground").trim() || "#6b6656",
        ring: style.getPropertyValue("--foreground").trim() || "#16160f",
      };
      requestDraw();
    };
    readThemeColors();
    const observer = new MutationObserver(readThemeColors);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // size canvas to container + fit initial view to data extent
  React.useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const fit = () => {
      const rect = container.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      sizeRef.current = { width: rect.width, height: rect.height, dpr };
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;

      const xExtent = d3.extent(data.nodes, (d) => d.x) as [number, number];
      const yExtent = d3.extent(data.nodes, (d) => d.y) as [number, number];
      const dataW = Math.max(xExtent[1] - xExtent[0], 0.01);
      const dataH = Math.max(yExtent[1] - yExtent[0], 0.01);
      const k = 0.86 * Math.min(rect.width / dataW, rect.height / dataH);
      const cx = (xExtent[0] + xExtent[1]) / 2;
      const cy = (yExtent[0] + yExtent[1]) / 2;
      const initial = d3.zoomIdentity
        .translate(rect.width / 2, rect.height / 2)
        .scale(k)
        .translate(-cx, -cy);
      transformRef.current = initial;
      requestDraw();
    };

    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(container);
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  // zoom/pan + click-to-select
  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !interactive) return;

    const zoom = d3
      .zoom<HTMLCanvasElement, unknown>()
      .scaleExtent([0.3, 10])
      .on("zoom", (event) => {
        transformRef.current = event.transform;
        requestDraw();
      });

    const selection = d3.select(canvas);
    selection.call(zoom);
    zoom.transform(selection, transformRef.current);

    const handleClick = (event: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const [mx, my] = [event.clientX - rect.left, event.clientY - rect.top];
      const [wx, wy] = transformRef.current.invert([mx, my]);
      const tolerance = 10 / transformRef.current.k;
      const found = quadtree.find(wx, wy, tolerance);
      onSelect?.(found ?? null);
    };
    canvas.addEventListener("click", handleClick);

    const handleMouseMove = (event: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const [mx, my] = [event.clientX - rect.left, event.clientY - rect.top];
      const [wx, wy] = transformRef.current.invert([mx, my]);
      const tolerance = 10 / transformRef.current.k;
      const found = quadtree.find(wx, wy, tolerance) ?? null;

      const tooltip = tooltipRef.current;
      if (tooltip) {
        tooltip.style.transform = `translate(${mx}px, ${my}px)`;
      }
      canvas.style.cursor = found ? "pointer" : "grab";
      setHoveredNode((prev) => (prev?.id === found?.id ? prev : found));
    };
    const handleMouseLeave = () => setHoveredNode(null);
    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("mouseleave", handleMouseLeave);

    return () => {
      selection.on(".zoom", null);
      canvas.removeEventListener("click", handleClick);
      canvas.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, [quadtree, onSelect, interactive, requestDraw]);

  // slow ambient drift for decorative/non-interactive hero use
  React.useEffect(() => {
    if (interactive) return;
    let raf: number;
    let angle = 0;
    const tick = () => {
      angle += 0.00012;
      const base = transformRef.current;
      transformRef.current = base.translate(Math.sin(angle) * 0.02, Math.cos(angle) * 0.02);
      draw();
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interactive]);

  React.useEffect(() => {
    requestDraw();
  }, [requestDraw, selectedId, highlightIds]);

  return (
    <div ref={containerRef} className={cn("relative h-full w-full", className)}>
      <canvas
        ref={canvasRef}
        className={interactive ? "cursor-grab active:cursor-grabbing" : "pointer-events-none"}
      />
      {interactive && (
        // No dynamic `style` prop here on purpose: position is mutated
        // imperatively (mousemove) so it never fights a React re-render
        // triggered by hoveredNode changing; only opacity is state-driven.
        <div ref={tooltipRef} className="pointer-events-none absolute left-0 top-0 z-20 will-change-transform">
          <div
            className={cn(
              "-translate-x-1/2 -translate-y-[calc(100%+10px)] whitespace-nowrap rounded-lg border border-border bg-card px-2.5 py-1.5 text-[11px] shadow-lg transition-opacity duration-100",
              hoveredNode ? "opacity-100" : "opacity-0"
            )}
          >
            <div className="font-mono font-medium text-foreground">{hoveredNode?.label}</div>
            <div className="text-muted-foreground">
              {hoveredNode && (
                <>
                  PageRank {hoveredNode.pagerank.toFixed(4)} · degree {hoveredNode.degree.toFixed(1)}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
