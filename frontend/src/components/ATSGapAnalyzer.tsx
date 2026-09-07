"use client";

import React from "react";
import { Target, CheckCircle2, AlertTriangle, Lightbulb, Sparkles } from "lucide-react";
import { ATSAnalysisResponse } from "@/lib/types";

interface ATSGapAnalyzerProps {
  data: ATSAnalysisResponse | null;
  loading: boolean;
  onAnalyze: () => void;
}

export default function ATSGapAnalyzer({
  data,
  loading,
  onAnalyze,
}: ATSGapAnalyzerProps) {
  return (
    <div className="bg-[#fffdf9] p-6 rounded-xl border-2 border-ink shadow-dossier my-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b-2 border-ink/20 gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] uppercase tracking-widest bg-ink text-paper px-2 py-0.5 font-bold">
              ATS MATCH MATRIX
            </span>
            <span className="font-mono text-[10px] text-ink-muted uppercase">
              SEMANTIC KEYWORD GAP ANALYSIS
            </span>
          </div>
          <h3 className="text-xl font-serif font-bold text-ink flex items-center gap-2">
            <Target className="w-5 h-5 text-terracotta" />
            ATS Keyword Gap & Match Matrix
          </h3>
          <p className="text-xs font-serif italic text-ink-muted mt-0.5">
            Compares job description requirements against your ChromaDB verified background.
          </p>
        </div>

        <button
          type="button"
          onClick={onAnalyze}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded border-2 border-ink shadow-press transition-all disabled:opacity-50 shrink-0"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-paper border-t-transparent rounded-full animate-spin" />
              ANALYZING ATS MATCH...
            </>
          ) : (
            <>
              <Sparkles className="w-3.5 h-3.5 text-paper" />
              ANALYZE ATS MATCH
            </>
          )}
        </button>
      </div>

      {data ? (
        <div className="space-y-4">
          {/* Header Score Row */}
          <div className="flex items-center justify-between p-4 bg-manila/50 border-2 border-ink rounded-lg shadow-press">
            <div>
              <span className="font-mono text-[10px] uppercase font-bold text-ink-muted">ATS OVERALL VERDICT</span>
              <p className="font-serif text-xs text-ink font-semibold mt-0.5">{data.summary_verdict}</p>
            </div>
            <div className="shrink-0 border-2 border-dashed border-terracotta px-3.5 py-1.5 rounded bg-[#fffdf9] text-center font-mono">
              <span className="text-2xl font-black text-terracotta">{data.ats_score}%</span>
              <span className="block text-[8px] uppercase tracking-wider font-bold text-ink-muted">MATCH SCORE</span>
            </div>
          </div>

          {/* Matched & Missing Skill Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Matched Skills */}
            <div className="p-4 bg-emerald-50/60 border border-emerald-800/30 rounded-lg">
              <h4 className="font-mono text-xs font-bold uppercase text-emerald-900 mb-2.5 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                Matched Technical Skills ({data.matched_skills.length})
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {data.matched_skills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="bg-emerald-100 text-emerald-900 border border-emerald-400 font-mono text-[10px] px-2 py-0.5 rounded font-medium"
                  >
                    ✓ {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Missing Skills */}
            <div className="p-4 bg-amber-50/60 border border-amber-800/30 rounded-lg">
              <h4 className="font-mono text-xs font-bold uppercase text-amber-900 mb-2.5 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-700" />
                Missing Technical Keywords ({data.missing_skills.length})
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {data.missing_skills.length > 0 ? (
                  data.missing_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="bg-amber-100 text-amber-900 border border-amber-400 font-mono text-[10px] px-2 py-0.5 rounded font-medium"
                    >
                      + {skill}
                    </span>
                  ))
                ) : (
                  <span className="font-serif text-xs text-amber-900 italic">No critical missing skills detected!</span>
                )}
              </div>
            </div>
          </div>

          {/* Bullet Recommendations */}
          {data.bullet_recommendations && data.bullet_recommendations.length > 0 && (
            <div className="p-3.5 bg-paper border border-ink/30 rounded-lg">
              <h4 className="font-mono text-[11px] font-bold uppercase text-ink mb-1.5 flex items-center gap-1.5">
                <Lightbulb className="w-3.5 h-3.5 text-vintage-gold" />
                ATS Bullet Optimization Feedback:
              </h4>
              <ul className="list-disc list-inside space-y-1 font-serif text-xs text-ink/90">
                {data.bullet_recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        !loading && (
          <div className="text-center py-4 text-xs font-serif italic text-ink-muted">
            Click <strong>"ANALYZE ATS MATCH"</strong> above to extract keyword matches and missing skills for this role.
          </div>
        )
      )}
    </div>
  );
}
