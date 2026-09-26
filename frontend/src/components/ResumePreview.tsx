"use client";

import React, { useEffect, useState } from "react";
import { AlertCircle, CheckCircle, Download, Edit3, Eye, FolderOpen, ScrollText, Sparkles, X } from "lucide-react";
import { exportPDF, getDownloadUrl, renderResumeHTML } from "@/lib/api";
import { ResumeData } from "@/lib/types";

type ResumeTemplate = "vintage" | "modern" | "minimal";

function SaveAsModal({ suggestedName, downloadUrl, onClose }: {
  suggestedName: string;
  downloadUrl: string;
  onClose: () => void;
}) {
  const [filename, setFilename] = useState(suggestedName);

  const triggerDownload = () => {
    const trimmedName = filename.trim();
    const anchor = document.createElement("a");
    anchor.href = downloadUrl;
    anchor.download = trimmedName.endsWith(".pdf") ? trimmedName : `${trimmedName}.pdf`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/60 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-md overflow-hidden rounded-xl border-2 border-ink bg-[#fffdf9] shadow-dossier">
        <div className="flex items-center justify-between bg-ink px-5 py-3 text-paper">
          <div className="flex items-center gap-2">
            <FolderOpen className="h-4 w-4 text-[#f5c842]" />
            <span className="font-mono text-xs font-bold uppercase tracking-widest">Save PDF Document</span>
          </div>
          <button onClick={onClose} className="text-paper/60 hover:text-paper" aria-label="Close save dialog">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-4 p-6">
          <div>
            <label htmlFor="pdf-filename" className="mb-1.5 block font-mono text-[11px] font-bold uppercase tracking-widest text-ink">File Name</label>
            <div className="flex items-center gap-2">
              <input
                id="pdf-filename"
                type="text"
                value={filename}
                onChange={(event) => setFilename(event.target.value)}
                onKeyDown={(event) => event.key === "Enter" && filename.trim() && triggerDownload()}
                className="flex-1 rounded-lg border-2 border-ink bg-paper px-3 py-2.5 font-mono text-xs text-ink focus:outline-none focus:ring-2 focus:ring-terracotta/40"
                placeholder="resume_candidate"
                autoFocus
              />
              <span className="shrink-0 rounded-lg border-2 border-ink bg-manila px-2 py-2.5 font-mono text-xs text-ink-muted">.pdf</span>
            </div>
            <p className="mt-1.5 font-mono text-[10px] text-ink-muted">Saved to your browser&apos;s default Downloads folder.</p>
          </div>
          <div className="flex items-start gap-1.5 rounded-lg border border-ink/20 bg-manila/60 p-3 font-mono text-[10px] text-ink-muted">
            <CheckCircle className="mt-0.5 h-3 w-3 shrink-0 text-fountain-teal" />
            <span>The PDF is ready. Choose its name, then download it.</span>
          </div>
        </div>
        <div className="flex justify-end gap-3 px-6 pb-5">
          <button onClick={onClose} className="rounded-lg border-2 border-ink bg-paper px-4 py-2 font-mono text-xs font-bold text-ink shadow-press hover:bg-manila">Cancel</button>
          <button
            onClick={triggerDownload}
            disabled={!filename.trim()}
            className="flex items-center gap-2 rounded-lg border-2 border-ink bg-terracotta px-5 py-2 font-mono text-xs font-bold uppercase tracking-wider text-paper shadow-press hover:bg-[#b03d25] disabled:opacity-40"
          >
            <Download className="h-3.5 w-3.5" /> Download
          </button>
        </div>
      </div>
    </div>
  );
}

interface ResumePreviewProps {
  resume: ResumeData | null;
  onUpdateResume: (updated: ResumeData) => void;
}

const templateOptions: Array<{ value: ResumeTemplate; label: string }> = [
  { value: "vintage", label: "[01] Vintage Press" },
  { value: "modern", label: "[02] Modern Tech" },
  { value: "minimal", label: "[03] Minimalist" },
];

export default function ResumePreview({ resume, onUpdateResume }: ResumePreviewProps) {
  const [template, setTemplate] = useState<ResumeTemplate>("vintage");
  const [isEditing, setIsEditing] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [saveAsModal, setSaveAsModal] = useState<{ url: string; suggestedName: string } | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    if (!resume) {
      setPreviewHtml("");
      setPreviewError(null);
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setPreviewLoading(true);
      setPreviewError(null);
      try {
        setPreviewHtml(await renderResumeHTML(resume, template, controller.signal));
      } catch (error) {
        if (!controller.signal.aborted) {
          setPreviewError(error instanceof Error ? error.message : "Failed to render resume preview");
        }
      } finally {
        if (!controller.signal.aborted) setPreviewLoading(false);
      }
    }, 200);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [resume, template]);

  if (!resume) {
    return (
      <div className="rounded-xl border-2 border-ink bg-[#fffdf9] p-12 text-center shadow-dossier sm:p-16">
        <ScrollText className="mx-auto mb-4 h-14 w-14 text-ink-muted/50" />
        <h3 className="font-serif text-xl font-bold text-ink">No Archival Resume Generated Yet</h3>
        <p className="mx-auto mt-2 max-w-md font-serif text-sm italic leading-relaxed text-ink-muted">
          Open the <strong className="font-mono not-italic text-terracotta">[02] Job Tailor</strong> dossier and generate an ATS-grounded CV.
        </p>
      </div>
    );
  }

  const buildSuggestedName = () => {
    const namePart = (resume.name || "Candidate").trim().replace(/\s+/g, "_").replace(/[^a-zA-Z0-9_-]/g, "");
    return `resume_${namePart}_${new Date().toISOString().slice(0, 10)}`;
  };

  const handleExportPDF = async () => {
    setDownloading(true);
    setExportError(null);
    try {
      const result = await exportPDF(resume, template);
      setSaveAsModal({ url: getDownloadUrl(result.filename), suggestedName: buildSuggestedName() });
    } catch (error) {
      setExportError(error instanceof Error ? error.message : "PDF export failed");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <>
      {saveAsModal && (
        <SaveAsModal
          suggestedName={saveAsModal.suggestedName}
          downloadUrl={saveAsModal.url}
          onClose={() => setSaveAsModal(null)}
        />
      )}
      <div className="space-y-6">
        <div className="flex flex-col items-center justify-between gap-4 rounded-xl border-2 border-ink bg-[#fffdf9] p-4 shadow-press-lg sm:flex-row">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1 rounded-lg border-2 border-ink bg-manila p-1">
              {templateOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setTemplate(option.value)}
                  className={`rounded px-3 py-1 font-mono text-xs font-bold ${template === option.value ? "bg-terracotta text-paper shadow-press" : "text-ink hover:text-terracotta"}`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <button
              onClick={() => setIsEditing((current) => !current)}
              className={`flex items-center gap-1.5 rounded-lg border-2 border-ink px-3 py-1.5 font-mono text-xs font-bold shadow-press ${isEditing ? "bg-vintage-gold text-ink" : "bg-paper text-ink hover:bg-manila"}`}
            >
              {isEditing ? <Eye className="h-3.5 w-3.5" /> : <Edit3 className="h-3.5 w-3.5" />}
              {isEditing ? "READ VIEW" : "EDIT DRAFT"}
            </button>
          </div>
          <div className="flex w-full items-center justify-end gap-3 sm:w-auto">
            {resume._ai_provider && (
              <span className="hidden rounded border border-ink bg-manila px-2.5 py-1 font-mono text-[11px] text-ink-muted md:inline">
                ENGINE: <strong className="text-ink">{resume._ai_provider}</strong>
              </span>
            )}
            <button
              onClick={handleExportPDF}
              disabled={downloading}
              className="inline-flex items-center gap-2 rounded-lg border-2 border-ink bg-terracotta px-5 py-2 font-mono text-xs font-bold uppercase tracking-wider text-paper shadow-press hover:bg-[#b03d25] disabled:opacity-50"
            >
              {downloading ? <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-paper border-t-transparent" /> : <Download className="h-3.5 w-3.5" />}
              {downloading ? "PRESSING PDF..." : "PRINT-READY PDF"}
            </button>
          </div>
        </div>

        {exportError && (
          <div className="flex items-center gap-2 rounded-lg border-2 border-ink bg-red-50 p-3.5 font-mono text-xs text-red-800 shadow-press">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
            <span className="flex-1">{exportError}</span>
            <button onClick={() => setExportError(null)} aria-label="Dismiss export error"><X className="h-3.5 w-3.5" /></button>
          </div>
        )}

        {resume.tailored_match_notes && resume.tailored_match_notes.length > 0 && (
          <div className="rounded-xl border-2 border-ink bg-manila/70 p-4 shadow-press">
            <div className="mb-2 flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider text-ink">
              <Sparkles className="h-4 w-4 text-terracotta" /> AI Tailoring Strategy &amp; Grounding Proofs
            </div>
            <ul className="list-inside list-disc space-y-1 font-serif text-xs text-ink-muted">
              {resume.tailored_match_notes.map((note, index) => <li key={index}>{note}</li>)}
            </ul>
          </div>
        )}

        {isEditing && (
          <div className="rounded-xl border-2 border-ink bg-[#fffdf9] p-4 shadow-press">
            <label htmlFor="resume-summary-editor" className="mb-2 block font-mono text-xs font-bold uppercase tracking-wider text-ink">Professional Summary</label>
            <textarea
              id="resume-summary-editor"
              rows={5}
              value={resume.summary}
              onChange={(event) => onUpdateResume({ ...resume, summary: event.target.value })}
              className="w-full rounded-lg border-2 border-ink bg-paper p-3 font-serif text-sm text-ink focus:outline-none focus:ring-2 focus:ring-terracotta/40"
            />
            <p className="mt-2 font-mono text-[10px] text-ink-muted">The backend refreshes the print template after you pause typing.</p>
          </div>
        )}

        <div className="relative min-h-[720px] overflow-hidden rounded-xl border-2 border-ink bg-[#fffdf9] shadow-dossier">
          {previewLoading && <div className="absolute inset-x-0 top-0 z-10 h-1 animate-pulse bg-terracotta" />}
          {previewError ? (
            <div className="flex min-h-[720px] flex-col items-center justify-center p-10 text-center">
              <AlertCircle className="mb-3 h-8 w-8 text-red-500" />
              <h3 className="font-serif font-bold text-ink">Preview unavailable</h3>
              <p className="mt-2 max-w-lg font-mono text-xs text-ink-muted">{previewError}</p>
            </div>
          ) : previewHtml ? (
            <iframe title={`${template} resume preview`} srcDoc={previewHtml} sandbox="" className="block min-h-[1120px] w-full border-0 bg-white" />
          ) : (
            <div className="flex min-h-[720px] items-center justify-center font-mono text-xs text-ink-muted">Rendering backend template...</div>
          )}
        </div>
      </div>
    </>
  );
}
