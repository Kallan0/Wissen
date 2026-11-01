"use client";

import React, { useEffect, useState } from "react";
import { X, Plus, Trash2, UserCheck, Briefcase, GraduationCap, Code, Sparkles, FolderGit2 } from "lucide-react";
import { fetchKBStats, ingestProfile } from "@/lib/api";

type EntryMode = "profile" | "experience" | "project" | "education";

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
  const [skillsStr, setSkillsStr] = useState("");

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
  const [identityRequired, setIdentityRequired] = useState<boolean | null>(null);
  const [entryMode, setEntryMode] = useState<EntryMode>("profile");

  useEffect(() => {
    if (!isOpen) return;

    let cancelled = false;
    setIdentityRequired(null);
    fetchKBStats()
      .then((stats) => {
        if (cancelled) return;
        const isEmpty = stats.total_items === 0;
        setIdentityRequired(isEmpty);
        setEntryMode(isEmpty ? "profile" : "experience");
      })
      .catch(() => {
        if (cancelled) return;
        // Be conservative if the knowledge-base status cannot be verified.
        setIdentityRequired(true);
        setEntryMode("profile");
      });

    return () => {
      cancelled = true;
    };
  }, [isOpen]);

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

  const resetForm = () => {
    setName("");
    setTitle("");
    setEmail("");
    setPhone("");
    setLocation("");
    setLinkedin("");
    setGithub("");
    setSummary("");
    setSkillsStr("");
    setExperiences([{ company: "", role: "", duration: "", location: "", bullets: [""] }]);
    setProjects([{ name: "", description: "", technologies: "", link: "" }]);
    setEducation([{ institution: "", degree: "", year: "", details: "" }]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (identityRequired && !name.trim()) {
      setError("Please enter your full name.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const projectPayload = projects.map(({ technologies, ...project }) => ({
        ...project,
        technologies_text: technologies,
      }));
      const payload: Record<string, any> = entryMode === "profile"
        ? {
            name,
            title,
            contact: { email, phone, location, linkedin, github },
            summary,
            skills_text: skillsStr,
            experience: experiences,
            projects: projectPayload,
            education,
          }
        : entryMode === "experience"
          ? { experience: experiences }
          : entryMode === "project"
            ? { projects: projectPayload }
            : { education };

      await ingestProfile(payload);
      resetForm();
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

          {identityRequired === null ? (
            <div className="p-3 bg-manila/50 border border-ink/30 rounded font-mono text-xs text-ink-muted">
              Checking whether this is a new or existing profile...
            </div>
          ) : !identityRequired ? (
            <div className="space-y-2">
              <div className="font-mono text-[10px] uppercase font-bold text-ink-muted">
                What would you like to add?
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {([
                  ["experience", "Experience"],
                  ["project", "Project"],
                  ["education", "Education"],
                  ["profile", "Profile details"],
                ] as [EntryMode, string][]).map(([mode, label]) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setEntryMode(mode)}
                    className={`p-2 border-2 rounded font-mono text-[11px] font-bold uppercase transition-colors ${
                      entryMode === mode
                        ? "bg-ink text-paper border-ink"
                        : "bg-paper text-ink border-ink/30 hover:border-ink"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <p className="font-serif text-xs italic text-ink-muted">
                Your saved identity will be reused. Only the selected section is submitted.
              </p>
            </div>
          ) : (
            <div className="p-3 bg-manila/50 border border-ink/30 rounded font-serif text-xs text-ink-muted">
              The knowledge base is empty. Create the profile identity first; future entries can be added individually.
            </div>
          )}

          {/* Personal Info */}
          {entryMode === "profile" && <div className="space-y-3">
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-ink flex items-center gap-1.5 border-b border-ink/20 pb-1">
              <UserCheck className="w-4 h-4 text-terracotta" />
              1. Candidate Contact & Profile Header
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="font-mono text-[10px] uppercase text-ink-muted block mb-1">
                  Full Name {identityRequired ? "*" : ""}
                </label>
                <input
                  type="text"
                  required={identityRequired === true}
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
                  placeholder="e.g. Software Engineering Intern"
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
              <div>
                <label className="font-mono text-[10px] uppercase text-ink-muted block mb-1">GitHub Profile</label>
                <input
                  type="text"
                  placeholder="github.com/janedoe"
                  value={github}
                  onChange={(e) => setGithub(e.target.value)}
                  className="w-full font-mono text-xs p-2 border-2 border-ink/40 rounded focus:border-ink bg-paper"
                />
              </div>
            </div>
          </div>}

          {/* Executive Summary */}
          {entryMode === "profile" && <div>
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
          </div>}

          {/* Technical Skills */}
          {entryMode === "profile" && <div>
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
          </div>}

          {/* Work Experience */}
          {(entryMode === "profile" || entryMode === "experience") && <div className="space-y-4">
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
          </div>}

          {/* Projects */}
          {(entryMode === "profile" || entryMode === "project") && <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-ink/20 pb-1">
              <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-ink flex items-center gap-1.5">
                <FolderGit2 className="w-4 h-4 text-terracotta" />
                Projects
              </h3>
              <button
                type="button"
                onClick={() => setProjects([...projects, { name: "", description: "", technologies: "", link: "" }])}
                className="font-mono text-[11px] bg-manila hover:bg-manila/80 px-2.5 py-1 rounded border border-ink font-bold flex items-center gap-1"
              >
                <Plus className="w-3 h-3 text-terracotta" /> ADD PROJECT
              </button>
            </div>
            {projects.map((project, idx) => (
              <div key={idx} className="p-4 bg-manila/40 border-2 border-ink/40 rounded-lg space-y-3">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-[10px] uppercase font-bold text-ink-muted">PROJECT #{idx + 1}</span>
                  {projects.length > 1 && (
                    <button type="button" onClick={() => setProjects(projects.filter((_, i) => i !== idx))} className="text-terracotta text-xs font-mono flex items-center gap-1">
                      <Trash2 className="w-3.5 h-3.5" /> REMOVE
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {([
                    ["name", "Project Name"],
                    ["technologies", "Technologies (comma separated)"],
                    ["link", "Project Link"],
                  ] as const).map(([field, placeholder]) => (
                    <input
                      key={field}
                      type="text"
                      placeholder={placeholder}
                      value={project[field]}
                      onChange={(e) => {
                        const copy = [...projects];
                        copy[idx] = { ...copy[idx], [field]: e.target.value };
                        setProjects(copy);
                      }}
                      className="font-mono text-xs p-2 border-2 border-ink/30 rounded bg-paper"
                    />
                  ))}
                </div>
                <textarea
                  rows={3}
                  placeholder="Crisp description of what you built, your contribution, and the result..."
                  value={project.description}
                  onChange={(e) => {
                    const copy = [...projects];
                    copy[idx] = { ...copy[idx], description: e.target.value };
                    setProjects(copy);
                  }}
                  className="w-full font-mono text-xs p-2 border-2 border-ink/30 rounded bg-paper"
                />
              </div>
            ))}
          </div>}

          {/* Education */}
          {(entryMode === "profile" || entryMode === "education") && <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-ink/20 pb-1">
              <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-ink flex items-center gap-1.5">
                <GraduationCap className="w-4 h-4 text-fountain-teal" />
                Education & Credentials
              </h3>
              <button
                type="button"
                onClick={() => setEducation([...education, { institution: "", degree: "", year: "", details: "" }])}
                className="font-mono text-[11px] bg-manila hover:bg-manila/80 px-2.5 py-1 rounded border border-ink font-bold flex items-center gap-1"
              >
                <Plus className="w-3 h-3 text-terracotta" /> ADD EDUCATION
              </button>
            </div>
            {education.map((edu, idx) => (
              <div key={idx} className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 bg-manila/30 border border-ink/30 rounded relative">
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
                <textarea
                  rows={2}
                  placeholder="Coursework, honors, or other verified details"
                  value={edu.details}
                  onChange={(e) => {
                    const copy = [...education];
                    copy[idx].details = e.target.value;
                    setEducation(copy);
                  }}
                  className="sm:col-span-3 font-mono text-xs p-2 border border-ink/30 rounded bg-paper"
                />
                {education.length > 1 && (
                  <button type="button" onClick={() => setEducation(education.filter((_, i) => i !== idx))} className="sm:col-span-3 justify-self-end text-terracotta text-xs font-mono flex items-center gap-1">
                    <Trash2 className="w-3.5 h-3.5" /> REMOVE
                  </button>
                )}
              </div>
            ))}
          </div>}

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
              disabled={loading || identityRequired === null}
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
                  {entryMode === "profile" ? "SAVE PROFILE TO KNOWLEDGE BASE" : `ADD ${entryMode.toUpperCase()}`}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
