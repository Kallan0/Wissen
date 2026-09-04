"use client";

import React, { useState } from "react";
import { Download, Edit3, Eye, FileText, CheckCircle, Sparkles, LayoutTemplate } from "lucide-react";
import { ResumeData } from "@/lib/types";
import { exportPDF, getDownloadUrl } from "@/lib/api";

interface ResumePreviewProps {
  resume: ResumeData | null;
  onUpdateResume: (updated: ResumeData) => void;
}

export default function ResumePreview({ resume, onUpdateResume }: ResumePreviewProps) {
  const [template, setTemplate] = useState<"modern" | "minimal">("modern");
  const [isEditing, setIsEditing] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [pdfDownloadUrl, setPdfDownloadUrl] = useState<string | null>(null);
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  if (!resume) {
    return (
      <div className="bg-white p-12 rounded-xl border border-slate-200 text-center shadow-sm">
        <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-slate-700">No Resume Generated Yet</h3>
        <p className="text-sm text-slate-500 max-w-md mx-auto mt-1">
          Go to the <strong>Job Tailor</strong> tab, paste a Job Description, and click "Generate Tailored Resume" to see your tailored CV and download high-resolution PDFs.
        </p>
      </div>
    );
  }

  const handleExportPDF = async () => {
    setDownloading(true);
    setExportNotice(null);
    try {
      const res = await exportPDF(resume, template);
      const url = getDownloadUrl(res.filename);
      setPdfDownloadUrl(url);
      setExportNotice("PDF rendered successfully! Download ready.");
      
      // Auto-trigger download
      const a = document.createElement("a");
      a.href = url;
      a.download = res.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (err: any) {
      console.error(err);
      setExportNotice("Failed to export PDF: " + err.message);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Action Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg border border-slate-200">
            <button
              onClick={() => setTemplate("modern")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                template === "modern" ? "bg-white text-blue-600 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Modern Tech
            </button>
            <button
              onClick={() => setTemplate("minimal")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                template === "minimal" ? "bg-white text-blue-600 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Minimalist Executive
            </button>
          </div>

          <button
            onClick={() => setIsEditing(!isEditing)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
              isEditing ? "bg-amber-50 text-amber-700 border-amber-300" : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
            }`}
          >
            {isEditing ? <Eye className="w-3.5 h-3.5" /> : <Edit3 className="w-3.5 h-3.5" />}
            {isEditing ? "Preview Mode" : "Edit Mode"}
          </button>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          {resume._ai_provider && (
            <span className="text-xs text-slate-500 bg-slate-100 px-2.5 py-1 rounded border border-slate-200 hidden md:inline">
              Engine: <strong className="text-slate-700">{resume._ai_provider}</strong>
            </span>
          )}

          <button
            onClick={handleExportPDF}
            disabled={downloading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
          >
            {downloading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Rendering PDF...
              </>
            ) : (
              <>
                <Download className="w-3.5 h-3.5" />
                Download Print-Ready PDF
              </>
            )}
          </button>
        </div>
      </div>

      {exportNotice && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-blue-600" />
            {exportNotice}
          </span>
          {pdfDownloadUrl && (
            <a
              href={pdfDownloadUrl}
              target="_blank"
              rel="noreferrer"
              className="font-semibold underline hover:text-blue-900"
            >
              Direct Link
            </a>
          )}
        </div>
      )}

      {/* Tailoring Insights Banner */}
      {resume.tailored_match_notes && resume.tailored_match_notes.length > 0 && (
        <div className="p-4 bg-indigo-50/60 border border-indigo-100 rounded-xl">
          <div className="text-xs font-bold text-indigo-900 uppercase tracking-wide flex items-center gap-1.5 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            AI Tailoring Strategy & JD Alignment Notes
          </div>
          <ul className="list-disc list-inside text-xs text-indigo-800 space-y-1">
            {resume.tailored_match_notes.map((note, idx) => (
              <li key={idx}>{note}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Resume Document Canvas */}
      <div className="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
        {template === "modern" ? (
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
