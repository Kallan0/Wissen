"use client";

import React from "react";
import { AlertTriangle, Upload, FileEdit, Database, Sparkles } from "lucide-react";
import { seedSampleProfile } from "@/lib/api";

interface EmptyKBBannerProps {
  onOpenUpload?: () => void;
  onOpenQuestionnaire: () => void;
  onRefresh?: () => void;
}

export default function EmptyKBBanner({
  onOpenUpload,
  onOpenQuestionnaire,
  onRefresh,
}: EmptyKBBannerProps) {
  const [seeding, setSeeding] = React.useState(false);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await seedSampleProfile();
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error(err);
      alert("Failed to seed sample profile.");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="bg-[#fff0ed] p-6 sm:p-7 rounded-xl border-2 border-terracotta shadow-dossier relative overflow-hidden my-4">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
        <div className="flex items-start gap-4">
          <div className="w-11 h-11 rounded-lg bg-terracotta text-paper flex items-center justify-center shrink-0 shadow-press border-2 border-ink">
            <AlertTriangle className="w-6 h-6" />
          </div>

          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-[10px] uppercase tracking-widest bg-terracotta text-paper px-2 py-0.5 font-bold rounded-sm">
                ACTION REQUIRED &bull; KNOWLEDGE BASE EMPTY
              </span>
            </div>
            <h3 className="text-xl font-serif font-bold text-ink tracking-tight">
              No Resume or Candidate Background Ingested Yet
            </h3>
            <p className="text-xs sm:text-sm font-serif italic text-ink-muted mt-1 max-w-2xl leading-relaxed">
              Your local ChromaDB vector database contains <strong>0 items</strong>. To generate accurate ATS resumes and role recommendations grounded in your <em>actual experience</em>, please upload your resume PDF or complete the quick profile questionnaire.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-terracotta/30">
          <button
            type="button"
            onClick={onOpenQuestionnaire}
            className="flex-1 md:flex-none inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press transition-all"
          >
            <FileEdit className="w-3.5 h-3.5" />
            START QUESTIONNAIRE
          </button>

          {onOpenUpload && (
            <button
              type="button"
              onClick={onOpenUpload}
              className="flex-1 md:flex-none inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-manila hover:bg-manila/80 text-ink font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press transition-all"
            >
              <Upload className="w-3.5 h-3.5 text-terracotta" />
              UPLOAD PDF RESUME
            </button>
          )}

          <button
            type="button"
            onClick={handleSeed}
            disabled={seeding}
            title="Load demo profile for instant testing"
            className="inline-flex items-center justify-center gap-1.5 px-3 py-2.5 bg-paper hover:bg-paper/80 text-ink-muted hover:text-ink font-mono text-[11px] uppercase tracking-wider rounded border-2 border-ink/40 transition-all disabled:opacity-50"
          >
            <Database className="w-3.5 h-3.5 text-vintage-gold" />
            {seeding ? "SEEDING..." : "SEED DEMO PROFILE"}
          </button>
        </div>
      </div>
    </div>
  );
}
