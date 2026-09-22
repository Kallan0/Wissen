"use client";

import React, { useState } from "react";
import {
  Compass,
  FileText,
  Layers,
  Database,
  ScrollText,
  Sparkles,
  RefreshCw,
  Menu,
  X,
} from "lucide-react";
import { HealthResponse } from "@/lib/types";

interface NavbarProps {
  health: HealthResponse | null;
  activeTab: "roles" | "tailor" | "preview" | "connectors" | "knowledge";
  setActiveTab: (tab: "roles" | "tailor" | "preview" | "connectors" | "knowledge") => void;
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
  const [mobileOpen, setMobileOpen] = useState(false);
  const isOllamaUp = health?.ollama?.online;
  const totalItems = health?.knowledge_base?.total_items ?? 0;

  const NAV_ITEMS = [
    { id: "roles" as const, label: "Role Matches", code: "[01]", icon: Compass },
    { id: "tailor" as const, label: "Job Tailor", code: "[02]", icon: ScrollText },
    { id: "preview" as const, label: "Resume & PDF", code: "[03]", icon: FileText },
    { id: "connectors" as const, label: "Connectors", code: "[04]", icon: Layers },
    { id: "knowledge" as const, label: "Archive Stock", code: "[05]", icon: Database },
  ];

  return (
    <>
      {/* 
        TOP HEADER:
        Matches Google Stitch layout.
        Includes MCP logo, name "Wissen", and responsive mobile navigation drawer toggle.
      */}
      <header className="fixed top-0 left-0 right-0 lg:right-72 z-40 bg-[#fff8f4]/95 backdrop-blur-md border-b-2 border-ink shadow-[0_2px_0px_#221a12] h-16">
        <div className="h-full px-5 sm:px-8 flex items-center justify-between">
          {/* Logo + Name */}
          <div className="flex items-center gap-3">
            <img
              alt="Wissen Typewriter Key Logo"
              className="h-8 w-auto object-contain"
              src="/wissen-logo.png"
            />
            <span className="font-serif text-2xl font-bold text-ink tracking-tight leading-none">
              Wissen
            </span>
          </div>

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden flex items-center gap-1.5 px-3 py-1.5 rounded border-2 border-ink bg-manila font-mono text-xs font-bold text-ink shadow-press hover:bg-terracotta hover:text-paper transition-all"
            aria-label="Toggle Navigation Menu"
          >
            {mobileOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            <span className="uppercase text-[11px]">{mobileOpen ? "Close" : "Menu"}</span>
          </button>
        </div>
      </header>

      {/* Backdrop for Mobile Drawer */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-ink/40 z-40 lg:hidden backdrop-blur-xs"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* 
        RIGHT NAVIGATION PANEL:
        Fixed vertical aside matching the Stitch screen layout exactly.
      */}
      <aside
        className={`fixed right-0 top-0 bottom-0 w-72 bg-manila border-l-2 border-ink shadow-[-3px_0_0px_#221a12] z-50 flex flex-col justify-between transition-transform duration-200 ease-in-out ${
          mobileOpen ? "translate-x-0" : "translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="p-6 flex flex-col gap-6">
          {/* Top Profile / Mode Header */}
          <div className="flex items-center justify-between pb-4 border-b-2 border-ink/20">
            <div className="flex items-center gap-3">
              <img
                alt="Artisan Profile"
                className="w-9 h-9 rounded-full object-cover border-2 border-ink shadow-press"
                src="/artisan-avatar.png"
              />
              <div className="flex flex-col">
                <span className="font-mono text-xs font-bold uppercase text-ink leading-tight">
                  Artisan Desk
                </span>
                <span className="font-mono text-[10px] text-ink-muted leading-tight">
                  Curator Mode
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] uppercase bg-[#fffdf9] px-2 py-0.5 rounded text-ink border-2 border-ink font-bold shadow-sm">
                Ref. 08
              </span>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="lg:hidden p-1 rounded hover:bg-terracotta hover:text-paper border border-ink text-ink transition-colors"
                title="Close Drawer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Navigation Items (The App's Core Tabs) */}
          <nav className="flex flex-col gap-2">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setMobileOpen(false);
                  }}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded font-mono text-xs uppercase tracking-wider transition-all border-2 text-left ${isActive
                      ? "bg-terracotta text-paper font-bold border-ink shadow-press translate-x-1"
                      : "text-ink border-transparent hover:bg-paper/90 hover:border-ink/30 hover:text-ink"
                    }`}
                >
                  <span className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? "text-paper" : "text-ink-muted"}`} />
                    <span>{item.label}</span>
                  </span>
                  <span
                    className={`font-mono text-[10px] font-bold ${isActive ? "text-paper/90" : "text-ink-muted"
                      }`}
                  >
                    {item.code}
                  </span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Section: Action & Archival Telemetry */}
        <div className="p-6 border-t-2 border-ink/20 bg-paper/60 flex flex-col gap-3.5">
          <button
            type="button"
            onClick={() => {
              setActiveTab("tailor");
              setMobileOpen(false);
            }}
            className="w-full flex items-center justify-center gap-2 bg-terracotta hover:bg-[#b03d25] text-paper font-mono text-xs font-bold uppercase py-2.5 px-4 rounded border-2 border-ink shadow-press hover:translate-x-0.5 hover:translate-y-0.5 transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span>Draft Entry</span>
          </button>

          <div className="flex items-center justify-between font-mono text-[10px] text-ink-muted pt-1">
            <span className="font-bold">FOLIO ARCHIVE</span>
            <span>CHROMA: {totalItems} ITEMS</span>
          </div>

          {/* Engine Health Status */}
          <div className="flex items-center justify-between font-mono text-[10px] text-ink-muted border-t border-ink/10 pt-2.5">
            <span className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${isOllamaUp ? "bg-emerald-600 animate-pulse" : "bg-terracotta"
                  }`}
              />
              <span>
                {isOllamaUp
                  ? health?.ollama?.models && health.ollama.models.length > 0
                    ? `Ollama: ${health.ollama.models[0].split(":")[0]}`
                    : "Ollama: Active"
                  : "Ollama: Offline"}
              </span>
            </span>

            <button
              onClick={refreshHealth}
              disabled={isLoading}
              className="p-1 hover:bg-manila rounded text-ink transition"
              title="Refresh System Status"
            >
              <RefreshCw className={`w-3 h-3 ${isLoading ? "animate-spin text-terracotta" : ""}`} />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
