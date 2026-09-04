"use client";

import React, { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import JobTailor from "@/components/JobTailor";
import ResumePreview from "@/components/ResumePreview";
import KnowledgeBase from "@/components/KnowledgeBase";
import RetrievalMatches from "@/components/RetrievalMatches";
import RoleRecommender from "@/components/RoleRecommender";
import ConnectorsHub from "@/components/ConnectorsHub";
import { fetchHealth, fetchModels } from "@/lib/api";
import { HealthResponse, ResumeData, TailorResponse, RAGContext } from "@/lib/types";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"roles" | "tailor" | "preview" | "knowledge" | "connectors">("roles");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [isLoadingHealth, setIsLoadingHealth] = useState(false);

  // Active generated resume state
  const [currentResume, setCurrentResume] = useState<ResumeData | null>(null);
  const [ragContext, setRagContext] = useState<RAGContext | null>(null);

  // Pre-fill state from Role Recommender to Job Tailor
  const [tailorRole, setTailorRole] = useState<string | undefined>();
  const [tailorJd, setTailorJd] = useState<string | undefined>();

  const loadHealthAndModels = async () => {
    setIsLoadingHealth(true);
    try {
      const [h, m] = await Promise.all([fetchHealth().catch(() => null), fetchModels().catch(() => ["llama3"])]);
      if (h) setHealth(h);
      if (m) setModels(m);
    } catch (err) {
      console.error("Health check error:", err);
    } finally {
      setIsLoadingHealth(false);
    }
  };

  useEffect(() => {
    loadHealthAndModels();
  }, []);

  const handleTailored = (result: TailorResponse) => {
    setCurrentResume(result.resume);
    setRagContext(result.rag_context);
    // Switch to preview tab automatically so user sees the result immediately
    setActiveTab("preview");
  };

  const handleSelectRoleForTailoring = (role: string, sampleJd: string) => {
    setTailorRole(role);
    setTailorJd(sampleJd);
    setActiveTab("tailor");
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-100/70 text-slate-900">
      <Navbar
        health={health}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        refreshHealth={loadHealthAndModels}
        isLoading={isLoadingHealth}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {activeTab === "roles" && (
          <RoleRecommender
            models={models}
            onSelectRoleForTailoring={handleSelectRoleForTailoring}
          />
        )}

        {activeTab === "tailor" && (
          <div className="space-y-6">
            <JobTailor
              models={models}
              onTailored={handleTailored}
              initialRole={tailorRole}
              initialJd={tailorJd}
            />
            {ragContext && <RetrievalMatches context={ragContext} />}
          </div>
        )}

        {activeTab === "preview" && (
          <div className="space-y-6">
            {ragContext && <RetrievalMatches context={ragContext} />}
            <ResumePreview
              resume={currentResume}
              onUpdateResume={(updated) => setCurrentResume(updated)}
            />
          </div>
        )}

        {activeTab === "connectors" && (
          <ConnectorsHub onRefreshStats={loadHealthAndModels} />
        )}

        {activeTab === "knowledge" && (
          <KnowledgeBase onRefreshStats={loadHealthAndModels} />
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        Local AI Resume Builder &bull; Privacy-First &bull; ChromaDB + Ollama + Next.js + Playwright
      </footer>
    </div>
  );
}
