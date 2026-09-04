"use client";

import React from "react";
import { ShieldCheck, Cpu, Database, RefreshCw, FileText } from "lucide-react";
import { HealthResponse } from "@/lib/types";

interface NavbarProps {
  health: HealthResponse | null;
  activeTab: "tailor" | "preview" | "knowledge" | "roles" | "connectors";
  setActiveTab: (tab: "tailor" | "preview" | "knowledge" | "roles" | "connectors") => void;
  refreshHealth: () => void;
  isLoading: boolean;
}

export default function Navbar({
  health,
  activeTab,
  setActiveTab,
  refreshHealth,
  isLoading,
}: NavbarProps) {
  const isBackendUp = health?.status === "healthy";
  const isOllamaUp = health?.ollama?.online;
  const totalItems = health?.knowledge_base?.total_items ?? 0;

  return (
    <header className="sticky top-0 z-50 bg-slate-900 border-b border-slate-800 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-blue-600 to-indigo-500 rounded-lg shadow">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight">Local AI Resume</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
                  100% Privacy
                </span>
              </div>
              <p className="text-[11px] text-slate-400">ChromaDB RAG &bull; Ollama Local LLMs</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 bg-slate-800/80 p-1 rounded-lg border border-slate-700/60">
            <button
              onClick={() => setActiveTab("roles")}
              className={`px-3.5 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeTab === "roles"
                  ? "bg-blue-600 text-white shadow"
                  : "text-slate-300 hover:text-white hover:bg-slate-700/50"
              }`}
            >
              Role Matches
            </button>
            <button
              onClick={() => setActiveTab("tailor")}
              className={`px-3.5 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeTab === "tailor"
                  ? "bg-blue-600 text-white shadow"
                  : "text-slate-300 hover:text-white hover:bg-slate-700/50"
              }`}
            >
              Job Tailor
            </button>
            <button
              onClick={() => setActiveTab("preview")}
              className={`px-3.5 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeTab === "preview"
                  ? "bg-blue-600 text-white shadow"
                  : "text-slate-300 hover:text-white hover:bg-slate-700/50"
              }`}
            >
              Resume & PDF
            </button>
            <button
              onClick={() => setActiveTab("connectors")}
              className={`px-3.5 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeTab === "connectors"
                  ? "bg-blue-600 text-white shadow"
                  : "text-slate-300 hover:text-white hover:bg-slate-700/50"
              }`}
            >
              Connectors
            </button>
            <button
              onClick={() => setActiveTab("knowledge")}
              className={`px-3.5 py-1.5 rounded-md text-sm font-medium transition-all ${
                activeTab === "knowledge"
                  ? "bg-blue-600 text-white shadow"
                  : "text-slate-300 hover:text-white hover:bg-slate-700/50"
              }`}
            >
              Knowledge Base
            </button>
          </nav>

          {/* System Status Indicators */}
          <div className="hidden md:flex items-center space-x-3 text-xs">
            {/* Ollama Status */}
            <div
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full border ${
                isOllamaUp
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : "bg-amber-500/10 text-amber-400 border-amber-500/30"
              }`}
              title={isOllamaUp ? "Ollama running locally" : "Ollama offline; using local synthesized fallback"}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>{isOllamaUp ? "Ollama Online" : "Ollama Offline"}</span>
            </div>

            {/* Vector DB status */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              <span>ChromaDB: <strong className="text-white">{totalItems}</strong> items</span>
            </div>

            {/* Refresh button */}
            <button
              onClick={refreshHealth}
              disabled={isLoading}
              title="Refresh connection status"
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md transition"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-blue-400" : ""}`} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
