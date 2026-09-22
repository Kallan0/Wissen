"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, Briefcase, FileCode, CheckCircle2, AlertCircle, ScrollText, Stamp, Tag, Target, Mail } from "lucide-react";
import EmptyKBBanner from "@/components/EmptyKBBanner";
import ProfileQuestionnaireModal from "@/components/ProfileQuestionnaireModal";
import ATSGapAnalyzer from "@/components/ATSGapAnalyzer";
import CoverLetterModal from "@/components/CoverLetterModal";
import { tailorResume, fetchKBProfile, analyzeATSGap, generateCoverLetter } from "@/lib/api";
import { TailorResponse, ATSAnalysisResponse, CoverLetterResponse } from "@/lib/types";

interface JobTailorProps {
  models: string[];
  onTailored: (result: TailorResponse) => void;
  initialRole?: string;
  initialJd?: string;
}

const SAMPLE_JDS = [
  {
    label: "[REF-01] Senior AI & RAG Engineer",
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
    label: "[REF-02] Python Systems Architect",
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
  const [template, setTemplate] = useState("vintage");
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [candidateLocation, setCandidateLocation] = useState("");

  const [isKBEmpty, setIsKBEmpty] = useState(false);
  const [isQuestionnaireOpen, setIsQuestionnaireOpen] = useState(false);

  // ATS Gap Analysis State
  const [atsData, setAtsData] = useState<ATSAnalysisResponse | null>(null);
  const [atsLoading, setAtsLoading] = useState(false);

  // Cover Letter & Outreach State
  const [coverLetterData, setCoverLetterData] = useState<CoverLetterResponse | null>(null);
  const [coverLetterLoading, setCoverLetterLoading] = useState(false);
  const [isCoverLetterOpen, setIsCoverLetterOpen] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCandidateProfile = async () => {
    try {
      const prof = await fetchKBProfile();
      if (!prof.exists || prof.total_items === 0) {
        setIsKBEmpty(true);
      } else {
        setIsKBEmpty(false);
        if (prof.candidate?.name) setCandidateName(prof.candidate.name);
        if (prof.candidate?.email) setCandidateEmail(prof.candidate.email);
        if (prof.candidate?.location) setCandidateLocation(prof.candidate.location);
      }
    } catch (err) {
      console.error("Error loading candidate profile:", err);
    }
  };

  useEffect(() => {
    loadCandidateProfile();
  }, []);

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

  const handleAnalyzeATS = async () => {
    if (!jobDescription.trim()) {
      setError("Please enter a Job Description first to run the ATS Match Matrix.");
      return;
    }
    setError(null);
    setAtsLoading(true);
    try {
      const result = await analyzeATSGap(jobDescription, selectedModel);
      setAtsData(result);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "ATS analysis failed.");
    } finally {
      setAtsLoading(false);
    }
  };

  const handleOpenCoverLetter = async () => {
    if (!jobDescription.trim()) {
      setError("Please enter a Job Description first to generate a Cover Letter.");
      return;
    }
    setError(null);
    setIsCoverLetterOpen(true);
    if (!coverLetterData) {
      setCoverLetterLoading(true);
      try {
        const result = await generateCoverLetter(jobDescription, targetRole, selectedModel);
        setCoverLetterData(result);
      } catch (err: any) {
        console.error(err);
        setError(err.message || "Cover letter generation failed.");
      } finally {
        setCoverLetterLoading(false);
      }
    }
  };

  return (
    <div className="space-y-6">
      {isKBEmpty && (
        <EmptyKBBanner
          onOpenQuestionnaire={() => setIsQuestionnaireOpen(true)}
          onRefresh={loadCandidateProfile}
        />
      )}

      {/* Editorial Manila Dossier Container */}
      <div className="bg-[#fffdf9] p-6 sm:p-8 rounded-xl border-2 border-ink shadow-dossier relative overflow-hidden">
        {/* Top Header Badge Strip */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 mb-6 border-b-2 border-ink/20 gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-[11px] uppercase tracking-widest bg-ink text-paper px-2 py-0.5 font-bold">
                DOSSIER SPECIFICATION
              </span>
              <span className="font-mono text-[11px] text-ink-muted uppercase tracking-wider">
                SERIES: 2026-PRESS // ATS-GROUNDED
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-serif font-bold text-ink tracking-tight flex items-center gap-2.5">
              <ScrollText className="w-6 h-6 text-terracotta" />
              Tailor Resume to Job Description
            </h2>
            <p className="text-xs sm:text-sm text-ink-muted font-serif italic mt-1 max-w-2xl">
              ChromaDB performs vector similarity retrieval against your verified career database, and the local Ollama LLM synthesizes an ATS-optimized tactile CV.
            </p>
          </div>

          {/* Quick Samples */}
          <div className="flex flex-col items-start sm:items-end gap-1.5 shrink-0">
            <span className="font-mono text-[10px] uppercase tracking-widest text-ink-muted font-bold flex items-center gap-1">
              <Tag className="w-3 h-3 text-terracotta" /> Reference Samples:
            </span>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_JDS.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setJobDescription(s.text);
                    setTargetRole(s.role);
                  }}
                  className="font-mono text-xs bg-manila hover:bg-terracotta hover:text-paper text-ink font-semibold px-3 py-1 rounded border-2 border-ink shadow-press transition-all active:translate-x-[1px] active:translate-y-[1px]"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 mb-6 bg-[#fff0ed] border-2 border-terracotta rounded-lg flex items-start gap-3 text-terracotta shadow-press">
            <AlertCircle className="w-5 h-5 text-terracotta shrink-0 mt-0.5" />
            <div>
              <p className="font-mono font-bold text-xs uppercase tracking-wider">TELEGRAM DISPATCH NOTICE</p>
              <p className="text-xs font-serif mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Configuration Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-6">
          <div className="bg-manila/50 p-4 rounded-lg border-2 border-ink shadow-press">
            <label className="block font-mono text-[11px] font-bold text-ink mb-1.5 uppercase tracking-wider">
              [01] Target Role Title
            </label>
            <input
              type="text"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. Senior Full-Stack Engineer"
              className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
            />
          </div>

          <div className="bg-manila/50 p-4 rounded-lg border-2 border-ink shadow-press">
            <label className="block font-mono text-[11px] font-bold text-ink mb-1.5 uppercase tracking-wider">
              [02] Local Ollama Engine
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
            >
              {models.length > 0 ? (
                models.map((m) => (
                  <option key={m} value={m}>
                    {m} (Active)
                  </option>
                ))
              ) : (
                <option value="llama3">llama3 (Default)</option>
              )}
            </select>
          </div>

          <div className="bg-manila/50 p-4 rounded-lg border-2 border-ink shadow-press">
            <label className="block font-mono text-[11px] font-bold text-ink mb-1.5 uppercase tracking-wider">
              [03] Typography & Layout
            </label>
            <select
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
            >
              <option value="vintage">Wissen Vintage Press (Tactile Editorial)</option>
              <option value="modern">Modern Tech (Clean Blue Accent)</option>
              <option value="minimal">Minimalist Executive (Serif Monochrome)</option>
            </select>
          </div>
        </div>

        {/* Candidate Information Docket */}
        <div className="bg-paper p-4 rounded-lg border-2 border-ink mb-6 shadow-press">
          <div className="font-mono text-[11px] font-bold text-ink uppercase tracking-widest mb-3 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-fountain-teal" />
              Candidate Dossier Identity
            </span>
            <span className="text-[10px] text-ink-muted uppercase font-normal">
              EDITABLE PRE-FLIGHT OVERRIDES
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <span className="font-mono text-[9px] uppercase tracking-wider text-ink-muted block mb-1">CANDIDATE NAME</span>
              <input
                type="text"
                placeholder="Candidate Name"
                value={candidateName}
                onChange={(e) => setCandidateName(e.target.value)}
                className="w-full font-mono text-xs px-3 py-1.5 border-2 border-ink/40 focus:border-ink rounded bg-[#fffdf9]"
              />
            </div>
            <div>
              <span className="font-mono text-[9px] uppercase tracking-wider text-ink-muted block mb-1">CONTACT EMAIL</span>
              <input
                type="email"
                placeholder="Contact Email"
                value={candidateEmail}
                onChange={(e) => setCandidateEmail(e.target.value)}
                className="w-full font-mono text-xs px-3 py-1.5 border-2 border-ink/40 focus:border-ink rounded bg-[#fffdf9]"
              />
            </div>
            <div>
              <span className="font-mono text-[9px] uppercase tracking-wider text-ink-muted block mb-1">DISPATCH LOCATION</span>
              <input
                type="text"
                placeholder="Location"
                value={candidateLocation}
                onChange={(e) => setCandidateLocation(e.target.value)}
                className="w-full font-mono text-xs px-3 py-1.5 border-2 border-ink/40 focus:border-ink rounded bg-[#fffdf9]"
              />
            </div>
          </div>
        </div>

        {/* Job Description Textarea */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-1.5">
            <label className="block font-mono text-[11px] font-bold text-ink uppercase tracking-wider">
              [04] Target Job Description (Paste JD Text)
            </label>
            <span className="font-mono text-[10px] text-ink-muted uppercase">
              RAG VECTOR EMBEDDINGS MATCH AGAINST THIS CONTENT
            </span>
          </div>
          <textarea
            rows={9}
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the target job description or requirements here..."
            className="w-full font-mono text-xs p-4 border-2 border-ink rounded-lg bg-[#fffdf9] focus:outline-none focus:ring-2 focus:ring-terracotta leading-relaxed shadow-press"
          />
        </div>

        {/* Trigger Mechanical Action Button */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2 border-t-2 border-ink/10">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-600 animate-pulse" />
            <span className="font-mono text-[11px] text-ink-muted uppercase tracking-wider">
              Local Ollama Inference Engine &bull; Zero External Telemetry
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              onClick={handleAnalyzeATS}
              disabled={atsLoading}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-3 bg-manila hover:bg-[#ebd9c1] text-ink font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all disabled:opacity-50"
              title="Analyze ATS Match Score and Missing Keywords"
            >
              {atsLoading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-ink border-t-transparent rounded-full animate-spin" />
                  <span>ANALYZING ATS...</span>
                </>
              ) : (
                <>
                  <Target className="w-4 h-4 text-terracotta" />
                  <span>ATS MATCH MATRIX</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleOpenCoverLetter}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-3 bg-paper hover:bg-[#fffdf9] text-ink font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all"
              title="Synthesize Grounded Cover Letter & Outreach"
            >
              <Mail className="w-4 h-4 text-terracotta" />
              <span>COVER LETTER & OUTREACH</span>
            </button>

            <button
              type="button"
              onClick={handleGenerate}
              disabled={loading}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press-lg hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-press active:translate-x-[2px] active:translate-y-[2px] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-paper border-t-transparent rounded-full animate-spin" />
                  <span>QUERYING CHROMADB & SYNTHESIZING...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-paper" />
                  <span>EXECUTE PRESS & TAILOR RESUME</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Render ATS Gap Analyzer Inline when analyzed */}
      {atsData && (
        <ATSGapAnalyzer
          data={atsData}
          loading={atsLoading}
          onAnalyze={handleAnalyzeATS}
        />
      )}

      {/* Cover Letter & Recruiter Outreach Modal */}
      <CoverLetterModal
        isOpen={isCoverLetterOpen}
        onClose={() => setIsCoverLetterOpen(false)}
        data={coverLetterData}
        loading={coverLetterLoading}
      />

      <ProfileQuestionnaireModal
        isOpen={isQuestionnaireOpen}
        onClose={() => setIsQuestionnaireOpen(false)}
        onSuccess={loadCandidateProfile}
      />
    </div>
  );
}
