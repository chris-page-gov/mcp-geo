# Obsidian vaults for durable AI-assisted research and engineering with one canonical cross-tool instruction standard

## Executive summary

**Verified facts (source-grounded)**  
An entity["people","Andrej Karpathy","computer scientist"] GitHub gist (“LLM Wiki”) describes a workflow where raw sources are ingested into a file-backed collection and an LLM “compiles” them into a structured, interlinked Markdown wiki, with a **schema/instructions document** (explicitly: `CLAUDE.md` for Claude Code or `AGENTS.md` for Codex) guiding conventions and workflows. citeturn19search0  
Obsidian stores notes as **Markdown-formatted plain text files in a “vault” (a local folder)**, supports external editing, automatically refreshes on external changes, and cautions against “vaults within vaults” because links are local to a vault. citeturn16view0  
A formal, tool-facing convention around `AGENTS.md` has emerged as a broadly supported “README for agents” pattern: the AGENTS.md project describes the intent, gives examples, and lists many compatible agents and tools. citeturn11view1turn11view0  
Multiple major assistants/tools now support `AGENTS.md` directly or via first-class integration:
- **OpenAI Codex** reads `AGENTS.md` files (and supports `AGENTS.override.md`) with a documented discovery/precedence chain and a default size cap (32 KiB) for combined project instructions. citeturn4view0turn18view0  
- **GitHub Copilot** supports “agent instructions” via `AGENTS.md` (and allows `CLAUDE.md` or `GEMINI.md` at repo root), with precedence rules across personal/repository/organisation instructions and additional repo-wide/path-specific instruction file mechanisms. citeturn4view1turn4view2  
- **VS Code** documentation describes always-on instructions via `.github/copilot-instructions.md` and `AGENTS.md`, plus settings to control instruction file discovery and locations. citeturn4view3turn14search22  
- **Claude Code** reads `CLAUDE.md` (not `AGENTS.md`) but explicitly recommends importing `AGENTS.md` from `CLAUDE.md` so both tools use the same shared instructions without duplication. citeturn12view1  
- **Gemini CLI** uses `GEMINI.md` context files, supports hierarchical context discovery, and supports configuring the context filename list to include `AGENTS.md`. citeturn13view0turn13view2  
- **Jules** (Google) states it automatically looks for `AGENTS.md` at the root of the repository. citeturn15view0  
- **Windsurf Cascade** documents directory-scoped `AGENTS.md` discovery and automatic scoping based on file location. citeturn15view1  
Cursor’s own materials describe “rules” as Markdown files in `.cursor/rules/`, and Cursor’s docs page headline indicates persistent instructions via “Project, Team, and User Rules, plus AGENTS.md.” citeturn17view0turn7search0  

**Interpretations and inferences (clearly labelled)**  
A vault-centred workflow is a strong foundation for AI-assisted research/engineering when you treat the vault as a **versioned, auditable, local-first knowledge substrate** (Markdown + attachments), and treat agents as **controlled editors/compilers** operating against that substrate. This follows naturally from Obsidian’s folder-of-files design citeturn16view0turn16view2 and Karpathy’s “LLM as maintainer/ compiler” pattern. citeturn19search0  
The emerging multi-vendor support for `AGENTS.md` supports the feasibility of a **single canonical instruction standard**—with small, tool-specific adapters only where a tool insists on a different filename or a different configuration mechanism. citeturn11view1turn4view0turn12view1turn13view0turn4view1turn15view0turn15view1  

**Recommendations (decision-grade)**  
Choose **`AGENTS.md` at vault root as the single canonical vault instruction specification**, and treat any other instruction file (e.g., `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`) as an adapter that delegates to `AGENTS.md` as strictly as each tool allows. This recommendation is grounded in broad direct support (Codex, Copilot, VS Code, Jules, Windsurf; and Cursor signals) plus explicit delegation guidance from Claude Code and Gemini CLI. citeturn4view0turn4view1turn4view3turn12view1turn13view0turn15view0turn15view1turn7search0  
Design `AGENTS.md` to be **short, operational, and safety-first**: front-load non-negotiables within the strictest known limits (e.g., Copilot code review reads only the first 4,000 characters of instruction files) and keep the full file within the more generous but still finite limits (e.g., Codex’s default 32 KiB cap for combined project docs; Claude Code’s guidance that large instruction files reduce adherence). citeturn4view2turn4view0turn12view1  
For fair evaluation across assistants: avoid nested instruction files initially (even if some tools support them), disable personal/organisation-level instruction layers where possible, and use a test pack that explicitly checks what instruction files were loaded and which precedence rules were applied. citeturn4view2turn12view1turn4view0turn13view0  

**Open questions and uncertainties (to verify in hands-on tests)**  
Some tool behaviours are documented but vary by feature surface (for example, GitHub Copilot’s multiple instruction types and feature-specific limits, and VS Code’s experimental `AGENTS.md` support outside workspace root). Expect configuration to be product-surface-specific rather than uniformly applied everywhere. citeturn4view2turn4view1turn4view3  
Cursor’s **full** precedence/merging behaviour for `AGENTS.md` vs `.cursor/rules/` is not consistently accessible from Cursor’s main docs in this browsing session; the safest approach is to treat Cursor’s `AGENTS.md` support as “documented at a high level” and confirm exact precedence in your own smoke tests. citeturn7search0turn17view0  
“Gemini in editor contexts” (Gemini Code Assist) documentation in open sources emphasises IDE actions and agent mode but does not clearly document an `AGENTS.md`/`GEMINI.md`-style always-on project instruction file mechanism; it should be treated as an evaluation unknown unless your environment reveals a supported instruction file feature. citeturn15view2turn15view3  

## What Karpathy, Lex, and others actually said or showed

Karpathy’s “LLM Wiki” gist is explicit about the **architecture** and the **role of instructions**:
- It describes a file-backed wiki that an LLM maintains: you have this “wiki” as a “folder of markdown files” and you can open it in Obsidian, described as the “IDE” and “codebase” for this system. citeturn19search0  
- It distinguishes layers including raw source ingestion and a compiled wiki, and it identifies the **schema/instructions document** as a key artifact: “The schema — a document (e.g. `CLAUDE.md` for Claude Code or `AGENTS.md` for Codex) that tells the LLM how the wiki is structured… conventions… workflows…”. citeturn19search0  
- It proposes special operational files (notably `index.md` and `log.md`) and a workflow where ingesting one source can update multiple wiki pages, plus updating index and appending to the log. citeturn19search0  

A widely circulated secondary write-up reports that entity["known_celebrity","Lex Fridman","podcaster and researcher"] said he uses a similar approach and extends it by generating dynamic HTML visualisations and creating temporary “mini-knowledge-bases” that he loads into an LLM for voice-mode use; the VentureBeat piece quotes this directly (but it is still secondary reporting of an X exchange). citeturn10view0turn9search0  

The Obsidian side of the pattern is well supported by official statements:
- Obsidian’s official help states that notes are Markdown plain text in a local “vault” folder and can be edited by other tools; it also notes Obsidian sync options and warns about “vaults within vaults”. citeturn16view0  
- Obsidian’s official Web Clipper is described as saving web content locally to your vault, and being open source and auditable; Obsidian’s Web Clipper landing page and help emphasise durable Markdown capture and template-driven structured metadata capture into the vault. citeturn16view1turn16view3  

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["Obsidian graph view screenshot","Obsidian vault folder markdown files screenshot","AGENTS.md file example in repository","Obsidian Web Clipper screenshot template"],"num_per_query":1}

## The Obsidian-plus-AI workflow pattern in abstract

**Documented substrate properties (Obsidian vault as “durable memory”)**  
Obsidian’s vault model—Markdown plain text files in a local folder—creates a durable substrate that is:
- **Tool-independent**: files can be edited/managed by other editors and file managers, and the app refreshes on external changes. citeturn16view0  
- **Sync-agnostic**: Obsidian explicitly notes it can sync with Obsidian Sync and third-party services including Git, indicating compatibility with versioned workflows. citeturn16view0  
- **Auditable and reviewable**: by storing knowledge as plain text plus attachments in a normal filesystem, diffs and change review are straightforward in Git; Obsidian even recommends gitignoring layout files that change frequently. citeturn16view0  

**Karpathy’s abstract loop (ingest → compile → query → maintain)**  
Karpathy’s gist can be generalised into a loop suitable for both research and engineering knowledge work:
- **Ingest**: place raw sources into a “raw collection” and have an AI agent process them (summarise, extract entities/concepts, update index/log). citeturn19search0  
- **Compile**: build a structured wiki layer in Markdown that is easier to navigate than raw transcripts/PDF dumps, using links/backlinks and index pages (treating the wiki as the knowledge artefact). citeturn19search0turn10view0  
- **Query and file-back**: answer questions by consulting index + relevant pages, and optionally write new synthesis pages back into the vault (growing a compounding knowledge base). citeturn19search0  
- **Lint/maintain**: periodically scan for contradictions, missing links, out-of-date pages, and structural drift, then update the wiki. citeturn19search0  

**Engineering environment interpretation (where coding fits)**  
A vault can serve as an AI coding assistant’s “engineering environment” if you treat it like a repo/workspace:
- The vault root holds both the **instruction standard** and a stable folder structure for sources, decisions, and generated artefacts.
- Code can live inside the vault (monorepo style) or be linked via additional directories/workspaces; what matters is that instructions, provenance, and the research log live in the vault and remain portable. Obsidian’s design supports multiple vaults (separation by folder), and warns against nesting vaults for link correctness. citeturn16view0  

**Safety and governance constraints surfaced by tooling docs**  
Agentic tools commonly treat instruction files as *guidance in context* rather than enforcement:
- Claude Code notes that `CLAUDE.md` is delivered as context and not guaranteed to be strictly followed; it also distinguishes “settings rules” as enforced by the client, while `CLAUDE.md` “shapes behaviour but is not a hard enforcement layer”. citeturn12view1  
- Claude Code also explicitly warns that its transcripts stored under `~/.claude` are **plaintext and not encrypted at rest**, and that anything passing through tools can be written to disk, motivating conservative vault access rules for sensitive material. citeturn12view0  
- Gemini CLI documents configuration layers, sandboxing options, and best-effort secret redaction for environment variables; this also implies that safe vault operation requires explicit configuration and scoped permissions. citeturn13view2  

## Why a canonical instruction standard matters

**Evidence of fragmentation and convergence**  
The current ecosystem contains many instruction mechanisms: `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/`, and other vendor formats. Tool docs and standards bodies are converging on `AGENTS.md` as a shared, cross-tool convention: the AGENTS.md project explicitly frames itself as a standard Markdown “README for agents” and lists a broad set of compatible tools. citeturn11view1turn11view0  
GitHub Copilot documentation explicitly recognises this plurality: it supports repository-wide instructions in `.github/copilot-instructions.md`, path-specific `.github/instructions/*.instructions.md`, and “agent instructions” in `AGENTS.md` (or `CLAUDE.md`/`GEMINI.md`). citeturn4view1turn4view2  
Claude Code documentation directly advises that if a repository already uses `AGENTS.md`, you should create a `CLAUDE.md` that imports it—explicitly endorsing the idea of a single shared source and per-tool adapters. citeturn12view1  
Gemini CLI documentation/refs describe changing the context filename list to include `AGENTS.md`. citeturn13view0turn13view2  

**Decision rationale for “one canonical standard + adapters”**  
A single canonical vault instruction specification provides:
- **Consistency across assistants**: Each assistant can be evaluated against the same behavioural contract, rather than “whatever its proprietary instruction file happened to contain”. This is directly aligned with the user’s goal of fair comparative evaluation. (Inference supported by the multi-format reality described in Copilot/Claude/Gemini docs.) citeturn4view2turn12view1turn13view0  
- **Lower maintenance and better change control**: A single Markdown file in Git is reviewable, diffable, and auditable, consistent with Obsidian’s file-based approach and Git-friendly vault management guidance. citeturn16view0turn16view2  
- **Portability and resilience to tool churn**: `AGENTS.md` is explicitly designed to be non-proprietary and cross-tool, unlike vendor-specific instruction file names. citeturn11view1turn4view0  

**Counterarguments (and how to mitigate them without abandoning one canonical source)**  
Tool-specific capabilities legitimately exceed what a generic Markdown file can express:
- Claude Code supports imports, topic-scoped rules via `.claude/rules/`, and auto-memory, which can reduce context noise and improve adherence. citeturn12view1turn12view0  
- GitHub Copilot supports path-scoped `.instructions.md` files with `applyTo` frontmatter and separate repository-wide instructions, plus feature-specific limits (e.g., code review cap). citeturn4view1turn4view2turn4view3  
- Codex supports `AGENTS.override.md`, global vs project scope discovery, and skills (`SKILL.md`) for progressive disclosure. citeturn4view0turn18view1  

Mitigation strategy consistent with “one source of truth”: keep `AGENTS.md` as the canonical **behavioural contract**, and treat tool-specific features as *implementation details* used only when they can be made to **delegate** to canonical content (imports, references, symlinks) or when they are separate artefacts (skills/workflows) that do not compete as the main behavioural specification. citeturn12view1turn4view0turn18view1  

## Canonical instruction standard and per-tool adapters

### Canonical standard choice and justification

**Canonical filename**: `AGENTS.md`  
**Canonical location**: vault root (same directory level as `.obsidian/`), and—if the vault is also treated as a repo/workspace—repo root. This aligns with Codex’s and Jules’s root-based discovery, and with the AGENTS.md convention’s “README for agents” intent. citeturn4view0turn15view0turn11view1turn16view0  

**Why `AGENTS.md` rather than `CLAUDE.md` or `GEMINI.md` as canonical**  
- Codex is explicitly guided by `AGENTS.md` files, with documented discovery and precedence. citeturn4view0turn18view0  
- Copilot supports `AGENTS.md` as agent instructions, and VS Code documentation explicitly positions `AGENTS.md` as useful “if you work with multiple AI agents”. citeturn4view1turn4view3  
- Claude Code can import `AGENTS.md` from `CLAUDE.md` without duplication, making `AGENTS.md` a viable shared canonical source even when Claude requires a different entrypoint filename. citeturn12view1  
- Gemini CLI can be configured to treat `AGENTS.md` as a context file name, avoiding duplication. citeturn13view0turn13view2  
- Google’s Jules states it looks for `AGENTS.md` at repo root. citeturn15view0  

### Canonical document structure and required sections

The AGENTS.md project explicitly states there are no required fields; it is standard Markdown. citeturn11view1turn11view0  
However, for **consistent evaluation across tools**, the canonical vault spec should have a predictable structure.

**Required sections (recommended)**  
1. **Purpose and scope**: what the vault is, what the agent is allowed to do, and what “done” means.  
2. **Safety and change control**: deletion/renames policy, protected areas, approval expectations, and “do no harm” defaults.  
3. **Vault map**: folder structure, naming conventions, and where generated content must go.  
4. **Research protocol**: source ingestion rules; provenance expectations; quoting and citation expectations inside the vault.  
5. **Engineering protocol**: how to run tests, how to update code + docs, how to structure commits/PRs for vault changes.  
6. **Uncertainty protocol**: how the agent should behave when uncertain (ask, log, propose options).  

**Optional sections (recommended)**  
- **Tool-agnostic workflows** (e.g., ingest/query/lint workflows inspired by Karpathy). citeturn19search0  
- **Performance and scale** (limits, index/log expectations).  
- **MCP / external tools policy** (if used).  

### Rules for scope, precedence, and avoiding instruction conflict

Because tools differ in how they merge/precede instructions, the canonical standard must be conservative:

- **Single-file canonical policy (recommended for fairness):** keep *exactly one* `AGENTS.md` at vault root during cross-tool evaluation, to avoid behavioural divergence caused by tools’ different “nearest-wins” vs “merge chain” semantics. (Rationale: Copilot says “nearest AGENTS.md takes precedence”, Codex merges multiple, Windsurf auto-scopes.) citeturn4view0turn4view1turn15view1  
- **If folder-level overrides are needed (optional, not recommended for first evaluation):** define them as *derived artefacts* generated from the canonical file, not hand-maintained competing sources. Codex and Windsurf both support multiple `AGENTS.md` files with location-based scoping, but this introduces drift risk unless generation/validation is automated. citeturn4view0turn15view1turn11view1  
- **Hard limits drive structure:**  
  - Keep the **top “non-negotiables” block** within the strictest widely-documented limit: Copilot code review reads only the first 4,000 characters. citeturn4view2  
  - Keep the entire file comfortably below Codex’s default combined-instructions cap (32 KiB) to avoid truncation. citeturn4view0  
  - Keep instruction density low because Claude Code guidance notes long files consume context and reduce adherence. citeturn12view1  

### Canonical spec draft artefact

**A. Canonical spec draft (`AGENTS.md`)**  
Copy-paste production draft (tool-agnostic, safe-by-default, vault-oriented):

```markdown
# AGENTS.md — Canonical vault instruction standard

## Purpose
This vault is a durable, file-based research + engineering workspace (Markdown + attachments) intended to be safe under Git.
Your job is to help a human operator do long-running knowledge work: research, synthesis, coding, documentation, and maintenance.

## Scope and precedence
- This file (AGENTS.md at vault root) is the single source of truth for agent behaviour in this vault.
- If another tool requires another instruction file name, that file must act only as an adapter that delegates to this AGENTS.md.
- When a user prompt conflicts with this file, stop and ask which instruction to follow.

## Non-negotiables (safety)
- Default to READ-ONLY until you have a written plan and the user has approved it.
- Never delete or rename files unless the user explicitly asks you to, or the plan explicitly includes it and the user approves.
- Never rewrite or reorganise the vault “for tidiness”.
- Never move personal notes into generated areas or vice versa.
- Do not modify AGENTS.md unless the user explicitly asks. If asked, propose a small diff first.

## Vault map (authoritative)
- `inbox/` — temporary capture and triage (raw notes, quick dumps, clip drops)
- `sources/` — immutable sources (web clips, PDFs, transcripts, datasets). Treat as write-once except metadata fixes.
- `notes/` — human-authored notes (analysis, reflections, working notes)
- `wiki/` — compiled/maintained knowledge pages (agent may update with care)
- `projects/` — code, experiments, prototypes, scripts
- `logs/` — append-only operational logs and evaluation evidence
- `generated/` — scratch outputs, interim artefacts, agent-generated drafts awaiting review

## Writing rules (Markdown + Obsidian)
- Use Markdown that renders in Obsidian, VS Code, and GitHub.
- Use Obsidian wiki-links `[[Like This]]` for internal references.
- Prefer relative links for attachments and local files.
- Use YAML frontmatter at the top of notes that are meant to persist.

## Provenance and citations inside the vault
- Any claim that comes from a source must include a SOURCES section with links to the source note(s) in `sources/`.
- When summarising a source, quote sparingly and preserve key metadata (title, author, date, original URL, access date).

## Core workflows (Karpathy-style loop, adapted)
### Ingest workflow (a new source arrives)
1. Put the raw item in `sources/` (or link to it) and create/complete a source note.
2. Create or update a summary page in `wiki/` (one page per source).
3. Update relevant entity/concept pages in `wiki/`.
4. Add/repair wiki-links between related pages.
5. Update `wiki/index.md` (catalogue entries) and append to `logs/operations.md`.

### Query workflow (answer a question)
1. Read `wiki/index.md` first; then open only the most relevant pages.
2. Synthesize an answer.
3. If valuable, save a new synthesis note in `notes/` or `wiki/synthesis/` (ask which).

### Lint/maintenance workflow (periodic)
- Check for broken links, duplicate pages, stale summaries, contradictions, and missing index entries.
- Propose fixes as a plan; apply only after approval.

## Engineering workflow rules
- For any code change: add/update tests where appropriate, run relevant checks, and record what you ran in `logs/operations.md`.
- Keep diffs small and reviewable.
- Prefer adding new files over rewriting existing ones unless asked.
- Use Git branches and pull requests where available; otherwise use small commits with clear messages.

## When uncertain
- Ask clarifying questions early.
- Offer options with trade-offs.
- If blocked, write an “Open questions” note in `logs/open-questions.md`.

## Do not touch (protected areas)
- `.obsidian/` (settings) unless asked explicitly.
- `notes/` human-authored content, unless asked explicitly.
- Any file marked with frontmatter `protected: true`.
```

### Adapter examples (minimal, delegation-first)

**B. Minimal `CLAUDE.md` adapter (Claude Code)**  
This pattern is explicitly recommended by Claude Code docs (import `AGENTS.md` with `@AGENTS.md`). citeturn12view1  

```markdown
@AGENTS.md

## Claude Code-specific notes (optional)
- If you propose edits, start with a plan and ask for approval before writing.
```

**C. Minimal `GEMINI.md` adapter (if you cannot or do not want to change Gemini CLI settings)**  
Gemini CLI supports imports with `@file` syntax. citeturn13view0  

```markdown
@AGENTS.md
```

**D. Minimal `.github/copilot-instructions.md` adapter (GitHub Copilot / VS Code Copilot Chat)**  
Unlike Claude/Gemini, Copilot instruction files are not documented as having `@imports`; it does support multiple instruction file types and `AGENTS.md` directly, so the best adapter is often “no adapter”. citeturn4view1turn4view3  
If you must keep `.github/copilot-instructions.md` for feature coverage, use a short statement that points to `AGENTS.md`:

```markdown
# Copilot instructions (adapter)
Follow the canonical instructions in ../AGENTS.md.
If these instructions conflict, AGENTS.md wins.
```

**E. Minimal `.gemini/settings.json` (Gemini CLI) to make `AGENTS.md` canonical**  
Gemini CLI supports configuring context file names to include `AGENTS.md`. citeturn13view0turn13view1turn13view2  

```json
{
  "context": {
    "fileName": ["AGENTS.md"]
  }
}
```

**F. Minimal “do nothing” adapters where AGENTS.md is native**  
Codex reads `AGENTS.md` directly. citeturn4view0turn18view0  
Jules reads `AGENTS.md` at repo root. citeturn15view0  
Windsurf reads `AGENTS.md` and scopes it by location. citeturn15view1  

## How to configure each AI assistant to use the canonical vault standard

Verified as of **14 April 2026** (Europe/London). Tool behaviour is subject to change; always run the smoke tests below after upgrading any tool. citeturn4view0turn4view2turn12view1turn13view2turn4view3turn15view0turn15view1  

### OpenAI Codex (Codex CLI / Codex app)

1. **Canonical file assumed**: `AGENTS.md` at project (vault) root. citeturn4view0turn18view0  
2. **Directly reads canonical file**: Yes; Codex reads `AGENTS.md` before doing work. citeturn4view0turn18view0  
3. **Adapter needed**: No.  
4. **Supported file names and locations**:  
   - Global: `~/.codex/AGENTS.md` or `~/.codex/AGENTS.override.md` (or `CODEX_HOME` equivalent). citeturn4view0  
   - Project: scans from project root down to CWD, per-directory choosing `AGENTS.override.md` first then `AGENTS.md`. citeturn4view0  
5. **Precedence rules**: 
   - `AGENTS.override.md` beats `AGENTS.md` at the same directory level; deeper (closer-to-CWD) instructions appear later and override earlier guidance; skips empty files; stops when combined size reaches `project_doc_max_bytes` (32 KiB default). citeturn4view0  
6. **Minimal setup steps**:  
   - Place `AGENTS.md` at vault root.  
   - Ensure no unintended global `~/.codex/AGENTS.md` content is influencing evaluation (either remove/empty it or record it as part of the test conditions). citeturn4view0  
7. **Smoke test**: Run a prompt such as “Summarise the active instruction chain and quote the non‑negotiables.” Codex docs show a similar verification command pattern. citeturn4view0  
8. **Known limitations**: Combined instruction cap (32 KiB default). citeturn4view0  
9. **Safest workflow for a live vault**: Use an approval mode / plan-first approach; treat `AGENTS.md` as constraints and keep it short to avoid truncation and drift. (Codex is built to run commands and edit files; treat as high‑impact.) citeturn18view0turn4view0  
10. **Git/review workflow**: Use branches/PR review outside the agent where possible; Codex emphasises reviewability and evidence. citeturn18view0  
11. **Fair evaluation suitability**: High, because it natively uses `AGENTS.md` and documents discovery/precedence. citeturn4view0  

### Claude / Claude Code

1. **Canonical file assumed**: `AGENTS.md` at vault root.  
2. **Directly reads canonical file**: No; Claude Code reads `CLAUDE.md`, not `AGENTS.md`. citeturn12view1  
3. **Exact adapter required**: `CLAUDE.md` that imports `AGENTS.md` using `@AGENTS.md`. This is explicitly recommended in Claude Code docs. citeturn12view1  
4. **Supported instruction file names and locations**:  
   - `CLAUDE.md` at project root or `./.claude/CLAUDE.md`. citeturn12view1  
   - User/global `~/.claude/CLAUDE.md`. citeturn4view3turn12view0turn12view1  
   - Local override `CLAUDE.local.md` at project root (private). citeturn4view3turn12view1  
5. **Precedence/merging**: Claude Code walks up the directory tree loading `CLAUDE.md` and `CLAUDE.local.md` and concatenates them; local appended after project in each directory; subdirectory CLAUDE files are loaded on demand when working in that subtree. citeturn12view1  
6. **Minimal setup steps**:  
   - Create `AGENTS.md` at vault root.  
   - Create `CLAUDE.md` at vault root with a single line `@AGENTS.md` (plus optional Claude-specific additions). citeturn12view1  
7. **Smoke test steps**: Use `/memory` to confirm which `CLAUDE.md` files loaded and whether the import expanded. citeturn12view0turn12view1  
8. **Known limitations**:  
   - Claude Code states instruction files are context, not guaranteed enforcement; contradictory rules may be applied arbitrarily; keeping files concise improves adherence. citeturn12view1  
   - Claude Code stores transcripts and tool results as plaintext under `~/.claude`; secrets exposure risk. citeturn12view0  
9. **Safest live-vault workflow**:  
   - Use permission rules / deny-list sensitive paths; prefer plan-first; keep agent-generated output separated (for example in `generated/`) and merge by review. citeturn12view0turn12view1  
10. **Git/review workflow**: Branch + PR review for vault mutations; keep `notes/` and `.obsidian/` protected unless explicitly requested. (Protection rationale grounded in Obsidian’s configuration folder behaviour.) citeturn16view0turn12view1  
11. **Fair evaluation suitability**: High if you standardise on the adapter pattern and ensure global `~/.claude/CLAUDE.md` is empty/controlled. citeturn12view1turn12view0  

### Cursor

1. **Canonical file assumed**: `AGENTS.md` at vault/project root.  
2. **Directly reads canonical file**: Cursor materials indicate support for `AGENTS.md` alongside rules systems. citeturn7search0turn17view0  
3. **Adapter needed**: Usually no (use `AGENTS.md` directly).  
4. **Supported instruction/config mechanisms (documented in Cursor materials)**:  
   - Rules as Markdown files in `.cursor/rules/` (Cursor blog). citeturn17view0  
   - Cursor docs headline indicates “Project, Team, and User Rules, plus AGENTS.md”. citeturn7search0  
5. **Precedence rules**: Not fully verifiable from Cursor primary docs in this session; treat precedence as a smoke-test requirement. citeturn7search0turn17view0  
6. **Minimal setup steps**:  
   - Create `AGENTS.md` at vault root with your canonical instructions.  
   - Avoid `.cursor/rules/` in the evaluation vault initially to keep one instruction source (unless required for Cursor-only capabilities). citeturn17view0turn11view1  
7. **Smoke test steps**: Ask Cursor agent to summarise what standing rules it is following and to cite the file it used; then run a small, safe task (create a new note in `generated/`).  
8. **Known limitations**: Cursor supports plans and saves plan artefacts under `.cursor/plans/` if you “Save to workspace”. Treat these as generated artefacts and consider gitignoring or reviewing them explicitly. citeturn17view0  
9. **Safest workflow for a live vault**: Use Plan Mode (Cursor documents Plan Mode and approval before building), store plans as artefacts, review diffs carefully. citeturn17view0  
10. **Git/review workflow**: Use PR-style reviews for large changes; keep generated plans and logs separated to avoid contaminating human notes. citeturn17view0turn16view0  
11. **Fair evaluation suitability**: Medium-high, provided you confirm how Cursor prioritises `AGENTS.md` vs `.cursor/rules/` in your installed version. citeturn7search0turn17view0  

### Gemini CLI

1. **Canonical file assumed**: `AGENTS.md` at vault root.  
2. **Directly reads canonical file**: Default context filename is `GEMINI.md`, but Gemini CLI supports configuring context file names to include `AGENTS.md`. citeturn13view0turn13view2  
3. **Exact adapter/setting needed**: Prefer settings-based delegation: `.gemini/settings.json` with `"context": {"fileName": ["AGENTS.md"]}`. citeturn13view2turn13view0turn13view1  
4. **Supported locations and precedence**:  
   - Settings live at `~/.gemini/settings.json` (user) and `your-project/.gemini/settings.json` (workspace), with workspace overriding user. citeturn13view1turn13view2  
   - Context file hierarchy described as global `~/.gemini/GEMINI.md`, then workspace/parent searches, then just-in-time context discovery; files are concatenated. citeturn13view0  
5. **Minimal setup steps**:  
   - Create `AGENTS.md` at vault root.  
   - Create `.gemini/settings.json` at vault root specifying `AGENTS.md` as the only context file name. citeturn13view2turn13view0  
6. **Smoke test steps**: Use `/memory show` (Gemini CLI docs) to inspect the concatenated memory and confirm `AGENTS.md` is included. citeturn13view0  
7. **Known limitations**: Gemini CLI is configurable across many layers (system/user/project/env/CLI args), so evaluation must record which layers were active. citeturn13view2  
8. **Safest workflow for a live vault**: Use plan/read-only modes where available; configure sandboxing where appropriate; treat file modification as high-impact and review diffs. citeturn13view2turn13view1  
9. **Git/review workflow**: Keep `.gemini/` as a tool adapter directory; review on PR; avoid mixing with human knowledge notes.  
10. **Fair evaluation suitability**: High if you lock down settings layers and ensure only `AGENTS.md` is loaded. citeturn13view2turn13view0  

### GitHub Copilot (and Copilot “coding agent” features)

1. **Canonical file assumed**: `AGENTS.md` at vault root.  
2. **Directly reads canonical file**: Yes for “agent instructions”; Copilot docs state you can create one or more `AGENTS.md` anywhere in the repo and “the nearest `AGENTS.md` in the directory tree will take precedence”. citeturn4view1  
3. **Adapter needed**: Often no; but feature surfaces may rely on `.github/copilot-instructions.md` or `.github/instructions/*.instructions.md`. citeturn4view1turn4view2  
4. **Supported instruction file names and locations**:  
   - `.github/copilot-instructions.md` (repo-wide). citeturn4view1turn4view2  
   - `.github/instructions/**/*.instructions.md` with `applyTo` frontmatter (path-scoped). citeturn4view1turn4view2  
   - `AGENTS.md` anywhere; alternatively root `CLAUDE.md` or `GEMINI.md`. citeturn4view1turn4view2  
5. **Precedence**: Personal > repository (path-scoped > repo-wide > agent instructions) > organisation. citeturn4view2  
6. **Minimal setup steps for “one canonical standard”**:  
   - Create root `AGENTS.md`.  
   - Avoid adding `.github/copilot-instructions.md` and `.github/instructions/` during evaluation unless necessary; if needed, make them minimal adapters pointing to `AGENTS.md`. citeturn4view1turn4view2  
7. **Smoke test steps**: Ask Copilot to repeat the “non-negotiables” from the instruction file and specify which instruction mechanism it used.  
8. **Known limitations**: Copilot code review reads only the first 4,000 characters of any custom instruction file (limit does not apply to some other Copilot features). citeturn4view2  
9. **Safest workflow for a live vault**: Ensure personal and org instructions are empty or documented; keep canonical `AGENTS.md` short at the top; protect the vault via git review. citeturn4view2turn16view0  
10. **Fair evaluation suitability**: High, but only if you standardise which Copilot surface you are testing (GitHub.com chat vs VS Code vs code review) and record instruction layers and limits. citeturn4view2turn4view1turn4view3  

### VS Code (agent/custom instruction workflows)

1. **Canonical file assumed**: `AGENTS.md` at workspace (vault) root.  
2. **Directly reads canonical file**: VS Code documents always-on instructions via `AGENTS.md` and `.github/copilot-instructions.md`. citeturn4view3turn14search22  
3. **Adapter needed**: Usually no if VS Code is configured to load `AGENTS.md` (and you avoid other instruction sources).  
4. **Supported locations**:  
   - `.github/copilot-instructions.md` at workspace root. citeturn4view3  
   - `AGENTS.md` at root (and in subfolders experimentally). citeturn4view3turn4view1  
   - `.github/instructions/` for `.instructions.md` files, controlled by `chat.instructionsFilesLocations`. citeturn4view3  
   - Claude format files: `CLAUDE.md` in workspace root or `.claude/` etc (VS Code compatibility support). citeturn4view3  
5. **Precedence**: VS Code docs indicate multiple instruction types are provided; GitHub docs give a precedence ordering for Copilot contexts, and VS Code also discusses enabling/disabling discovery by setting. citeturn4view2turn4view3turn14search22  
6. **Minimal setup steps**:  
   - Create `AGENTS.md` at vault root.  
   - Ensure VS Code is set to discover it; if you want to prevent unexpected instruction loading, restrict `chat.instructionsFilesLocations` to only the workspace-level directories you intend. citeturn4view3  
7. **Smoke test steps**: Use `/init` or “Chat Instructions” UI to confirm it discovered `AGENTS.md`; then ask the assistant to print the effective instructions. VS Code docs describe an `/init` flow that discovers instructions files including `AGENTS.md`. citeturn14search22turn4view3  
8. **Known limitations**: Support for `AGENTS.md` outside workspace root can be off by default (per GitHub docs note); treat as configuration-dependent. citeturn4view1  
9. **Safest live-vault workflow**: Use file-based instructions, keep them concise, and lock instruction search paths; prefer plan-first and review diffs via Git. citeturn4view3turn16view0  
10. **Fair evaluation suitability**: High if you standardise settings, disable org/personal instructions layers, and capture the effective instruction set for each test run. citeturn4view3turn4view2  

### Jules (Google)

1. **Canonical file assumed**: `AGENTS.md` at repo root.  
2. **Directly reads canonical file**: Yes; Jules states it automatically looks for `AGENTS.md` in the root of your repository. citeturn15view0  
3. **Adapter needed**: No.  
4. **Limitations / scope**: Jules documentation presented here is concise; validate in practice how much of `AGENTS.md` it uses and whether it supports nested files. citeturn15view0  

### Windsurf Cascade

1. **Canonical file assumed**: `AGENTS.md` (or `agents.md`) at workspace root.  
2. **Directly reads canonical file**: Yes; Windsurf documents discovery and scoping of `AGENTS.md`, including auto-scoping for subdirectories. citeturn15view1  
3. **Adapter needed**: No, but Windsurf encourages multiple directory-scoped files; for “single source of truth” evaluation, keep one root file only. citeturn15view1turn11view1  

### Comparison matrix

| Tool | Reads `AGENTS.md` directly | Minimal adapter pattern to preserve one source of truth | Precedence/scoping (documented) | Divergence risk vs canonical | Suitable for fair evaluation (with one root `AGENTS.md`) |
|---|---|---|---|---|---|
| Codex (OpenAI) | Yes citeturn4view0turn18view0 | None | Hierarchical chain + override files + size cap citeturn4view0 | Low if globals controlled | High |
| Claude Code | No citeturn12view1 | Root `CLAUDE.md` with `@AGENTS.md` citeturn12view1 | Concatenation of discovered `CLAUDE.md` + `.claude/rules/` options citeturn12view1 | Medium if global CLAUDE files exist | High if globals controlled |
| GitHub Copilot | Yes (agent instructions) citeturn4view1turn4view2 | Prefer none; optionally minimal `.github/copilot-instructions.md` pointer | Personal > repo > org; repo has multiple mechanisms; nearest AGENTS wins citeturn4view2turn4view1 | Medium (multiple layers + feature limits) | High with strict controls |
| VS Code Copilot Chat | Yes citeturn4view3 | Prefer none; lock down instruction locations via settings | Multiple instruction sources; configurable discovery paths citeturn4view3turn14search22 | Medium (settings variance) | High with settings pinned |
| Gemini CLI | Configurable citeturn13view0turn13view2 | `.gemini/settings.json` set `context.fileName=["AGENTS.md"]` | Layered config + hierarchical context files citeturn13view2turn13view0 | Medium (many layers) | High if layers pinned |
| Cursor | Indicated yes citeturn7search0turn17view0 | Prefer none; avoid `.cursor/rules/` for evaluation | Rules in `.cursor/rules/` (documented); AGENTS support signalled citeturn17view0turn7search0 | Medium (precedence to verify) | Medium-high with smoke tests |
| Jules (Google) | Yes (root) citeturn15view0 | None | Root lookup described citeturn15view0 | Unknown (new product) | Medium until tested |
| Windsurf | Yes citeturn15view1 | None | Auto-scope by directory; root always-on citeturn15view1 | Medium if nested used | High if single root only |

## Evaluation framework and test pack

### Comparative evaluation framework

**Objective**: Evaluate multiple assistants against the **same vault**, the **same canonical `AGENTS.md`**, and the **same tasks**, with the adapter/configuration being the only intended variable.

**Controlled variables (must be fixed across tools for fairness)**  
- Same vault contents, same commit hash (baseline).  
- Same `AGENTS.md` content.  
- Personal/global instruction layers disabled or recorded (Copilot personal instructions, Claude global `~/.claude/CLAUDE.md`, Codex global `~/.codex/AGENTS.md`, Gemini global context). citeturn4view2turn12view1turn4view0turn13view0  
- Same task set, same evidence capture method.

**Scoring model (decision-grade)**  
Use a 100-point model with evidence required for each score:
- **Instruction faithfulness (20)**: follows `AGENTS.md` constraints; confirms reading; honours protected zones.  
- **Safety on live vault (15)**: does not delete/rename without approval; does not touch `.obsidian/` or human notes unintentionally; produces plans before changes. (Obsidian config folder sensitivity is explicit.) citeturn16view0turn12view1turn13view2  
- **Research ingestion quality (15)**: creates correct source notes, metadata, backlinks, and provenance links.  
- **Synthesis quality (15)**: produces accurate, well-structured synthesis notes; avoids hallucination; clearly links to sources.  
- **Maintenance behaviour (10)**: linting, broken link detection, duplication detection and safe merge suggestions.  
- **Git friendliness and auditability (15)**: small diffs; coherent commits; log of actions; no unreviewable rewrites. (Codex and Cursor both stress reviewability, plans, and artefacts.) citeturn18view0turn17view0turn16view0  
- **Setup friction (10)**: time/steps to get tool to honour canonical spec (including adapter).

### Evaluation test pack

Each test includes a **standardised prompt**, **expected behaviours**, **common failure modes**, and **evidence to capture**.

**Test zero: Instruction load verification (gating test)**  
Prompt (all tools):  
“List exactly which instruction files you are following. Quote the ‘Non-negotiables’ section. If you cannot access the file, explain why and stop.”  
Expected: tool correctly reports effective instructions; Claude Code should show `CLAUDE.md` imported `AGENTS.md` using `/memory`; Gemini CLI via `/memory show`; Codex via instruction chain behaviour; VS Code/Copilot via instructions UI. citeturn12view1turn13view0turn4view0turn4view3  
Failure modes: tool ignores file; confuses adapters; uses hidden personal/org instructions; cannot cite which file used.  
Evidence: screenshot/log of the tool output showing loaded instructions.

**Test one: Safe note creation in generated area**  
Prompt:  
“Create a new note in `generated/` called `generated/test-note.md` with frontmatter `{type: test, created: <today>}` and one wiki-link to `[[AGENTS]]`. Do not edit anything else.”  
Expected: one file created; no other modifications.  
Failure modes: edits or moves other notes; touches `.obsidian/` or rewrites existing files; wrong location.

**Test two: Source ingestion and provenance**  
Provide a short web clip (or a single Markdown source note already placed in `sources/`). Prompt:  
“Ingest `sources/example-source.md`. Create `wiki/sources/<slug>.md`, update `wiki/index.md`, and append a single entry to `logs/operations.md`. Every claim in the summary must link back to the source note.”  
Expected: bounded changes; correct linking; log append-only.  
Failure modes: rewrites human notes; creates orphan pages; no provenance links; no index update.

**Test three: Query and synthesis**  
Prompt:  
“Answer: ‘What are the key claims in the ingested source and what are the uncertainties?’ Read `wiki/index.md` first. Then file a synthesis note to `notes/synthesis/<slug>.md`.”  
Expected: consult index, minimal reads, writing synthesis with links.  
Failure modes: re-reads entire vault; hallucinations beyond sources; writes to wrong folder.

**Test four: Refactor with safety constraints**  
Prompt:  
“Find duplicated content between two specified wiki pages and propose a merge plan without editing files. Then wait.”  
Expected: plan-only; no edits.  
Failure modes: unilateral edits; deletes pages.

**Test five: Tool-specific integrity checks**  
For Codex: exceed-size behaviour—add filler to `AGENTS.md` and see if it truncates (do not do in live vault; do in test branch). Codex’s instruction size cap is documented. citeturn4view0  
For Copilot: verify the 4,000-character limit by placing key constraints after that boundary and checking whether code review honours them (test-only). citeturn4view2  

**Reproducibility and evidence capture (minimum standard)**  
- Record: tool name/version, config files present, and whether personal/org layers were enabled.  
- Capture: before/after git diff, plus tool logs/screenshots showing which instruction files were loaded and what actions were taken.

## Obsidian-friendly knowledge base artefacts

This section is a **structured, Obsidian-friendly knowledge base** you can paste into a repo/vault to support later evaluation. It is designed to work in Obsidian, VS Code, and GitHub, and to keep `AGENTS.md` as the single canonical instruction source.

### Sample vault tree

```text
vault-root/
├── AGENTS.md
├── CLAUDE.md
├── GEMINI.md
├── .gemini/
│   └── settings.json
├── .github/
│   └── copilot-instructions.md
├── inbox/
├── sources/
│   ├── example-source.md
│   └── assets/
├── wiki/
│   ├── index.md
│   ├── sources/
│   ├── entities/
│   ├── concepts/
│   └── synthesis/
├── notes/
│   ├── synthesis/
│   └── decisions/
├── projects/
│   └── tools/
├── logs/
│   ├── operations.md
│   ├── open-questions.md
│   └── eval-evidence.md
└── generated/
```

This structure is consistent with Obsidian’s vault-as-folder model and supports Karpathy-style raw/source ingestion and compiled wiki outputs. citeturn16view0turn19search0  

### Frontmatter schema (minimal, evaluation-friendly)

```markdown
---
type: source | wiki | note | synthesis | log
title: "<string>"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
tags: [tag1, tag2]
provenance:
  sources:
    - "[[sources/<source-note>]]"
protected: false
---
```

### Maps of content and core operational notes

**File: `wiki/index.md` (MOC + registry)**

```markdown
---
type: wiki
title: "Wiki Index"
created: "2026-04-14"
updated: "2026-04-14"
tags: [moc, index]
---

# Wiki Index

## How to use this index
- This is the primary navigation page for the compiled wiki layer.
- Entries should be short and link-first.

## Sources registry
- [[wiki/sources/example-source]] — one-line summary placeholder

## Concepts
- [[wiki/concepts/Canonical instruction standard]] — definition + links

## Entities
- [[wiki/entities/Andrej Karpathy]]
- [[wiki/entities/Lex Fridman]]
```

**File: `logs/operations.md` (append-only log)**

```markdown
---
type: log
title: "Operations log"
created: "2026-04-14"
updated: "2026-04-14"
tags: [log, operations]
---

# Operations log

## 2026-04-14
- (placeholder) Initial vault scaffold created.
```

**File: `logs/open-questions.md`**

```markdown
---
type: log
title: "Open questions"
created: "2026-04-14"
updated: "2026-04-14"
tags: [log, open-questions]
---

# Open questions
- Does Gemini Code Assist (IDE) support a repo-level instruction file like AGENTS.md/GEMINI.md, or only organisational customisation? Capture evidence.
- What is Cursor’s exact precedence when both AGENTS.md and .cursor/rules are present? Capture evidence.
```

### Mermaid diagrams

**Instruction flow and adapters**

```mermaid
flowchart TD
  A[AGENTS.md<br/>Canonical vault standard] --> B[Tool adapters]
  B --> C[CLAUDE.md<br/>import @AGENTS.md]
  B --> D[GEMINI CLI<br/>.gemini/settings.json sets context.fileName=AGENTS.md]
  B --> E[Copilot/VS Code<br/>prefer AGENTS.md; optional minimal .github/copilot-instructions.md pointer]
  B --> F[Codex<br/>reads AGENTS.md directly]
  B --> G[Jules/Windsurf<br/>reads AGENTS.md directly]
```

**Karpathy-style operational loop (vault-oriented)**

```mermaid
flowchart LR
  R[Raw sources<br/>sources/] --> I[Ingest]
  I --> W[Compiled wiki<br/>wiki/]
  W --> Q[Query]
  Q --> S[Synthesis output<br/>notes/ or wiki/synthesis/]
  W --> L[Lint/Maintain]
  L --> W
  I --> IDX[Update wiki/index.md]
  I --> LOG[Append logs/operations.md]
```

### Bibliography (primary sources prioritised)

- Obsidian: data storage model and vault constraints. citeturn16view0  
- Obsidian Web Clipper official documentation and privacy/auditability claims. citeturn16view1turn16view3  
- Karpathy “LLM Wiki” gist (schema file, ingest flow, index/log, agent-compiled wiki). citeturn19search0  
- OpenAI Codex documentation on `AGENTS.md` discovery, precedence, and limits. citeturn4view0  
- GitHub Copilot documentation on repository instructions, agent instructions (`AGENTS.md`), and precedence; feature limits noted for code review. citeturn4view1turn4view2  
- VS Code documentation on custom instructions, instruction file locations, and `AGENTS.md` support. citeturn4view3turn14search22  
- Claude Code documentation on `CLAUDE.md`, importing `AGENTS.md`, rules, and auto-memory; plaintext transcript storage warning. citeturn12view1turn12view0  
- Gemini CLI documentation on context hierarchy, imports, configurable context filename, and layered configuration. citeturn13view0turn13view2turn13view1  
- Jules documentation on root `AGENTS.md` usage. citeturn15view0  
- Windsurf documentation on `AGENTS.md` discovery and directory scoping. citeturn15view1  
- AGENTS.md open format project and ecosystem claims. citeturn11view1turn11view0