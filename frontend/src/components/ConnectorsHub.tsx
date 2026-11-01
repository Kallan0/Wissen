"use client";

import React, { useState, useEffect } from "react";
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
  Cpu,
  Brain,
  Download,
  Copy,
  Check,
  Terminal,
  ExternalLink,
  RefreshCw,
  FileCode,
} from "lucide-react";
import {
  syncGitHub,
  syncCanvaProject,
  scanLocalProject,
  parseLinkedInCSV,
  scanVault,
  exportFineTuningDataset,
  fetchFineTuningStatus,
} from "@/lib/api";
import {
  GitHubSyncResult,
  FilesystemScanResult,
  VaultScanResult,
  FineTuningStatus,
  ExportDatasetResult,
} from "@/lib/types";

interface ConnectorsHubProps {
  onRefreshStats: () => void;
}

export default function ConnectorsHub({ onRefreshStats }: ConnectorsHubProps) {
  const [activeSubTab, setActiveSubTab] = useState<
    "github" | "canva" | "creative" | "linkedin" | "vault" | "finetuning"
  >("github");
  const [statusMessage, setStatusMessage] = useState<{ text: string; isError: boolean } | null>(null);

  // Fine-Tuning State
  const [ftStatus, setFtStatus] = useState<FineTuningStatus | null>(null);
  const [ftCount, setFtCount] = useState<number>(150);
  const [exportingDataset, setExportingDataset] = useState<boolean>(false);
  const [exportResult, setExportResult] = useState<ExportDatasetResult | null>(null);
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

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

  // Load Fine-Tuning Status
  const loadFtStatus = async () => {
    try {
      const s = await fetchFineTuningStatus();
      setFtStatus(s);
    } catch (err) {
      console.error("Could not fetch fine-tuning status:", err);
    }
  };

  useEffect(() => {
    loadFtStatus();
  }, []);

  // LinkedIn CSV Parser Handler
  const handleLinkedinParse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!linkedinPositionsCsv.trim() && !linkedinSkillsCsv.trim()) return;
    setParsingLinkedin(true);
    setStatusMessage(null);
    try {
      const res = await parseLinkedInCSV(linkedinPositionsCsv || undefined, linkedinSkillsCsv || undefined);
      setStatusMessage({
        text: `Successfully imported LinkedIn data! Ingested: ${Object.entries(res.ingested_counts)
          .map(([k, v]) => `${v} ${k}`)
          .join(", ")}`,
        isError: false,
      });
      onRefreshStats();
    } catch (err: any) {
      setStatusMessage({ text: err.message || "Failed to parse LinkedIn CSV", isError: true });
    } finally {
      setParsingLinkedin(false);
    }
  };

  // Markdown Vault Scanner Handler
  const handleVaultScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vaultPath.trim()) return;
    setScanningVault(true);
    setStatusMessage(null);
    try {
      const res = await scanVault(vaultPath);
      setVaultResult(res);
      setStatusMessage({
        text: `Scanned Markdown Vault: ${res.files_scanned} files (${res.total_chunks} chunks) indexed into ChromaDB!`,
        isError: false,
      });
      onRefreshStats();
    } catch (err: any) {
      setStatusMessage({ text: err.message || "Failed to scan vault", isError: true });
    } finally {
      setScanningVault(false);
    }
  };

  // Fine-Tuning Dataset Export Handler
  const handleExportDataset = async () => {
    setExportingDataset(true);
    setStatusMessage(null);
    try {
      const res = await exportFineTuningDataset(ftCount);
      setExportResult(res);
      setStatusMessage({
        text: `Generated ${res.generated_count ?? res.count} examples: ${res.count} training and ${res.holdout_count ?? 0} holdout.`,
        isError: false,
      });
      const downloadUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002"}${res.download_url}`;
      window.open(downloadUrl, "_blank");
    } catch (err: any) {
      setStatusMessage({ text: err.message || "Failed to export dataset", isError: true });
    } finally {
      setExportingDataset(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(id);
    setTimeout(() => setCopiedCmd(null), 2500);
  };

  return (
    <div className="space-y-6">
      {/* Editorial Header */}
      <div className="bg-[#fffdf9] p-6 sm:p-8 rounded-xl border-2 border-ink shadow-dossier">
        {/* Title row — no longer shares row with tabs */}
        <div className="pb-5 mb-5 border-b-2 border-ink/20">
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
            Creative Connectors &amp; Repository Sync
          </h2>
          <p className="text-xs sm:text-sm font-serif italic text-ink-muted mt-1 max-w-2xl leading-relaxed">
            Connect external and local creative archives (GitHub, Canva / Figma portfolios, Unity / Blender project directories) to automatically populate your ChromaDB vector ledger.
          </p>
        </div>

        {/* Subtabs — full-width single row, scrollable on small screens */}
        <div className="overflow-x-auto -mx-1 px-1 pb-1 mb-6">
          <div className="flex items-center gap-1.5 bg-manila p-1.5 rounded-lg border-2 border-ink w-fit min-w-full">
            <button
              onClick={() => setActiveSubTab("github")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-xs font-bold transition-all whitespace-nowrap ${activeSubTab === "github"
                ? "bg-terracotta text-paper shadow-press"
                : "text-ink hover:text-terracotta"
                }`}
            >
              <Github className="w-3.5 h-3.5" />
              [01] GitHub
            </button>
            <button
              onClick={() => setActiveSubTab("canva")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-xs font-bold transition-all ${activeSubTab === "canva"
                ? "bg-terracotta text-paper shadow-press"
                : "text-ink hover:text-terracotta"
                }`}
            >
              <Palette className="w-3.5 h-3.5" />
              [02] Canva / Design
            </button>
            <button
              onClick={() => setActiveSubTab("creative")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-xs font-bold transition-all ${activeSubTab === "creative"
                ? "bg-terracotta text-paper shadow-press"
                : "text-ink hover:text-terracotta"
                }`}
            >
              <Boxes className="w-3.5 h-3.5" />
              [03] Local Workspace
            </button>
            <button
              onClick={() => setActiveSubTab("linkedin")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-xs font-bold transition-all ${activeSubTab === "linkedin"
                ? "bg-terracotta text-paper shadow-press"
                : "text-ink hover:text-terracotta"
                }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              [04] LinkedIn CSV
            </button>
            <button
              onClick={() => setActiveSubTab("vault")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-xs font-bold transition-all ${activeSubTab === "vault"
                ? "bg-terracotta text-paper shadow-press"
                : "text-ink hover:text-terracotta"
                }`}
            >
              <FolderTree className="w-3.5 h-3.5" />
              [05] Vault
            </button>
            <button
              onClick={() => setActiveSubTab("finetuning")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-xs font-bold transition-all ${activeSubTab === "finetuning"
                ? "bg-fountain-teal text-paper shadow-press"
                : "text-ink hover:text-fountain-teal"
                }`}
            >
              <Brain className="w-3.5 h-3.5 text-yellow-300" />
              [06] Fine-Tuning
              {ftStatus?.has_custom_model_active && (
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              )}
            </button>
          </div>
        </div>

        {statusMessage && (
          <div
            className={`p-4 rounded-lg border-2 font-mono text-xs flex items-center gap-2 mb-6 shadow-press ${statusMessage.isError
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

        {/* --- LINKEDIN CSV IMPORT TAB --- */}
        {activeSubTab === "linkedin" && (
          <div className="space-y-4">
            <div className="bg-manila/40 p-5 rounded-xl border-2 border-ink shadow-press">
              <h3 className="font-serif text-base font-bold text-ink flex items-center gap-2 mb-1">
                <FileSpreadsheet className="w-4 h-4 text-terracotta" />
                Import LinkedIn Data Export (Positions.csv & Skills.csv)
              </h3>
              <p className="font-serif italic text-xs text-ink-muted mb-4">
                Paste the contents of your downloaded LinkedIn data export files (`Positions.csv` and `Skills.csv`) to parse and vectorize work history and technical competencies into ChromaDB.
              </p>

              <form onSubmit={handleLinkedinParse} className="space-y-4">
                <div>
                  <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                    Positions.csv Content
                  </label>
                  <textarea
                    rows={4}
                    value={linkedinPositionsCsv}
                    onChange={(e) => setLinkedinPositionsCsv(e.target.value)}
                    placeholder="Company Name,Title,Description,Location,Started On,Finished On..."
                    className="w-full font-mono text-xs p-3 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                  />
                </div>

                <div>
                  <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                    Skills.csv Content
                  </label>
                  <textarea
                    rows={3}
                    value={linkedinSkillsCsv}
                    onChange={(e) => setLinkedinSkillsCsv(e.target.value)}
                    placeholder="Name\nPython\nTypeScript\nFastAPI..."
                    className="w-full font-mono text-xs p-3 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={parsingLinkedin || (!linkedinPositionsCsv.trim() && !linkedinSkillsCsv.trim())}
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all disabled:opacity-50"
                  >
                    {parsingLinkedin ? "IMPORTING CSV..." : "PARSE & INDEX LINKEDIN CSV"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* --- MARKDOWN VAULT TAB --- */}
        {activeSubTab === "vault" && (
          <div className="space-y-4">
            <div className="bg-manila/40 p-5 rounded-xl border-2 border-ink shadow-press">
              <h3 className="font-serif text-base font-bold text-ink flex items-center gap-2 mb-1">
                <FolderTree className="w-4 h-4 text-terracotta" />
                Scan Obsidian / Local Markdown Knowledge Vault
              </h3>
              <p className="font-serif italic text-xs text-ink-muted mb-4">
                Point to an Obsidian notes vault or directory of `.md` / `.txt` files. Each document will be chunked and indexed into ChromaDB.
              </p>

              <form onSubmit={handleVaultScan} className="space-y-4">
                <div>
                  <label className="block font-mono text-[11px] font-bold text-ink mb-1 uppercase tracking-wider">
                    Vault Directory Path
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. C:\Users\Username\Documents\ObsidianVault"
                    value={vaultPath}
                    onChange={(e) => setVaultPath(e.target.value)}
                    required
                    className="w-full font-mono text-xs px-3 py-2 border-2 border-ink rounded bg-[#fffdf9] text-ink focus:outline-none focus:ring-2 focus:ring-terracotta"
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={scanningVault}
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded-lg border-2 border-ink shadow-press hover:translate-x-[1px] hover:translate-y-[1px] transition-all disabled:opacity-50"
                  >
                    {scanningVault ? "INDEXING VAULT..." : "SCAN & EMBED MARKDOWN VAULT"}
                  </button>
                </div>
              </form>
            </div>

            {vaultResult && (
              <div className="p-5 bg-[#fffdf9] border-2 border-ink rounded-xl shadow-press space-y-2 font-serif text-xs">
                <div className="flex items-center justify-between font-bold text-ink border-b-2 border-ink/20 pb-2">
                  <span>Vault: {vaultResult.vault_path}</span>
                  <span className="font-mono text-xs text-fountain-teal bg-fountain-teal/10 px-2 py-0.5 rounded border border-fountain-teal/30">
                    {vaultResult.files_scanned} files ({vaultResult.total_chunks} chunks)
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* --- FINE-TUNING & CUSTOM OLLAMA MODELS TAB --- */}
        {activeSubTab === "finetuning" && (
          <div className="space-y-6">
            {/* Status Card */}
            <div className="bg-manila/50 p-6 rounded-xl border-2 border-ink shadow-press">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b-2 border-ink/20 pb-4 mb-5">
                <div>
                  <div className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-terracotta" />
                    <h3 className="font-serif text-lg font-bold text-ink">
                      Ollama Model Fine-Tuning & Custom Adaptation
                    </h3>
                  </div>
                  <p className="font-serif italic text-xs text-ink-muted mt-0.5">
                    Train and customize local models to output perfect ATS resumes conforming to the Google XYZ formula with zero hallucinations.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={loadFtStatus}
                  className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3 py-1.5 bg-paper border border-ink text-ink font-mono text-xs rounded hover:bg-manila transition-all"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Refresh Status
                </button>
              </div>

              {/* Model Status Indicators */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="p-4 bg-paper rounded-lg border-2 border-ink">
                  <div className="font-mono text-[10px] uppercase font-bold text-ink-muted tracking-wider">
                    Custom Tailor Model
                  </div>
                  <div className="flex items-center gap-2 mt-1.5">
                    {ftStatus?.has_custom_model_active ? (
                      <>
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="font-mono text-sm font-bold text-emerald-700">
                          {ftStatus.custom_models.join(", ")}
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                        <span className="font-mono text-xs font-semibold text-amber-800">
                          Not Installed Yet
                        </span>
                      </>
                    )}
                  </div>
                  <p className="font-serif text-[11px] text-ink-muted mt-1">
                    {ftStatus?.has_custom_model_active
                      ? "Custom resume specialist active and selectable in model dropdown."
                      : "Using base zero-shot prompt. Build custom model below for 3x quality."}
                  </p>
                </div>

                <div className="p-4 bg-paper rounded-lg border-2 border-ink">
                  <div className="font-mono text-[10px] uppercase font-bold text-ink-muted tracking-wider">
                    Available Base Models
                  </div>
                  <div className="font-mono text-xs font-bold text-ink mt-1.5 truncate">
                    {ftStatus?.base_models.length ? ftStatus.base_models.join(", ") : "llama3"}
                  </div>
                  <p className="font-serif text-[11px] text-ink-muted mt-1">
                    Local Ollama foundation models installed on your machine.
                  </p>
                </div>

                <div className="p-4 bg-paper rounded-lg border-2 border-ink">
                  <div className="font-mono text-[10px] uppercase font-bold text-ink-muted tracking-wider">
                    Training Toolkit
                  </div>
                  <div className="flex items-center gap-2 mt-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span className="font-mono text-xs font-bold text-ink">Ready & Configured</span>
                  </div>
                  <p className="font-serif text-[11px] text-ink-muted mt-1">
                    Modelfile, Colab notebook, & export scripts ready
                  </p>
                </div>
              </div>

              {/* Step 1: Export Dataset */}
              <div className="p-5 bg-paper rounded-xl border-2 border-ink space-y-3 mb-6">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <span className="font-mono text-[10px] font-bold uppercase tracking-wider bg-terracotta text-paper px-2 py-0.5 rounded">
                      STEP 1
                    </span>
                    <h4 className="font-serif text-sm font-bold text-ink mt-1">
                      Generate SFT Training Dataset from Your Knowledge Base
                    </h4>
                    <p className="font-serif italic text-xs text-ink-muted">
                      Synthesizes diverse job scenarios (Fullstack, Backend, AI, Cloud) paired with verified facts from your ChromaDB ledger into Llama-3 instruction JSONL.
                    </p>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <div className="flex items-center gap-2">
                      <label className="font-mono text-xs text-ink">Samples:</label>
                      <select
                        value={ftCount}
                        onChange={(e) => setFtCount(Number(e.target.value))}
                        className="font-mono text-xs px-2 py-1 border border-ink rounded bg-manila text-ink"
                      >
                        <option value={100}>100</option>
                        <option value={150}>150</option>
                        <option value={200}>200</option>
                      </select>
                    </div>

                    <button
                      type="button"
                      onClick={handleExportDataset}
                      disabled={exportingDataset}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-ink text-paper font-mono text-xs font-bold rounded border border-ink hover:bg-terracotta transition-all disabled:opacity-50"
                    >
                      {exportingDataset ? (
                        <>
                          <div className="w-3.5 h-3.5 border-2 border-paper border-t-transparent rounded-full animate-spin" />
                          GENERATING...
                        </>
                      ) : (
                        <>
                          <Download className="w-3.5 h-3.5" />
                          EXPORT DATASET (.JSONL)
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {exportResult && (
                  <div className="p-3 bg-[#eefaf4] border border-emerald-300 rounded font-mono text-xs text-emerald-800 flex items-center justify-between gap-3">
                    <span>{exportResult.count} training / {exportResult.holdout_count ?? 0} holdout ({(exportResult.file_size_bytes / 1024).toFixed(1)} KB training)</span>
                    <div className="flex items-center gap-3">
                      <a
                        href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002"}${exportResult.download_url}`}
                        download="training_data.jsonl"
                        className="underline font-bold hover:text-emerald-950 flex items-center gap-1"
                      >
                        <Download className="w-3 h-3" /> Training
                      </a>
                      {exportResult.holdout_download_url && (
                        <a
                          href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002"}${exportResult.holdout_download_url}`}
                          download="holdout_eval.jsonl"
                          className="underline font-bold hover:text-emerald-950 flex items-center gap-1"
                        >
                          <Download className="w-3 h-3" /> Holdout
                        </a>
                      )}
                    </div>
                  </div>
                )}
              </div>


            </div>
          </div>
        )}
      </div>
    </div>
  );
}
