"use client";

import React, { useState } from "react";
import {
  Github,
  Palette,
  Boxes,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Layers,
  FileSearch,
  ScrollText,
  Stamp,
  FileSpreadsheet,
  FolderTree,
} from "lucide-react";
import { syncGitHub, syncCanvaProject, scanLocalProject, parseLinkedInCSV, scanVault } from "@/lib/api";
import { GitHubSyncResult, FilesystemScanResult, VaultScanResult } from "@/lib/types";

interface ConnectorsHubProps {
  onRefreshStats: () => void;
}

export default function ConnectorsHub({ onRefreshStats }: ConnectorsHubProps) {
  const [activeSubTab, setActiveSubTab] = useState<"github" | "canva" | "creative" | "linkedin" | "vault">("github");
  const [statusMessage, setStatusMessage] = useState<{ text: string; isError: boolean } | null>(null);

  // LinkedIn State
  const [linkedinPositionsCsv, setLinkedinPositionsCsv] = useState("");
  const [linkedinSkillsCsv, setLinkedinSkillsCsv] = useState("");
  const [parsingLinkedin, setParsingLinkedin] = useState(false);

  // Vault State
  const [vaultPath, setVaultPath] = useState("");
  const [scanningVault, setScanningVault] = useState(false);
  const [vaultResult, setVaultResult] = useState<VaultScanResult | null>(null);

  // GitHub State
  const [githubUser, setGithubUser] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [fetchReadme, setFetchReadme] = useState(true);
  const [syncingGithub, setSyncingGithub] = useState(false);
  const [githubResult, setGithubResult] = useState<GitHubSyncResult | null>(null);

  // Canva / Design State
  const [canvaTitle, setCanvaTitle] = useState("Fintech Mobile Banking App Redesign");
  const [canvaDesc, setCanvaDesc] = useState(
    "Led complete UX redesign of client onboarding flow, decreasing drop-off rates and introducing accessible dark mode components."
  );
  const [canvaType, setCanvaType] = useState("UI/UX & Design System");
  const [canvaTools, setCanvaTools] = useState("Canva, Figma, Adobe XD");
  const [canvaUrl, setCanvaUrl] = useState("https://canva.com/design/sample-portfolio");
  const [canvaDeliverables, setCanvaDeliverables] = useState("Interactive Prototypes, 40+ Screen Component Library, User Journey Maps");
  const [canvaImpact, setCanvaImpact] = useState("Reduced onboarding abandonment by 34% across 120,000 monthly active users.");
  const [syncingCanva, setSyncingCanva] = useState(false);

  // Creative Filesystem State
  const [fsPath, setFsPath] = useState("");
  const [fsProjectName, setFsProjectName] = useState("");
  const [scanningFs, setScanningFs] = useState(false);
  const [fsResult, setFsResult] = useState<FilesystemScanResult | null>(null);

  // GitHub Sync Handler
  const handleGithubSync = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubUser.trim()) return;
    setSyncingGithub(true);
    setStatusMessage(null);
    try {
      const res = await syncGitHub(githubUser, githubToken || undefined, 15, fetchReadme);
      setGithubResult(res.result);
      setStatusMessage({
        text: `Successfully synced ${res.result.repos_synced} repositories and ${res.result.skills_extracted} skills for '${githubUser}'!`,
        isError: false,
      });
      onRefreshStats();
    } catch (err: any) {
      setStatusMessage({ text: err.message || "Failed to sync GitHub", isError: true });
    } finally {
      setSyncingGithub(false);
    }
  };

  // Canva Sync Handler
  const handleCanvaSync = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canvaTitle.trim() || !canvaDesc.trim()) return;
    setSyncingCanva(true);
    setStatusMessage(null);
    try {
      const toolList = canvaTools.split(",").map((t) => t.trim()).filter(Boolean);
      const delivList = canvaDeliverables.split(",").map((d) => d.trim()).filter(Boolean);
      await syncCanvaProject({
        title: canvaTitle,
        description: canvaDesc,
        design_type: canvaType,
        tools_used: toolList,
        prototype_url: canvaUrl,
        deliverables: delivList,
        user_impact: canvaImpact,
      });
      setStatusMessage({
        text: `Design case study "${canvaTitle}" indexed into ChromaDB projects and skills!`,
        isError: false,
      });
      onRefreshStats();
    } catch (err: any) {
      setStatusMessage({ text: err.message || "Failed to index design project", isError: true });
    } finally {
      setSyncingCanva(false);
    }
  };

  // Local Project Filesystem Scanner Handler
  const handleFsScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fsPath.trim()) return;
    setScanningFs(true);
    setStatusMessage(null);
    try {
      const res = await scanLocalProject(fsPath, fsProjectName || undefined);
      setFsResult(res.result);
      setStatusMessage({
        text: `Detected ${res.result.project_type}: "${res.result.project_name}" and indexed into ChromaDB!`,
        isError: false,
      });
      onRefreshStats();
    } catch (err: any) {
      setStatusMessage({ text: err.message || "Failed to scan folder", isError: true });
    } finally {
      setScanningFs(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Editorial Header */}
      <div className="bg-[#fffdf9] p-6 sm:p-8 rounded-xl border-2 border-ink shadow-dossier">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5 pb-5 border-b-2 border-ink/20 mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-[11px] uppercase tracking-widest bg-ink text-paper px-2 py-0.5 font-bold">
                INTEGRATION DOCKET
              </span>
              <span className="font-mono text-[11px] text-ink-muted uppercase tracking-wider">
                EXTERNAL ARCHIVES // CRAWLERS
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-serif font-bold text-ink tracking-tight flex items-center gap-2.5">
              <Layers className="w-6 h-6 text-terracotta" />
              Creative Connectors & Repository Sync
            </h2>
            <p className="text-xs sm:text-sm font-serif italic text-ink-muted mt-1 max-w-2xl leading-relaxed">
              Connect external and local creative archives (GitHub, Canva / Figma portfolios, Unity / Blender project directories) to automatically populate your ChromaDB vector ledger.
            </p>
          </div>

          {/* Subtabs */}
          <div className="flex flex-wrap items-center gap-1.5 bg-manila p-1.5 rounded-lg border-2 border-ink shrink-0">
            <button
              onClick={() => setActiveSubTab("github")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-xs font-bold transition-all ${
                activeSubTab === "github"
                  ? "bg-terracotta text-paper shadow-press"
                  : "text-ink hover:text-terracotta"
              }`}
            >
              <Github className="w-3.5 h-3.5" />
              [01] GitHub
            </button>
            <button
              onClick={() => setActiveSubTab("canva")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-xs font-bold transition-all ${
                activeSubTab === "canva"
                  ? "bg-terracotta text-paper shadow-press"
                  : "text-ink hover:text-terracotta"
              }`}
            >
              <Palette className="w-3.5 h-3.5" />
              [02] Canva / Design
            </button>
            <button
              onClick={() => setActiveSubTab("creative")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-xs font-bold transition-all ${
                activeSubTab === "creative"
                  ? "bg-terracotta text-paper shadow-press"
                  : "text-ink hover:text-terracotta"
              }`}
            >
              <Boxes className="w-3.5 h-3.5" />
              [03] Local Workspace
            </button>
          </div>
        </div>

        {statusMessage && (
          <div
            className={`p-4 rounded-lg border-2 font-mono text-xs flex items-center gap-2 mb-6 shadow-press ${
              statusMessage.isError
                ? "bg-[#fff0ed] border-terracotta text-terracotta"
                : "bg-paper border-ink text-ink"
            }`}
          >
            {statusMessage.isError ? (
              <AlertCircle className="w-4 h-4 text-terracotta shrink-0" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-fountain-teal shrink-0" />
            )}
            <span>{statusMessage.text}</span>
          </div>
        )}

        {/* --- GITHUB CONNECTOR TAB --- */}
        {activeSubTab === "github" && (
          <div className="space-y-6">
            <div className="bg-manila/40 p-5 rounded-xl border-2 border-ink shadow-press">
              <h3 className="font-serif text-base font-bold text-ink flex items-center gap-2 mb-1">
                <Github className="w-4 h-4 text-terracotta" />
                Sync Public GitHub Repositories & READMEs
              </h3>
              <p className="font-serif italic text-xs text-ink-muted mb-4">
                Pulls all your public repositories, star counts, programming languages, and README summaries directly into ChromaDB.
              </p>

              <form onSubmit={handleGithubSync} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                      GitHub Username
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. your_github_username"
                      value={githubUser}
                      onChange={(e) => setGithubUser(e.target.value)}
                      required
                      className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                    />
                  </div>
                  <div>
                    <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                      Personal Access Token <span className="text-ink-muted font-normal">(Optional, for higher rate limits)</span>
                    </label>
                    <input
                      type="password"
                      placeholder="ghp_xxxxxxxxxxxx"
                      value={githubToken}
                      onChange={(e) => setGithubToken(e.target.value)}
                      className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                    />
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                  <label className="flex items-center gap-2 font-serif text-xs text-ink cursor-pointer">
                    <input
                      type="checkbox"
                      checked={fetchReadme}
                      onChange={(e) => setFetchReadme(e.target.checked)}
                      className="rounded text-terracotta border-ink focus:ring-terracotta"
                    />
                    <span>Fetch and summarize repository README markdown for deep RAG ingestion</span>
                  </label>

                  <button
                    type="submit"
                    disabled={syncingGithub}
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all disabled:opacity-50"
                  >
                    {syncingGithub ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-paper border-t-transparent rounded-full animate-spin" />
                        INDEXING REPOSITORIES...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        SYNC GITHUB TO CHROMADB
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Results Grid */}
            {githubResult && (
              <div className="border-2 border-ink rounded-xl p-5 bg-[#fffdf9] shadow-press space-y-3">
                <div className="flex items-center justify-between font-mono text-xs font-bold text-ink border-b-2 border-ink/20 pb-2">
                  <span>SYNCED REPOSITORIES ({githubResult.repos_synced})</span>
                  <span className="text-terracotta">{githubResult.skills_extracted} SKILLS EXTRACTED</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 max-h-60 overflow-y-auto pr-1">
                  {githubResult.repositories.map((repo, idx) => (
                    <div key={idx} className="p-3 bg-paper rounded border-2 border-ink/20 font-serif text-xs">
                      <div className="flex items-center justify-between font-bold text-ink">
                        <span className="truncate">{repo.name}</span>
                        <span className="font-mono text-vintage-gold font-bold text-[11px] shrink-0">★ {repo.stars}</span>
                      </div>
                      <div className="font-mono text-[10px] text-ink-muted mt-1">LANG: {repo.language}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* --- CANVA / UI-UX DESIGN CONNECTOR TAB --- */}
        {activeSubTab === "canva" && (
          <div className="bg-manila/40 p-5 rounded-xl border-2 border-ink shadow-press space-y-4">
            <h3 className="font-serif text-base font-bold text-ink flex items-center gap-2 mb-1">
              <Palette className="w-4 h-4 text-terracotta" />
              Canva & UI/UX Design Project Ingestor
            </h3>
            <p className="font-serif italic text-xs text-ink-muted mb-3">
              Export design metadata from Canva, Figma, or your design portfolio. Embeds creative case studies, tools, prototypes, and user metrics into your vector database.
            </p>

            <form onSubmit={handleCanvaSync} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="sm:col-span-2">
                  <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                    Project / Case Study Title
                  </label>
                  <input
                    type="text"
                    value={canvaTitle}
                    onChange={(e) => setCanvaTitle(e.target.value)}
                    required
                    className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                  />
                </div>
                <div>
                  <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                    Design Discipline
                  </label>
                  <select
                    value={canvaType}
                    onChange={(e) => setCanvaType(e.target.value)}
                    className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                  >
                    <option value="UI/UX & Design System">UI/UX & Design System</option>
                    <option value="Visual & Brand Identity">Visual & Brand Identity</option>
                    <option value="Wireframing & Prototyping">Wireframing & Prototyping</option>
                    <option value="Motion & Marketing Graphics">Motion & Marketing Graphics</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                  Project Description & Overview
                </label>
                <textarea
                  rows={3}
                  value={canvaDesc}
                  onChange={(e) => setCanvaDesc(e.target.value)}
                  required
                  className="w-full font-mono text-xs p-3 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                    Creative Tools Used
                  </label>
                  <input
                    type="text"
                    value={canvaTools}
                    onChange={(e) => setCanvaTools(e.target.value)}
                    placeholder="Canva, Figma, Blender, Adobe Illustrator"
                    className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                  />
                </div>
                <div>
                  <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                    Prototype / Portfolio URL
                  </label>
                  <input
                    type="url"
                    value={canvaUrl}
                    onChange={(e) => setCanvaUrl(e.target.value)}
                    placeholder="https://canva.com/design/..."
                    className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                    Key Deliverables
                  </label>
                  <input
                    type="text"
                    value={canvaDeliverables}
                    onChange={(e) => setCanvaDeliverables(e.target.value)}
                    placeholder="User Personas, High-Fidelity Mockups, Design Tokens"
                    className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                  />
                </div>
                <div>
                  <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                    Quantifiable Impact / Metrics
                  </label>
                  <input
                    type="text"
                    value={canvaImpact}
                    onChange={(e) => setCanvaImpact(e.target.value)}
                    placeholder="e.g. Increased checkout completion by 22%"
                    className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={syncingCanva}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all disabled:opacity-50"
                >
                  {syncingCanva ? "INDEXING DESIGN CASE STUDY..." : "INDEX DESIGN PROJECT TO CHROMADB"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* --- CREATIVE / GAME ENGINE FILESYSTEM CONNECTOR TAB --- */}
        {activeSubTab === "creative" && (
          <div className="space-y-4">
            <div className="bg-manila/40 p-5 rounded-xl border-2 border-ink shadow-press">
              <h3 className="font-serif text-base font-bold text-ink flex items-center gap-2 mb-1">
                <Boxes className="w-4 h-4 text-terracotta" />
                Unity, Blender & Local Workspace Scanner
              </h3>
              <p className="font-serif italic text-xs text-ink-muted mb-4">
                Point to any local project folder. The scanner automatically detects Unity assets (`Assets/`, `ProjectSettings/`, C# scripts), Blender `.blend` 3D scene files, and `project_summary.txt` notes.
              </p>

              <form onSubmit={handleFsScan} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="sm:col-span-2">
                    <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                      Local Directory Path
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. C:\Users\Username\Projects\GameProject"
                      value={fsPath}
                      onChange={(e) => setFsPath(e.target.value)}
                      required
                      className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                    />
                  </div>
                  <div>
                    <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                      Project Name (Optional)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. SciFi Physics Simulation"
                      value={fsProjectName}
                      onChange={(e) => setFsProjectName(e.target.value)}
                      className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={scanningFs}
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all disabled:opacity-50"
                  >
                    {scanningFs ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-paper border-t-transparent rounded-full animate-spin" />
                        SCANNING DIRECTORY...
                      </>
                    ) : (
                      <>
                        <FileSearch className="w-3.5 h-3.5" />
                        SCAN & EMBED LOCAL PROJECT
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Scan Result */}
            {fsResult && (
              <div className="p-5 bg-[#fffdf9] border-2 border-ink rounded-xl shadow-press space-y-2.5 font-serif text-xs">
                <div className="flex items-center justify-between font-bold text-ink border-b-2 border-ink/20 pb-2">
                  <span className="text-sm">{fsResult.project_name}</span>
                  <span className="font-mono text-xs text-terracotta bg-[#fff0ed] px-2.5 py-0.5 rounded border border-terracotta/40">
                    {fsResult.project_type}
                  </span>
                </div>
                <div className="text-ink-muted">
                  <strong>Path:</strong> <code className="font-mono bg-manila px-1.5 py-0.5 rounded border border-ink/20">{fsResult.directory_path}</code>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {fsResult.detected_technologies.map((t, idx) => (
                    <span key={idx} className="bg-manila text-ink font-mono text-[10px] px-2 py-0.5 rounded border border-ink/30">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

