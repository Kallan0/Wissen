"use client";

import React, { useState } from "react";
import { X, Copy, Check, Mail, Send, Sparkles, FileText } from "lucide-react";
import { CoverLetterResponse } from "@/lib/types";

interface CoverLetterModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: CoverLetterResponse | null;
  loading: boolean;
}

export default function CoverLetterModal({
  isOpen,
  onClose,
  data,
  loading,
}: CoverLetterModalProps) {
  const [copiedLetter, setCopiedLetter] = useState(false);
  const [copiedOutreach, setCopiedOutreach] = useState(false);
  const [activeSubTab, setActiveSubTab] = useState<"letter" | "outreach">("letter");

  if (!isOpen) return null;

  const handleCopyLetter = () => {
    if (data?.cover_letter_body) {
      navigator.clipboard.writeText(data.cover_letter_body);
      setCopiedLetter(true);
      setTimeout(() => setCopiedLetter(false), 2000);
    }
  };

  const handleCopyOutreach = () => {
    if (data?.linkedin_outreach_message) {
      navigator.clipboard.writeText(data.linkedin_outreach_message);
      setCopiedOutreach(true);
      setTimeout(() => setCopiedOutreach(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-ink/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-fade-in">
      <div className="bg-[#fffdf9] max-w-3xl w-full rounded-xl border-2 border-ink shadow-dossier relative max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-5 bg-manila border-b-2 border-ink flex items-center justify-between shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-[10px] uppercase tracking-widest bg-ink text-paper px-2 py-0.5 font-bold">
                APPLICATION OUTREACH SYNTHESIZER
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-serif font-bold text-ink flex items-center gap-2">
              <Mail className="w-5 h-5 text-terracotta" />
              Tailored Cover Letter & Recruiter Outreach
            </h2>
            <p className="text-xs font-serif italic text-ink-muted">
              Grounded strictly in your verified achievements from ChromaDB.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-ink/10 rounded-lg text-ink transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Subtab Toggle Header */}
        <div className="flex border-b-2 border-ink/20 bg-manila/30 shrink-0">
          <button
            type="button"
            onClick={() => setActiveSubTab("letter")}
            className={`flex-1 py-3 font-mono text-xs font-bold uppercase tracking-wider border-b-2 flex items-center justify-center gap-2 transition-all ${
              activeSubTab === "letter"
                ? "border-terracotta text-terracotta bg-[#fffdf9]"
                : "border-transparent text-ink-muted hover:text-ink"
            }`}
          >
            <FileText className="w-4 h-4" />
            3-PARAGRAPH COVER LETTER
          </button>

          <button
            type="button"
            onClick={() => setActiveSubTab("outreach")}
            className={`flex-1 py-3 font-mono text-xs font-bold uppercase tracking-wider border-b-2 flex items-center justify-center gap-2 transition-all ${
              activeSubTab === "outreach"
                ? "border-terracotta text-terracotta bg-[#fffdf9]"
                : "border-transparent text-ink-muted hover:text-ink"
            }`}
          >
            <Send className="w-4 h-4" />
            LINKEDIN COLD MESSAGE
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {loading ? (
            <div className="py-16 text-center space-y-3">
              <div className="w-8 h-8 border-3 border-terracotta border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="font-mono text-xs uppercase font-bold text-ink tracking-wider">
                SYNTHESIZING GROUNDED OUTREACH FROM CHROMADB...
              </p>
            </div>
          ) : data ? (
            <>
              {activeSubTab === "letter" && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-[11px] font-bold text-ink uppercase">
                      TARGET: {data.role_title} @ {data.company_name}
                    </span>
                    <button
                      type="button"
                      onClick={handleCopyLetter}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded border border-ink shadow-press transition-all"
                    >
                      {copiedLetter ? (
                        <>
                          <Check className="w-3.5 h-3.5" /> COPIED!
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" /> COPY COVER LETTER
                        </>
                      )}
                    </button>
                  </div>
                  <div className="p-5 bg-paper border-2 border-ink rounded-lg font-serif text-sm text-ink leading-relaxed whitespace-pre-wrap shadow-press font-normal">
                    {data.cover_letter_body}
                  </div>
                </div>
              )}

              {activeSubTab === "outreach" && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-[11px] font-bold text-ink uppercase">
                      DIRECT RECRUITER / HIRING MANAGER MESSAGE
                    </span>
                    <button
                      type="button"
                      onClick={handleCopyOutreach}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded border border-ink shadow-press transition-all"
                    >
                      {copiedOutreach ? (
                        <>
                          <Check className="w-3.5 h-3.5" /> COPIED!
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" /> COPY OUTREACH MESSAGE
                        </>
                      )}
                    </button>
                  </div>
                  <div className="p-5 bg-paper border-2 border-ink rounded-lg font-serif text-sm text-ink leading-relaxed whitespace-pre-wrap shadow-press font-normal">
                    {data.linkedin_outreach_message}
                  </div>
                </div>
              )}

              {/* Verified Proof Points Cited */}
              {data.key_highlights_cited && data.key_highlights_cited.length > 0 && (
                <div className="p-3 bg-manila/50 border border-ink/30 rounded font-mono text-[11px] text-ink">
                  <strong className="uppercase">Proof Points Cited:</strong>{" "}
                  {data.key_highlights_cited.join(" • ")}
                </div>
              )}
            </>
          ) : (
            <div className="py-12 text-center text-xs font-serif italic text-ink-muted">
              No cover letter generated yet. Click "GENERATE COVER LETTER" in Job Tailor.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-manila border-t-2 border-ink flex justify-end shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 bg-paper hover:bg-paper/80 text-ink font-mono text-xs uppercase font-bold rounded border-2 border-ink shadow-press"
          >
            CLOSE
          </button>
        </div>
      </div>
    </div>
  );
}
