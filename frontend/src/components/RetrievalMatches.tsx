"use client";

import React from "react";
import { Database, Key, Sparkles, Check } from "lucide-react";
import { RAGContext } from "@/lib/types";

interface RetrievalMatchesProps {
  context: RAGContext | null;
}

export default function RetrievalMatches({ context }: RetrievalMatchesProps) {
  if (!context || context.match_count === 0) return null;

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-indigo-600" />
          <h3 className="text-sm font-bold text-slate-800">
            ChromaDB RAG Retrieval Provenance ({context.match_count} Verified Highlights)
          </h3>
        </div>
        <span className="text-xs bg-indigo-50 text-indigo-700 px-2.5 py-0.5 rounded-full font-medium border border-indigo-100">
          Zero-Hallucination Grounding
        </span>
      </div>

      {/* Keywords matched */}
      {context.keywords && context.keywords.length > 0 && (
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5 flex items-center gap-1">
            <Key className="w-3 h-3" />
            Extracted JD Keywords
          </div>
          <div className="flex flex-wrap gap-1.5">
            {context.keywords.map((kw, idx) => (
              <span
                key={idx}
                className="bg-slate-100 text-slate-700 text-xs px-2 py-0.5 rounded border border-slate-200 font-mono"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Retrieved items grid */}
      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {context.retrieved_items.map((item, idx) => {
          const matchPercent = Math.round(item.similarity * 100);
          return (
            <div
              key={idx}
              className="p-2.5 bg-slate-50 rounded-lg border border-slate-200/80 text-xs hover:border-indigo-300 transition"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-slate-700 uppercase text-[10px] tracking-wide">
                  [{item.collection}]
                </span>
                <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
                  {matchPercent}% Relevance
                </span>
              </div>
              <p className="text-slate-600 leading-normal">{item.content}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
