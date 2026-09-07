"use client";

import React, { useState, useEffect, useRef } from "react";
import { Database, Plus, RefreshCw, Trash2, CheckCircle2, FileText, Github, Sparkles, Upload, FileUp, ScrollText, Stamp, FolderArchive } from "lucide-react";
import ProfileQuestionnaireModal from "@/components/ProfileQuestionnaireModal";
import { fetchKBStats, fetchKBItems, ingestText, uploadResumePDF, seedSampleProfile, clearKnowledgeBase } from "@/lib/api";
import { KnowledgeBaseStats } from "@/lib/types";

interface KnowledgeBaseProps {
  onRefreshStats: () => void;
}

export default function KnowledgeBase({ onRefreshStats }: KnowledgeBaseProps) {
  const [stats, setStats] = useState<KnowledgeBaseStats | null>(null);
  const [items, setItems] = useState<Record<string, any[]>>({});
  const [loading, setLoading] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [isQuestionnaireOpen, setIsQuestionnaireOpen] = useState(false);

  // Ingest Text Form state
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("raw_documents");
  const [tags, setTags] = useState("portfolio, bio");
  const [ingestingText, setIngestingText] = useState(false);

  // PDF Upload state
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingPdf(true);
    setActionNotice(null);
    try {
      const res = await uploadResumePDF(file);
      setActionNotice(res.message);
      await loadData();
    } catch (err: any) {
      setActionNotice("PDF Upload error: " + err.message);
    } finally {
      setUploadingPdf(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, i] = await Promise.all([fetchKBStats(), fetchKBItems()]);
      setStats(s);
      setItems(i);
      onRefreshStats();
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSeed = async () => {
    setLoading(true);
    setActionNotice(null);
    try {
      const res = await seedSampleProfile();
      setActionNotice("ChromaDB successfully seeded with full developer profile!");
      await loadData();
    } catch (err: any) {
      setActionNotice("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    if (!confirm("Are you sure you want to clear all data in the local vector database?")) return;
    setLoading(true);
    try {
      await clearKnowledgeBase();
      setActionNotice("ChromaDB cleared.");
      await loadData();
    } catch (err: any) {
      setActionNotice("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleIngestText = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setIngestingText(true);
    try {
      const tagList = tags.split(",").map((t) => t.trim()).filter(Boolean);
      const res = await ingestText(title, content, category, tagList);
      setActionNotice(`Ingested ${res.chunks} chunks for "${title}"!`);
      setTitle("");
      setContent("");
      await loadData();
    } catch (err: any) {
      setActionNotice("Failed to ingest: " + err.message);
    } finally {
      setIngestingText(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Dossier */}
      <div className="bg-[#fffdf9] p-6 sm:p-8 rounded-xl border-2 border-ink shadow-dossier">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-5 border-b-2 border-ink/20 mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-[11px] uppercase tracking-widest bg-ink text-paper px-2 py-0.5 font-bold">
                ARCHIVAL LEDGER
              </span>
              <span className="font-mono text-[11px] text-ink-muted uppercase tracking-wider">
                CHROMADB // ZERO-CLOUD
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-serif font-bold text-ink tracking-tight flex items-center gap-2.5">
              <FolderArchive className="w-6 h-6 text-terracotta" />
              ChromaDB Archival Ledger
            </h2>
            <p className="text-xs sm:text-sm font-serif italic text-ink-muted mt-1 max-w-2xl leading-relaxed">
              All personal records remain 100% on your local disk. Documents are indexed into local vector embeddings for similarity-grounded retrieval.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setIsQuestionnaireOpen(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono text-xs font-bold rounded border-2 border-ink shadow-press transition-all active:translate-x-[1px]"
            >
              <FileText className="w-3.5 h-3.5" />
              PROFILE QUESTIONNAIRE
            </button>
            <button
              onClick={handleSeed}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-manila hover:bg-vintage-gold text-ink font-mono text-xs font-bold rounded border-2 border-ink shadow-press transition-all active:translate-x-[1px]"
            >
              <Sparkles className="w-3.5 h-3.5 text-terracotta" />
              SEED DEMO PROFILE
            </button>
            <button
              onClick={handleClear}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#fff0ed] hover:bg-terracotta hover:text-paper text-terracotta font-mono text-xs font-bold rounded border-2 border-ink shadow-press transition-all active:translate-x-[1px]"
            >
              <Trash2 className="w-3.5 h-3.5" />
              RESET DB
            </button>
            <button
              onClick={loadData}
              disabled={loading}
              className="p-2 bg-manila hover:bg-paper text-ink rounded border-2 border-ink shadow-press transition-all"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-terracotta" : ""}`} />
            </button>
          </div>
        </div>

        {actionNotice && (
          <div className="mb-6 p-4 bg-[#fff8f4] border-2 border-ink rounded-lg font-mono text-xs text-ink flex items-center gap-2 shadow-press">
            <CheckCircle2 className="w-4 h-4 text-fountain-teal" />
            {actionNotice}
          </div>
        )}

        {/* Counts Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
          <StatBox label="Work Experiences" count={stats?.experiences ?? 0} />
          <StatBox label="Projects & Portfolios" count={stats?.projects ?? 0} />
          <StatBox label="Technical Skills" count={stats?.skills ?? 0} />
          <StatBox label="Education" count={stats?.education ?? 0} />
          <StatBox label="Raw Notes / Docs" count={stats?.raw_documents ?? 0} />
        </div>
      </div>

      {/* PDF Resume Ingestion Card */}
      <div className="bg-manila/50 p-6 sm:p-7 rounded-xl border-2 border-ink shadow-press">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <span className="font-mono text-[10px] uppercase tracking-widest bg-ink text-paper px-2 py-0.5 font-bold inline-block mb-1.5">
              AUTOMATIC INGESTION
            </span>
            <h3 className="text-xl font-serif font-bold text-ink flex items-center gap-2">
              <FileUp className="w-5 h-5 text-terracotta" />
              Upload Prior Physical Resume (PDF)
            </h3>
            <p className="font-serif italic text-xs text-ink-muted mt-1 max-w-2xl leading-relaxed">
              Upload an existing PDF resume. The system parses your real employment history, education, and credentials locally into ChromaDB with zero cloud exposure.
            </p>
          </div>

          <div className="shrink-0">
            <input
              type="file"
              ref={fileInputRef}
              accept=".pdf"
              onChange={handlePdfUpload}
              className="hidden"
            />
            <button
              type="button"
              disabled={uploadingPdf}
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-2 px-5 py-3 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all disabled:opacity-50"
            >
              {uploadingPdf ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-paper border-t-transparent rounded-full animate-spin" />
                  PARSING PDF...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  SELECT RESUME PDF
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Ingestion Panels: Add Note & GitHub */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Add Text Note */}
        <div className="bg-[#fffdf9] p-6 rounded-xl border-2 border-ink shadow-press">
          <h3 className="font-serif text-lg font-bold text-ink flex items-center gap-2 mb-1">
            <Plus className="w-4 h-4 text-terracotta" />
            Add Note, Bio, or Project Description
          </h3>
          <p className="font-serif italic text-xs text-ink-muted mb-4">
            Paste raw text, project briefs, or custom career notes. They will be chunked and embedded automatically.
          </p>

          <form onSubmit={handleIngestText} className="space-y-4">
            <div>
              <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                Title / Identifier
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Distributed Consensus Engine Overview"
                required
                className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-paper text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
              />
            </div>

            <div>
              <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                Content (Markdown / Text)
              </label>
              <textarea
                rows={5}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Paste details, accomplishments, metrics, tools used..."
                required
                className="w-full font-mono text-xs p-3 border-2 border-ink rounded bg-paper text-ink focus:outline-none focus:ring-2 focus:ring-terracotta leading-relaxed"
              />
            </div>

            <div>
              <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                Tags (Comma-separated)
              </label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full font-mono text-xs px-3 py-1.5 border-2 border-ink rounded bg-paper text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
              />
            </div>

            <button
              type="submit"
              disabled={ingestingText}
              className="w-full py-2.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all disabled:opacity-50"
            >
              {ingestingText ? "EMBEDDING INTO CHROMADB..." : "INDEX INTO KNOWLEDGE BASE"}
            </button>
          </form>
        </div>

        {/* GitHub Ingestion & File Ingest Info */}
        <div className="bg-[#fffdf9] p-6 rounded-xl border-2 border-ink shadow-press space-y-4">
          <h3 className="font-serif text-lg font-bold text-ink flex items-center gap-2 mb-1">
            <Github className="w-4 h-4 text-terracotta" />
            CLI Automation Script
          </h3>
          <p className="font-serif italic text-xs text-ink-muted leading-relaxed">
            You can automatically index all your public GitHub repositories, stars, languages, and README summaries into ChromaDB using the included CLI script:
          </p>

          <div className="bg-ink text-paper p-3.5 rounded-lg font-mono text-xs overflow-x-auto border-2 border-ink">
            <code>backend\venv\Scripts\python backend/scripts/ingest_github.py your_username</code>
          </div>

          <div className="border-t-2 border-ink/20 pt-4">
            <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-ink mb-1 flex items-center gap-1.5">
              <Stamp className="w-3.5 h-3.5 text-terracotta" />
              100% Zero-Cloud Privacy Guarantee
            </h4>
            <p className="font-serif text-xs text-ink-muted leading-relaxed">
              Neither your resume, job descriptions, nor vector embeddings leave your device. All vectors are stored in <code className="font-mono bg-manila px-1.5 py-0.5 rounded border border-ink/20">backend/data/chroma_db</code> and evaluated locally with local HuggingFace embeddings and local Ollama models.
            </p>
          </div>
        </div>
      </div>

      {/* Stored Items Viewer */}
      <div className="bg-[#fffdf9] p-6 rounded-xl border-2 border-ink shadow-press">
        <h3 className="font-serif text-lg font-bold text-ink mb-4 flex items-center justify-between">
          <span>Indexed Vector Store Records</span>
          <span className="font-mono text-xs text-ink-muted font-normal uppercase">LOCAL CHROMADB REPOSITORY</span>
        </h3>
        <div className="space-y-4 max-h-96 overflow-y-auto pr-1">
          {Object.entries(items).map(([colName, records]) => {
            if (!records || records.length === 0) return null;
            return (
              <div key={colName} className="border-2 border-ink/30 rounded-lg p-4 bg-manila/30">
                <div className="font-mono text-xs font-bold text-ink uppercase mb-2 flex items-center justify-between">
                  <span>COLLECTION: {colName}</span>
                  <span className="text-ink-muted font-normal">[{records.length} ITEMS]</span>
                </div>
                <div className="space-y-2">
                  {records.slice(0, 5).map((r, rIdx) => (
                    <div key={rIdx} className="font-serif text-xs p-3 bg-paper rounded border border-ink/20 text-ink/90 leading-relaxed">
                      {r.document}
                    </div>
                  ))}
                  {records.length > 5 && (
                    <p className="font-mono text-[11px] text-ink-muted italic text-right">
                      + {records.length - 5} more records in {colName}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <ProfileQuestionnaireModal
        isOpen={isQuestionnaireOpen}
        onClose={() => setIsQuestionnaireOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
}

function StatBox({ label, count }: { label: string; count: number }) {
  return (
    <div className="bg-manila/50 p-4 rounded-lg border-2 border-ink shadow-press text-center">
      <div className="font-serif text-3xl font-bold text-ink">{count}</div>
      <div className="font-mono text-[10px] uppercase font-bold text-ink-muted mt-1 tracking-wider leading-tight">
        {label}
      </div>
    </div>
  );
}

