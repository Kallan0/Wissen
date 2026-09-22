export interface ContactInfo {
  email?: string;
  phone?: string;
  location?: string;
  linkedin?: string;
  github?: string;
  portfolio?: string;
}

export interface SkillCategory {
  category: string;
  items: string[];
}

export interface ExperienceItem {
  company: string;
  role: string;
  duration: string;
  location?: string;
  bullets: string[];
  technologies?: string[];
}

export interface ProjectItem {
  name: string;
  description?: string;
  technologies: string[];
  bullets?: string[];
  highlights?: string[];
  link?: string;
}

export interface EducationItem {
  institution: string;
  degree: string;
  year: string;
  details?: string;
}

export interface ResumeData {
  name: string;
  title: string;
  contact: ContactInfo;
  summary: string;
  skills: SkillCategory[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  education: EducationItem[];
  tailored_match_notes?: string[];
  _ai_provider?: string;
}

export interface RAGItem {
  id: string;
  collection: string;
  content: string;
  metadata: Record<string, any>;
  similarity: number;
}

export interface RAGContext {
  match_count: number;
  retrieved_items: RAGItem[];
  keywords: string[];
}

export interface TailorResponse {
  resume: ResumeData;
  rag_context: RAGContext;
}

export interface KnowledgeBaseStats {
  experiences: number;
  projects: number;
  skills: number;
  education: number;
  raw_documents: number;
  total_items: number;
}

export interface CandidateProfileResponse {
  exists: boolean;
  total_items: number;
  candidate: ContactInfo & { name?: string };
  experiences: ExperienceItem[];
  projects: ProjectItem[];
  skills: SkillCategory[];
  education: EducationItem[];
}

export interface OllamaStatus {
  online: boolean;
  models: string[];
  url: string;
}

export interface HealthResponse {
  status: string;
  ollama: OllamaStatus;
  knowledge_base: KnowledgeBaseStats;
}

export interface RecommendedPosition {
  title: string;
  seniority: string;
  fit_score: number;
  description: string;
  why_qualified: string[];
  skills_leveraged: string[];
  recommended_focus: string;
  sample_jd_prompt: string;
}

export interface CareerRecommendationsResponse {
  profile_summary: string;
  recommended_positions: RecommendedPosition[];
  _ai_provider?: string;
}

export interface GitHubSyncResult {
  username: string;
  repos_synced: number;
  skills_extracted: number;
  repositories: Array<{
    name: string;
    language: string;
    stars: number;
    url: string;
    topics: string[];
  }>;
}

export interface CanvaProjectPayload {
  title: string;
  description: string;
  design_type?: string;
  tools_used?: string[];
  prototype_url?: string;
  deliverables?: string[];
  user_impact?: string;
}

export interface FilesystemScanResult {
  project_name: string;
  project_type: string;
  detected_technologies: string[];
  directory_path: string;
  highlights_count: number;
}

export interface ATSAnalysisResponse {
  ats_score: number;
  summary_verdict: string;
  matched_skills: string[];
  missing_skills: string[];
  bullet_recommendations: string[];
  _ai_provider?: string;
}

export interface CoverLetterResponse {
  company_name: string;
  role_title: string;
  cover_letter_body: string;
  linkedin_outreach_message: string;
  key_highlights_cited: string[];
  _ai_provider?: string;
}

export interface VaultScanResult {
  status: string;
  vault_path: string;
  files_scanned: number;
  total_chunks: number;
  processed_files: Array<{ title: string; path: string; chunks: number }>;
}

export interface ExportDatasetResult {
  status: string;
  count: number;
  generated_count?: number;
  holdout_count?: number;
  filename: string;
  file_size_bytes: number;
  download_url: string;
  holdout_filename?: string;
  holdout_download_url?: string;
}

export interface FineTuningStatus {
  installed_models: string[];
  custom_models: string[];
  base_models: string[];
  has_custom_model_active: boolean;
  toolkit: {
    modelfile_available: boolean;
    colab_notebook_available: boolean;
  };
}
