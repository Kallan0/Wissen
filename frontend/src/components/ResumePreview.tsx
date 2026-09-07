"use client";

import React, { useState } from "react";
import { Download, Edit3, Eye, CheckCircle, Sparkles, ScrollText, X, FolderOpen, AlertCircle } from "lucide-react";
import { ResumeData } from "@/lib/types";
import { exportPDF, getDownloadUrl } from "@/lib/api";

// ── Save-As Modal ─────────────────────────────────────────────────────────────
function SaveAsModal({
  suggestedName,
  downloadUrl,
  onClose,
}: {
  suggestedName: string;
  downloadUrl: string;
  onClose: () => void;
}) {
  const [filename, setFilename] = useState(suggestedName);

  const triggerDownload = () => {
    const a = document.createElement("a");
    a.href = downloadUrl;
    const finalName = filename.trim().endsWith(".pdf") ? filename.trim() : `${filename.trim()}.pdf`;
    a.download = finalName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/60 backdrop-blur-sm">
      <div className="bg-[#fffdf9] border-2 border-ink rounded-xl shadow-[6px_6px_0px_#221a12] w-full max-w-md mx-4 overflow-hidden">
        <div className="bg-ink text-paper px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-[#f5c842]" />
            <span className="font-mono text-xs font-bold uppercase tracking-widest">Save PDF Document</span>
          </div>
          <button onClick={onClose} className="text-paper/60 hover:text-paper transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="block font-mono text-[11px] font-bold uppercase tracking-widest text-ink mb-1.5">
              File Name
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && triggerDownload()}
                className="flex-1 font-mono text-xs px-3 py-2.5 border-2 border-ink rounded-lg bg-paper focus:outline-none focus:ring-2 focus:ring-terracotta/40 text-ink"
                placeholder="resume_candidate"
                autoFocus
              />
              <span className="font-mono text-xs text-ink-muted bg-manila px-2 py-2.5 border-2 border-ink rounded-lg shrink-0">.pdf</span>
            </div>
            <p className="font-mono text-[10px] text-ink-muted mt-1.5">
              Saved to your browser's default Downloads folder. Edit the name above to customise.
            </p>
          </div>
          <div className="p-3 bg-manila/60 border border-ink/20 rounded-lg">
            <div className="font-mono text-[10px] text-ink-muted flex items-start gap-1.5">
              <CheckCircle className="w-3 h-3 text-fountain-teal shrink-0 mt-0.5" />
              <span>PDF is ready on the server. Click <strong className="text-ink">Download</strong> to save it to your machine.</span>
            </div>
          </div>
        </div>
        <div className="px-6 pb-5 flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 font-mono text-xs font-bold border-2 border-ink rounded-lg bg-paper hover:bg-manila text-ink transition-colors shadow-[2px_2px_0px_#221a12] hover:translate-x-[1px] hover:translate-y-[1px]"
          >
            Cancel
          </button>
          <button
            onClick={triggerDownload}
            disabled={!filename.trim()}
            className="flex items-center gap-2 px-5 py-2 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-[2px_2px_0px_#221a12] hover:translate-x-[1px] hover:translate-y-[1px] transition-all disabled:opacity-40"
          >
            <Download className="w-3.5 h-3.5" />
            Download
          </button>
        </div>
      </div>
    </div>
  );
}
// ─────────────────────────────────────────────────────────────────────────────

interface ResumePreviewProps {
  resume: ResumeData | null;
  onUpdateResume: (updated: ResumeData) => void;
}

export default function ResumePreview({ resume, onUpdateResume }: ResumePreviewProps) {
  const [template, setTemplate] = useState<"vintage" | "modern" | "minimal">("vintage");
  const [isEditing, setIsEditing] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [saveAsModal, setSaveAsModal] = useState<{ url: string; suggestedName: string } | null>(null);
  const [exportNotice, setExportNotice] = useState<{ type: "success" | "error"; message: string } | null>(null);

  if (!resume) {
    return (
      <div className="bg-[#fffdf9] p-12 sm:p-16 rounded-xl border-2 border-ink shadow-dossier text-center">
        <ScrollText className="w-14 h-14 text-ink-muted/50 mx-auto mb-4" />
        <h3 className="text-xl font-serif font-bold text-ink">No Archival Resume Generated Yet</h3>
        <p className="font-serif italic text-sm text-ink-muted max-w-md mx-auto mt-2 leading-relaxed">
          Open the <strong className="text-terracotta not-italic font-mono">[02] Job Tailor</strong> dossier, input target job requirements, and press the lever to synthesize an ATS-grounded CV.
        </p>
      </div>
    );
  }

  const buildSuggestedName = () => {
    const namePart = (resume?.name || "Candidate")
      .trim()
      .replace(/\s+/g, "_")
      .replace(/[^a-zA-Z0-9_\-]/g, "");
    const today = new Date().toISOString().slice(0, 10);
    return `resume_${namePart}_${today}`;
  };

  const handleExportPDF = async () => {
    setDownloading(true);
    setExportNotice(null);
    try {
      const res = await exportPDF(resume, template);
      const url = getDownloadUrl(res.filename);
      // Show Save-As modal so user can set destination & name
      setSaveAsModal({ url, suggestedName: buildSuggestedName() });
    } catch (err: any) {
      console.error(err);
      setExportNotice({ type: "error", message: err.message });
    } finally {
      setDownloading(false);
    }
  };

  return (
    <>
      {/* Save-As modal – rendered outside the scroll container */}
      {saveAsModal && (
        <SaveAsModal
          suggestedName={saveAsModal.suggestedName}
          downloadUrl={saveAsModal.url}
          onClose={() => setSaveAsModal(null)}
        />
      )}

    <div className="space-y-6">
      {/* Editorial Action Bar */}
      <div className="bg-[#fffdf9] p-4 rounded-xl border-2 border-ink shadow-press-lg flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Template Switcher */}
          <div className="flex items-center gap-1 bg-manila p-1 rounded-lg border-2 border-ink">
            <button
              onClick={() => setTemplate("vintage")}
              className={`px-3 py-1 rounded font-mono text-xs font-bold transition-all ${
                template === "vintage"
                  ? "bg-terracotta text-paper shadow-press"
                  : "text-ink hover:text-terracotta"
              }`}
            >
              [01] Vintage Press
            </button>
            <button
              onClick={() => setTemplate("modern")}
              className={`px-3 py-1 rounded font-mono text-xs font-bold transition-all ${
                template === "modern"
                  ? "bg-terracotta text-paper shadow-press"
                  : "text-ink hover:text-terracotta"
              }`}
            >
              [02] Modern Tech
            </button>
            <button
              onClick={() => setTemplate("minimal")}
              className={`px-3 py-1 rounded font-mono text-xs font-bold transition-all ${
                template === "minimal"
                  ? "bg-terracotta text-paper shadow-press"
                  : "text-ink hover:text-terracotta"
              }`}
            >
              [03] Minimalist
            </button>
          </div>

          <button
            onClick={() => setIsEditing(!isEditing)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-mono text-xs font-bold border-2 border-ink transition-all ${
              isEditing
                ? "bg-vintage-gold text-ink shadow-press"
                : "bg-paper text-ink shadow-press hover:bg-manila"
            }`}
          >
            {isEditing ? <Eye className="w-3.5 h-3.5" /> : <Edit3 className="w-3.5 h-3.5" />}
            {isEditing ? "READ VIEW" : "EDIT DRAFT"}
          </button>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          {resume._ai_provider && (
            <span className="font-mono text-[11px] text-ink-muted bg-manila px-2.5 py-1 rounded border border-ink hidden md:inline">
              ENGINE: <strong className="text-ink">{resume._ai_provider}</strong>
            </span>
          )}

          <button
            onClick={handleExportPDF}
            disabled={downloading}
            className="inline-flex items-center gap-2 px-5 py-2 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all disabled:opacity-50"
          >
            {downloading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-paper border-t-transparent rounded-full animate-spin" />
                PRESSING PDF...
              </>
            ) : (
              <>
                <Download className="w-3.5 h-3.5" />
                PRINT-READY PDF
              </>
            )}
          </button>
        </div>
      </div>

      {exportNotice && (
        <div className={`p-3.5 border-2 border-ink rounded-lg font-mono text-xs flex items-center gap-2 shadow-press ${
          exportNotice.type === "error" ? "bg-red-50 text-red-800" : "bg-[#fff8f4] text-ink"
        }`}>
          {exportNotice.type === "error" ? (
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
          ) : (
            <CheckCircle className="w-4 h-4 text-fountain-teal shrink-0" />
          )}
          <span className="flex-1">{exportNotice.message}</span>
          <button onClick={() => setExportNotice(null)} className="text-ink-muted hover:text-ink ml-2">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Tailoring Insights Banner */}
      {resume.tailored_match_notes && resume.tailored_match_notes.length > 0 && (
        <div className="p-4 bg-manila/70 border-2 border-ink rounded-xl shadow-press">
          <div className="font-mono text-xs font-bold text-ink uppercase tracking-wider flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-terracotta" />
            AI Tailoring Strategy & Grounding Proofs
          </div>
          <ul className="list-disc list-inside font-serif text-xs text-ink-muted space-y-1">
            {resume.tailored_match_notes.map((note, idx) => (
              <li key={idx} className="leading-relaxed">{note}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Living Document Sheet */}
      <div className="bg-[#fffdf9] rounded-xl shadow-dossier border-2 border-ink overflow-hidden relative">
        {template === "vintage" ? (
          <VintageResumeView
            resume={resume}
            isEditing={isEditing}
            onUpdateResume={onUpdateResume}
          />
        ) : template === "modern" ? (
          <ModernResumeView
            resume={resume}
            isEditing={isEditing}
            onUpdateResume={onUpdateResume}
          />
        ) : (
          <MinimalResumeView
            resume={resume}
            isEditing={isEditing}
            onUpdateResume={onUpdateResume}
          />
        )}
      </div>
    </div>
    </>
  );
}

function ModernResumeView({
  resume,
  isEditing,
  onUpdateResume,
}: {
  resume: ResumeData;
  isEditing: boolean;
  onUpdateResume: (updated: ResumeData) => void;
}) {
  return (
    <div className="p-8 sm:p-12 text-slate-800 max-w-4xl mx-auto font-sans leading-relaxed">
      {/* Header */}
      <header className="border-b-2 border-blue-600 pb-4 mb-6">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">{resume.name}</h1>
        <div className="text-blue-600 font-semibold text-base mt-1">{resume.title}</div>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500 mt-2">
          {resume.contact.email && <span>✉ {resume.contact.email}</span>}
          {resume.contact.phone && <span>☎ {resume.contact.phone}</span>}
          {resume.contact.location && <span>📍 {resume.contact.location}</span>}
          {resume.contact.linkedin && <span>🔗 {resume.contact.linkedin}</span>}
          {resume.contact.github && <span>🐙 {resume.contact.github}</span>}
        </div>
      </header>

      {/* Summary */}
      <section className="mb-6">
        <h2 className="text-xs font-bold uppercase tracking-wider text-blue-900 border-b border-slate-200 pb-1 mb-2">
          Professional Summary
        </h2>
        {isEditing ? (
          <textarea
            rows={3}
            value={resume.summary}
            onChange={(e) => onUpdateResume({ ...resume, summary: e.target.value })}
            className="w-full text-xs p-2 border border-slate-300 rounded"
          />
        ) : (
          <p className="text-xs text-slate-600 leading-relaxed">{resume.summary}</p>
        )}
      </section>

      {/* Skills */}
      {resume.skills && resume.skills.length > 0 && (
        <section className="mb-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-blue-900 border-b border-slate-200 pb-1 mb-3">
            Technical Skills
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            {resume.skills.map((s, idx) => (
              <div key={idx} className="flex items-start gap-1">
                <span className="font-semibold text-slate-800 shrink-0">{s.category}:</span>
                <span className="text-slate-600">{s.items.join(", ")}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Experience */}
      {resume.experience && resume.experience.length > 0 && (
        <section className="mb-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-blue-900 border-b border-slate-200 pb-1 mb-3">
            Professional Experience
          </h2>
          <div className="space-y-4">
            {resume.experience.map((exp, idx) => (
              <div key={idx} className="text-xs">
                <div className="flex justify-between items-baseline">
                  <div>
                    <span className="font-bold text-slate-900 text-sm">{exp.role}</span>
                    <span className="text-slate-600 font-semibold"> | {exp.company}</span>
                    {exp.location && <span className="text-slate-400"> ({exp.location})</span>}
                  </div>
                  <span className="text-slate-400 font-medium">{exp.duration}</span>
                </div>
                <ul className="list-disc list-inside mt-1.5 space-y-1 text-slate-600">
                  {exp.bullets.map((b, bIdx) => (
                    <li key={bIdx} className="leading-relaxed">
                      {b}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Projects */}
      {resume.projects && resume.projects.length > 0 && (
        <section className="mb-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-blue-900 border-b border-slate-200 pb-1 mb-3">
            Key Projects
          </h2>
          <div className="space-y-4">
            {resume.projects.map((proj, idx) => (
              <div key={idx} className="text-xs">
                <div className="flex justify-between items-baseline">
                  <span className="font-bold text-slate-900 text-sm">{proj.name}</span>
                  <div className="flex gap-1">
                    {proj.technologies?.map((t, tIdx) => (
                      <span key={tIdx} className="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[10px]">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                {proj.description && <p className="text-slate-600 mt-1">{proj.description}</p>}
                <ul className="list-disc list-inside mt-1 space-y-1 text-slate-600">
                  {(proj.bullets || proj.highlights || []).map((b, bIdx) => (
                    <li key={bIdx}>{b}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Education */}
      {resume.education && resume.education.length > 0 && (
        <section>
          <h2 className="text-xs font-bold uppercase tracking-wider text-blue-900 border-b border-slate-200 pb-1 mb-3">
            Education
          </h2>
          <div className="space-y-2 text-xs">
            {resume.education.map((edu, idx) => (
              <div key={idx} className="flex justify-between items-baseline">
                <div>
                  <span className="font-bold text-slate-900">{edu.degree}</span>
                  <span className="text-slate-600"> | {edu.institution}</span>
                  {edu.details && <p className="text-slate-500 text-[11px] mt-0.5">{edu.details}</p>}
                </div>
                <span className="text-slate-400">{edu.year}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function MinimalResumeView({
  resume,
  isEditing,
  onUpdateResume,
}: {
  resume: ResumeData;
  isEditing: boolean;
  onUpdateResume: (updated: ResumeData) => void;
}) {
  return (
    <div className="p-8 sm:p-12 text-slate-900 max-w-4xl mx-auto font-serif leading-relaxed">
      {/* Header */}
      <header className="text-center mb-6">
        <h1 className="text-2xl font-normal uppercase tracking-widest text-slate-900">{resume.name}</h1>
        <div className="italic text-sm text-slate-600 mt-1">{resume.title}</div>
        <div className="text-xs text-slate-600 mt-2 space-x-2">
          {resume.contact.location && <span>{resume.contact.location} &bull;</span>}
          {resume.contact.email && <span>{resume.contact.email} &bull;</span>}
          {resume.contact.phone && <span>{resume.contact.phone}</span>}
        </div>
      </header>

      {/* Summary */}
      <section className="mb-5">
        <h2 className="text-xs font-bold uppercase tracking-widest border-b border-slate-800 pb-0.5 mb-2">
          Summary
        </h2>
        <p className="text-xs text-slate-700 leading-relaxed">{resume.summary}</p>
      </section>

      {/* Experience */}
      {resume.experience && resume.experience.length > 0 && (
        <section className="mb-5">
          <h2 className="text-xs font-bold uppercase tracking-widest border-b border-slate-800 pb-0.5 mb-2">
            Experience
          </h2>
          <div className="space-y-3">
            {resume.experience.map((exp, idx) => (
              <div key={idx} className="text-xs">
                <div className="flex justify-between font-bold">
                  <span>{exp.company}</span>
                  <span className="font-normal text-slate-500">{exp.duration}</span>
                </div>
                <div className="italic text-slate-600">{exp.role} - {exp.location}</div>
                <ul className="list-disc list-inside mt-1 space-y-0.5 text-slate-700">
                  {exp.bullets.map((b, bIdx) => (
                    <li key={bIdx}>{b}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Projects */}
      {resume.projects && resume.projects.length > 0 && (
        <section className="mb-5">
          <h2 className="text-xs font-bold uppercase tracking-widest border-b border-slate-800 pb-0.5 mb-2">
            Projects
          </h2>
          <div className="space-y-3">
            {resume.projects.map((proj, idx) => (
              <div key={idx} className="text-xs">
                <div className="flex justify-between font-bold">
                  <span>{proj.name}</span>
                  <span className="font-normal text-slate-500">{(proj.technologies || []).join(", ")}</span>
                </div>
                <ul className="list-disc list-inside mt-1 space-y-0.5 text-slate-700">
                  {(proj.bullets || proj.highlights || []).map((b, bIdx) => (
                    <li key={bIdx}>{b}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Skills */}
      {resume.skills && resume.skills.length > 0 && (
        <section className="mb-5">
          <h2 className="text-xs font-bold uppercase tracking-widest border-b border-slate-800 pb-0.5 mb-2">
            Technical Skills
          </h2>
          <div className="space-y-1 text-xs">
            {resume.skills.map((s, idx) => (
              <div key={idx}>
                <strong>{s.category}:</strong> {s.items.join(", ")}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Education */}
      {resume.education && resume.education.length > 0 && (
        <section>
          <h2 className="text-xs font-bold uppercase tracking-widest border-b border-slate-800 pb-0.5 mb-2">
            Education
          </h2>
          <div className="space-y-1 text-xs">
            {resume.education.map((edu, idx) => (
              <div key={idx} className="flex justify-between">
                <div>
                  <span className="font-bold">{edu.institution}</span> &mdash; {edu.degree}
                </div>
                <span className="text-slate-500">{edu.year}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function VintageResumeView({
  resume,
  isEditing,
  onUpdateResume,
}: {
  resume: ResumeData;
  isEditing: boolean;
  onUpdateResume: (updated: ResumeData) => void;
}) {
  return (
    <div className="relative p-6 sm:p-12 text-ink max-w-4xl mx-auto font-serif leading-relaxed bg-[#fffdf9]">
      {/* Decorative Air-Mail Stripe Border on the Left */}
      <div className="absolute left-0 top-0 bottom-0 w-2.5 air-mail-ribbon border-r-2 border-ink hidden sm:block" />

      {/* Header Container */}
      <header className="border-b-2 border-ink pb-5 mb-6 relative">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="space-y-1">
            <span className="font-mono text-[10px] uppercase tracking-widest bg-ink text-paper px-2 py-0.5 font-bold inline-block mb-1">
              CURRICULUM VITAE // ATS GROUNDED
            </span>
            <h1 className="text-3xl sm:text-5xl font-serif font-bold text-ink tracking-tight">
              {resume.name}
            </h1>
            <div className="text-terracotta font-serif italic text-base sm:text-lg font-medium">
              {resume.title}
            </div>

            {/* Contact Strip */}
            <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-ink-muted pt-2">
              {resume.contact.email && <span>✉ {resume.contact.email}</span>}
              {resume.contact.phone && <span>☎ {resume.contact.phone}</span>}
              {resume.contact.location && <span>📍 {resume.contact.location}</span>}
              {resume.contact.linkedin && <span>🔗 {resume.contact.linkedin}</span>}
              {resume.contact.github && <span>🐙 {resume.contact.github}</span>}
            </div>
          </div>

          {/* Postal Stamp Mark */}
          <div className="shrink-0 border-2 border-dashed border-terracotta p-2.5 rounded bg-manila/30 rotate-[-2deg] text-center font-mono text-terracotta shadow-press hidden sm:block">
            <div className="text-[10px] font-bold uppercase tracking-widest border-b border-terracotta/40 pb-0.5">
              AIR MAIL &bull; PAR AVION
            </div>
            <div className="text-[8px] pt-1 text-terracotta/90 tracking-wider">
              OFFICIAL DISPATCH 2026
            </div>
            <div className="text-[7px] text-ink-muted uppercase">CHROMADB VERIFIED</div>
          </div>
        </div>
      </header>

      {/* Professional Summary */}
      <section className="mb-6">
        <div className="border-b-2 border-ink pb-1 mb-2.5 flex items-center justify-between">
          <h2 className="font-mono text-xs font-bold uppercase tracking-widest text-ink">
            [01] Executive Dossier & Summary
          </h2>
          <span className="font-mono text-[9px] text-ink-muted uppercase">VERIFIED SYNOPSIS</span>
        </div>
        {isEditing ? (
          <textarea
            rows={4}
            value={resume.summary}
            onChange={(e) => onUpdateResume({ ...resume, summary: e.target.value })}
            className="w-full font-mono text-xs p-3 border-2 border-ink rounded bg-paper"
          />
        ) : (
          <p className="font-serif text-sm text-ink/90 leading-relaxed text-justify">
            {resume.summary}
          </p>
        )}
      </section>

      {/* Experience */}
      {resume.experience && resume.experience.length > 0 && (
        <section className="mb-6">
          <div className="border-b-2 border-ink pb-1 mb-3 flex items-center justify-between">
            <h2 className="font-mono text-xs font-bold uppercase tracking-widest text-ink">
              [02] Professional Engagements & Field Record
            </h2>
            <span className="font-mono text-[9px] text-ink-muted uppercase">CHRONOLOGICAL</span>
          </div>
          <div className="space-y-5">
            {resume.experience.map((exp, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1">
                  <div>
                    <span className="font-serif font-bold text-ink text-base">{exp.role}</span>
                    <span className="font-serif italic text-terracotta font-medium"> &mdash; {exp.company}</span>
                    {exp.location && (
                      <span className="font-mono text-[11px] text-ink-muted ml-2">[{exp.location}]</span>
                    )}
                  </div>
                  <span className="font-mono text-xs text-ink-muted font-bold shrink-0">{exp.duration}</span>
                </div>
                <ul className="list-disc list-outside ml-4 mt-1.5 space-y-1 font-serif text-xs text-ink/90">
                  {exp.bullets.map((b, bIdx) => (
                    <li key={bIdx} className="leading-relaxed">
                      {b}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Projects */}
      {resume.projects && resume.projects.length > 0 && (
        <section className="mb-6">
          <div className="border-b-2 border-ink pb-1 mb-3 flex items-center justify-between">
            <h2 className="font-mono text-xs font-bold uppercase tracking-widest text-ink">
              [03] Verified System Projects & Works
            </h2>
            <span className="font-mono text-[9px] text-ink-muted uppercase">PROVENANCE BACKED</span>
          </div>
          <div className="space-y-4">
            {resume.projects.map((proj, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1">
                  <span className="font-serif font-bold text-ink text-sm sm:text-base">{proj.name}</span>
                  <div className="flex flex-wrap gap-1">
                    {proj.technologies?.map((t, tIdx) => (
                      <span
                        key={tIdx}
                        className="font-mono text-[10px] bg-manila text-ink px-2 py-0.5 rounded border border-ink/40"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                {proj.description && (
                  <p className="font-serif italic text-xs text-ink-muted">{proj.description}</p>
                )}
                <ul className="list-disc list-outside ml-4 mt-1 space-y-1 font-serif text-xs text-ink/90">
                  {(proj.bullets || proj.highlights || []).map((b, bIdx) => (
                    <li key={bIdx} className="leading-relaxed">
                      {b}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Technical Skills */}
      {resume.skills && resume.skills.length > 0 && (
        <section className="mb-6">
          <div className="border-b-2 border-ink pb-1 mb-3 flex items-center justify-between">
            <h2 className="font-mono text-xs font-bold uppercase tracking-widest text-ink">
              [04] Technical Ledger & Skills Inventory
            </h2>
            <span className="font-mono text-[9px] text-ink-muted uppercase">INDEXED</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {resume.skills.map((s, idx) => (
              <div key={idx} className="p-2.5 bg-manila/30 border border-ink/20 rounded">
                <span className="font-mono text-[11px] font-bold text-ink uppercase block mb-0.5">
                  {s.category}
                </span>
                <span className="font-serif text-xs text-ink-muted leading-relaxed">
                  {s.items.join(", ")}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Education */}
      {resume.education && resume.education.length > 0 && (
        <section>
          <div className="border-b-2 border-ink pb-1 mb-2.5 flex items-center justify-between">
            <h2 className="font-mono text-xs font-bold uppercase tracking-widest text-ink">
              [05] Academic Credentials & Formation
            </h2>
            <span className="font-mono text-[9px] text-ink-muted uppercase">OFFICIAL</span>
          </div>
          <div className="space-y-2">
            {resume.education.map((edu, idx) => (
              <div key={idx} className="flex justify-between items-baseline">
                <div>
                  <span className="font-serif font-bold text-ink text-sm">{edu.degree}</span>
                  <span className="font-serif italic text-ink-muted"> &mdash; {edu.institution}</span>
                  {edu.details && (
                    <p className="font-mono text-[10px] text-ink-muted mt-0.5">{edu.details}</p>
                  )}
                </div>
                <span className="font-mono text-xs text-ink-muted font-bold">{edu.year}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

