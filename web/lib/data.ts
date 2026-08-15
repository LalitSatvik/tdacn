import type {
  FindingsData,
  GraphData,
  OverviewData,
  Period,
  SegmentationData,
} from "@/lib/types";

// All data lives as static JSON in public/data/, written by
// scripts/export_dashboard_data.py. These helpers work both server-side
// (Server Components, via fs) and client-side (via fetch), covering
// every place data is loaded across the app.

async function readJson<T>(filename: string): Promise<T> {
  if (typeof window === "undefined") {
    const fs = await import("fs/promises");
    const path = await import("path");
    const filePath = path.join(process.cwd(), "public", "data", filename);
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw) as T;
  }
  const res = await fetch(`/data/${filename}`);
  if (!res.ok) {
    throw new Error(`Failed to load /data/${filename}: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function getGraph(period: Period): Promise<GraphData> {
  return readJson<GraphData>(`graph_${period}.json`);
}

export function getOverview(): Promise<OverviewData> {
  return readJson<OverviewData>("overview.json");
}

export function getSegmentation(): Promise<SegmentationData> {
  return readJson<SegmentationData>("segmentation.json");
}

export function getFindings(): Promise<FindingsData> {
  return readJson<FindingsData>("findings.json");
}
