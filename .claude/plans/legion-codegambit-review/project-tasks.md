# CodeGambit Review — Master Task List

**Generated:** 2026-03-18
**Team:** legion-codegambit-review
**Status:** Ready for implementation

---

## Module 1: Security Fixes (P1)

### Task 1.1 — Sandbox subprocess leaks environment variables [CRITICAL]
- **Risk Tier:** T1 (Critical Security)
- **File:** `backend/app/services/sandbox.py` → `_run_subprocess()` (line 135)
- **Bug:** `subprocess.run()` inherits the parent process environment by default, exposing `ANTHROPIC_API_KEY` and all other env vars to user-submitted code.
- **Fix:** Pass `env={}` (or a minimal safe env) to `subprocess.run()`. Only include `PATH`, `HOME`, `LANG` — nothing sensitive.
- **Verification:** Write a test that executes `import os; print(os.environ)` in the sandbox and confirms no sensitive keys are present.

### Task 1.2 — Reference solution endpoint has no auth [CRITICAL]
- **Risk Tier:** T1 (Critical Security)
- **File:** `backend/app/api/challenges.py` → `get_reference_solution()` (line 52)
- **Bug:** `GET /api/challenges/{id}/reference-solution` returns the full reference solution to any caller with no authentication or guard. Users can see answers before attempting challenges.
- **Fix:** Gate the endpoint behind submission completion: only return the reference solution if the requesting user has a `completed` submission for that challenge. Alternatively, require a valid evaluation exists for the (user, challenge) pair.

### Task 1.3 — No input size validation on code submission [HIGH]
- **Risk Tier:** T2 (Security)
- **File:** `backend/app/api/submissions.py` → `create_submission()` (line 51)
- **Bug:** No validation on `body.code` length. A user could submit megabytes of code, causing memory/CPU exhaustion in the sandbox and evaluator.
- **Fix:** Add a `max_length` constraint to `SubmissionCreate.code` (e.g., 50KB). Return 400 if exceeded.

### Task 1.4 — No rate limiting on submissions [HIGH]
- **Risk Tier:** T2 (Security)
- **File:** `backend/app/api/submissions.py`
- **Bug:** No rate limit on `POST /api/submissions`. A client can flood the system with submissions, exhausting sandbox resources and API credits.
- **Fix:** Add a rate limiter (e.g., `slowapi` or custom middleware). Suggested: 5 submissions/minute per client IP.

### Task 1.5 — CORS overly permissive [MEDIUM]
- **Risk Tier:** T2 (Security)
- **File:** `backend/app/main.py` (line 25-31)
- **Bug:** `allow_methods=["*"]` and `allow_headers=["*"]` are broader than needed. While `allow_origins` is configurable, the wildcard methods/headers reduce defense-in-depth.
- **Fix:** Restrict `allow_methods` to `["GET", "POST", "OPTIONS"]` and `allow_headers` to `["Content-Type", "Authorization"]`.

### Task 1.6 — Sandbox temp file race condition [LOW]
- **Risk Tier:** T3 (Defense-in-depth)
- **File:** `backend/app/services/sandbox.py` → `_run_subprocess()` (line 130-131)
- **Bug:** `NamedTemporaryFile(delete=False)` creates the file, closes it, then `subprocess.run` opens it. On a multi-tenant system, another process could replace the file between creation and execution (TOCTOU).
- **Fix:** Use `os.open()` with `O_EXCL` or use `tempfile.mkdtemp()` with restrictive permissions. Low priority since this is a single-user app currently.

---

## Module 2: Backend Bug Fixes (P1)

### Task 2.1 — datetime.utcnow() deprecated, produces naive datetimes [HIGH]
- **Risk Tier:** T2 (Correctness)
- **Files:**
  - `backend/app/models/user.py` (lines 21-23)
  - `backend/app/models/evaluation.py` (line 27)
  - `backend/app/models/elo_history.py` (lines 20, 33, 47)
- **Bug:** `datetime.utcnow` is deprecated in Python 3.12+ and produces timezone-naive datetimes. This causes `DeprecationWarning` and can lead to timezone comparison bugs.
- **Fix:** Replace all `datetime.utcnow` with `datetime.now(datetime.timezone.utc)` (or `from datetime import timezone; datetime.now(timezone.utc)`).

### Task 2.2 — challenges_completed counter never incremented [HIGH]
- **Risk Tier:** T2 (Correctness)
- **File:** `backend/app/api/submissions.py` → `run_evaluation_pipeline()` (line 291)
- **Bug:** The pipeline sets `submission.status = "completed"` and increments `user.total_submissions` (in `elo.py` line 97), but `user.challenges_completed` is never incremented anywhere. The Dashboard shows it as always 0.
- **Fix:** After a successful evaluation, increment `user.challenges_completed` (with dedup — only count distinct challenge_ids).

### Task 2.3 — _clamp_score defined but never called on real evaluations [MEDIUM]
- **Risk Tier:** T2 (Correctness)
- **File:** `backend/app/services/evaluator.py` → `_clamp_score()` (line 269) and `_result_from_parsed()` (line 248)
- **Bug:** `_clamp_score` is defined and used only in `_mock_evaluation` (line 279-280). `_result_from_parsed` (used for real API responses) does not clamp scores — a malformed Claude response could return scores outside 0-100.
- **Fix:** Apply `_clamp_score` to all score fields in `_result_from_parsed`.

### Task 2.4 — Socratic phase 2 doesn't update ELO [MEDIUM]
- **Risk Tier:** T2 (Correctness)
- **File:** `backend/app/api/submissions.py` → `run_socratic_phase2()` (line 306-370)
- **Bug:** Phase 2 updates the Evaluation scores (lines 348-361) but does not recalculate ELO based on the new (potentially better/worse) scores. The ELO from phase 1 persists unchanged.
- **Fix:** After updating the Evaluation, call `elo_service.update_elo()` with the new scores (or implement an ELO adjustment method).

### Task 2.5 — Race condition in submission pipeline (no status lock) [MEDIUM]
- **Risk Tier:** T2 (Correctness)
- **File:** `backend/app/api/submissions.py` → `run_evaluation_pipeline()` (line 187)
- **Bug:** If a user submits the same challenge rapidly, multiple background pipelines can run concurrently for overlapping submissions. No locking prevents two pipelines from updating the same user's ELO simultaneously.
- **Fix:** Add `SELECT ... FOR UPDATE` on the submission row at pipeline start, or use an asyncio lock keyed by user_id.

### Task 2.6 — Docker container.attrs stale (OOM undetected) [MEDIUM]
- **Risk Tier:** T2 (Correctness)
- **File:** `backend/app/services/sandbox.py` → `_run_docker()` (line 91)
- **Bug:** `container.attrs` is cached from container creation time. After `container.wait()`, the attrs are stale and `OOMKilled` will always be `False`. Must call `container.reload()` first.
- **Fix:** Add `container.reload()` before reading `container.attrs` on line 91.

### Task 2.7 — ELO delta variable shadowing [LOW]
- **Risk Tier:** T3 (Code Quality)
- **File:** `backend/app/services/elo.py` → `update_elo()` (lines 77-87)
- **Bug:** `delta` is calculated as `round(k * (actual - expected))` (line 77), but then `new_elo = max(100, current_elo + delta)` may clamp, making the actual delta different. The `ELOHistory.delta` (line 88) correctly uses `new_elo - current_elo`, but the local `delta` variable is misleading since it's computed but never used after the clamped assignment.
- **Fix:** Minor — rename or remove the intermediate `delta` variable to avoid confusion.

---

## Module 3: Frontend Bug Fixes (P1)

### Task 3.1 — Recursive polling stack overflow risk in Calibration.tsx [HIGH]
- **Risk Tier:** T2 (Stability)
- **File:** `frontend/src/pages/Calibration.tsx` → `handleSubmit()` (lines 115-137)
- **Bug:** The `poll()` function calls itself recursively with `return poll()` after `setTimeout`. For long evaluations (up to 150 polls * 2s = 5 min), this builds up a deep call stack. With 150 MAX_POLLS, it won't overflow in practice, but the pattern is fragile and inconsistent with SubmissionFlow.tsx which uses `setInterval`.
- **Fix:** Refactor to use `setInterval` (consistent with SubmissionFlow.tsx) or iterative `while` loop with `await`.

### Task 3.2 — ChallengeList swallows API errors silently [HIGH]
- **Risk Tier:** T2 (UX)
- **File:** `frontend/src/pages/ChallengeList.tsx` (lines 44-45)
- **Bug:** The `catch {}` block is empty — if the API is down or returns an error, the user sees "No challenges available yet." with no indication that something went wrong.
- **Fix:** Set an error state and display an error message (e.g., "Failed to load challenges. Is the backend running?").

### Task 3.3 — Dashboard stats hardcoded / derived from incorrect source [MEDIUM]
- **Risk Tier:** T2 (Correctness)
- **File:** `frontend/src/pages/Dashboard.tsx` (lines 122-138)
- **Bug:** The `stats` object uses hardcoded totals (10, 5, 5 for modes; 4, 6, 6, 2, 2 for difficulties) and derives `byMode`/`byDifficulty` completion from `challenges_completed` with arbitrary arithmetic. A `/api/user/stats` endpoint exists but is not used.
- **Fix:** Fetch from `userApi.getStats()` and/or compute from the actual challenge list. Remove hardcoded totals.

### Task 3.4 — Inconsistent difficulty color mapping [LOW]
- **Risk Tier:** T3 (UX Consistency)
- **File:** `frontend/src/pages/ChallengeList.tsx` (lines 17-23)
- **Bug:** The `DIFFICULTY_COLORS` map exists only in ChallengeList. Other pages (ChallengeIDE, Calibration) don't use a consistent mapping. Not a functional bug, but a consistency gap.
- **Fix:** Extract `DIFFICULTY_COLORS` to a shared constants file and use it everywhere difficulty badges appear.

### Task 3.5 — Calibration editor doesn't use MonacoEditor wrapper [LOW]
- **Risk Tier:** T3 (Consistency)
- **File:** `frontend/src/pages/Calibration.tsx` (lines 300-312)
- **Bug:** Calibration imports `Editor` directly from `@monaco-editor/react` instead of using the `MonacoEditor` wrapper component. The wrapper disables autocomplete/suggestions — the Calibration editor has these enabled, which is inconsistent with the main IDE and could be considered unfair during calibration.
- **Fix:** Replace the direct `Editor` import with the `MonacoEditor` wrapper component.

---

## Module 4: UX/UI Design System Fixes (P1)

### Task 4.1 — Broken brand color tokens [HIGH]
- **Risk Tier:** T2 (Visual)
- **File:** `frontend/tailwind.config.js`
- **Bug:** Only `brand-500`, `brand-600`, `brand-700` are defined. The codebase uses `brand-300`, `brand-400` (in ChallengeIDE.tsx line 184, SubmissionFlow.tsx lines 183-194, EvaluationResults.tsx line 128) which resolve to nothing — elements using these tokens are invisible or fall back to default.
- **Fix:** Add `brand-300`, `brand-400` to the Tailwind config. Suggested: `300: '#86efac'`, `400: '#4ade80'` (green palette continuation).

### Task 4.2 — JetBrains Mono font not imported [HIGH]
- **Risk Tier:** T2 (Visual)
- **File:** `frontend/tailwind.config.js` declares `JetBrains Mono` as primary mono font, but it's never loaded.
- **Bug:** The font is declared in config but no `@import` or `<link>` exists in `index.html` or `index.css`. Falls back to `Fira Code` then generic `monospace`.
- **Fix:** Add Google Fonts import for JetBrains Mono in `index.html` `<head>` or `index.css`.

### Task 4.3 — Page title says "frontend" [HIGH]
- **Risk Tier:** T2 (Polish)
- **File:** `frontend/index.html` (line 7)
- **Bug:** `<title>frontend</title>` — should be "CodeGambit".
- **Fix:** Change to `<title>CodeGambit</title>`.

### Task 4.4 — Native <select> elements unstyled in dark mode [MEDIUM]
- **Risk Tier:** T2 (Visual)
- **File:** `frontend/src/pages/ChallengeList.tsx` (lines 92-109)
- **Bug:** Native `<select>` dropdowns on dark backgrounds show white/system-styled dropdown menus. The `<option>` elements inherit the dark `bg-gray-900` for the control but the dropdown menu rendering is OS-dependent.
- **Fix:** Style with `appearance-none` and custom arrow, or use a custom dropdown component.

### Task 4.5 — Responsive sidebar (collapsible on mobile) [MEDIUM]
- **Risk Tier:** T2 (Responsive)
- **File:** `frontend/src/components/Sidebar.tsx`
- **Bug:** Sidebar is fixed at `w-64` with no mobile breakpoint. On small screens it takes up most of the viewport with no way to collapse.
- **Fix:** Add a hamburger toggle, hide sidebar by default on `sm` breakpoint, show as overlay/drawer on mobile.

---

## Module 5: UX/UI Polish (P2)

### Task 5.1 — Add skeleton loading states [MEDIUM]
- **Risk Tier:** T3 (Polish)
- **Files:** `Dashboard.tsx`, `ChallengeList.tsx`, `ChallengeIDE.tsx`, `Calibration.tsx`
- **Bug:** All loading states show plain "Loading..." text with `animate-pulse`. This is functional but visually jarring.
- **Fix:** Replace with skeleton shimmer components that match the layout shape (cards, text lines, etc.).

### Task 5.2 — Add Ctrl+Enter keyboard shortcut for submit [MEDIUM]
- **Risk Tier:** T3 (UX)
- **File:** `frontend/src/components/SubmissionFlow.tsx`
- **Bug:** No keyboard shortcut to submit code. Power users expect Ctrl+Enter / Cmd+Enter.
- **Fix:** Add a `useEffect` with a `keydown` listener for Ctrl/Cmd+Enter that triggers `handleSubmit`.

### Task 5.3 — Add 404/Not Found catch-all route [MEDIUM]
- **Risk Tier:** T3 (UX)
- **File:** `frontend/src/App.tsx` (line 11-18)
- **Bug:** No catch-all `*` route. Navigating to an invalid URL shows a blank page inside the Layout.
- **Fix:** Add a `<Route path="*" element={<NotFoundPage />} />` with a styled 404 page.

### Task 5.4 — Score animation on evaluation results [LOW]
- **Risk Tier:** T3 (Polish)
- **File:** `frontend/src/components/EvaluationResults.tsx`
- **Bug:** Scores appear instantly. A count-up animation would improve the user experience.
- **Fix:** Animate the overall score number counting up from 0 to the final value. Animate score bars width with CSS transitions (some already have `transition-all`).

### Task 5.5 — Chess theme enhancement [LOW]
- **Risk Tier:** T3 (Polish)
- **File:** `frontend/src/components/Sidebar.tsx`
- **Bug:** Chess piece icons are Unicode characters which render inconsistently across platforms. Sidebar tagline is generic.
- **Fix:** Replace Unicode chess pieces with SVG icons. Add chess-themed tagline (e.g., "Master your next move").

### Task 5.6 — Challenge completion indicators on ChallengeList [LOW]
- **Risk Tier:** T3 (UX)
- **File:** `frontend/src/pages/ChallengeList.tsx`
- **Bug:** No visual indicator of which challenges the user has already completed.
- **Fix:** Fetch completed challenge IDs from user submissions and show a checkmark/badge on completed cards.

### Task 5.7 — Accessibility improvements [MEDIUM]
- **Risk Tier:** T3 (Accessibility)
- **Files:** `Sidebar.tsx`, `ChallengeList.tsx`, `SubmissionFlow.tsx`, `Layout.tsx`
- **Bug:** Missing `aria-label` on nav, form controls, and buttons. No skip-to-content link. `<label>` not associated with inputs.
- **Fix:** Add `<nav aria-label="Main navigation">`, `aria-label` on icon-only buttons, `<label>` associations, and a skip-to-content link in Layout.

---

## Module 6: Test Coverage (P1)

### Task 6.1 — sandbox.py tests [CRITICAL]
- **Risk Tier:** T1 (Test Coverage — highest risk code)
- **File:** `backend/tests/test_sandbox.py` (new)
- **Tests needed:**
  - `test_parse_memory_limit` — unit test for all suffix variants
  - `test_subprocess_env_sanitized` — verify no env leakage (after Task 1.1 fix)
  - `test_subprocess_timeout` — verify timeout handling
  - `test_subprocess_memory_limit` — verify resource limits applied
  - `test_execute_code_fallback` — verify Docker fallback path

### Task 6.2 — evaluator.py tests [HIGH]
- **Risk Tier:** T2 (Test Coverage)
- **File:** `backend/tests/test_evaluator.py` (new)
- **Tests needed:**
  - `test_mock_evaluation` — verify mock mode returns valid structure
  - `test_parse_json_response` — with clean JSON, markdown-wrapped, invalid JSON
  - `test_clamp_score` — boundary values
  - `test_result_from_parsed` — verify score extraction and defaults

### Task 6.3 — calibration.py tests [HIGH]
- **Risk Tier:** T2 (Test Coverage)
- **File:** `backend/tests/test_calibration.py` (new)
- **Tests needed:**
  - `test_current_band_index` — boundary and mid-band steps
  - `test_start_calibration` — resets ELO to 1200
  - `test_complete_calibration` — sets flag, returns ELO
  - `test_get_next_challenge_after_complete` — returns already_complete

### Task 6.4 — challenge_service.py tests [MEDIUM]
- **Risk Tier:** T2 (Test Coverage)
- **File:** `backend/tests/test_challenge_service.py` (new)
- **Tests needed:**
  - `test_get_challenges_with_filters`
  - `test_get_recommendations_excludes_completed`
  - `test_get_calibration_challenges_sorted`

### Task 6.5 — Frontend page-level tests [MEDIUM]
- **Risk Tier:** T3 (Test Coverage)
- **Files:** `frontend/src/pages/__tests__/` (new directory)
- **Tests needed:**
  - Dashboard: renders loading state, renders calibration prompt if not calibrated, renders stats
  - ChallengeList: renders challenge cards, handles empty state, handles error state
  - Basic smoke tests for ChallengeIDE and Calibration

### Task 6.6 — Socratic answers endpoint tests [MEDIUM]
- **Risk Tier:** T2 (Test Coverage)
- **File:** `backend/tests/test_api_submissions.py` (extend)
- **Tests needed:**
  - `test_submit_socratic_answers_success`
  - `test_submit_socratic_answers_wrong_mode`
  - `test_submit_socratic_answers_no_questions`
  - `test_submit_socratic_answers_already_submitted`

---

## Module 7: Integration (P1)

### Task 7.1 — Fix CI pipeline (GitHub Actions) [HIGH]
- **Risk Tier:** T2 (Infrastructure)
- **File:** `.github/workflows/ci.yml`
- **Bug:** CI pipeline is broken. The workflow structure looks correct (backend: pip install, ruff, pytest; frontend: npm ci, lint, test, build), but needs verification and fixes. Potential issues to investigate:
  1. **Backend `ruff check`** — any lint violations introduced by code changes will fail CI. Must run `ruff check .` locally and fix violations before pushing.
  2. **Frontend `npm run lint` (eslint)** — ESLint flat config with TypeScript. Any lint warnings treated as errors will fail CI. Must run `npm run lint` locally and fix.
  3. **Frontend `npm test` (vitest run)** — existing tests in `components/__tests__/` must pass. Any new tests added by Module 6 must also pass.
  4. **Frontend `npm run build` (`tsc -b && vite build`)** — TypeScript strict compilation. Any type errors from code changes will fail CI.
  5. **Backend `pytest`** — all existing + new tests must pass with `DATABASE_URL=sqlite+aiosqlite:///./test.db` and empty `ANTHROPIC_API_KEY`.
- **Fix:** Run the full CI pipeline locally, identify all failures, and fix them. Ensure all code changes from other modules pass lint + test + build.
- **Wave Assignment:** Wave 2 (depends on all code changes being complete) — assigned to Agent H alongside Task 7.2.

### Task 7.2 — Git commit and push all changes
- **Risk Tier:** T3
- **Depends on:** All other modules complete + Task 7.1 (CI must pass)
- **Actions:** Stage all modified/new files, create a structured commit message, push to remote.

---

## Wave Plan

### Wave 1 (5 agents, parallel)

| Agent | Module | Tasks | Est. Complexity |
|-------|--------|-------|----------------|
| **Agent A: Security** | Module 1 | 1.1, 1.2, 1.3, 1.4, 1.5, 1.6 | High |
| **Agent B: Backend Bugs** | Module 2 | 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7 | High |
| **Agent C: Frontend Bugs** | Module 3 | 3.1, 3.2, 3.3, 3.4, 3.5 | Medium |
| **Agent D: UX/UI Design System** | Module 4 | 4.1, 4.2, 4.3, 4.4, 4.5 | Medium |
| **Agent E: Test Infrastructure** | Module 6 | 6.1, 6.2, 6.3, 6.4 | High |

### Wave 2 (3 agents, parallel — starts after Wave 1)

| Agent | Module | Tasks | Est. Complexity |
|-------|--------|-------|----------------|
| **Agent F: UX Polish** | Module 5 | 5.1, 5.2, 5.3, 5.4, 5.5, 5.6 | Medium |
| **Agent G: A11y + Responsive IDE** | Module 5 | 5.7 + ChallengeIDE responsive layout | Medium |
| **Agent H: Integration + Remaining Tests** | Module 6+7 | 6.5, 6.6, 7.1 (CI fix), 7.2 (git commit) | High |

### Dependency Notes

- **Agent E (Tests)** should coordinate with Agent A (Security) and Agent B (Backend) — tests should validate the fixes.
- **Wave 2** agents should pull/rebase from Wave 1 changes before starting.
- **Agent H** must be last to run Task 7.1 (git commit) after all other work is verified.

---

## Risk Summary

| Tier | Count | Description |
|------|-------|-------------|
| T1 (Critical) | 3 | Sandbox env leak, reference solution auth, sandbox tests |
| T2 (High/Medium) | 23 | Core bugs, security hardening, UX, test gaps, CI pipeline |
| T3 (Low/Polish) | 10 | Code quality, polish, theme, a11y |
| **Total** | **36** | |
