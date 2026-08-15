import { getSegmentation } from "@/lib/data";
import { Card, SectionHeading } from "@/components/ui/card";
import { BarChart } from "@/components/charts/bar-chart";
import { ScatterPlot } from "@/components/charts/scatter-plot";
import { Reveal, StaggerGroup, StaggerItem } from "@/components/motion/reveal";

const SIZE_LABELS: Record<string, string> = {
  "1-LAF": "Large accelerated filer",
  "2-ACC": "Accelerated filer",
  "3-SRA": "Smaller reporting, accelerated",
  "4-NON": "Non-accelerated / smaller filer",
};

export default async function SegmentationPage() {
  const seg = await getSegmentation();

  const bySizeLabeled = seg.bySize.map((s) => ({ ...s, group: SIZE_LABELS[s.group] ?? s.group }));
  const byComplexityLabeled = seg.byComplexity.map((s) => ({
    ...s,
    group: `${s.group[0].toUpperCase()}${s.group.slice(1)} complexity`,
  }));

  const standard = seg.customVsStandard.drift.find((d) => !d.isCustom);
  const custom = seg.customVsStandard.drift.find((d) => d.isCustom);

  return (
    <div className="mx-auto max-w-6xl px-6 pb-28 pt-32">
      <Reveal>
        <SectionHeading
          accent="Segmentation:"
          title="does drift differ by industry, size, or complexity?"
          description={
            <>
              Each concept is attributed to the plurality industry, filer-size
              class, and reporting-complexity profile of the entities that
              report it (Q1, {seg.sampleSize.toLocaleString()} accounting-fact
              concepts) — a proxy method, not fully rebuilt per-segment
              subgraphs.
            </>
          }
        />
      </Reveal>

      <Reveal index={1}>
        <Card variant="tinted" interactive className="mt-10 p-8">
          <div className="text-sm font-medium text-primary">Most surprising segmentation finding</div>
          <p className="font-display mt-3 text-2xl leading-snug text-foreground">
            Larger, more &ldquo;core&rdquo; accounting concepts drift more, not
            less. Non-accelerated (smaller) filers show{" "}
            <span className="font-semibold">less</span> drift than large
            accelerated filers — the opposite of the naive hypothesis, because
            PMI weighting discounts ubiquitous co-occurrence.
          </p>
        </Card>
      </Reveal>

      <StaggerGroup className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <StaggerItem className="lg:col-span-2">
          <Card interactive className="h-full p-6">
            <div className="text-sm font-semibold text-foreground">Drift by industry</div>
            <div className="mb-5 mt-0.5 text-xs text-muted-foreground">
              Mean cosine drift, Q1→Q2. Faded bars = small sample, treat cautiously.
            </div>
            <BarChart data={seg.byIndustry} />
          </Card>
        </StaggerItem>
        <StaggerItem>
          <Card interactive className="h-full p-6">
            <div className="text-sm font-semibold text-foreground">Drift by filer size</div>
            <div className="mb-5 mt-0.5 text-xs text-muted-foreground">SEC accelerated-filer class</div>
            <BarChart data={bySizeLabeled} smallN={0} />
          </Card>
        </StaggerItem>
      </StaggerGroup>

      <StaggerGroup className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <StaggerItem>
          <Card interactive className="h-full p-6">
            <div className="text-sm font-semibold text-foreground">Drift by complexity tercile</div>
            <div className="mb-5 mt-0.5 text-xs text-muted-foreground">
              Terciles of mean unique tags used per reporting entity
            </div>
            <BarChart data={byComplexityLabeled} smallN={0} />
          </Card>
        </StaggerItem>
        <StaggerItem className="lg:col-span-2">
          <Card interactive className="h-full p-6">
            <div className="text-sm font-semibold text-foreground">Centrality vs. drift</div>
            <div className="mb-3 mt-0.5 text-xs text-muted-foreground">
              Q1 PageRank vs. Q1→Q2 cosine drift, one point per concept (hover
              to inspect) — more central concepts drift less (Spearman ≈ −0.29).
            </div>
            <ScatterPlot
              data={seg.centralityVsDrift.map((d) => ({ id: d.conceptId, x: d.pagerank, y: d.drift }))}
              xLabel="Q1 PageRank"
              yLabel="Cosine drift"
            />
          </Card>
        </StaggerItem>
      </StaggerGroup>

      <Reveal>
        <Card interactive className="mt-4 overflow-hidden p-6">
          <div className="text-sm font-semibold text-foreground">Regression: what predicts drift?</div>
          <div className="mb-5 mt-0.5 font-mono text-xs text-muted-foreground">{seg.regressionFormula}</div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="py-2 pr-4 font-medium">Term</th>
                  <th className="py-2 pr-4 font-medium">Coefficient</th>
                  <th className="py-2 pr-4 font-medium">Std. error</th>
                  <th className="py-2 font-medium">p-value</th>
                </tr>
              </thead>
              <tbody>
                {seg.regression.map((r) => (
                  <tr key={r.term} className="border-b border-border/50 transition-colors last:border-0 hover:bg-secondary/60">
                    <td className="py-2 pr-4 font-mono text-foreground">{r.term}</td>
                    <td className="py-2 pr-4 tabular-nums text-foreground">{r.coef.toFixed(4)}</td>
                    <td className="py-2 pr-4 tabular-nums text-muted-foreground">{r.stdErr.toFixed(4)}</td>
                    <td
                      className={
                        r.significant ? "py-2 tabular-nums font-medium text-primary" : "py-2 tabular-nums text-muted-foreground"
                      }
                    >
                      {r.pValue < 0.001 ? "<0.001" : r.pValue.toFixed(4)}
                      {r.significant && " *"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[11px] text-muted-foreground">
            * p &lt; 0.05. Standard errors are not clustered by filer — see Findings for known limitations.
          </p>
        </Card>
      </Reveal>

      {standard && custom && (
        <Reveal>
          <Card interactive className="mt-4 p-6">
            <div className="text-sm font-semibold text-foreground">Custom vs. standard tags</div>
            <div className="mt-4 grid grid-cols-1 gap-6 text-sm sm:grid-cols-2">
              <div>
                <div className="text-xs text-muted-foreground">Mean drift, Q1→Q2</div>
                <div className="mt-1 flex items-baseline gap-3">
                  <span className="font-display text-xl text-foreground">{standard.mean.toFixed(3)}</span>
                  <span className="text-xs text-muted-foreground">standard</span>
                  <span className="font-display text-xl text-foreground">{custom.mean.toFixed(3)}</span>
                  <span className="text-xs text-muted-foreground">custom</span>
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">Essentially no difference in drift.</p>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Mean weighted degree, Q1</div>
                <div className="mt-1 flex items-baseline gap-3">
                  <span className="font-display text-xl text-foreground">
                    {seg.customVsStandard.weightedDegree.find((d) => !d.isCustom)?.mean.toFixed(1)}
                  </span>
                  <span className="text-xs text-muted-foreground">standard</span>
                  <span className="font-display text-xl text-foreground">
                    {seg.customVsStandard.weightedDegree.find((d) => d.isCustom)?.mean.toFixed(1)}
                  </span>
                  <span className="text-xs text-muted-foreground">custom</span>
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Custom tags that survive min-support are more, not less, connected.
                </p>
              </div>
            </div>
          </Card>
        </Reveal>
      )}
    </div>
  );
}
