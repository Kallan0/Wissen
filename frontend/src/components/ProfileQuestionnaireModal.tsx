"use client";

import React, { useState } from "react";
import { X, Plus, Trash2, CheckCircle2, UserCheck, Briefcase, GraduationCap, Code, Sparkles, FolderGit2 } from "lucide-react";
import { ingestProfile } from "@/lib/api";

interface ProfileQuestionnaireModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ProfileQuestionnaireModal({
  isOpen,
  onClose,
  onSuccess,
}: ProfileQuestionnaireModalProps) {
  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [github, setGithub] = useState("");
  const [summary, setSummary] = useState("");

  // Skills
  const [skillsStr, setSkillsStr] = useState("Python, TypeScript, FastAPI, React, Next.js, PostgreSQL, Docker, Git");

  // Experience items
  const [experiences, setExperiences] = useState([
    {
      company: "",
      role: "",
      duration: "",
      location: "",
      bullets: [""],
    },
  ]);

  // Project items
  const [projects, setProjects] = useState([
    {
      name: "",
      description: "",
      technologies: "",
      link: "",
    },
  ]);

  // Education items
  const [education, setEducation] = useState([
    {
      institution: "",
      degree: "",
      year: "",
      details: "",
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleAddExperience = () => {
    setExperiences([
      ...experiences,
      { company: "", role: "", duration: "", location: "", bullets: [""] },
    ]);
  };

  const handleRemoveExperience = (idx: number) => {
    setExperiences(experiences.filter((_, i) => i !== idx));
  };

  const handleExperienceChange = (idx: number, field: string, value: any) => {
    const copy = [...experiences];
    (copy[idx] as any)[field] = value;
    setExperiences(copy);
  };

  const handleAddBullet = (expIdx: number) => {
    const copy = [...experiences];
    copy[expIdx].bullets.push("");
    setExperiences(copy);
  };

  const handleBulletChange = (expIdx: number, bulletIdx: number, val: string) => {
    const copy = [...experiences];
    copy[expIdx].bullets[bulletIdx] = val;
    setExperiences(copy);
  };

  const handleRemoveBullet = (expIdx: number, bulletIdx: number) => {
    const copy = [...experiences];
    copy[expIdx].bullets = copy[expIdx].bullets.filter((_, b) => b !== bulletIdx);
    setExperiences(copy);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter your full name.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      // Parse skills string into skill categories
      const skillItems = skillsStr
        .split(",")
        .map((s) => s.strip ? s.strip() : s.trim())
        .filter(Boolean);

      const payload = {
        name: name.trim(),
        title: title.trim() || "Software Engineer",
        contact: {
          email: email.trim(),
          phone: phone.trim(),
          location: location.trim(),
          linkedin: linkedin.trim(),
          github: github.trim(),
        },
        summary: summary.trim(),
        skills: [
          {
            category: "Core Technical Competencies",
            items: skillItems.length > 0 ? skillItems : ["Software Engineering"],
          },
        ],
        experience: experiences
          .filter((e) => e.company.trim() || e.role.trim())
          .map((e) => ({
            company: e.company.trim() || "Organization",
            role: e.role.trim() || "Role",
            duration: e.duration.trim() || "",
            location: e.location.trim() || "",
            bullets: e.bullets.filter((b) => b.trim().length > 0),
          })),
        projects: projects
          .filter((p) => p.name.trim())
          .map((p) => ({
            name: p.name.trim(),
            description: p.description.trim(),
            technologies: p.technologies
              .split(",")
              .map((t) => t.trim())
              .filter(Boolean),
            link: p.link.trim(),
          })),
        education: education
          .filter((e) => e.institution.trim() || e.degree.trim())
          .map((e) => ({
            institution: e.institution.trim(),
            degree: e.degree.trim(),
            year: e.year.trim(),
            details: e.details.trim(),
          })),
      };

      await ingestProfile(payload);
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to ingest profile into ChromaDB.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-ink/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-fade-in">
      <div className="bg-[#fffdf9] max-w-4xl w-full rounded-xl border-2 border-ink shadow-dossier relative max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-5 sm:p-6 bg-manila border-b-2 border-ink flex items-center justify-between shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-[10px] uppercase tracking-widest bg-ink text-paper px-2 py-0.5 font-bold">
                CANDIDATE DOSSIER BUILDER
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-serif font-bold text-ink flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-terracotta" />
              Ingest Profile & Work Experience Questionnaire
            </h2>
            <p className="text-xs font-serif italic text-ink-muted">
              Enter your real work history, internships, education, and skills to index them directly into ChromaDB.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-ink/10 rounded-lg text-ink transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Form */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-6 flex-1">
          {error && (
            <div className="p-3 bg-[#fff0ed] border-2 border-terracotta rounded text-xs text-terracotta font-mono">
              {error}
            </div>
          )}

          {/* Personal Info */}
          <div className="space-y-3">
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-ink flex items-center gap-1.5 border-b border-ink/20 pb-1">
              <UserCheck className="w-4 h-4 text-terracotta" />
              1. Candidate Contact & Profile Header
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="font-mono text-[10px] uppercase text-ink-muted block mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Jane Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full font-mono text-xs p-2 border-2 border-ink/40 rounded focus:border-ink bg-paper"
                />
              </div>
              <div>
                <label className="font-mono text-[10px] uppercase text-ink-muted block mb-1">Target Title</label>
                <input
                  type="text"
                  placeholder="e.g. Senior Full-Stack Engineer"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full font-mono text-xs p-2 border-2 border-ink/40 rounded focus:border-ink bg-paper"
                />
              </div>
              <div>
                <label className="font-mono text-[10px] uppercase text-ink-muted block mb-1">Email Address</label>
                <input
                  type="email"
                  placeholder="jane.doe@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full font-mono text-xs p-2 border-2 border-ink/40 rounded focus:border-ink bg-paper"
                />
              </div>
              <div>
                <label className="font-mono text-[10px] uppercase text-ink-muted block mb-1">Phone Number</label>
                <input
                  type="text"
                  placeholder="+1 (555) 000-0000"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full font-mono text-xs p-2 border-2 border-ink/40 rounded focus:border-ink bg-paper"
                />
              </div>
              <div>
                <label className="font-mono text-[10px] uppercase text-ink-muted block mb-1">Location</label>
                <input
                  type="text"
                  placeholder="City, State / Remote"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full font-mono text-xs p-2 border-2 border-ink/40 rounded focus:border-ink bg-paper"
                />
              </div>
              <div>
                <label className="font-mono text-[10px] uppercase text-ink-muted block mb-1">LinkedIn Profile</label>
                <input
                  type="text"
                  placeholder="linkedin.com/in/janedoe"
                  value={linkedin}
                  onChange={(e) => setLinkedin(e.target.value)}
                  className="w-full font-mono text-xs p-2 border-2 border-ink/40 rounded focus:border-ink bg-paper"
                />
              </div>
            </div>
          </div>

          {/* Executive Summary */}
          <div>
            <label className="font-mono text-xs font-bold uppercase tracking-wider text-ink block mb-1">
              2. Executive Summary / Bio Overview
            </label>
            <textarea
              rows={3}
              placeholder="Summary of your career achievements, core specializations, and engineering strengths..."
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="w-full font-mono text-xs p-3 border-2 border-ink/40 rounded focus:border-ink bg-paper leading-relaxed"
            />
          </div>

          {/* Technical Skills */}
          <div>
            <label className="font-mono text-xs font-bold uppercase tracking-wider text-ink block mb-1 flex items-center gap-1.5">
              <Code className="w-3.5 h-3.5 text-fountain-teal" />
              3. Technical Skills (Comma Separated)
            </label>
            <input
              type="text"
              placeholder="Python, TypeScript, FastAPI, React, PostgreSQL, Docker..."
              value={skillsStr}
              onChange={(e) => setSkillsStr(e.target.value)}
              className="w-full font-mono text-xs p-2.5 border-2 border-ink/40 rounded focus:border-ink bg-paper"
            />
          </div>

          {/* Work Experience */}
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-ink/20 pb-1">
              <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-ink flex items-center gap-1.5">
                <Briefcase className="w-4 h-4 text-terracotta" />
                4. Work Experience & Internships
              </h3>
              <button
                type="button"
                onClick={handleAddExperience}
                className="font-mono text-[11px] bg-manila hover:bg-manila/80 px-2.5 py-1 rounded border border-ink font-bold flex items-center gap-1"
              >
                <Plus className="w-3 h-3 text-terracotta" /> ADD POSITION
              </button>
            </div>

            {experiences.map((exp, idx) => (
              <div key={idx} className="p-4 bg-manila/40 border-2 border-ink/40 rounded-lg space-y-3 relative">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-[10px] uppercase font-bold text-ink-muted">POSITION #{idx + 1}</span>
                  {experiences.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveExperience(idx)}
                      className="text-terracotta hover:text-red-700 text-xs font-mono flex items-center gap-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> REMOVE
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder="Company / Organization Name"
                    value={exp.company}
                    onChange={(e) => handleExperienceChange(idx, "company", e.target.value)}
                    className="font-mono text-xs p-2 border-2 border-ink/30 rounded bg-paper"
                  />
                  <input
                    type="text"
                    placeholder="Job Title / Role"
                    value={exp.role}
                    onChange={(e) => handleExperienceChange(idx, "role", e.target.value)}
                    className="font-mono text-xs p-2 border-2 border-ink/30 rounded bg-paper"
                  />
                  <input
                    type="text"
                    placeholder="Duration (e.g. 2022 - Present)"
                    value={exp.duration}
                    onChange={(e) => handleExperienceChange(idx, "duration", e.target.value)}
                    className="font-mono text-xs p-2 border-2 border-ink/30 rounded bg-paper"
                  />
                  <input
                    type="text"
                    placeholder="Location (e.g. Remote / City)"
                    value={exp.location}
                    onChange={(e) => handleExperienceChange(idx, "location", e.target.value)}
                    className="font-mono text-xs p-2 border-2 border-ink/30 rounded bg-paper"
                  />
                </div>

                {/* Bullets */}
                <div className="space-y-2 pt-1">
                  <label className="font-mono text-[10px] font-bold text-ink-muted uppercase block">
                    Key Achievements / Bullets
                  </label>
                  {exp.bullets.map((b, bIdx) => (
                    <div key={bIdx} className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Bullet point describing accomplishment, tech stack, or impact..."
                        value={b}
                        onChange={(e) => handleBulletChange(idx, bIdx, e.target.value)}
                        className="flex-1 font-mono text-xs p-2 border border-ink/30 rounded bg-paper"
                      />
                      {exp.bullets.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveBullet(idx, bIdx)}
                          className="px-2 text-ink-muted hover:text-terracotta"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => handleAddBullet(idx)}
                    className="font-mono text-[10px] text-terracotta hover:underline font-bold"
                  >
                    + Add Bullet Point
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Education */}
          <div className="space-y-3">
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-ink flex items-center gap-1.5 border-b border-ink/20 pb-1">
              <GraduationCap className="w-4 h-4 text-fountain-teal" />
              5. Education & Credentials
            </h3>
            {education.map((edu, idx) => (
              <div key={idx} className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 bg-manila/30 border border-ink/30 rounded">
                <input
                  type="text"
                  placeholder="Institution Name"
                  value={edu.institution}
                  onChange={(e) => {
                    const copy = [...education];
                    copy[idx].institution = e.target.value;
                    setEducation(copy);
                  }}
                  className="font-mono text-xs p-2 border border-ink/30 rounded bg-paper"
                />
                <input
                  type="text"
                  placeholder="Degree / Major"
                  value={edu.degree}
                  onChange={(e) => {
                    const copy = [...education];
                    copy[idx].degree = e.target.value;
                    setEducation(copy);
                  }}
                  className="font-mono text-xs p-2 border border-ink/30 rounded bg-paper"
                />
                <input
                  type="text"
                  placeholder="Year (e.g. 2023)"
                  value={edu.year}
                  onChange={(e) => {
                    const copy = [...education];
                    copy[idx].year = e.target.value;
                    setEducation(copy);
                  }}
                  className="font-mono text-xs p-2 border border-ink/30 rounded bg-paper"
                />
              </div>
            ))}
          </div>

          {/* Submit Action */}
          <div className="pt-4 border-t-2 border-ink/20 flex justify-end gap-3 shrink-0">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border-2 border-ink rounded font-mono text-xs uppercase font-bold"
            >
              CANCEL
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 bg-terracotta hover:bg-[#b03d25] text-paper font-mono font-bold text-xs uppercase tracking-wider rounded border-2 border-ink shadow-press transition-all disabled:opacity-50 inline-flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-paper border-t-transparent rounded-full animate-spin" />
                  INDEXING INTO CHROMADB...
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5 text-paper" />
                  SAVE & INGEST TO KNOWLEDGE BASE
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
