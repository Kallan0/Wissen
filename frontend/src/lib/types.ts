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
  year?: string;
}

export interface EducationItem {
  institution: string;
  degree: string;
  year: string;
  details?: string;
  location?: string;
}

export interface JSONResumeCustomData {
  wissenPress?: {
    displayDate?: string;
    location?: string;
    tailoredMatchNotes?: string[];
    aiProvider?: string;
    groundingValidation?: Record<string, unknown>;
  };
  [key: string]: unknown;
}

export interface JSONResumeBasics {
  name?: string;
  label?: string;
  image?: string;
  email?: string;
  phone?: string;
  url?: string;
  summary?: string;
  location?: {
    address?: string;
    postalCode?: string;
    city?: string;
    countryCode?: string;
    region?: string;
  };
  profiles?: Array<{ network?: string; username?: string; url?: string }>;
}

export interface JSONResumeWork {
  name?: string;
  position?: string;
  location?: string;
  description?: string;
  url?: string;
  startDate?: string;
  endDate?: string;
  summary?: string;
  highlights?: string[];
  keywords?: string[];
  custom?: JSONResumeCustomData;
}

export interface JSONResumeProject {
  name?: string;
  summary?: string;
  highlights?: string[];
  keywords?: string[];
  startDate?: string;
  endDate?: string;
  url?: string;
  roles?: string[];
  entity?: string;
  type?: string;
  custom?: JSONResumeCustomData;
}

export interface JSONResumeEducation {
  institution?: string;
  url?: string;
  area?: string;
  studyType?: string;
  startDate?: string;
  endDate?: string;
  score?: string;
  courses?: string[];
  summary?: string;
  custom?: JSONResumeCustomData;
}

export interface JSONResumeSkill {
  name?: string;
  level?: string;
  keywords?: string[];
}

export interface ResumeData {
  basics?: JSONResumeBasics;
  work?: JSONResumeWork[];
  education?: JSONResumeEducation[];
  skills?: JSONResumeSkill[];
  projects?: JSONResumeProject[];
  volunteer?: unknown[];
  awards?: unknown[];
  certificates?: unknown[];
  publications?: unknown[];
  languages?: unknown[];
  interests?: unknown[];
  references?: unknown[];
  meta?: { canonical?: string; version?: string; lastModified?: string; theme?: string };
  custom?: JSONResumeCustomData;
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
  expanded_concepts?: string[];
  context_metrics?: {
    characters: number;
    approximate_tokens: number;
    source_sections_available: number;
    source_sections_included: number;
    max_characters: number;
  };
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
  enabled?: boolean;
  online: boolean;
  models: string[];
  url: string;
}

export interface CloudProviderStatus {
  configured: boolean;
  online: boolean;
  models: string[];
}

export interface HealthResponse {
  status: string;
  api_revision?: string;
  ollama: OllamaStatus;
  groq?: CloudProviderStatus;
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
