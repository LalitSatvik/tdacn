"use client";

import * as React from "react";
import { NetworkGraph } from "@/components/graph/network-graph";
import { LiquidChrome } from "@/components/background/liquid-chrome";
import type { GraphData } from "@/lib/types";

/**
 * The homepage/architecture-page hero visual: a live WebGL "chrome water"
 * shader (topology.vc's material) with the *real* concept graph rendered
 * on top in screen-blend, decoratively (no pan/zoom/click) -- the graph
 * is our own mechanism, not borrowed decoration, fused into the material
 * everything else on the page also uses for buttons and cards.
 */
export function HeroGraph({ data, intensity = 1 }: { data: GraphData; intensity?: number }) {
  return (
    <div className="absolute inset-0 overflow-hidden bg-[#0a0a08]">
      <LiquidChrome className="absolute inset-0 h-full w-full" intensity={intensity} />
      <div className="absolute inset-0 opacity-[0.65] mix-blend-screen">
        <NetworkGraph data={data} colorBy="category" interactive={false} />
      </div>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-background" />
    </div>
  );
}
