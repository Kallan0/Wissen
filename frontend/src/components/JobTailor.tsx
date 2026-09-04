"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, Briefcase, FileCode, CheckCircle2, AlertCircle } from "lucide-react";
import { tailorResume } from "@/lib/api";
import { TailorResponse } from "@/lib/types";

interface JobTailorProps {
  models: string[];
  onTailored: (result: TailorResponse) => void;
  initialRole?: string;
  initialJd?: string;
}

const SAMPLE_JDS = [
  {
    label: "Senior Full-Stack & RAG Engineer",
    role: "Senior AI / Full-Stack Engineer",
    text: `About the Role:
We are seeking an experienced Senior Full-Stack Engineer to architect our next-generation privacy-first AI intelligence platform. You will be responsible for designing high-performance backend microservices in Python (FastAPI), connecting retrieval-augmented generation (RAG) pipelines using ChromaDB and local LLMs (Ollama / Llama 3), and delivering polished web applications with Next.js and Tailwind CSS.

Requirements:
- 4+ years building production web platforms with Python (FastAPI/Flask) and TypeScript (React/Next.js).
- Deep experience with Vector Databases (ChromaDB, Pinecone, or pgvector) and RAG document ingestion pipelines.
- Familiarity running local open-weights LLMs (Ollama, vLLM, LangChain) with zero external data leaks.
- Strong grounding in headless browser PDF generation and automated test workflows.`,
  },
  {
    label: "Python Backend & Systems Developer",
    role: "Senior Python Backend Engineer",
    text: `Job Description:
We are hiring a Senior Python Backend Developer to design high-throughput microservices, optimize distributed database schemas, and build resilient ETL pipelines. 

Key Responsibilities:
- Build low-latency asynchronous APIs with FastAPI and Uvicorn.
- Manage persistent caching with Redis and schema migrations with PostgreSQL.
- Implement robust telemetry, unit test suites, and Dockerized deployments.
- Collaborate with frontend engineers to expose clean RESTful endpoints.`,
  },
];

export default function JobTailor({ models, onTailored, initialRole, initialJd }: JobTailorProps) {
  const [jobDescription, setJobDescription] = useState(initialJd || SAMPLE_JDS[0].text);
  const [targetRole, setTargetRole] = useState(initialRole || SAMPLE_JDS[0].role);
  const [selectedModel, setSelectedModel] = useState(models[0] || "llama3");
  const [template, setTemplate] = useState("modern");
  const [candidateName, setCandidateName] = useState("Joji Developer");
  const [candidateEmail, setCandidateEmail] = useState("joji.dev@example.com");
  const [candidateLocation, setCandidateLocation] = useState("Bengaluru, India / Remote");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (models.length > 0 && (!selectedModel || selectedModel === "llama3")) {
      setSelectedModel(models[0]);
    }
  }, [models]);

  useEffect(() => {
    if (initialRole) setTargetRole(initialRole);
    if (initialJd) setJobDescription(initialJd);
  }, [initialRole, initialJd]);

  const handleGenerate = async () => {
    if (!jobDescription.trim()) {
      setError("Please provide a Job Description.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const result = await tailorResume(
        jobDescription,
        targetRole,
        selectedModel,
        candidateName,
        candidateEmail,
        template
      );
      onTailored(result);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "An error occurred during resume tailoring.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-100 gap-2">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-blue-600" />
              Tailor Resume to Job Description
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              ChromaDB performs vector similarity retrieval against your verified career database, and the local LLM synthesizes an ATS-optimized resume.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-500">Quick Samples:</span>
            {SAMPLE_JDS.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setJobDescription(s.text);
                  setTargetRole(s.role);
                }}
                className="text-xs bg-slate-100 hover:bg-blue-50 hover:text-blue-600 text-slate-700 font-medium px-2.5 py-1 rounded transition border border-slate-200"
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="p-4 mb-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3 text-red-700 text-sm">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Generation Notice</p>
              <p>{error}</p>
            </div>
          </div>
        )}

        {/* Configuration Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wide">
              Target Role Title
            </label>
            <input
              type="text"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. Senior Full-Stack Engineer"
              className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wide">
              Local Ollama Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {models.length > 0 ? (
                models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))
              ) : (
                <option value="llama3">llama3 (Default)</option>
              )}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wide">
              Resume Style Template
            </label>
            <select
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="modern">Modern Tech (Clean Blue Accent)</option>
              <option value="minimal">Minimalist Executive (Serif Monochrome)</option>
            </select>
          </div>
        </div>

        {/* Candidate Information (Collapsible / Customizable) */}
        <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 mb-5">
          <div className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Candidate Header Overrides
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <input
              type="text"
              placeholder="Candidate Name"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              className="text-xs px-3 py-1.5 border border-slate-300 rounded bg-white"
            />
            <input
              type="email"
              placeholder="Contact Email"
              value={candidateEmail}
              onChange={(e) => setCandidateEmail(e.target.value)}
              className="text-xs px-3 py-1.5 border border-slate-300 rounded bg-white"
            />
            <input
              type="text"
              placeholder="Location"
              value={candidateLocation}
              onChange={(e) => setCandidateLocation(e.target.value)}
              className="text-xs px-3 py-1.5 border border-slate-300 rounded bg-white"
            />
          </div>
        </div>

        {/* Job Description Textarea */}
        <div className="mb-6">
          <label className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wide">
            Job Description (JD)
          </label>
          <textarea
            rows={10}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the target job description here..."
            className="w-full text-sm font-mono p-3.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent leading-relaxed"
          />
        </div>

        {/* Trigger Button */}
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleGenerate}
            disabled={loading}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-lg shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Querying ChromaDB & Ollama...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate Tailored Resume
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
