import { ArrowRight } from "lucide-react";
import { getGraph } from "@/lib/data";
import { subsampleGraph } from "@/lib/graph-utils";
import { HeroGraph } from "@/components/graph/hero-graph";
import { Card, SectionHeading } from "@/components/ui/card";
import { Reveal, StaggerGroup, StaggerItem } from "@/components/motion/reveal";

const STAGES = [
  { label: "Raw filings", detail: "SEC DERA sub/tag/num/pre.txt" },
  { label: "Adapter", detail: "SecDeraAdapter → CanonicalBundle" },
  { label: "Graph", detail: "support → edges → PMI → sparsify → blend" },
  { label: "Embed", detail: "node2vec + Procrustes alignment" },
  { label: "Metrics", detail: "embedding / graph / global drift" },
  { label: "Export", detail: "export_dashboard_data.py → JSON" },
];

const MODULES = [
  { module: "schema.py", responsibility: "Canonical tables + validation" },
  { module: "adapters/", responsibility: "AdapterBase, SecDeraAdapter" },
  { module: "ingest/", responsibility: "concat_bundles, save/load_bundle (Parquet cache)" },
  { module: "graph/", responsibility: "support → edges → pmi → sparsify → blend → build/pipeline" },
  { module: "embed/", responsibility: "train_node2vec, procrustes_align / align_periods" },
  { module: "metrics/", responsibility: "embedding_drift, graph_drift, global_drift, validation" },
  { module: "segment/", responsibility: "industry, complexity, concept_category, concept_profile, regression" },
];

export default async function ArchitecturePage() {
  const graphQ1 = await getGraph("Q1");
  const strip = subsampleGraph(graphQ1, 260);

  return (
    <div>
      <section className="relative flex h-[46vh] min-h-[320px] items-end overflow-hidden">
        <HeroGraph data={strip} intensity={0.7} />
        <div className="relative z-10 mx-auto w-full max-w-6xl px-6 pb-14">
          <h1 className="font-display max-w-2xl text-4xl font-semibold text-white sm:text-5xl">
            How the pipeline is built
          </h1>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-6 pb-28 pt-16">
        <Reveal>
          <p className="max-w-2xl text-sm text-muted-foreground">
            All analysis code operates on a canonical schema (<code className="font-mono">tdacn.schema</code>)
            — five abstract tables never touched by dataset-specific column names. A dataset adapter
            is the only place that knows about a specific source format; porting to a new source
            means writing a new adapter, no other code changes.
          </p>
        </Reveal>

        <StaggerGroup className="mt-12 flex flex-wrap items-stretch gap-2 overflow-x-auto pb-2">
          {STAGES.map((s, i) => (
            <StaggerItem key={s.label} className="flex items-stretch gap-2">
              <Card interactive className="flex w-44 shrink-0 flex-col justify-center gap-1 p-4">
                <div className="text-sm font-semibold text-foreground">{s.label}</div>
                <div className="text-[11px] text-muted-foreground">{s.detail}</div>
              </Card>
              {i < STAGES.length - 1 && (
                <ArrowRight className="my-auto h-4 w-4 shrink-0 text-primary" />
              )}
            </StaggerItem>
          ))}
        </StaggerGroup>

        <Reveal>
          <Card interactive className="mt-12 overflow-hidden p-6">
            <div className="text-sm font-semibold text-foreground">Package layout — src/tdacn/</div>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="py-2 pr-4 font-medium">Module</th>
                    <th className="py-2 font-medium">Responsibility</th>
                  </tr>
                </thead>
                <tbody>
                  {MODULES.map((m) => (
                    <tr key={m.module} className="border-b border-border/50 transition-colors last:border-0 hover:bg-secondary/60">
                      <td className="py-2.5 pr-4 font-mono text-foreground">{m.module}</td>
                      <td className="py-2.5 text-muted-foreground">{m.responsibility}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </Reveal>

        <Reveal>
          <Card variant="tinted" className="mt-6 p-6 text-sm text-muted-foreground">
            This dashboard is itself a new final pipeline stage —{" "}
            <code className="font-mono text-foreground">scripts/export_dashboard_data.py</code> reads
            the cached parquet/pickle outputs above and writes the JSON this site reads directly, so
            nothing here re-derives or re-fits anything the pipeline didn&rsquo;t already compute.
          </Card>
        </Reveal>
      </div>
    </div>
  );
}
