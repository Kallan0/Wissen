"use client";

import React from "react";
import { Database, Key, Sparkles, Check, Stamp } from "lucide-react";
import { RAGContext } from "@/lib/types";

interface RetrievalMatchesProps {
  context: RAGContext | null;
}

export default function RetrievalMatches({ context }: RetrievalMatchesProps) {
  if (!context || context.match_count === 0) return null;

  return (
    <div className="bg-[#fffdf9] p-5 sm:p-6 rounded-xl border-2 border-ink shadow-press space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b-2 border-ink/20 pb-3 gap-2">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-terracotta" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-ink">
            ChromaDB RAG Retrieval Docket ({context.match_count} Verified Highlights)
          </h3>
        </div>
        <span className="font-mono text-[10px] uppercase tracking-widest bg-ink text-paper px-2 py-0.5 font-bold rounded">
          ZERO-HALLUCINATION GROUNDING
        </span>
      </div>

      {context.context_metrics && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <div className="rounded border border-ink/20 bg-paper p-2 font-mono text-[10px] text-ink">
            <div className="font-bold">{context.context_metrics.source_sections_included}/{context.context_metrics.source_sections_available}</div>
            <div className="uppercase text-ink-muted">Source sections</div>
          </div>
          <div className="rounded border border-ink/20 bg-paper p-2 font-mono text-[10px] text-ink">
            <div className="font-bold">~{context.context_metrics.approximate_tokens.toLocaleString()}</div>
            <div className="uppercase text-ink-muted">Context tokens</div>
          </div>
          <div className="rounded border border-ink/20 bg-paper p-2 font-mono text-[10px] text-ink">
            <div className="font-bold">{context.context_metrics.characters.toLocaleString()}</div>
            <div className="uppercase text-ink-muted">Characters</div>
          </div>
          <div className="rounded border border-ink/20 bg-paper p-2 font-mono text-[10px] text-ink">
            <div className="font-bold">Complete</div>
            <div className="uppercase text-ink-muted">Coverage mode</div>
          </div>
        </div>
      )}

      {/* Keywords matched */}
      {context.keywords && context.keywords.length > 0 && (
        <div>
          <div className="font-mono text-[10px] font-bold uppercase tracking-wider text-ink-muted mb-1.5 flex items-center gap-1">
            <Key className="w-3 h-3 text-terracotta" />
            Extracted JD Matching Signals
          </div>
          <div className="flex flex-wrap gap-1.5">
            {context.keywords.map((kw, idx) => (
              <span
                key={idx}
                className="bg-manila text-ink font-mono text-xs px-2 py-0.5 rounded border border-ink/30"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {context.expanded_concepts && context.expanded_concepts.length > 0 && (
        <div>
          <div className="mb-1.5 flex items-center gap-1 font-mono text-[10px] font-bold uppercase tracking-wider text-ink-muted">
            <Sparkles className="h-3 w-3 text-fountain-teal" />
            LLM Query Expansion
          </div>
          <div className="flex flex-wrap gap-1.5">
            {context.expanded_concepts.map((concept, index) => (
              <span key={index} className="rounded border border-fountain-teal/40 bg-fountain-teal/10 px-2 py-0.5 font-mono text-xs text-ink">
                {concept}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Retrieved items grid */}
      <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
        {context.retrieved_items.map((item, idx) => {
          const matchPercent = Math.round(item.similarity * 100);
          return (
            <div
              key={idx}
              className="p-3 bg-paper rounded-lg border-2 border-ink/20 text-xs hover:border-ink transition font-serif"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono font-bold text-ink uppercase text-[10px] tracking-wide bg-manila px-1.5 py-0.5 rounded border border-ink/30">
                  [{item.collection}]
                </span>
                <span className="font-mono text-[10px] font-bold text-terracotta bg-[#fff0ed] px-2 py-0.5 rounded border border-terracotta/40">
                  {matchPercent}% RELEVANCE
                </span>
              </div>
              <p className="text-ink/90 leading-relaxed">{item.content}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

