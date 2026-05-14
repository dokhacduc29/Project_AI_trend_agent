# 🚀 STANDARDIZED PROJECT INITIALIZATION — CLAUDE CODE VERSION

**Purpose:** Comprehensive prompt specifically for **Claude Code CLI** (`claude` command) — execute full review, documentation restructuring, standard setup, and AI agent workflow for .NET projects (Clean Architecture) for first-time collaboration with AI.

**Tools:** Claude Code CLI — `claude` / `claude --dangerously-skip-permissions`

**How to use:**
1. Copy everything from `---BEGIN PROMPT---` to `---END PROMPT---` and paste into terminal running `claude`
2. Or save as `.claude/commands/init.md` to reuse with `/project:init`

**Author:** FPT FIM Team — 2026-04-23

---

---BEGIN PROMPT---

# 🚀 STANDARDIZED PROJECT INITIALIZATION — FIRST CLAUDE CODE SESSION

## PROJECT INFORMATION

> **Step 0 will automatically detect:**
> - 🟢 **GREENFIELD** (new project, no code yet) → AI will **request user to manually fill** information below
> - 🟠 **BROWNFIELD** (running project, code already exists) → AI will **auto-scan code**, user skips this section

### For GREENFIELD — Fill if this is a new project

```
Project Name:      [PROJECT_NAME]                    (e.g., FPT CSR CMS)
Short Description: [What system does, who it serves]
Tech Stack:        [.NET 9/10] | [SQL Server/PostgreSQL] | [Azure AD/JWT] | [MVC/Vanilla JS]
Main Domain:       [e.g., CMS, E-commerce, ERP, Portal]
Environment:       [Dev: localhost | UAT: uat.xxx.com | Prod: xxx.com]
Solution File:     [SOLUTION_NAME].slnx               (e.g., MyApp.slnx)
WebApi Port:       [WEBAPI_PORT]                     (e.g., 5288)
Admin Port:        [ADMIN_PORT]                      (e.g., 5100)
Portal Port:       [PORTAL_PORT]                     (e.g., 8080)
Local DB:          [LOCAL_DB_NAME]                   (e.g., MyAppDb)
.NET Version:      [VERSION]                         (e.g., 10.x)
Auth Type:         [Azure AD / JWT / Cookie / None]
```

### For BROWNFIELD — Skip if project is already running

Claude Code will automatically detect:
- ✅ Tech stack, .NET version
- ✅ Projects, Layers (Domain/Application/Infrastructure/Presentation)
- ✅ Ports from `appsettings.json`
- ✅ Database from Migrations
- ✅ Auth config

If detection is incorrect, AI will **ask for corrections**.

---

## ⚡ 22 IRON LAWS — GLOBAL RULES (INVIOLABLE)

> These laws apply **always, everywhere**, in **every session**, for **every AI agent** working with this project.
> Violating any law = **refuse execution and report immediately to user**.

| # | Law | Requirement |
|---|-----|-------------|
| L01 | **No commit secrets** | Connection strings, API keys, tokens, passwords MUST NOT appear in source code or documentation. Use Environment Variables or Secret Manager. |
| L02 | **No plaintext passwords** | All passwords must be hashed with `BCrypt.HashPassword()` before saving. Never store plain text in `PasswordHash` column. |
| L03 | **No raw SQL interpolation** | Never use `ExecuteSqlRaw($"...")` or `string.Format` to build SQL queries. Use only EF Core LINQ or parameterized queries. |
| L04 | **No reverse layer imports** | Domain never imports EF Core / Infrastructure. Application never imports Presentation / WebApi. Violation → intentional compile error. |
| L05 | **No blocking async** | Never use `.Result`, `.Wait()`, or `Thread.Sleep()` on Task. Always `await`. |
| L06 | **Sanitize HTML before render** | All rich-text content (CKEditor, user input) must pass through `HtmlSanitizer` before rendering to View. `@Html.Raw(unsafeContent)` is violation. |
| L07 | **CSRF token on all forms** | Every `<form method="post">` must have `@Html.AntiForgeryToken()` + `[ValidateAntiForgeryToken]`. |
| L08 | **File upload — 4 mandatory steps** | (1) Extension whitelist server-side; (2) MIME check actual byte stream; (3) Size limit in Service layer; (4) Rename to UUID before saving. Missing any step = violation. |
| L09 | **Auth on all endpoints** | Every Controller action must have: `[Authorize]`, `[RequirePermission("...")]`, or `[AllowAnonymous]` — explicit. |
| L10 | **No browser modal/dialog** | Never use `alert()`, `confirm()`, `prompt()`, SweetAlert, Toastr — use only Custom Modal System. |
| L11 | **Paginate all queries** | All queries returning lists must have `.Take(n)` or pagination (`pageIndex` + `pageSize`). Never load entire table into memory. |
| L12 | **Update memory-log.md** | Every completed task must update `docs/ai-context/memory-log.md`. |
| L13 | **Soft Delete only** | All new modules must implement Soft Delete. Entity must have `IsDeleted (bool)` + `DeletedAt (DateTime?)`. Repository `DeleteAsync()` only sets `IsDeleted = true`. `HasQueryFilter(e => !e.IsDeleted)` mandatory in `AppDbContext`. |
| L14 | **Rate Limiting mandatory** | Every API endpoint must have rate limiting. Login/search/upload/OTP endpoints must use stricter limits. |
| L15 | **No JWT in localStorage** | JWT access tokens MUST NOT be stored in `localStorage` or `sessionStorage`. Use `httpOnly; Secure; SameSite=Strict` cookie. |
| L16 | **No sensitive logging** | Logs MUST NOT contain: password, hash, JWT token, API key, connection string, payment info, ID numbers, health info. Log only userId/requestId. |
| L17 | **Error response hides internals** | `GlobalExceptionMiddleware` MUST return generic message — no `exception.Message`, `StackTrace`, class names, DB table names. Swagger off in Production. |
| L18 | **Input Validation on all DTOs** | Every DTO receiving client input must have `[Required]`, `[MaxLength(n)]`, `[Range(min, max)]`. Controller uses `[ApiController]` or checks `ModelState.IsValid`. |
| L19 | **No Magic Numbers / Magic Strings** | Any literal value with business meaning → `const`, `static readonly`, or `enum`. No `if (status == 2)`, `role == "admin"`, `Take(50)` hardcoded. |
| L20 | **No IDOR** | Every Service method Update/Delete/GetDetail must check: `entity.CreatedBy == currentUserId` or `currentUser.IsAdmin`. `[Authorize]` only checks valid token — not ownership. |
| L21 | **No Open Redirect / No SSRF** | Redirect from user URL → `Url.IsLocalUrl()`. `HttpClient` with URL from user/DB → validate host against allowlist. |
| L22 | **Concurrency Control** | Entities edited by multiple users must have `[Timestamp] byte[] RowVersion`. Catch `DbUpdateConcurrencyException` → return 409 Conflict. |

> **22 Iron Laws have no exceptions.** If user requests violation, AI must refuse, explain the reason, and propose a compliant alternative.

---

## 📋 NAMING CONVENTION FOR FILES

> **Global rule for all .md files created:**
> - ✅ **All documentation files:** `lowercase-with-hyphens.md` (no underscores, no UPPERCASE)
> - ✅ **Config files:** `.env`, `appsettings.json`, `tsconfig.json` (per tool convention)
> - ✅ **Code files:** PascalCase (C#, TypeScript) or camelCase (JavaScript)
>
> **Examples:**
> - ✅ `context-index.md`, `agent-guide.md`, `memory-log.md`, `api-specification.md`
> - ❌ `context_index.md`, `agent_guide.md`, `api_specification.md`

---

## 📌 TASK WORKFLOW DISCIPLINE

> **Project-level task governance** — applies to all tasks

**Every large task (> 1 file, > 30 lines changed) must follow:**

1. **📋 Task Plan** — describe work, scope, list of affected files
   - "I will: [list 3-5 specific actions]"
   - "Affected files: [list of relative paths]"
   - "Before/After comparison: [brief description of changes]"

2. **⏳ Wait for User CONFIRM** — don't implement until user says "OK" / "Proceed"
   - Exception: GF-1→GF-7, BF-A→BF-D are automated workflows; only CONFIRM at **GF-0** and **BF-B Gate**

3. **📝 Output Format** — professional Markdown
   - Clear headings (h2-h3, not h1)
   - Tables for comparison / matrix
   - Code blocks for commands / code snippets
   - Bullet lists for action items
   - `> ⚠️ TODO: [description]` for missing content (user needs to fill)
   - `[VERIFY]` tag for ambiguous requirements (needs user clarification)

4. **🔍 Ambiguity Handling**
   - If requirement is unclear → **STOP, mark `[VERIFY]`, ask user** instead of assuming
   - Example: `[VERIFY] API response format — unclear on pagination schema: Top 10 or offset/limit?`
   - DON'T make up content (hallucinate)

**When to apply:**
- ✅ Session initialization (GF-0, BF-A/B)
- ✅ Create/modify architecture > 1 layer
- ✅ Add new feature
- ✅ Security review with fixes
- ❌ Small bugfixes (< 3 files, < 50 lines)
- ❌ Typos, small documentation updates

---

## 📦 CONTEXT MANAGEMENT — TIERED MANIFEST STRUCTURE

> **Goal:** AI reads only "Source of Truth" (Canonical files), reduce context noise

**Tier Structure:**

```
Tier 1 — Project-level Catalog
  File: docs/ai-context/context-index.md
  Content: Always Read (4 files) + On-Demand (5 files) + Workflow Commands
  Purpose: Single entry point for AI

Tier 2 — Folder-level Status (expanded in context-index.md)
  Table "Always Read" + "On-Demand" adds "Status" column
  Status marks:
    - 🟢 Canonical: Actively maintained, up-to-date → ✅ Read
    - 🟡 Draft: Incomplete, has TODO → ⚠️ Read + [VERIFY]
    - 🔴 Archive: Deprecated, old version → ❌ Skip
```

**Example expanded context-index.md (Tier 2):**

```markdown
## Always Read (per session)

| File | Purpose | Status | Last Updated |
|------|---------|--------|--------------|
| agent-guide.md | WATCH-OUT + DATA RULES | 🟢 Canonical | 2026-04-22 |
| project-overview.md | Overview, Security Notes | 🟢 Canonical | 2026-04-15 |
| memory-log.md | Decisions, lessons learned | 🟢 Canonical | 2026-04-22 |
| engineering-standards.md | Code standards | 🟢 Canonical | 2026-03-26 |

## On-Demand (per task)

| File | When | Status | Last Updated |
|------|------|--------|--------------|
| api-specification.md | Create API endpoint | 🟡 Draft | — |
| data-modeling.md | Add entity/schema | 🟢 Canonical | 2026-03-20 |
| security-guide.md | Review security | 🟢 Canonical | 2026-04-01 |
| test-cases.md | Write tests | 🟢 Canonical | 2026-04-10 |
| development-workflows.md | Build/run local | 🟢 Canonical | 2026-03-26 |
```

**AI Reading Rules:**
1. ✅ Always read Tier 1 (`context-index.md`) first
2. ✅ Use Status column to decide which files to read
3. ✅ If Status = 🟡 Draft → add `[VERIFY]` tag when using its content
4. ❌ Skip Status = 🔴 Archive entirely
5. ⚠️ If needed file is not in context-index.md → report to user, don't guess

**Maintaining Tier 2:**
- Every quarter (3 months) → review Status marks
- When file is finalized → change 🟡 → 🟢
- When file expires → change 🟢 → 🔴 + move to `/docs/archive/`

---

## 🔍 GF-4.5 — SETUP UNDERSTAND-ANYTHING (if needed)

> **Purpose:** Automatically analyze codebase into interactive knowledge graph — helps AI agents understand architecture and dependencies faster.

**Run auto-setup script (PowerShell):**

```powershell
# Navigate to project root
cd <project-root>

# Setup for Claude Code only
./scripts/setup-understand-anything.ps1 -Platform claude-code

# Or all platforms (Copilot, Cursor, Claude Code):
./scripts/setup-understand-anything.ps1 -Platform all

# Enable Git LFS for large projects (> 10MB graphs):
./scripts/setup-understand-anything.ps1 -Platform claude-code -EnableGitLfs
```

**After setup, run in Claude Code:**

```
/understand                   # Build knowledge graph (run once)
/understand-dashboard         # Explore architecture interactively
/understand-diff              # Check impact before committing
```

---

## SESSION TASKS

> **Fill in your specific tasks for this session before running this prompt.**

```
Task 1: [describe first task — e.g., "Initialize documentation structure (GF-2)"]
Task 2: [describe second task — e.g., "Create CLAUDE.md + slash commands (GF-7)"]
Task 3: [describe third task — e.g., "Review security config (L01, L08, L09)"]
```

> ⚠️ TODO: Replace placeholder tasks above with your actual session objectives.

---

## STEP 0 — DETERMINE PROJECT TYPE (MANDATORY FIRST)

> Answer this question before doing anything else.

**Check workspace:**
- Is there actual code in projects (`.cs` files, Migrations, Controllers)?
- Is there old documentation in `docs/`?

| Condition | Project Type | Path |
|-----------|-------------|------|
| Workspace **empty or newly created** — only solution file, no actual code | 🟢 **GREENFIELD** | → Execute **Section 2** below |
| Project **already running** — has code, entities, migrations | 🟠 **BROWNFIELD** | → Execute **Section 3** below |

---

## 🟢 SECTION 2 — GREENFIELD FLOW _(Completely new project)_

> Only execute this section if Step 0 determined: 🟢 GREENFIELD.
> If BROWNFIELD → skip entirely, jump to `## 🟠 SECTION 3`.

---

## GF-0 — INITIAL SETUP (CONFIRM GATE)

1. Present Task Plan to user describing what will be done across GF-1 through GF-7.
2. **WAIT for user confirmation** before proceeding to GF-1.
3. Fill PROJECT INFORMATION section above (user provides project details for new project).

---

## GF-1 — PROJECT SURVEY & MAPPING

1. Read entire workspace directory tree (`list_dir` from root).
2. Read architecture config files:
   - `*.csproj` (all projects) — identify project names, number of layers
   - `Program.cs` or `Startup.cs` — middleware stack, DI, auth mechanism
   - `appsettings.json` — DB name (don't log values), feature flags
   - Any existing `README.md` files
3. Determine: number of projects, architecture (Clean Architecture / Layered / Monolith), actual tech stack.
4. **DO NOT** list Controllers, Entities, Domain Models yet — will fill after user provides business requirements.

### GF-1.S — SECURITY & SECRETS DEEP SCAN (MANDATORY — DO BEFORE CONTINUING)

> This is a safety checkpoint. Complete both sub-steps below and report results before proceeding.

#### GF-1.S.1 — Audit `.gitignore`

Read `.gitignore` at root. Check each item below is listed:

| Item to ignore | Required pattern | Status |
|----------------|-----------------|--------|
| appsettings Production | `**/appsettings.Production.json` | ✅/❌ |
| appsettings Development | `**/appsettings.Development.json` | ✅/❌ |
| .env files | `.env` / `.env.*` | ✅/❌ |
| secrets.json (User Secrets) | `**/secrets.json` | ✅/❌ |
| Build output | `**/bin/` / `**/obj/` | ✅/❌ |
| Upload files | `**/wwwroot/Uploads/` | ✅/❌ |
| IDE / OS files | `.vs/` / `.DS_Store` / `Thumbs.db` | ✅/❌ |

**Mandatory action if missing:** Add missing patterns immediately to `.gitignore`. If sensitive files are already tracked in Git history → warn user immediately with instructions to use `git rm --cached`.

```powershell
# Check if file is currently tracked by Git
git ls-files --error-unmatch **/appsettings.Production.json
git ls-files --error-unmatch .env
# "error: pathspec..." result = NOT tracked (safe)
# Path result = IS TRACKED → must fix immediately
```

#### GF-1.S.2 — Hardcoded Secrets Detection

Scan all source code (`.cs`, `.json`, `.js`, `.ts`, `.razor`, `.html`, `.config`, `.xml`) for suspicious strings using these patterns:

```
Pattern 1: password\s*=\s*"[^"]{4,}"
Pattern 2: connectionString\s*=\s*"[^"]{10,}"
Pattern 3: apiKey\s*[:=]\s*"[^"]{8,}"
Pattern 4: secret\s*[:=]\s*"[^"]{8,}"
Pattern 5: Bearer\s+[A-Za-z0-9\-_]{20,}
```

**Classification:**

| Severity | Condition | Action |
|----------|-----------|--------|
| 🔴 **CRITICAL** | Real secret in file that will be committed (not in `.gitignore`) | **STOP ENTIRE SESSION** — report immediately |
| 🟠 **HIGH** | Real secret in ignored file but still in code | Warn + propose moving to Environment Variables |
| 🟡 **LOW** | Clear placeholder (`[FROM_ENV]`, `YOUR_KEY_HERE`, `xxx`) | Note — not a real secret |
| 🟢 **SAFE** | No suspicious strings found | Confirm safe |

> If **CRITICAL** found, report in this format and do nothing else:
>
> ```
> 🚨 SECURITY ALERT — HARDCODED SECRET DETECTED
> File:    [file path]
> Line:    [line number]
> Pattern: [type — password / apikey / connectionstring]
> Action:  STOP SESSION — User must resolve before continuing
> ```

---

### GF-1.D — DATA INTEGRITY & RELATIONSHIP AUDIT (MANDATORY)

> Goal: AI must fully understand data structure **before writing any CRUD code** — to avoid constraint violations, orphan records, or missing soft delete filters.

#### GF-1.D.1 — Relationship Mapping

Read all Entity classes in Domain layer and `AppDbContext` (all `OnModelCreating` configurations). Build relationship map in this format:

```
RELATIONSHIP MAP — [PROJECT NAME]

One-to-Many:
  Category (1) ──── (*) NewsArticle         [FK: CategoryId, Required]
  Division  (1) ──── (*) User               [FK: DivisionId, Nullable]

Many-to-Many:
  Project (*) ──── (*) Tag                  [Join table: ProjectTag]
  User    (*) ──── (*) Role                 [Join table: UserRole]

Self-referencing:
  Category (1) ──── (*) Category            [FK: ParentId, Nullable — category tree]

Owned / Value Object:
  NewsArticle owns SeoMetadata              [no separate table]
```

**Check danger points:**

| Check Point | Question to answer |
|-------------|-------------------|
| Cascade Delete | When parent entity deleted, are children deleted or Set Null? Data loss risk? |
| Required vs Optional FK | Which FKs are `Required` (NOT NULL)? Creating entity without these → exception. |
| Many-to-Many Join Table | Does join table have additional payload fields? If yes → cannot use implicit many-to-many. |
| Circular Reference | Is there A→B→C→A cycle? If yes → JSON serialization will fail with StackOverflow. |

**Sample output — Danger zones:**
```
⚠️  NewsArticle.CategoryId: Required FK — DO NOT create NewsArticle without existing Category
⚠️  Project → Tags: Many-to-many has DisplayOrder field in join table
    → DO NOT use .Tags.Add(tag), must create ProjectTag entity directly
⚠️  Category.ParentId: Self-referencing nullable
    → When querying recursively, limit depth or use CTE
```

#### GF-1.D.2 — Shadow Logic Discovery (Soft Delete & Audit Trail)

Find and document how the project implements these "implicit" mechanisms. New code **must respect the existing mechanisms**:

**A. Soft Delete — search patterns:**

```powershell
grep_search "IsDeleted"           # flag column
grep_search "DeletedAt"           # timestamp column
grep_search "HasQueryFilter"      # EF Core global filter
grep_search "OnDelete"            # cascade config
grep_search "IgnoreQueryFilters"  # where filter is bypassed
```

Determine and document:

| Question | Answer (from actual code) |
|----------|--------------------------|
| Soft delete uses which column? | `IsDeleted` (bool) / `DeletedAt` (DateTime?) / other |
| Global Query Filter registered? | `modelBuilder.Entity<X>().HasQueryFilter(...)` in which file? |
| Which entities have NO soft delete? | List — hard delete is OK for these |
| Where is `.IgnoreQueryFilters()` called? | List — admin reports / audit queries |
| What does `Delete()` method in Repository do? | Hard delete or set `IsDeleted = true`? |

> If project uses Global Query Filter:
> - **NEVER** write `WHERE IsDeleted = false` manually — already filtered automatically.
> - Only use `.IgnoreQueryFilters()` when intentionally querying deleted records (admin restore, audit).

**B. Audit Trail — search patterns:**

```powershell
grep_search "CreatedAt"
grep_search "UpdatedAt"
grep_search "CreatedBy"
grep_search "UpdatedBy"
grep_search "SaveChangesAsync"    # override to auto-set timestamps?
grep_search "BaseEntity"          # base class with audit fields?
```

Determine and document:

| Question | Answer (from actual code) |
|----------|--------------------------|
| `BaseEntity` has all 4 fields: `CreatedAt`, `UpdatedAt`, `CreatedBy`, `UpdatedBy`? | ✅/❌ — list actual fields |
| `SaveChangesAsync` overridden to auto-set `UpdatedAt`? | ✅/❌ — which file, what mechanism |
| `CreatedBy`/`UpdatedBy` comes from where? | `ICurrentUserService`? `IHttpContextAccessor`? hardcoded? |
| Which entities do NOT inherit `BaseEntity`? | List — for these, set timestamps manually |

**C. Summary — CRUD rules for this project:**

After completing GF-1.D.1 and GF-1.D.2, synthesize into concrete data rules:

```
DATA RULES — [PROJECT NAME] (derived from audit, not a template)

CREATE:
  ✅ Always set [...] when creating new entity (if BaseEntity doesn't auto-set)
  ✅ Validate FK [...] exists before SaveChanges
  ⚠️  For entity [...]: must create join table [...] directly — don't use .Add()

READ:
  ✅ Global filter IsDeleted is active — no manual WHERE needed
  ✅ Use .IgnoreQueryFilters() only for: [list valid cases]
  ⚠️  Relationship [...] has circular reference — use DTO projection

UPDATE:
  ✅ UpdatedAt auto-set in SaveChangesAsync — don't set manually
  ⚠️  Required FK [...] cannot be set to null

DELETE (Soft) — L13 MANDATORY FOR ALL NEW MODULES:
  ✅ Repository.DeleteAsync() sets IsDeleted = true + DeletedAt = DateTime.UtcNow
  ✅ Global Query Filter auto-hides records — SELECT won't return deleted records
  ✅ Use .IgnoreQueryFilters() only for admin restore / audit queries
  ❌ DO NOT use DbContext.Remove() / RemoveRange() — violates L13
  ❌ DO NOT set IsDeleted manually in Service — must go through Repository.DeleteAsync()
  ⚠️  After soft delete, check related entities: cascade soft delete needed?
  ⚠️  Unique constraints on other columns (e.g. Slug, Code): handle collision on restore
```

---

**GF-1 Output:**
- Number of projects, actual tech stack, current architecture
- `.gitignore` audit results (✅/❌ table)
- Secrets scan results (SAFE / list of suspects if any)
- **DO NOT** list entities, controllers, routes, roles yet

---

## GF-2 — CREATE STANDARD DOCUMENTATION STRUCTURE

Create `docs/` folder with this structure (restructure if already exists):

```
docs/
├── README.md
├── restructure-report.md
├── 01-strategy/
│   ├── product-vision.md
│   ├── product-roadmap.md
│   └── pricing-model.md          ← Skip for internal projects
├── 02-requirements/
│   ├── brd.md
│   ├── prd.md
│   ├── user-stories.md
│   ├── user-roles.md
│   └── content-workflow.md
├── 03-engineering/
│   ├── architecture.md
│   ├── api-specification.md
│   ├── data-modeling.md
│   ├── engineering-standards.md
│   └── security-guide.md
├── 04-quality/
│   ├── development-workflows.md
│   ├── test-cases.md
│   └── test-reports/
│       └── README.md
├── 05-support/
│   └── deployment-guide.md
└── ai-context/
    ├── context-index.md             ← Catalog — READ FIRST
    ├── project-overview.md
    ├── agent-guide.md
    └── memory-log.md
```

**File naming rules:**
- Each file starts with: `# [Icon] FILE NAME — [PROJECT NAME]`
- Header: `**Created:** YYYY-MM-DD | **Updated:** YYYY-MM-DD | **Stack:** ...`
- Sections use `> ⚠️ TODO: Must fill in` for all business content
- Exception: technical info read from config (project name, port, DB name, tech stack) — fill immediately

---

## GF-3 — SKELETON CONTENT FOR EACH FILE

> Create **skeleton files** with correct section structure. Use `> ⚠️ TODO: ...` for all business sections. Content only filled when user provides it.

### `docs/ai-context/context-index.md` ← CREATE FIRST

Lightweight catalog file — AI reads this **first** to know entire document structure without crawling directories.

Create with this structure:

- `## Always Read` → Table of 4 files, 4 columns: `File | Description | ~Tokens | Notes`
  - `project-overview.md` | Technical snapshot + Security Notes | ~800 tokens |
  - `agent-guide.md` | WATCH-OUT + DATA RULES | ~600 tokens |
  - `memory-log.md` | Decision history, lessons learned | ~400–1200 tokens (grows) |
  - `engineering-standards.md` | Coding + Security + Test conventions | ~1500 tokens |
- `## On-Demand` → Table of 5 files, 3 columns: `File | When to read | ~Tokens`
  - `architecture.md` | Adding new service/middleware/auth | ~800 tokens |
  - `api-specification.md` | Adding/modifying endpoints | ~1000 tokens |
  - `data-modeling.md` | Adding entities/migrations | ~700 tokens |
  - `user-roles.md` | Changing permissions/roles | ~500 tokens |
  - `security-guide.md` | Auth/upload/sensitive data tasks | ~600 tokens |
- `## Workflow Prompts` → Table of workflows: new-feature, bugfix, run, deploy + file paths
- `## Last Updated` → Date format: YYYY-MM-DD

---

### `docs/ai-context/project-overview.md`
- `## Project Goal` → `> ⚠️ TODO: Must fill in`
- `## Architecture Diagram` → `> ⚠️ TODO: Must fill in`
- `## Components` → Fill ports/paths from config immediately (technical info)
- `## Modules / Features` → `> ⚠️ TODO: Must fill in`
- `## Main Entities` → `> ⚠️ TODO: Must fill in`
- `## Security Notes` → Document **known security risks** specific to this project. Use `[!CAUTION]` callout. Example:
  ```markdown
  > [!CAUTION]
  > - **[Endpoint/feature name] has NO `[Authorize]`** — reason / risk.
  > - **[Field] uses string instead of Guid** → privilege escalation risk.
  > - **[Feature] not yet implemented** — role XYZ may access out-of-scope.
  ```
  If new project with no known risks: `> ✅ No known security issues detected.`
- `## Roadmap` → Short summary (checked/unchecked phases) + cross-ref link to `docs/01-strategy/product-roadmap.md`

---

### `docs/03-engineering/security-guide.md` ← CREATE IMMEDIATELY

> Mandatory for all projects — even when no known issues. AI references this file in every workflow.

```markdown
# 🔐 SECURITY GUIDE — [PROJECT NAME]

**Created:** YYYY-MM-DD
**Updated:** YYYY-MM-DD
**Review Cycle:** Every sprint / after each auth/upload/data feature

## 1. KNOWN SECURITY RISKS (DEBT)

> [!CAUTION]
> Known risks — must read before implementing new features.

| # | Risk | Severity | Status | Notes |
|---|------|----------|--------|-------|
| 1 | _(No known risk yet)_ | — | — | — |

## 2. OWASP TOP 10 — CURRENT MAPPING

| OWASP | Name | Current Mitigation |
|-------|------|--------------------|
| A01 | Broken Access Control | `[RequirePermission]` + `[Authorize]` + RBAC |
| A02 | Cryptographic Failures | HTTPS/HSTS + BCrypt(cost=10) |
| A03 | Injection | EF Core parameterized + HtmlSanitizer |
| A04 | Insecure Design | Workflow state machine + File Scan |
| A05 | Security Misconfiguration | Security headers middleware |
| A06 | Vulnerable Components | `dotnet list package --vulnerable` periodically |
| A07 | Authentication Failures | SSO/BCrypt + session timeout |
| A09 | Security Logging | WorkflowTransition audit trail |
| A10 | SSRF | > ⚠️ TODO: Check all outbound HTTP client calls |

## 3. SECURITY CHECKLIST — BEFORE MERGE

Authentication & Authorization:
- [ ] Every action needing auth has [Authorize] or [RequirePermission]
- [ ] Resource ownership checked in Service (CreatedBy == currentUserId)
- [ ] userId/role taken only from ClaimsPrincipal, not from request body

Input Validation:
- [ ] All DTOs have [Required], [MaxLength], [Range]
- [ ] HTML from rich editor passes through HtmlSanitizer before render
- [ ] No string interpolation to build SQL query

File Upload (L08 — 4 mandatory steps):
- [ ] (1) Extension whitelist enforced server-side
- [ ] (2) MIME type checked via actual byte stream — NOT IFormFile.ContentType
- [ ] (3) Size limit checked in Service layer
- [ ] (4) Renamed to UUID — never use original filename from client

CSRF & Headers:
- [ ] @Html.AntiForgeryToken() on all form POST
- [ ] [ValidateAntiForgeryToken] on all POST actions
- [ ] Security headers middleware not disabled

## 4. INCIDENT LOG

| Date | Description | Severity | Fix | PR/Commit |
|------|-------------|----------|-----|----------|
| — | No incidents yet | — | — | — |
```

---

### `docs/ai-context/agent-guide.md`
- `## Reading Order` → Point to `docs/ai-context/context-index.md` — no need to re-list here
- `## Task Workflow` → Standard flow: Analysis → Planning → Implementation → Verification → Documentation
- `## WATCH-OUT` → `> ⚠️ TODO: Fill in after entities and business logic are established`
- `## Doc Freshness Rule` → Add at end of file:
  ```
  ⚠️ Any docs file not updated in >90 days → VERIFY against actual code before trusting.
  Check: the `Updated:` date in each file's header vs. today's date.
  ```
- `## DATA RULES` → Copy from GF-1.D.2 output when available

### `docs/ai-context/memory-log.md`
Create with:
- Standard header format
- Section `## [YYYY-MM-DD] — Init: Project Initialization` with date and tech stack summary

### `docs/04-quality/development-workflows.md`

Fill immediately (this is pure technical info, not business content):

````markdown
## COMMON COMMANDS

### Build & Run
```powershell
# Build solution
dotnet build [SOLUTION_NAME].slnx

# Run WebApi
cd [WEBAPI_PATH]
dotnet run --launch-profile http

# Run Admin
cd [ADMIN_PATH]
dotnet run
```

### Tests & Reports

```powershell
# Run all tests (MANDATORY before commit — must 100% pass)
dotnet test [SOLUTION_NAME].slnx

# Run + save TRX report to test-reports/ (use before deploy)
dotnet test [SOLUTION_NAME].slnx `
  --logger "trx;LogFileName=test-results-$(Get-Date -Format 'yyyy-MM-dd').trx" `
  --results-directory "docs/04-quality/test-reports"

# Run with code coverage
dotnet test [SOLUTION_NAME].slnx `
  --collect "XPlat Code Coverage" `
  --results-directory "docs/04-quality/test-reports/coverage"

# Run only one module's tests
dotnet test [SOLUTION_NAME].slnx --filter "FullyQualifiedName~TC_NEWS"

# TDD watch mode (auto-rerun when code changes)
dotnet watch test --project [TESTS_PATH]
```

### Database Migrations
```powershell
dotnet ef migrations add [MigrationName] `
  --project [INFRASTRUCTURE_PATH] `
  --startup-project [WEBAPI_PATH]

dotnet ef database update `
  --project [INFRASTRUCTURE_PATH] `
  --startup-project [WEBAPI_PATH]
```

### Git Workflow
```
feature/[ticket-id]-[brief-name]  →  develop  →  main
Commit: type(scope): description
Types: feat | fix | refactor | docs | chore | security | perf
```

## PRE-PUSH CHECKLIST
- [ ] dotnet build — 0 errors, 0 new warnings
- [ ] dotnet test — 100% pass
- [ ] No Console.Write in code
- [ ] No hardcoded secrets
- [ ] appsettings.Production.json NOT in commit
````

### `docs/03-engineering/architecture.md`
- `## Layer Diagram` → Fill ASCII Clean Architecture diagram; middleware details read from `Program.cs`
- `## Dependency Rules` → Fill standard rules (Domain/Application/Infrastructure/Presentation)
- `## Auth Flow` → `> ⚠️ TODO: Must fill in`
- `## CORS Policy` → `> ⚠️ TODO: Must fill in`
- `## Middleware Pipeline` → Fill actual order read from `Program.cs`

### `docs/03-engineering/api-specification.md`
- `## Response Envelope` → Fill standard `{ success, data, message, errors }`
- `## Error Codes` → `> ⚠️ TODO: Must fill in`
- `## Pagination Schema` → Fill standard `pageIndex`, `pageSize`, `totalCount`
- `## Endpoints` → `> ⚠️ TODO: Must fill in`

### `docs/03-engineering/data-modeling.md`
- `## BaseEntity` → Fill standard (Guid Id, **IsDeleted** [L13], **DeletedAt** [L13], CreatedAt, UpdatedAt, CreatedBy, UpdatedBy, **RowVersion** `[Timestamp] byte[]` [L22])
- `## Entities` → `> ⚠️ TODO: Must fill in`
- `## ERD` → `> ⚠️ TODO: Must fill in`
- `## Index Strategy` → `> ⚠️ TODO: Must fill in`

### `docs/02-requirements/user-roles.md`
- `## Roles` → `> ⚠️ TODO: Must fill in`
- `## Permission Matrix` → `> ⚠️ TODO: Must fill in`
- `## Permission Mechanism` → `> ⚠️ TODO: Must fill in`

### `docs/03-engineering/engineering-standards.md`

Fill all 5 sections (these are fixed technical standards, not business-dependent):

**SECTION 1 — CODING STANDARDS**

```
C# Naming:
| Type       | Convention        | Example             |
|------------|-------------------|---------------------|
| Entity     | PascalCase, sing  | NewsArticle         |
| Interface  | I{Name}           | INewsService        |
| Service    | {Entity}Service   | NewsService         |
| DTO        | {Entity}Dto       | NewsDto             |
| Controller | {Entity}Controller| NewsController      |

Architecture Rules:
❌ Domain Layer MUST NOT import EF Core / Infrastructure
❌ Application Layer MUST NOT import Presentation
✅ DI registered in Program.cs
✅ All entities inherit BaseEntity (IsDeleted, DeletedAt, CreatedAt, UpdatedAt, CreatedBy, UpdatedBy)
✅ async/await for all DB operations
✅ Exceptions caught only in GlobalExceptionMiddleware — return generic message, NO exception.Message/StackTrace to client [L17]
✅ XSS: Sanitize on-read, not on-write
✅ Soft Delete: Repository.DeleteAsync() sets IsDeleted flag — NEVER hard delete [L13]
✅ HasQueryFilter(e => !e.IsDeleted) registered for all entities with IsDeleted in AppDbContext [L13]
❌ NEVER call DbContext.Remove() / RemoveRange() — violates L13
✅ Rate Limiting middleware registered in Program.cs — login/search/upload/OTP have separate policies [L14]
✅ JWT token: httpOnly Secure SameSite=Strict cookie — NOT localStorage/sessionStorage [L15]
✅ All client-input DTOs have [Required], [MaxLength], [Range] [L18]
❌ NO magic number/string in business logic — use const/enum/static readonly [L19]
✅ Service method Update/Delete/GetDetail checks ownership (entity.CreatedBy == currentUserId) [L20]
✅ Redirect URL from user through Url.IsLocalUrl() before redirect [L21]
✅ Entities edited by multiple users have [Timestamp] byte[] RowVersion; catch DbUpdateConcurrencyException → 409 [L22]
```

**SECTION 2 — SECURITY STANDARDS (OWASP Top 10)**

Security Code Review Checklist:
```
Authentication & Authorization:
- [ ] Every action needing auth has [Authorize] or [RequirePermission]
- [ ] Resource ownership checked in Service (CreatedBy == currentUserId)
- [ ] userId/role taken only from ClaimsPrincipal, not request body
- [ ] JWT not stored in localStorage or sessionStorage [L15]
- [ ] Cookie set httpOnly + Secure + SameSite=Strict [L15]

Input Validation:
- [ ] All DTOs have [Required], [MaxLength], [Range] [L18]
- [ ] Controller uses [ApiController] or checks ModelState.IsValid [L18]
- [ ] HTML from rich editor passes HtmlSanitizer before render
- [ ] No string interpolation to build SQL query

File Upload (L08 — 4 mandatory steps):
- [ ] (1) Extension whitelist enforced server-side
- [ ] (2) MIME type checked via actual byte stream — NOT IFormFile.ContentType
- [ ] (3) Size limit checked in Service layer
- [ ] (4) Renamed to UUID — never use original filename

CSRF & Headers:
- [ ] @Html.AntiForgeryToken() on all form POST
- [ ] [ValidateAntiForgeryToken] on all POST actions
- [ ] Security headers middleware not disabled

Soft Delete & Data Integrity (L13):
- [ ] New entity inherits BaseEntity — has IsDeleted (bool) + DeletedAt (DateTime?)
- [ ] HasQueryFilter(e => !e.IsDeleted) registered in AppDbContext
- [ ] Repository.DeleteAsync() sets flag — does not remove from DB
- [ ] .IgnoreQueryFilters() only for admin/audit — with explanatory comment

Rate Limiting (L14):
- [ ] Rate limiting middleware registered in Program.cs
- [ ] Login/register/search/upload endpoints have separate stricter policies

Error Handling & Logging (L17 + L16):
- [ ] GlobalExceptionMiddleware returns generic message — no exception.Message/StackTrace
- [ ] Logs don't contain password, token, API key, PII
- [ ] Swagger UI disabled in Production
```

**SECTION 3 — PERFORMANCE STANDARDS**

```
Targets:
| Metric                    | Target    |
|---------------------------|-----------|
| Largest Contentful Paint  | < 2.5s    |
| First Contentful Paint    | < 1.5s    |
| Cumulative Layout Shift   | < 0.1     |
| Total Blocking Time       | < 200ms   |
| Time to Interactive       | < 3.8s    |
| JS Bundle Size (gzip)     | < 200 KB  |
| API P95 response time     | < 500ms   |
| Lighthouse score (mobile) | ≥ 85      |

DB/EF Core Rules:
- [ ] No N+1 query — use Include() or Select() projection
- [ ] AsNoTracking() for all read-only queries
- [ ] Take(n) / pagination — never load entire table
- [ ] SaveChanges() not called inside loop
- [ ] IQueryable<T> from Repository; ToListAsync() only in Service
```

**SECTION 4 — UNIT TEST CONVENTIONS**

```
Framework: xUnit + Moq + FluentAssertions

Naming: TC_{MODULE}_{NNN}_{MethodName}_{Context}_{ExpectedResult}
// Example: TC_NEWS_007_CreateAsync_ValidRequest_ReturnsDto

Pattern: Arrange-Act-Assert (mandatory)
[Fact]
public async Task TC_XXX_Method_Context_Result()
{
    // Arrange
    // Act
    // Assert — use FluentAssertions
}

Mandatory rules:
✅ GlobalUsings.cs contains global using Xunit — don't repeat in each file
✅ CreateSut() creates new SUT instance for each test
✅ Mocks at field level: private readonly Mock<IService> _mock = new();
✅ All tests are async Task — NEVER .Result or .Wait()
❌ Don't hardcode Guid — use Guid.NewGuid()
❌ No Console.Write in tests
```

**SECTION 5 — CODE QUALITY GATES**

```
Security Gate (ANY fail → Block merge):
S1: No hardcoded secret / credential
S2: No raw SQL string interpolation
S3: Input DTO has validation attributes
S4: Controller action has auth attribute
S5: HTML output passed through HtmlSanitizer
S6: Form POST has anti-forgery token
S7: File upload calls 4-step scan before saving [L08]
S8: Logs don't contain sensitive data
S9: New entity has IsDeleted flag + HasQueryFilter registered [L13]
S10: _logger.* doesn't contain password/token/API key/PII [L16]
S11: Error response has no exception.Message/StackTrace [L17]
S12: All new DTOs have annotation/FluentValidation before entering Service [L18]
S13: No magic number/string in logic — use const/enum/static readonly [L19]
S14: dotnet list package --vulnerable → no HIGH/CRITICAL dependency issues
S15: Service Update/Delete has ownership check (entity.CreatedBy == currentUserId) [L20]
S16: Entity with concurrent editors has [Timestamp] RowVersion; DbUpdateConcurrencyException → 409 [L22]

Performance Gate (P1/P2/P4 fail → Block merge):
P1: No N+1 query
P2: AsNoTracking() for GET queries
P3: List endpoints have pagination
P4: No .Result / .Wait()
P5: <img> has loading="lazy" (except above-fold)
P6: External <script> has defer/async
P7: Independent async calls use Task.WhenAll() — no sequential await
P8: No string concatenation in loops — use StringBuilder
P9: No O(n²) nested loops — use Dictionary/HashSet
P10: CSS + JS minified/bundled for production build
P11: Lighthouse score ≥ 85 (mobile) before deploying to Production

Pre-release Gate:
[ ] Unit tests pass 100%
[ ] dotnet list package --vulnerable → no HIGH/CRITICAL
[ ] Security headers correctly configured
[ ] SSL cert valid for ≥ 30 days
[ ] Swagger UI disabled in Production [L17]
[ ] appsettings.Production.json NOT in Git history [L01]
[ ] Lighthouse score ≥ 85 (mobile) [P11]
[ ] Console Errors = 0 on homepage
[ ] Rate limiting registered — login/search/upload have separate policies [L14]
[ ] No DbContext.Remove() / RemoveRange() in new code [L13]
[ ] grep for "_logger.*password|_logger.*token|_logger.*secret" → 0 results [L16]
[ ] No magic number/string in business logic [L19]
[ ] Service Update/Delete has ownership check (entity.CreatedBy == currentUserId) [L20]
[ ] Entities with concurrent editors have [Timestamp] RowVersion; DbUpdateConcurrencyException → 409 [L22]
```

---

## GF-3b — INITIALIZE TEST PROJECT (execute immediately after GF-3)

> New project with no test project → this step is MANDATORY. This is infrastructure, not business logic.

### Step 1 — Check if test project exists

```powershell
# Check for *.Tests.csproj in solution
dotnet sln [SOLUTION_NAME].slnx list | Select-String ".Tests"
# Empty result → doesn't exist → proceed to Step 2
# Has result → already exists → skip GF-3b, go to GF-4
```

### Step 2 — Scaffold test project

```powershell
# Create xUnit project
dotnet new xunit -n [SOLUTION_NAME].Tests --output Backend/[SOLUTION_NAME].Tests

# Add to solution
dotnet sln [SOLUTION_NAME].slnx add Backend/[SOLUTION_NAME].Tests/[SOLUTION_NAME].Tests.csproj

# Add project references
dotnet add Backend/[SOLUTION_NAME].Tests/[SOLUTION_NAME].Tests.csproj reference `
  Backend/[SOLUTION_NAME].Application/[SOLUTION_NAME].Application.csproj
dotnet add Backend/[SOLUTION_NAME].Tests/[SOLUTION_NAME].Tests.csproj reference `
  Backend/[SOLUTION_NAME].Infrastructure/[SOLUTION_NAME].Infrastructure.csproj
```

### Step 3 — Add required packages

```powershell
cd Backend/[SOLUTION_NAME].Tests

dotnet add package Moq
dotnet add package FluentAssertions
dotnet add package Microsoft.EntityFrameworkCore.InMemory
dotnet add package coverlet.collector
```

### Step 4 — Create standard folder structure

```
[SOLUTION_NAME].Tests/
├── [SOLUTION_NAME].Tests.csproj
├── GlobalUsings.cs          ← centralized global usings
├── Services/                ← tests for Application Services
│   └── .gitkeep
├── Controllers/             ← tests for Controllers (if needed)
│   └── .gitkeep
└── Domain/                  ← tests for Domain logic (if any)
    └── .gitkeep
```

```powershell
New-Item -ItemType Directory -Path "Backend/[SOLUTION_NAME].Tests/Services" -Force
New-Item -ItemType Directory -Path "Backend/[SOLUTION_NAME].Tests/Controllers" -Force
New-Item -ItemType Directory -Path "Backend/[SOLUTION_NAME].Tests/Domain" -Force
```

### Step 5 — Create `GlobalUsings.cs`

```csharp
// GlobalUsings.cs — [SOLUTION_NAME].Tests
global using Xunit;
global using Moq;
global using FluentAssertions;
global using Microsoft.EntityFrameworkCore;
```

> Delete the default `UnitTest1.cs` created by `dotnet new xunit`:
> ```powershell
> Remove-Item Backend/[SOLUTION_NAME].Tests/UnitTest1.cs
> ```

### Step 6 — Create placeholder test to verify setup

```csharp
// Services/SetupVerificationTest.cs
/// <summary>
/// Placeholder test to verify test project setup is correct.
/// Delete or replace when real test cases exist.
/// </summary>
public class SetupVerificationTest
{
    [Fact]
    public void TestProject_IsConfiguredCorrectly()
    {
        // Arrange & Act & Assert
        // Placeholder — test project successfully configured
        true.Should().BeTrue();
    }
}
```

### Step 7 — Verify build and test run

```powershell
dotnet build [SOLUTION_NAME].slnx
dotnet test [SOLUTION_NAME].slnx
# Expected: 1 test passed ✅
```

---

## GF-4 — UPDATE `docs/README.md`

Overview index with:
- Directory structure table
- Links to each file (relative path)
- One-line description per file
- Badge: `Updated: YYYY-MM-DD | Stack: ... | Tests: N cases`

---

## GF-5 — CREATE `docs/restructure-report.md`

Full report:
- Before/After comparison table (file count, folder count)
- Old structure (ASCII tree)
- New structure (ASCII tree)
- List of files created / moved / deleted
- Notes: missing items (TODO)

---

## GF-6 — IMPORTANT RULES FOR AI

```
✅ Only write content based on actual code read
✅ Write TODO if information is insufficient
✅ Keep code files unchanged — only create/edit files in docs/ and ai-context/
✅ Each docs file must be readable independently (self-contained)
✅ Use Markdown tables instead of long paragraphs

❌ Don't create fake content (hallucinate) about features that don't exist
❌ Don't commit secrets, connection strings into documentation
❌ Don't modify source code in this session — only docs
❌ Don't skip any step in the sequence above
❌ DO NOT self-fill entities, controllers, API routes, user roles, test cases, ERD
   — these are business content, only fill when user explicitly requests
❌ DO NOT interpret existing code as "business context" to fill docs
   — this session only sets up the framework, business content added in later sessions
```

---

## GF-7 — CREATE AI AGENT FILES (Claude Code specific)

> For Claude Code CLI, create the `CLAUDE.md` and `.claude/commands/` slash commands structure.

### 7.1 — File Structure

```
[ROOT]/
├── CLAUDE.md                        ← Claude Code — auto-read on startup
│
├── .claude/
│   └── commands/
│       ├── run.md                   ← /project:run
│       ├── new-feature.md           ← /project:new-feature
│       ├── bugfix.md                ← /project:bugfix
│       ├── deploy.md                ← /project:deploy
│       ├── security-review.md       ← /project:security-review
│       ├── tdd.md                   ← /project:tdd
│       ├── db-migration.md          ← /project:db-migration
│       └── code-review.md           ← /project:code-review
│
└── docs/ai-context/                 ← SOURCE OF TRUTH (edit here)
    ├── context-index.md
    ├── project-overview.md
    ├── agent-guide.md
    └── memory-log.md
```

### 7.2 — CLAUDE.md (root)

```markdown
# [PROJECT NAME] — AI Agent Instructions

## MANDATORY RULES (violation → refuse and report)

- L01: No hardcoded secrets — use Environment Variables
- L02: No plaintext passwords — always BCrypt.HashPassword()
- L03: No raw SQL interpolation — EF Core LINQ only
- L04: Layer boundary — Domain never imports Infrastructure
- L05: No blocking async — no .Result / .Wait()
- L06: Sanitize HTML before render — HtmlSanitizer
- L07: CSRF token on every form POST
- L08: File upload — 4 steps: (1) extension whitelist; (2) MIME check; (3) size limit; (4) rename UUID
- L09: Auth attribute on every Controller action
- L10: No browser alert/confirm — Custom Modal System
- L11: Paginate all list queries
- L12: Update docs/ai-context/memory-log.md after each task
- L13: Soft Delete — no DbContext.Remove(), use IsDeleted+DeletedAt, HasQueryFilter mandatory
- L14: Rate Limiting — every endpoint, stricter for login/search/upload/OTP
- L15: JWT not in localStorage/sessionStorage — use httpOnly cookie
- L16: No password/token/PII in logs — only userId/requestId
- L17: Error response generic — no exception.Message/StackTrace to client
- L18: All DTOs have [Required],[MaxLength],[Range] — no raw input to Service
- L19: No magic numbers/strings — use const/enum/static readonly for business values
- L20: Service Update/Delete/GetDetail checks ownership (entity.CreatedBy == currentUserId)
- L21: Redirect URL from user via Url.IsLocalUrl(); HttpClient URL from user via host allowlist
- L22: Entities with concurrent editors: [Timestamp] RowVersion; catch DbUpdateConcurrencyException → 409

## PROJECT CONTEXT

- Read `docs/ai-context/context-index.md` FIRST before doing anything
- Coding standards: `docs/03-engineering/engineering-standards.md`
- Task history: `docs/ai-context/memory-log.md`
- WATCH-OUT + DATA RULES: `docs/ai-context/agent-guide.md`

## ARCHITECTURE

```
[Stack: .NET Clean Architecture — Domain / Application / Infrastructure / Presentation]
[Auth: [AUTH TYPE — Azure AD / JWT / Cookie]]
[DB: [DB TYPE] + EF Core + Soft Delete (IsDeleted) + Global Query Filter]
[WebApi: :PORT | Admin: :PORT | Portal: :PORT]
```

## SKILLS

| Skill | Command |
|-------|---------|
| Security Review | `/project:security-review` |
| TDD Workflow | `/project:tdd` |
| DB Migration Safety | `/project:db-migration` |
| Code Review | `/project:code-review` |
| Performance Optimizer | See `.claude/commands/new-feature.md` for performance gates |

## EXTENDED CONTEXT (auto-loaded)

@docs/ai-context/context-index.md
@docs/ai-context/project-overview.md
@docs/ai-context/agent-guide.md
@docs/ai-context/memory-log.md
```

### 7.3 — `.claude/commands/run.md` (slash command: /project:run)

```markdown
# ▶️ WORKFLOW: BUILD & RUN — [PROJECT NAME] (LOCAL DEV)

> Start local environment: WebApi (:[WEBAPI_PORT]), Admin (:[ADMIN_PORT]), Portal (:[PORTAL_PORT]).

## ARCHITECTURE

```
Browser
  ├── Portal      → http://localhost:[PORTAL_PORT]   (Static HTML/JS)
  ├── Admin       → https://localhost:[ADMIN_PORT]   (Razor MVC)
  └── WebApi      → http://localhost:[WEBAPI_PORT]   (REST API)
                        └── LocalDB: [LOCAL_DB_NAME]
```

## STEP 0: CHECK PREREQUISITES

```powershell
dotnet --version   # must be >= [VERSION]
dotnet build [SOLUTION_NAME].slnx
```

Check `appsettings.Development.json` — this file is not committed, must be created manually. See `docs/04-quality/development-workflows.md` for template.

> **WARNING:** NEVER commit `appsettings.Development.json`.

## STEP 1: START WEBAPI

Open Terminal 1:
```powershell
cd [WEBAPI_PATH]
dotnet run --launch-profile http
```
Confirm: `http://localhost:[WEBAPI_PORT]/health` → `{"status":"healthy"}`

## STEP 2: START ADMIN

Open Terminal 2:
```powershell
cd [ADMIN_PATH]
dotnet run
```
Confirm: `https://localhost:[ADMIN_PORT]` → Login page.

## STEP 3: START PORTAL

Open Terminal 3 — use **Live Server** (VS Code extension) or:
```powershell
cd [PORTAL_PATH]
npx http-server -p [PORTAL_PORT]
```
Confirm: `http://localhost:[PORTAL_PORT]` → Homepage.

## TROUBLESHOOTING

| Error | Solution |
|-------|----------|
| Port in use | `netstat -ano \| findstr :[PORT]` → kill PID |
| DB connection fail | Check connection string in `appsettings.Development.json` |
| SSL certificate | `dotnet dev-certs https --trust` |
| Build fail | `dotnet clean` → `dotnet restore` → `dotnet build` |
```

### 7.4 — `.claude/commands/new-feature.md` (slash command: /project:new-feature)

```markdown
# 🚀 WORKFLOW: NEW FEATURE — [PROJECT NAME]

## STEP 0: SYNC & READ DOCS (MANDATORY)

```powershell
git pull origin main
```

Read in order:
1. `docs/ai-context/project-overview.md`
2. `docs/03-engineering/engineering-standards.md`
3. `docs/ai-context/agent-guide.md`
4. `docs/ai-context/memory-log.md`

### 🔒 SECURITY DEBT CHECK (MANDATORY)
Read `docs/ai-context/project-overview.md` → **Security Notes** section.

> **COMMIT BEFORE CODING:** I have read Security Notes.
> This task will **NOT** create additional risk similar to listed items.
> If implementation risks amplifying existing vulnerabilities → **stop and report to User**.

### 🛡️ MANDATORY GUARDRAILS

| # | Rule | Description |
|---|------|-------------|
| G1 | No Plaintext Password | BCrypt only |
| G2 | No Config Tampering | Don't modify appsettings.Production.json |
| G3 | No External Modal | No alert(), confirm(), SweetAlert2 |
| G4 | No Hardcoded Secrets | Environment Variables only |
| G5 | Layer Boundary | Domain never imports Infrastructure |
| G6 | CSRF Protection | AntiForgeryToken on all form POST |
| G7 | File Upload Safety | Whitelist + UUID rename + size limit |
| G8 | No Hardcoded Paths | Use IWebHostEnvironment |

## STEP 1: BUSINESS ANALYSIS & CLARIFICATION

> **Goal:** Understand and interpret business requirements — confirm with User before proceeding.

### 1.1 Summarize the requirement (Restate the Problem)
Answer 3 questions:
- **What does this feature do?** (describe expected behavior from user perspective)
- **Who uses it?** (Admin / Editor / Reviewer / Public User)
- **What business problem does it solve?**

### 1.2 Business Observations
- Impact on Content Workflow (state machine: Draft → Pending → Published → Archived)?
- Relationship with existing modules?
- Implicit business constraints?
- Business risk? (accidental data deletion, info leak, breaking existing workflow?)

### 1.3 Open Questions
| # | Question | Why clarification needed | Temporary assumption (if any) |
|---|----------|--------------------------|-------------------------------|
| Q1 | | | |

### 1.4 Proposed Scope (high level)
- Backend (Domain / Service / API)?
- Admin UI? Portal? Database schema?
- Which docs need updating?

> **STOP — WAIT FOR USER CONFIRMATION** before proceeding to Step 2.

## STEP 2: RESEARCH

1. Confirm technical scope based on business approved in Step 1.
2. `grep_search` related modules in Domain, Application, Infrastructure.
3. Check `docs/03-engineering/api-specification.md` — endpoint already exists?
4. Check `docs/03-engineering/data-modeling.md` — schema changes needed?
5. Assess impact: DB migration? Breaking API change? Which frontends affected?

## STEP 3: SUBMIT PLAN

### 3.1 Files to create / modify

```
[ ] Domain      → Entities/{Entity}.cs
[ ] Application → DTOs/{Entity}Dto.cs, Services/{Entity}Service.cs, Interfaces/I{Entity}Service.cs
[ ] Infra       → Repositories/{Entity}Repository.cs, Data/AppDbContext.cs (add DbSet), Migrations/...
[ ] WebApi      → Controllers/{Entity}Controller.cs
[ ] Admin       → Controllers/{Entity}Controller.cs, Views/{Entity}/...
[ ] Tests       → Services/{Entity}ServiceTests.cs
```

### 3.2 Quality Checklist (7 Groups)

**Group 1 — Clean Architecture**
- [ ] Entity inherits `BaseEntity` (Guid Id, IsDeleted, CreatedAt, UpdatedAt)
- [ ] Service communicates via Interface (`I{Entity}Service`)
- [ ] Repository injected via DI, not `new`-ed directly
- [ ] DI registered in `Program.cs`
- [ ] No magic number/string in logic — use const/enum/static readonly [L19]

**Group 2 — Security**
- [ ] Form has `@Html.AntiForgeryToken()` + `[ValidateAntiForgeryToken]`
- [ ] Action has `[RequirePermission]` or `[Authorize]`
- [ ] Rich text through `HtmlSanitizer` before render
- [ ] Input DTO has full validation (Required, MaxLength, Range)
- [ ] No hardcoded secrets
- [ ] Service Update/Delete/GetDetail has ownership check (entity.CreatedBy == currentUserId) [L20]
- [ ] Redirect URL from user via Url.IsLocalUrl(); HttpClient URL via host allowlist [L21]

**Group 3 — Database**
- [ ] `DbSet<{Entity}>` added to `AppDbContext`
- [ ] Migration reviewed carefully (not dropping important columns)
- [ ] Appropriate indexes for common query patterns
- [ ] Soft delete: use `IsDeleted`, never hard delete
- [ ] Entities with concurrent editors have [Timestamp] RowVersion; catch DbUpdateConcurrencyException → 409 [L22]

**Group 4 — Business Workflow**
- [ ] Entities with status → implement state machine
- [ ] Validate state transitions before changing state
- [ ] Audit trail: log all important transitions

**Group 5 — File Upload**
- [ ] Extension whitelist enforced server-side
- [ ] Renamed to UUID before saving
- [ ] Image resized to max dimensions
- [ ] Path uses `IWebHostEnvironment`, not hardcoded

**Group 6 — Performance**
- [ ] All DB operations use `async/await`
- [ ] `AsNoTracking()` on all read-only queries
- [ ] Use `.Select()` projection instead of loading full entity
- [ ] `dotnet build` — 0 errors, 0 warnings

**Group 7 — Documentation** ← Update AFTER coding
- [ ] `docs/03-engineering/api-specification.md` — new/changed endpoints
- [ ] `docs/03-engineering/data-modeling.md` — schema changes
- [ ] `docs/03-engineering/architecture.md` — new service, middleware, integration
- [ ] `docs/03-engineering/security-guide.md` — auth, sensitive data, OWASP risk
- [ ] `docs/03-engineering/test-cases.md` — new test cases (TC_{MODULE}_{NNN}...)
- [ ] `docs/04-quality/test-reports/README.md` — test run results
- [ ] `docs/ai-context/memory-log.md` — lessons from this task (MANDATORY)

> **STOP — WAIT FOR APPROVAL** before writing any code.

## STEP 4: IMPLEMENTATION

Implement in layer order:
1. **Domain** → Entity, Value Objects
2. **Application** → Interface, DTO, Service
3. **Infrastructure** → Repository, Migration
4. **WebApi** → Controller, route
5. **Admin** → Controller, Views, JS
6. **Tests** → Unit tests `TC_{MODULE}_{NNN}_{Method}_{Context}_{Result}`

After each backend layer: `dotnet build` — must have zero errors before continuing.

## STEP 5: VERIFY

```powershell
dotnet test [SOLUTION_NAME].slnx
```

All tests must pass 100% before proceeding.

## STEP 6: UPDATE DOCUMENTATION (MANDATORY)

Complete all items from Step 3.2 Group 7 checklist. Don't skip any applicable item.
```

### 7.5 — `.claude/commands/bugfix.md` (slash command: /project:bugfix)

```markdown
# 🐛 WORKFLOW: BUG FIX — [PROJECT NAME]

## STEP 0: SYNC & READ DOCS (MANDATORY)

```powershell
git pull origin main
```

Read:
1. `docs/ai-context/project-overview.md`
2. `docs/03-engineering/engineering-standards.md`
3. `docs/ai-context/memory-log.md` — **MANDATORY**: has similar bug occurred before?

### 🔒 SECURITY DEBT CHECK (MANDATORY)
Read **Security Notes** in `project-overview.md`.

> **COMMIT BEFORE FIX:** I have read Security Notes.
> This fix will **NOT** create additional risk or worsen known vulnerabilities.

## STEP 1: DIAGNOSIS

### 1.1 Gather Information
If bug description is insufficient → **STOP AND ASK USER**:
- Which feature / URL?
- Specific user action? (click, submit, page load)
- Error message / HTTP status code?
- Consistent or intermittent?
- Environment: Local / UAT / Production?

### 1.2 Identify Error Type
- 🔴 **Compile Error** → read `dotnet build` output
- 🟠 **Runtime Exception** → read stack trace
- 🟡 **Logic Error** → trace data flow
- 🔵 **UI Bug** → check browser console

### 1.3 Find Root Cause
Answer 3 questions:
1. Where is the bug? (File + Method + specific line)
2. Why? (null ref, wrong condition, missing validation, stale data...)
3. Which convention in `engineering-standards.md` was violated?

### 1.4 Regression Test (mandatory)

```csharp
// Regression: {Brief description} — found {YYYY-MM-DD}
// This test MUST FAIL before fix
[Fact]
public async Task {MethodName}_ShouldNot_{BugBehavior}_When_{Condition}()
{
    // Arrange - reproduce exact conditions that cause the bug
    // Act
    // Assert - verify correct behavior
}
```

## STEP 2: IMPACT ANALYSIS & PROPOSAL

### 2.1 Impact Matrix

| Area | Severity | Description |
|------|----------|-------------|
| Main module | 🔴 | [Module with bug] |
| API Endpoints | 🟠/🟢 | [Breaking change?] |
| Database | 🟠/🟢 | [Migration needed?] |
| Related modules | 🟡/🟢 | [Shared code affected?] |

### 2.2 Proposed Solution
1. **Main approach:** Which file, which section, what to change
2. **Reason:** Addresses root cause, not just symptom
3. **Risk:** Potential side effects after fix

> **STOP — WAIT FOR APPROVAL** before modifying any code.

## STEP 3: IMPLEMENT FIX

Fix with minimal scope. After each change: `dotnet build`.

## STEP 4: VERIFY

```powershell
dotnet test [SOLUTION_NAME].slnx
```

- Regression test just created must **PASS**
- All other tests still **PASS**

## STEP 5: UPDATE DOCUMENTATION (MANDATORY)

- [ ] `docs/03-engineering/test-cases.md` — add regression test entry
- [ ] `docs/04-quality/test-reports/README.md` — add test run results
- [ ] `docs/03-engineering/security-guide.md` — if bug is a security vulnerability
- [ ] `docs/03-engineering/engineering-standards.md` — if bug leads to new guardrail
- [ ] `docs/ai-context/memory-log.md` — root cause, fix, lesson learned (MANDATORY)

Memory log format:
```markdown
## [YYYY-MM-DD] — Fix: {Bug name (short)}
**Root Cause:** [Technical explanation]
**Fix:** [Description of change]
**Lesson:** [Convention / Guardrail to remember]
**Regression Test:** `TC_{MODULE}_{NNN}_...`
**Docs updated:** [list of updated files]
```
```

### 7.6 — `.claude/commands/deploy.md` (slash command: /project:deploy)

```markdown
# 🚀 WORKFLOW: DEPLOY — [PROJECT NAME]

> **WARNING:** Never allow Breaking Changes without prior notice.
> Any DB schema, API endpoint, or config changes must be confirmed in Step 0.

## STEP 0: PRE-FLIGHT CHECK (5 mandatory questions)

| # | Question | Mandatory action if "Yes" |
|---|----------|--------------------------|
| 1 | DB Migration changes schema? | Confirm migration created; prepare DB backup script |
| 2 | API Breaking Change? | Notify team; check Frontend calling that endpoint |
| 3 | `appsettings.json` has new key? | Ensure key exists on server (Env Vars) |
| 4 | Still has `Console.Write` / debug code? | `grep_search "Console.Write"` → must return 0 results |
| 5 | Secret committed? | `git status` — no sensitive files in staging |

Any "Yes" not resolved → **STOP and resolve first**.

## STEP 1: SYNC DOCS (360° DOC SYNC)

Summarize changes this session:
```
feat: [Feature — 1 line]
fix:  [Bug — 1 line]
docs: [Docs updated]
```

Mandatory checklist before commit:
- [ ] `docs/ai-context/memory-log.md` — task log updated (MANDATORY)
- [ ] `docs/03-engineering/api-specification.md` — matches current endpoints
- [ ] `docs/03-engineering/data-modeling.md` — matches current schema
- [ ] `docs/03-engineering/architecture.md` — if middleware/service changed
- [ ] `docs/03-engineering/security-guide.md` — if auth/sensitive data changed
- [ ] `docs/03-engineering/test-cases.md` — test cases list updated
- [ ] `docs/04-quality/test-reports/README.md` — has latest test run entry (MANDATORY before deploy)
- [ ] `docs/ai-context/context-index.md` — if new docs file created in this session

## STEP 2: STAGING

```powershell
git status
git add .
git diff --cached --stat
```

> Confirm `.gitignore` is excluding:
> `**/appsettings.Development.json` | `**/appsettings.Production.json` | `**/bin/` | `**/obj/`

## STEP 3: BUILD CHECK

```powershell
dotnet build [SOLUTION_NAME].slnx
```
- ✅ `Build succeeded` → continue
- ❌ Build error → **STOP** — fix first, never commit broken code

## STEP 3.5: UNIT TEST (MANDATORY — HARD GATE)

> **Hard gate** — cannot skip, cannot ask user. Every commit needs 100% test pass.
> Only exception: pure documentation commit (`*.md` only, no code).

```powershell
dotnet test [SOLUTION_NAME].slnx `
  --configuration Release `
  --logger "trx;LogFileName=test-results-$(Get-Date -Format 'yyyy-MM-dd').trx" `
  --results-directory "docs/04-quality/test-reports"
```

- ✅ 100% pass + report saved → update `docs/04-quality/test-reports/README.md` → proceed
- ❌ ANY test FAIL → **STOP** — fix tests first, never commit

## STEP 4: COMMIT

```powershell
# type(scope): short description <= 72 chars
# Types: feat | fix | refactor | docs | chore | style | perf | security
git commit -m "type(scope): [brief description]"
```

## STEP 5: PUSH & CI/CD

```powershell
git push origin [BRANCH_NAME]
```

### Pre-release Gate (required before Production deploy)
```
[ ] Unit tests pass 100%
[ ] dotnet list package --vulnerable → no HIGH/CRITICAL
[ ] Security headers correctly configured
[ ] SSL cert valid ≥ 30 days
[ ] Swagger UI disabled in Production
[ ] appsettings.Production.json NOT in Git history
[ ] Lighthouse score ≥ 85 (mobile)
[ ] Console Errors = 0 on homepage
```
```

---

## GF-OUTPUT — GREENFIELD SESSION RESULT

After completing GF-1 through GF-7, report:

```
✅ Created:    [list all new files]
✅ Updated:    [list modified files]
⚠️  TODO:      [info needing manual input]
🔧 Agent files: CLAUDE.md + .claude/commands/ (8 slash commands)
📊 Summary:   [3–5 sentences about current project state]
```

---

## ⚡ QUICK DOD — 5 QUESTIONS (CHECK RIGHT BEFORE ENDING SESSION)

> Answer these 5 questions **before** closing the session. Any ❌ → must complete before ending.

| # | Question | ✅ / ❌ |
|---|---------|--------|
| Q1 | `docs/ai-context/memory-log.md` updated with this session? | |
| Q2 | All mandatory docs files in standard structure created? | |
| Q3 | `.gitignore` audit clean + secrets scan has no CRITICAL? | |
| Q4 | Claude Code agent files (CLAUDE.md + .claude/commands/) created? | |
| Q5 | No important TODOs remaining that AI can complete from current code? | |

5/5 ✅ → End session. Under 5/5 → complete remaining items first.

---

## DEFINITION OF DONE — AI SELF-ASSESSMENT (MANDATORY END OF SESSION)

> Before ending session, AI must honestly evaluate its understanding by answering each question below.
> Only valid answers: ✅ **Yes** (with evidence) | ⚠️ **Partial** (with unclear points) | ❌ **No** (with reason).
> Do NOT answer "Yes" without specific evidence from code or documentation read.

### Group 1 — Architecture & Codebase

| # | Question | Answer | Evidence / Notes |
|---|---------|--------|-----------------|
| A1 | Have I read and understood all 4 layers (Domain / Application / Infrastructure / Presentation)? | | |
| A2 | Do I know which file registers DI (`Program.cs`) and middleware pipeline order? | | |
| A3 | Do I know the folder structure of each project (folder names, standard namespace)? | | |
| A4 | Have I identified any Clean Architecture boundary violations (if any)? | | |

### Group 2 — Data & Domain

| # | Question | Answer | Evidence / Notes |
|---|---------|--------|-----------------|
| D1 | Can I draw the full Relationship Map without reading code again? | | |
| D2 | Do I know what fields `BaseEntity` has and whether `SaveChangesAsync` auto-sets timestamps? | | |
| D3 | Do I know which column Soft Delete uses and whether Global Query Filter is active? | | |
| D4 | Can I name at least 2 dangerous relationships (Required FK / Cascade / Circular) to watch out for? | | |

### Group 3 — Auth & Security

| # | Question | Answer | Evidence / Notes |
|---|---------|--------|-----------------|
| S1 | Do I understand the full Auth flow (login → token → middleware → claim → permission check)? | | |
| S2 | Do I know how `[RequirePermission]` is implemented and what permission strings look like? | | |
| S3 | Have I confirmed `.gitignore` audit is clean and secrets scan has no CRITICAL? | | |
| S4 | Do I know what origins and methods CORS policy allows? | | |
| S5 | Do I know where rate limiting is registered and which endpoints need separate policies? | | |
| S6 | Do I know what format `GlobalExceptionMiddleware` returns and confirmed stack trace not exposed? | | |

### Group 4 — Coding Conventions

| # | Question | Answer | Evidence / Notes |
|---|---------|--------|-----------------|
| C1 | Do I know naming conventions (Entity / Interface / Service / DTO / Controller) and can apply immediately? | | |
| C2 | Do I know unit test naming (`TC_{MODULE}_{NNN}_{Method}_{Context}_{Result}`)? | | |
| C3 | Do I know all 22 Iron Laws and can recall at least 10 without reading again? | | |
| C4 | Do I know Git commit convention (`type(scope): description`) and valid types? | | |
| C5 | Do I know Performance Gate P1–P11 and can identify N+1 query, O(n²) in code review? | | |

### Group 5 — Ready for Tasks

| # | Question | Answer | Evidence / Notes |
|---|---------|--------|-----------------|
| R1 | If user requests creating a new entity CRUD right now, do I know how many files and where to create them? | | |
| R2 | Do I know how to run build and tests without asking user? | | |
| R3 | Have I logged this initialization session in `docs/ai-context/memory-log.md`? | | |

### Group 6 — Skill Files

| # | Question | Answer | Evidence / Notes |
|---|---------|--------|-----------------|
| SK1 | Do I know how to trigger security-review skill and when to use it? | | |
| SK2 | Do I know the 3-phase zero-downtime migration pattern and when to apply it? | | |
| SK3 | Do I know the TDD cycle (RED → GREEN → REFACTOR) and 80% coverage gate? | | |
| SK4 | Do I know L20 IDOR ownership check is at which layer and L22 Concurrency uses [Timestamp] how? | | |

---

### Session Conclusion

**✅ Count:** ___ / 26
**⚠️ Count:** ___ (list items + unclear points to clarify)
**❌ Count:** ___ (list + reasons)

**Readiness Status:**

| Threshold | Status | Action |
|-----------|--------|--------|
| 24–26 ✅ | 🟢 **READY** | AI ready for any task |
| 17–23 ✅ | 🟡 **PARTIAL** | AI needs more context before complex tasks — list TODOs |
| ≤ 16 ✅ | 🔴 **NOT READY** | AI needs more reading — list files to read |

---

## 🟠 SECTION 3 — BROWNFIELD FLOW _(Project already running)_

> Only execute this section if Step 0 determined: 🟠 BROWNFIELD.
> If GREENFIELD → already completed in Section 2, skip Section 3 entirely.

---

## BF-A — SCAN _(read-only, no file changes yet)_

> **Goal:** Collect full context from existing documentation and code, record all issues. **Make NO changes during BF-A.**

### BF-A1 — Scan & Classify Existing Documentation

> **Goal:** Eliminate "information noise" — AI gets confused by outdated, conflicting documentation.
> Result: `docs/ai-context/` becomes the **single source of truth** that AI trusts.

#### BF-A1.1 — Scan and classify all existing documentation

Read through all `.md`, `.txt` files in workspace. Classify each file into one of 4 groups:

| Group | Definition | Action |
|-------|-----------|--------|
| 🟢 **KEEP** | Information still accurate, actively used | Keep as-is, update header |
| 🔵 **EXTRACT** | Contains important technical/business decisions but in wrong location | Extract content to `ai-context/`, then mark DEPRECATED |
| 🟡 **MERGE** | Content duplicated in another file | Merge into main file, delete copy |
| 🔴 **DELETE** | Outdated, inaccurate, no longer reflects actual system | Propose deletion (wait for user confirmation) |

**Output format:**

```
DOCUMENT AUDIT REPORT
═══════════════════════════════════════════════════════

🟢 KEEP (keep as-is):
  docs/03-engineering/architecture.md   — Still accurate, updated 2026-03-26
  docs/02-requirements/user-roles.md    — Still accurate

🔵 EXTRACT (extract → ai-context/):
  docs/old/meetings/2025-11-decision.md → Decision to use Azure AD
    → Extract to: ai-context/memory-log.md #"Auth Decisions"
  docs/changelog/2024-legacy.md         → Technical debt notes
    → Extract to: ai-context/memory-log.md #"Known Issues"

🟡 MERGE (merge together):
  docs/backend/api-old.md  ──┐
  docs/frontend/api-v2.md  ──┴→ Merge into: docs/03-engineering/api-specification.md

🔴 DELETE (propose deletion — needs user confirmation):
  docs/old/sprint-1-planning.md    — Sprint ended 2024, no longer relevant
  docs/backend/setup-2023.md       — Setup commands wrong for current .NET version
```

#### BF-A1.2 — Extract important decisions to `memory-log.md`

For each 🔵 EXTRACT file, extract in standard format:

```markdown
## [YYYY-MM-DD estimated] — Decision: {Decision name}
**Context:** [Why this decision was made]
**Decision:** [What was decided specifically]
**Consequences:** [How it affects the current codebase]
**Source:** [Original file name — marked DEPRECATED after extraction]
```

#### BF-A1.3 — Record deletion list _(don't execute yet)_

> **DO NOT delete any files in this step** — this is BF-A (scan). Record list in Scan Report; user confirms and AI executes in **BF-C**.

---

### BF-A2 — Source Code Scan

> Equivalent to GF-1 but focused on **currently running code**: entities, controllers, config, migrations. **Read-only.**

1. Read entire workspace directory tree.
2. Read architecture config files (`*.csproj`, `Program.cs`, `appsettings.json`, existing `README.md`).
3. Read all **Entity classes** in Domain layer and `AppDbContext`.
4. Read all **Controller classes** to list endpoints.
5. Read all **Migration files** to identify actual schema.

#### BF-A2.S — Security & Secrets Scan (MANDATORY)

> Same as GF-1.S — complete fully.

Run `.gitignore` audit table and hardcoded secrets detection with the 5 patterns. Same CRITICAL/HIGH/LOW/SAFE classification and reporting rules apply.

#### BF-A2.D — Data Integrity & Relationship Audit (MANDATORY)

> Same as GF-1.D — complete fully.

- Build Relationship Map with danger points
- Discover shadow logic (soft delete mechanism, audit trail)
- Synthesize DATA RULES specific to this project

---

**BF-A Output:**
- Number of projects, actual tech stack, current architecture
- `.gitignore` audit + secrets scan results
- Full Relationship Map + Danger Points
- Shadow Logic (soft delete, audit trail) + DATA RULES
- List of all Controllers + endpoints (preliminary)
- Document audit classification (KEEP/EXTRACT/MERGE/DELETE)

---

## BF-B — MAP & PLAN

### BF-B — Consolidate & Plan

After completing BF-A (BF-A1 + BF-A2), consolidate all results into 3 blocks:

#### BF-B.1 — Scan Report

```
╔══════════════════════════════════════════════════════════╗
║              BROWNFIELD SESSION SCAN REPORT              ║
╚══════════════════════════════════════════════════════════╝

BLOCK 1 — DOCUMENT AUDIT
────────────────────────────────────────────────────────
🟢 KEEP:     [N files] — [names]
🔵 EXTRACT:  [N files] → memory-log.md
🟡 MERGE:    [N file pairs] → [target files]
🔴 DELETE:   [N files] — [names and reasons]

BLOCK 2 — CODE SCAN
────────────────────────────────────────────────────────
Stack:       [.NET X | SQL Server | Auth type]
Projects:    [N projects] — [names and roles]
Entities:    [N entities] — [names]
Controllers: [N controllers + endpoint count]
Migrations:  [N migrations] — [date range]
Tests:       [N test cases] / [Coverage %]

Architecture Violations:
  [List any Clean Architecture boundary violations found]

BLOCK 3 — SECURITY & DATA AUDIT
────────────────────────────────────────────────────────
.gitignore:     [CLEAN / ISSUES FOUND: ...]
Secrets scan:   [SAFE / CRITICAL/HIGH findings]
Soft Delete:    [IMPLEMENTED / NOT IMPLEMENTED / PARTIAL]
Global Filter:  [ACTIVE / NOT REGISTERED]
Audit Trail:    [COMPLETE / PARTIAL / MISSING]
Concurrency:    [RowVersion PRESENT / MISSING on: ...]
```

#### BF-B.2 — Execution Plan

```
EXECUTION PLAN — PHASE C
════════════════════════

C1 — Delete confirmed files:
  [List files to delete]

C2 — Create standard structure:
  [List folders/files to create]

C3 — Fill content:
  [List files to fill with extracted/actual content]

C4 — Update README files and create reports

C5 — Create AI agent files (CLAUDE.md + .claude/commands/)

C6 — Verify cross-references

Estimated changes: [N files deleted, N created, N modified]
```

---

## ⛔ BF-B GATE — USER CONFIRMATION REQUIRED

> **STOP HERE.** Present Scan Report and Execution Plan to user.
> **DO NOT execute any changes** until user explicitly approves.
>
> Wait for user to say: "Approved", "Proceed", or "OK" with any modifications.
> If user modifies the plan → update Execution Plan and confirm again before proceeding.

---

## BF-C — EXECUTE (only after BF-B Gate approval)

Execute plan in this order:

**C1 — Delete confirmed files**
Delete all 🔴 DELETE files confirmed by user. Do NOT delete any file not in the confirmed list.

**C2 — Flatten & restructure**
Create standard `docs/` folder structure (same as GF-2).

**C3 — Fill content from actual code**
- Create all `ai-context/` files with real content from code scan
- Fill `project-overview.md` Components section from actual ports/config
- Fill `development-workflows.md` with actual commands
- Fill `data-modeling.md` BaseEntity from actual BaseEntity class
- Copy DATA RULES from BF-A2.D into `agent-guide.md`
- Copy Security Notes from scan into `project-overview.md`

**C4 — Update README files and create reports**
- Update `docs/README.md` as documentation index
- Create `docs/restructure-report.md` with before/after comparison

**C5 — Create AI agent files**
Create CLAUDE.md and `.claude/commands/` following GF-7 templates above, filling with actual project values (ports, paths, DB name, auth type).

**C6 — Scan and fix cross-references**
Scan all docs files for references to old file names/paths. Update to match new structure.

---

## BF-D — REPORT

Final report:

```
BROWNFIELD RESTRUCTURING REPORT
═══════════════════════════════

CHANGES MADE:
  ✅ Deleted:    [N files]
  ✅ Created:    [N files]  
  ✅ Modified:   [N files]
  ✅ Agent files: CLAUDE.md + .claude/commands/ (8 slash commands)

DOCUMENTATION STATUS:
  [Table: file | status | content quality]

SECURITY FINDINGS:
  [Summary of security issues found and fixed]

DATA RULES ESTABLISHED:
  [Key rules derived from codebase analysis]

OUTSTANDING TODOS:
  [Items requiring user to provide business content]

READINESS ASSESSMENT:
  [Copy Definition of Done table from GF section and fill in]
```

---

## REFERENCE DOCUMENTATION

For this project's specific documentation:
- **Agent Guide:** [agent-guide.md](../ai-context/agent-guide.md) — WATCH-OUT list + DATA RULES
- **Project Overview:** [project-overview.md](../ai-context/project-overview.md) — Architecture + Security Notes
- **Memory Log:** [memory-log.md](../ai-context/memory-log.md) — Decision history + lessons learned
- **Engineering Standards:** [engineering-standards.md](../03-engineering/engineering-standards.md) — Full coding standards

---END PROMPT---
