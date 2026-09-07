"use client";

import React, { useState } from "react";
import { Compass, Sparkles, CheckCircle2, ArrowRight, Target, Lightbulb, AlertCircle, Stamp, ScrollText } from "lucide-react";
import EmptyKBBanner from "@/components/EmptyKBBanner";
import ProfileQuestionnaireModal from "@/components/ProfileQuestionnaireModal";
import { fetchCareerRecommendations, fetchKBProfile } from "@/lib/api";
import { CareerRecommendationsResponse, RecommendedPosition } from "@/lib/types";

interface RoleRecommenderProps {
  models: string[];
  onSelectRoleForTailoring: (role: string, sampleJd: string) => void;
}

export default function RoleRecommender({
  models,
  onSelectRoleForTailoring,
}: RoleRecommenderProps) {
  const [selectedModel, setSelectedModel] = useState(models[0] || "llama3");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<CareerRecommendationsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isKBEmpty, setIsKBEmpty] = useState(false);
  const [isQuestionnaireOpen, setIsQuestionnaireOpen] = useState(false);

  const checkKBStatus = async () => {
    try {
      const prof = await fetchKBProfile();
      if (!prof.exists || prof.total_items === 0) {
        setIsKBEmpty(true);
      } else {
        setIsKBEmpty(false);
      }
    } catch (err) {
      console.error(err);
    }
  };

  React.useEffect(() => {
    checkKBStatus();
  }, []);

  React.useEffect(() => {
    if (models.length > 0 && (!selectedModel || selectedModel === "llama3")) {
      setSelectedModel(models[0]);
    }
  }, [models]);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchCareerRecommendations(selectedModel);
      setData(res);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to generate career recommendations.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {isKBEmpty && (
        <EmptyKBBanner
          onOpenQuestionnaire={() => setIsQuestionnaireOpen(true)}
          onRefresh={checkKBStatus}
        />
      )}

      {/* Editorial Header Banner */}
      <div className="bg-[#fffdf9] p-6 sm:p-8 rounded-xl border-2 border-ink shadow-dossier relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 pb-5 border-b-2 border-ink/20 mb-5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-[11px] uppercase tracking-widest bg-ink text-paper px-2 py-0.5 font-bold">
                BUREAU OF CAREER MATCHES
              </span>
              <span className="font-mono text-[11px] text-ink-muted uppercase tracking-wider">
                CHROMA-VECTOR PROVENANCE
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-serif font-bold text-ink tracking-tight flex items-center gap-2.5">
              <Compass className="w-6 h-6 text-terracotta" />
              AI Career Matcher & Opportunity Dispatch
            </h2>
            <p className="text-xs sm:text-sm font-serif italic text-ink-muted mt-1 max-w-2xl leading-relaxed">
              The local Ollama AI scans your ChromaDB vector database (verified career history, projects, and skills) to identify the highest-fit positions you can target right now.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-manila/50 text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
            >
              {models.map((m) => (
                <option key={m} value={m}>
                  {m} (Active)
                </option>
              ))}
            </select>

            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-paper border-t-transparent rounded-full animate-spin" />
                  SCANNED CHROMADB...
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5 text-paper" />
                  DISPATCH ROLE MATCHES
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-[#fff0ed] border-2 border-terracotta rounded-lg flex items-center gap-2 text-xs text-terracotta shadow-press mb-4">
            <AlertCircle className="w-4 h-4 text-terracotta shrink-0" />
            <span className="font-mono">{error}</span>
          </div>
        )}

        {data?.profile_summary && (
          <div className="p-4 bg-manila/60 border-2 border-ink rounded-lg font-serif text-xs text-ink leading-relaxed shadow-press">
            <span className="font-mono font-bold text-ink uppercase tracking-wider mr-2 flex items-center gap-1.5 inline-flex">
              <Target className="w-3.5 h-3.5 text-terracotta" />
              Verified Competency Assessment:
            </span>
            {data.profile_summary}
            {data._ai_provider && (
              <div className="mt-1.5 font-mono text-[10px] text-ink-muted uppercase">
                INFERENCE ENGINE: <strong className="text-ink">{data._ai_provider}</strong>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Recommended Positions Grid */}
      {data?.recommended_positions && data.recommended_positions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {data.recommended_positions.map((pos, idx) => (
            <div
              key={idx}
              className="bg-[#fffdf9] p-6 rounded-xl border-2 border-ink shadow-press flex flex-col justify-between hover:shadow-dossier transition-all"
            >
              <div>
                {/* Header & Fit Postal Stamp */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <span className="font-mono text-[9px] uppercase tracking-widest bg-ink text-paper px-2 py-0.5 font-bold inline-block mb-1">
                      {pos.seniority}
                    </span>
                    <h3 className="text-lg font-serif font-bold text-ink">{pos.title}</h3>
                    <p className="font-serif italic text-xs text-ink-muted mt-0.5">{pos.description}</p>
                  </div>
                  <div className="shrink-0 border-2 border-dashed border-terracotta px-2.5 py-1 rounded bg-manila/50 rotate-[2deg] text-center font-mono">
                    <span className="text-sm font-black text-terracotta">{pos.fit_score}%</span>
                    <span className="block text-[8px] uppercase tracking-wider text-ink-muted font-bold">FIT SCORE</span>
                  </div>
                </div>

                {/* Why Qualified Docket */}
                <div className="mt-4 pt-3 border-t border-ink/20">
                  <h4 className="font-mono text-[10px] font-bold uppercase tracking-wider text-ink mb-1.5 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-fountain-teal" />
                    Verified Evidence from ChromaDB:
                  </h4>
                  <ul className="list-disc list-inside space-y-1 font-serif text-xs text-ink/90">
                    {pos.why_qualified.map((reason, rIdx) => (
                      <li key={rIdx} className="leading-normal">
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Skills Leveraged */}
                {pos.skills_leveraged && pos.skills_leveraged.length > 0 && (
                  <div className="mt-3.5 flex flex-wrap gap-1.5">
                    {pos.skills_leveraged.map((s, sIdx) => (
                      <span
                        key={sIdx}
                        className="bg-manila text-ink font-mono text-[10px] px-2 py-0.5 rounded border border-ink/30"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}

                {/* Recommended Focus */}
                {pos.recommended_focus && (
                  <div className="mt-3.5 p-2.5 bg-paper border border-ink/30 rounded text-xs text-ink flex items-start gap-2">
                    <Lightbulb className="w-3.5 h-3.5 text-vintage-gold shrink-0 mt-0.5" />
                    <span className="font-serif">
                      <strong className="font-mono text-[10px] uppercase">Application Angle:</strong> {pos.recommended_focus}
                    </span>
                  </div>
                )}
              </div>

              {/* Action Button: One-Click Tailor */}
              <div className="mt-5 pt-3 border-t-2 border-ink/20 flex justify-end">
                <button
                  type="button"
                  onClick={() => onSelectRoleForTailoring(pos.title, pos.sample_jd_prompt)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all"
                >
                  TAILOR DOSSIER FOR THIS ROLE
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        !loading && (
          <div className="bg-[#fffdf9] p-12 sm:p-16 rounded-xl border-2 border-ink shadow-dossier text-center">
            <ScrollText className="w-12 h-12 text-ink-muted/40 mx-auto mb-3" />
            <h3 className="text-lg font-serif font-bold text-ink">Awaiting Archive Analysis</h3>
            <p className="font-serif italic text-xs text-ink-muted max-w-md mx-auto mt-1 mb-5">
              Press <strong>"DISPATCH ROLE MATCHES"</strong> above. The local Ollama LLM will synthesize vector embeddings from your ChromaDB ledger to produce tailored position recommendations.
            </p>
            <button
              onClick={handleAnalyze}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press"
            >
              <Sparkles className="w-3.5 h-3.5" />
              EXECUTE ANALYSIS NOW
            </button>
          </div>
        )
      )}

      <ProfileQuestionnaireModal
        isOpen={isQuestionnaireOpen}
        onClose={() => setIsQuestionnaireOpen(false)}
        onSuccess={checkKBStatus}
      />
    </div>
  );
}

