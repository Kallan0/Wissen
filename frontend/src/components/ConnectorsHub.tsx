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
} from "lucide-react";
import { syncGitHub, syncCanvaProject, scanLocalProject } from "@/lib/api";
import { GitHubSyncResult, FilesystemScanResult } from "@/lib/types";

interface ConnectorsHubProps {
  onRefreshStats: () => void;
}

export default function ConnectorsHub({ onRefreshStats }: ConnectorsHubProps) {
  const [activeSubTab, setActiveSubTab] = useState<"github" | "canva" | "creative">("github");
  const [statusMessage, setStatusMessage] = useState<{ text: string; isError: boolean } | null>(null);

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
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 mb-5">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-600" />
              Data Connectors & Integrations
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              Connect your external and local creative workspaces (GitHub, Canva / Figma, Unity / Blender folders) to automatically populate your ChromaDB vector knowledge base.
            </p>
          </div>

          {/* Subtabs */}
          <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg border border-slate-200">
            <button
              onClick={() => setActiveSubTab("github")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                activeSubTab === "github" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Github className="w-3.5 h-3.5" />
              GitHub
            </button>
            <button
              onClick={() => setActiveSubTab("canva")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                activeSubTab === "canva" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Palette className="w-3.5 h-3.5 text-pink-600" />
              Canva / UI-UX
            </button>
            <button
              onClick={() => setActiveSubTab("creative")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                activeSubTab === "creative" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Boxes className="w-3.5 h-3.5 text-blue-600" />
              Unity / Blender
            </button>
          </div>
        </div>

        {statusMessage && (
          <div
            className={`p-3 rounded-lg border text-xs flex items-center gap-2 mb-4 ${
              statusMessage.isError
                ? "bg-red-50 border-red-200 text-red-700"
                : "bg-emerald-50 border-emerald-200 text-emerald-800"
            }`}
          >
            {statusMessage.isError ? (
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            )}
            <span>{statusMessage.text}</span>
          </div>
        )}

        {/* --- GITHUB CONNECTOR TAB --- */}
        {activeSubTab === "github" && (
          <div className="space-y-5">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-1">
                <Github className="w-4 h-4 text-slate-800" />
                Sync Public GitHub Repositories
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Pulls all your public repositories, star counts, programming languages, and README summaries directly into ChromaDB.
              </p>

              <form onSubmit={handleGithubSync} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">GitHub Username</label>
                    <input
                      type="text"
                      placeholder="e.g. your_github_username"
                      value={githubUser}
                      onChange={(e) => setGithubUser(e.target.value)}
                      required
                      className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Personal Access Token <span className="text-slate-400 font-normal">(Optional, for higher rate limits)</span>
                    </label>
                    <input
                      type="password"
                      placeholder="ghp_xxxxxxxxxxxx"
                      value={githubToken}
                      onChange={(e) => setGithubToken(e.target.value)}
                      className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg bg-white font-mono"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={fetchReadme}
                      onChange={(e) => setFetchReadme(e.target.checked)}
                      className="rounded text-blue-600"
                    />
                    <span>Fetch and summarize repository README files for rich detail</span>
                  </label>

                  <button
                    type="submit"
                    disabled={syncingGithub}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
                  >
                    {syncingGithub ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Fetching & Indexing Repositories...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        Sync GitHub to ChromaDB
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Results Grid */}
            {githubResult && (
              <div className="border border-slate-200 rounded-xl p-4 bg-white space-y-3">
                <div className="flex items-center justify-between text-xs font-bold text-slate-800 border-b pb-2">
                  <span>Synced Repositories ({githubResult.repos_synced})</span>
                  <span className="text-indigo-600">{githubResult.skills_extracted} Skills Extracted</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-60 overflow-y-auto pr-1">
                  {githubResult.repositories.map((repo, idx) => (
                    <div key={idx} className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                      <div className="flex items-center justify-between font-bold text-slate-800">
                        <span className="truncate">{repo.name}</span>
                        <span className="text-amber-600 font-normal text-[11px] shrink-0">★ {repo.stars}</span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-1">Lang: {repo.language}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* --- CANVA / UI-UX DESIGN CONNECTOR TAB --- */}
        {activeSubTab === "canva" && (
          <div className="bg-slate-50 p-5 rounded-xl border border-slate-200 space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-1">
              <Palette className="w-4 h-4 text-pink-600" />
              Canva & UI/UX Design Project Ingestor
            </h3>
            <p className="text-xs text-slate-500 mb-3">
              Export design metadata from Canva, Figma, or your design portfolio. Embeds creative case studies, tools, prototypes, and user metrics into your vector database.
            </p>

            <form onSubmit={handleCanvaSync} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Project / Case Study Title</label>
                  <input
                    type="text"
                    value={canvaTitle}
                    onChange={(e) => setCanvaTitle(e.target.value)}
                    required
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Design Discipline</label>
                  <select
                    value={canvaType}
                    onChange={(e) => setCanvaType(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg bg-white"
                  >
                    <option value="UI/UX & Design System">UI/UX & Design System</option>
                    <option value="Visual & Brand Identity">Visual & Brand Identity</option>
                    <option value="Wireframing & Prototyping">Wireframing & Prototyping</option>
                    <option value="Motion & Marketing Graphics">Motion & Marketing Graphics</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Project Description & Overview</label>
                <textarea
                  rows={3}
                  value={canvaDesc}
                  onChange={(e) => setCanvaDesc(e.target.value)}
                  required
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Creative Tools Used</label>
                  <input
                    type="text"
                    value={canvaTools}
                    onChange={(e) => setCanvaTools(e.target.value)}
                    placeholder="Canva, Figma, Blender, Adobe Illustrator"
                    className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Prototype / Portfolio URL</label>
                  <input
                    type="url"
                    value={canvaUrl}
                    onChange={(e) => setCanvaUrl(e.target.value)}
                    placeholder="https://canva.com/design/..."
                    className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Key Deliverables</label>
                  <input
                    type="text"
                    value={canvaDeliverables}
                    onChange={(e) => setCanvaDeliverables(e.target.value)}
                    placeholder="User Personas, High-Fidelity Mockups, Design Tokens"
                    className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Quantifiable Impact / Metrics</label>
                  <input
                    type="text"
                    value={canvaImpact}
                    onChange={(e) => setCanvaImpact(e.target.value)}
                    placeholder="e.g. Increased checkout completion by 22%"
                    className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={syncingCanva}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-pink-600 hover:bg-pink-700 text-white text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
                >
                  {syncingCanva ? "Indexing Design Case Study..." : "Index Design Project to ChromaDB"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* --- CREATIVE / GAME ENGINE FILESYSTEM CONNECTOR TAB --- */}
        {activeSubTab === "creative" && (
          <div className="space-y-4">
            <div className="bg-slate-50 p-5 rounded-xl border border-slate-200">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-1">
                <Boxes className="w-4 h-4 text-blue-600" />
                Unity, Blender & Local Workspace Scanner
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Point to any local project folder. The scanner automatically detects Unity assets (`Assets/`, `ProjectSettings/`, C# scripts), Blender `.blend` 3D scene files, and `project_summary.txt` notes.
              </p>

              <form onSubmit={handleFsScan} className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Local Directory Path</label>
                    <input
                      type="text"
                      placeholder="e.g. C:\Users\Username\Projects\GameProject"
                      value={fsPath}
                      onChange={(e) => setFsPath(e.target.value)}
                      required
                      className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg bg-white font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Project Name (Optional)</label>
                    <input
                      type="text"
                      placeholder="e.g. SciFi Physics Simulation"
                      value={fsProjectName}
                      onChange={(e) => setFsProjectName(e.target.value)}
                      className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg bg-white"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-1">
                  <button
                    type="submit"
                    disabled={scanningFs}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow transition disabled:opacity-50"
                  >
                    {scanningFs ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Scanning Folder & Extracting Metadata...
                      </>
                    ) : (
                      <>
                        <FileSearch className="w-3.5 h-3.5" />
                        Scan & Embed Local Project
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Scan Result */}
            {fsResult && (
              <div className="p-4 bg-white border border-slate-200 rounded-xl space-y-2 text-xs">
                <div className="flex items-center justify-between font-bold text-slate-900 border-b pb-2">
                  <span>{fsResult.project_name}</span>
                  <span className="text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                    {fsResult.project_type}
                  </span>
                </div>
                <div className="text-slate-600">
                  <strong>Path:</strong> <code className="font-mono bg-slate-100 px-1 py-0.5 rounded">{fsResult.directory_path}</code>
                </div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {fsResult.detected_technologies.map((t, idx) => (
                    <span key={idx} className="bg-indigo-50 text-indigo-700 text-[10px] px-2 py-0.5 rounded border border-indigo-100 font-medium">
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
