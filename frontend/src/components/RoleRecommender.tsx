"use client";

import React, { useState } from "react";
import { Compass, Sparkles, CheckCircle2, ArrowRight, Target, Lightbulb, AlertCircle } from "lucide-react";
import { fetchCareerRecommendations } from "@/lib/api";
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
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 mb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <Compass className="w-5 h-5 text-indigo-600" />
              AI Career Matcher & Position Recommender
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              The local AI analyzes your entire ChromaDB vector database (verified work history, projects, and skills) to identify the highest-fit positions you can target.
            </p>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="text-xs px-3 py-2 border border-slate-300 rounded-lg bg-white"
            >
              {models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>

            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Scanning Vector DB...
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  Suggest Roles For Me
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-xs text-red-700">
            <AlertCircle className="w-4 h-4 text-red-500" />
            {error}
          </div>
        )}

        {data?.profile_summary && (
          <div className="p-4 bg-indigo-50/70 border border-indigo-100 rounded-xl text-xs text-indigo-900 leading-relaxed">
            <span className="font-bold text-indigo-950 uppercase tracking-wide mr-1.5 flex items-center gap-1 inline-flex">
              <Target className="w-3.5 h-3.5 text-indigo-600" />
              Verified Competency Assessment:
            </span>
            {data.profile_summary}
            {data._ai_provider && (
              <div className="mt-1 text-[11px] text-indigo-600 font-medium">
                Analysis Engine: {data._ai_provider}
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
              className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md hover:border-indigo-200 transition flex flex-col justify-between"
            >
              <div>
                {/* Title & Score */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">{pos.title}</h3>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                        {pos.seniority}
                      </span>
                      <span className="text-xs text-slate-500">{pos.description}</span>
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <div className="text-lg font-black text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                      {pos.fit_score}% Fit
                    </div>
                  </div>
                </div>

                {/* Why Qualified */}
                <div className="mt-3.5">
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1.5 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Why You're Qualified (From Your Data):
                  </h4>
                  <ul className="list-disc list-inside space-y-1 text-xs text-slate-600">
                    {pos.why_qualified.map((reason, rIdx) => (
                      <li key={rIdx} className="leading-normal">
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Skills Leveraged */}
                {pos.skills_leveraged && pos.skills_leveraged.length > 0 && (
                  <div className="mt-3">
                    <div className="flex flex-wrap gap-1">
                      {pos.skills_leveraged.map((s, sIdx) => (
                        <span
                          key={sIdx}
                          className="bg-indigo-50 text-indigo-700 text-[10px] font-medium px-2 py-0.5 rounded border border-indigo-100"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommended Focus */}
                {pos.recommended_focus && (
                  <div className="mt-3 p-2 bg-amber-50/70 border border-amber-200/70 rounded-lg text-xs text-amber-900 flex items-start gap-1.5">
                    <Lightbulb className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                    <span>
                      <strong>Application Angle:</strong> {pos.recommended_focus}
                    </span>
                  </div>
                )}
              </div>

              {/* Action Button: One-Click Tailor */}
              <div className="mt-5 pt-3 border-t border-slate-100 flex justify-end">
                <button
                  type="button"
                  onClick={() => onSelectRoleForTailoring(pos.title, pos.sample_jd_prompt)}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition"
                >
                  Tailor Resume for this Role
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        !loading && (
          <div className="bg-white p-12 rounded-xl border border-slate-200 text-center shadow-sm">
            <Compass className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-700">No Recommendations Yet</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">
              Click <strong>"Suggest Roles For Me"</strong> above. The local LLM will scan your ChromaDB knowledge base and identify the strongest job positions you qualify for.
            </p>
            <button
              onClick={handleAnalyze}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow transition"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Run Analysis Now
            </button>
          </div>
        )
      )}
    </div>
  );
}
