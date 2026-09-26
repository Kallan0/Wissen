# Frontend / Backend Boundary Audit

Date: 2026-09-24

## Decision rule

- Frontend owns interaction state, input controls, display formatting, loading/error feedback, and browser downloads.
- Backend owns verified-data normalization, validation, model prompts, resume generation, template rendering, and export behavior.
- The frontend may serialize form values, but it must not invent candidate facts or maintain a second rendering implementation.

## Findings and actions

| Priority | Area | Finding | Decision / status |
|---|---|---|---|
| High | Resume preview | `ResumePreview.tsx` contained three full resume layouts that duplicated `backend/pdf/templates.py`. Browser preview and exported PDF could drift. | **Moved.** The frontend now requests `/api/render-resume-html` and displays the backend-owned template in a sandboxed iframe. The three React template engines were removed. |
| High | Profile ingestion | `ProfileQuestionnaireModal.tsx` normalized domain data and inserted unverified fallbacks: `Software Engineer`, `Software Engineering`, `Organization`, and `Role`. It also prefilled a candidate skill set. | **Moved.** `rag/profile_normalization.py` now trims, normalizes, and validates raw questionnaire data. Synthetic frontend fallbacks and prefilled skills were removed. Incomplete factual records return HTTP 400. |
| High | Template safety | The Jinja string renderer did not auto-escape candidate-controlled values. The new shared HTML preview made this boundary more visible. | **Fixed.** Backend templates now use an auto-escaping Jinja environment; regression coverage rejects raw script markup. |
| Medium | API defaults | `frontend/src/lib/api.ts` still contains convenience defaults such as `Software Engineer` and `llama3`, which overlap backend request defaults. | **Follow-up.** Centralize deploy-time model defaults in backend configuration. Role text entered or selected by the user remains frontend state. |
| Medium | Template selection | Preview/export accepted arbitrary template strings and silently fell back to modern. | **Fixed.** The backend request contract now accepts only `modern`, `minimal`, or `vintage`; unknown names return HTTP 422. |
| Low | Comma-delimited form fields | `ConnectorsHub.tsx` and `KnowledgeBase.tsx` split comma-delimited tools, deliverables, and tags before transport. | **Keep for now.** This is form serialization, not candidate-fact inference. Move only if these endpoints adopt raw-form DTOs consistently. |
| Low | Sample job descriptions | `JobTailor.tsx` contains UI presets used to populate the form. | **Keep in UI.** They are visible user-selectable examples, not hidden generation or validation rules. If presets become remotely managed product content, expose them from the backend then. |
| Low | Download filename | `ResumePreview.tsx` creates the user-facing browser download name. | **Keep in UI.** Browser save behavior and filename choice are presentation concerns; server artifact naming remains backend-owned. |
| None | ATS, cover letter, roles | `ATSGapAnalyzer`, `CoverLetterModal`, and `RoleRecommender` render API results and maintain interaction state; generation already lives in the backend. | **No change.** Boundary is correct. |

## Resulting flow

1. Questionnaire UI submits raw values.
2. Backend rejects incomplete factual records and creates the canonical ingestion shape.
3. Backend generation produces structured resume data.
4. Backend renders the selected resume template for both preview and PDF.
5. Frontend controls selection, editing, feedback, and download interactions only.

## Verification

- `7 passed`: profile-boundary and PDF-template regression tests.
- Backend preview endpoint smoke test returned escaped, backend-rendered HTML.
- `npm.cmd run build`: passed TypeScript, lint checks, and production compilation.
- `ResumePreview.tsx`: reduced from roughly 711 lines with three renderers to a compact interaction/preview component.
- First-load JS: approximately 114 kB after the change (previously approximately 116 kB).

## Remaining recommended cleanup

1. Remove duplicated model and target-role defaults from API wrappers after backend configuration is made the single default owner.
2. Introduce explicit Pydantic request models for profile ingestion instead of the current dictionary boundary.
