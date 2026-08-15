import type { GraphData } from "@/lib/types";

/**
 * Keep only the top-N nodes by PageRank (plus edges between them). Used for
 * decorative/hero renders of the graph, where the full ~8-9K node / ~90K
 * edge period graph would be needlessly heavy for a blurred backdrop.
 */
export function subsampleGraph(data: GraphData, topN: number): GraphData {
  const top = [...data.nodes].sort((a, b) => b.pagerank - a.pagerank).slice(0, topN);
  const keep = new Set(top.map((n) => n.id));
  const edges = data.edges.filter(
    (e) => keep.has(e.source as unknown as string) && keep.has(e.target as unknown as string)
  );
  return { ...data, nodes: top, edges, nodeCount: top.length, edgeCount: edges.length };
}
