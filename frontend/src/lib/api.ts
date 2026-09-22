import {
  HealthResponse,
  KnowledgeBaseStats,
  CandidateProfileResponse,
  TailorResponse,
  ResumeData,
  CareerRecommendationsResponse,
  GitHubSyncResult,
  CanvaProjectPayload,
  FilesystemScanResult,
  VaultScanResult,
  CoverLetterResponse,
  ATSAnalysisResponse,
  ExportDatasetResult,
  FineTuningStatus,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("Failed to connect to backend");
  return res.json();
}

export async function fetchModels(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/models`);
  if (!res.ok) return ["llama3"];
  const data = await res.json();
  return data.models || ["llama3"];
}

export async function fetchKBStats(): Promise<KnowledgeBaseStats> {
  const res = await fetch(`${API_BASE}/api/knowledge-base/stats`);
  if (!res.ok) throw new Error("Failed to fetch knowledge base statistics");
  return res.json();
}

export async function fetchKBItems(): Promise<Record<string, any[]>> {
  const res = await fetch(`${API_BASE}/api/knowledge-base/items`);
  if (!res.ok) throw new Error("Failed to fetch knowledge base items");
  return res.json();
}

export async function fetchKBProfile(): Promise<CandidateProfileResponse> {
  const res = await fetch(`${API_BASE}/api/knowledge-base/profile`);
  if (!res.ok) throw new Error("Failed to fetch candidate profile");
  return res.json();
}

export async function ingestProfile(payload: any): Promise<{ message: string; indexed: Record<string, number> }> {
  const res = await fetch(`${API_BASE}/api/knowledge-base/ingest-profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to ingest structured profile");
  return res.json();
}

export async function ingestText(title: string, content: string, category = "raw_documents", tags: string[] = []): Promise<{ message: string; chunks: number }> {
  const res = await fetch(`${API_BASE}/api/knowledge-base/ingest-text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, content, category, tags }),
  });
  if (!res.ok) throw new Error("Failed to ingest text note");
  return res.json();
}

export async function uploadResumePDF(file: File): Promise<{ message: string; chunks: number; stats: KnowledgeBaseStats }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/knowledge-base/upload-resume-pdf`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to upload PDF resume");
  }
  return res.json();
}

export async function seedSampleProfile(): Promise<{ message: string; stats: KnowledgeBaseStats }> {
  const res = await fetch(`${API_BASE}/api/knowledge-base/seed-sample`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to seed sample profile");
  return res.json();
}

export async function clearKnowledgeBase(): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/api/knowledge-base/clear`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to clear knowledge base");
  return res.json();
}

export async function tailorResume(
  jobDescription: string,
  targetRole = "Software Engineer",
  model = "llama3",
  candidateName?: string,
  candidateEmail?: string,
  template = "modern"
): Promise<TailorResponse> {
  const res = await fetch(`${API_BASE}/api/tailor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_description: jobDescription,
      target_role: targetRole,
      model,
      candidate_name: candidateName,
      candidate_email: candidateEmail,
      template,
    }),
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Tailoring failed: ${errorText}`);
  }
  return res.json();
}

export async function exportPDF(resumeData: ResumeData, template = "modern"): Promise<{ filename: string; download_url: string }> {
  const res = await fetch(`${API_BASE}/api/export-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_data: resumeData,
      template,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PDF export failed: ${err}`);
  }
  return res.json();
}

export function getDownloadUrl(filename: string): string {
  return `${API_BASE}/api/download-pdf/${filename}`;
}

export async function fetchCareerRecommendations(model = "llama3"): Promise<CareerRecommendationsResponse> {
  const res = await fetch(`${API_BASE}/api/recommend-positions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Role recommendation failed: ${err}`);
  }
  return res.json();
}

export async function syncGitHub(
  username: string,
  token?: string,
  maxRepos = 15,
  fetchReadme = true
): Promise<{ status: string; result: GitHubSyncResult; stats: KnowledgeBaseStats }> {
  const res = await fetch(`${API_BASE}/api/connectors/github/sync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      token,
      max_repos: maxRepos,
      fetch_readme: fetchReadme,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to sync GitHub repositories");
  }
  return res.json();
}

export async function syncCanvaProject(
  payload: CanvaProjectPayload
): Promise<{ status: string; result: any; stats: KnowledgeBaseStats }> {
  const res = await fetch(`${API_BASE}/api/connectors/canva/sync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to sync Canva/Design project");
  }
  return res.json();
}

export async function scanLocalProject(
  directoryPath: string,
  customProjectName?: string
): Promise<{ status: string; result: FilesystemScanResult; stats: KnowledgeBaseStats }> {
  const res = await fetch(`${API_BASE}/api/connectors/filesystem/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      directory_path: directoryPath,
      custom_project_name: customProjectName,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to scan local project folder");
  }
  return res.json();
}

export async function parseLinkedInCSV(
  positionsCsv?: string,
  skillsCsv?: string
): Promise<{ status: string; ingested_counts: Record<string, number>; stats: KnowledgeBaseStats }> {
  const res = await fetch(`${API_BASE}/api/connectors/linkedin/parse-csv`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ positions_csv: positionsCsv, skills_csv: skillsCsv }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to parse LinkedIn CSV export");
  }
  return res.json();
}

export async function scanVault(
  directoryPath: string
): Promise<VaultScanResult> {
  const res = await fetch(`${API_BASE}/api/connectors/vault/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ directory_path: directoryPath }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to scan Markdown Vault");
  }
  return res.json();
}

export async function generateCoverLetter(
  jobDescription: string,
  targetRole = "Software Engineer",
  model = "llama3"
): Promise<CoverLetterResponse> {
  const res = await fetch(`${API_BASE}/api/generate-cover-letter`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_description: jobDescription, target_role: targetRole, model }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to generate Cover Letter");
  }
  return res.json();
}

export async function analyzeATSGap(
  jobDescription: string,
  model = "llama3"
): Promise<ATSAnalysisResponse> {
  const res = await fetch(`${API_BASE}/api/analyze-ats-gap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_description: jobDescription, model }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to analyze ATS Gap");
  }
  return res.json();
}

export async function exportFineTuningDataset(count = 150): Promise<ExportDatasetResult> {
  const res = await fetch(`${API_BASE}/api/finetuning/export-dataset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ count }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to export fine-tuning dataset");
  }
  return res.json();
}

export async function fetchFineTuningStatus(): Promise<FineTuningStatus> {
  const res = await fetch(`${API_BASE}/api/finetuning/status`);
  if (!res.ok) throw new Error("Failed to fetch fine-tuning status");
  return res.json();
}
