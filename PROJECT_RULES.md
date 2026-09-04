# Project Development & Versioning Rules

Whenever changes, features, or bugfixes are made to this project:
1. **Always create a new version markdown file** in the `versions/` directory:
   - Format: `versions/vX.Y.Z.md` (e.g. `versions/v1.2.0.md`).
2. **Each version file must detail**:
   - Release Version & Date
   - Overview of the update
   - Detailed list of changes made (files modified/created, APIs, UI components)
   - The rationale and reason for each change
3. **Update `CHANGELOG.md`** with a summarized entry pointing to the new version file.
