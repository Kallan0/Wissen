"use client";

import React, { useState, useEffect, useRef } from "react";
import { Database, Plus, RefreshCw, Trash2, CheckCircle2, FileText, Github, Sparkles, Upload, FileUp } from "lucide-react";
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
      {/* Overview Cards */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 mb-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-600" />
              ChromaDB Knowledge Base
            </h2>
            <p className="text-sm text-slate-500 mt-0.5">
              All personal data stays 100% local on your machine. Documents are indexed into local vector embeddings for similarity retrieval.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSeed}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold rounded-lg border border-indigo-200 transition"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Seed Sample Profile
            </button>
            <button
              onClick={handleClear}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-700 text-xs font-semibold rounded-lg border border-red-200 transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Reset DB
            </button>
            <button
              onClick={loadData}
              disabled={loading}
              className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-blue-600" : ""}`} />
            </button>
          </div>
        </div>

        {actionNotice && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-blue-600" />
            {actionNotice}
          </div>
        )}

        {/* Counts Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <StatBox label="Work Experiences" count={stats?.experiences ?? 0} />
          <StatBox label="Projects & Portfolios" count={stats?.projects ?? 0} />
          <StatBox label="Technical Skills" count={stats?.skills ?? 0} />
          <StatBox label="Education" count={stats?.education ?? 0} />
          <StatBox label="Raw Notes / Docs" count={stats?.raw_documents ?? 0} />
        </div>
      </div>

      {/* PDF Resume Ingestion Card */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <FileUp className="w-5 h-5 text-blue-600" />
              Upload Your Actual Resume (PDF)
            </h3>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              Upload your own existing PDF resume. The system extracts your real work history, education, and skills, parses them locally, and stores them in ChromaDB with zero cloud exposure.
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
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
            >
              {uploadingPdf ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Parsing & Indexing PDF...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Select Resume PDF
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Ingestion Panels: Add Note & GitHub */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Add Text Note */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-1">
            <Plus className="w-4 h-4 text-blue-600" />
            Add Note, Bio, or Project Description
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Paste raw text, project briefs (e.g. Unity/Blender summaries), or custom career notes. They will be chunked and embedded automatically.
          </p>

          <form onSubmit={handleIngestText} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Unity Physics Engine Project Summary"
                required
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Content (Markdown / Text)</label>
              <textarea
                rows={5}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Paste details, achievements, tools used..."
                required
                className="w-full text-xs p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Tags (Comma-separated)</label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-lg"
              />
            </div>

            <button
              type="submit"
              disabled={ingestingText}
              className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
            >
              {ingestingText ? "Embedding into ChromaDB..." : "Index into Knowledge Base"}
            </button>
          </form>
        </div>

        {/* GitHub Ingestion & File Ingest Info */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-1">
            <Github className="w-4 h-4 text-slate-800" />
            GitHub Ingestion Script
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            You can automatically index all your public GitHub repositories, stars, languages, and README summaries into ChromaDB using the included CLI script:
          </p>

          <div className="bg-slate-900 text-slate-100 p-3 rounded-lg font-mono text-xs overflow-x-auto">
            <code>backend\venv\Scripts\python backend/scripts/ingest_github.py your_github_username</code>
          </div>

          <div className="border-t border-slate-100 pt-3">
            <h4 className="text-xs font-bold text-slate-800 mb-1">Data Privacy Guarantee</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Neither your resume, job descriptions, nor vector embeddings leave your device. All vectors are stored in <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-[11px]">backend/data/chroma_db</code> and evaluated locally with local embeddings and Ollama.
            </p>
          </div>
        </div>
      </div>

      {/* Stored Items Viewer */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 mb-3">Indexed Vector Store Records</h3>
        <div className="space-y-4 max-h-96 overflow-y-auto pr-1">
          {Object.entries(items).map(([colName, records]) => {
            if (!records || records.length === 0) return null;
            return (
              <div key={colName} className="border border-slate-100 rounded-lg p-3 bg-slate-50">
                <div className="text-xs font-bold text-slate-800 uppercase mb-2 flex items-center justify-between">
                  <span>Collection: {colName}</span>
                  <span className="text-slate-500 font-normal">{records.length} items</span>
                </div>
                <div className="space-y-1.5">
                  {records.slice(0, 5).map((r, rIdx) => (
                    <div key={rIdx} className="text-xs p-2 bg-white rounded border border-slate-200 text-slate-600">
                      {r.document}
                    </div>
                  ))}
                  {records.length > 5 && (
                    <p className="text-[11px] text-slate-400 italic text-right">
                      + {records.length - 5} more records in {colName}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function StatBox({ label, count }: { label: string; count: number }) {
  return (
    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-center">
      <div className="text-xl font-extrabold text-slate-900">{count}</div>
      <div className="text-[11px] font-medium text-slate-500 mt-0.5">{label}</div>
    </div>
  );
}
