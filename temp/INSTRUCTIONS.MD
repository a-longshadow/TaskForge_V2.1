Below is a comprehensive, end-to-end map of your TaskForge application and engineering workflow—excluding Docker—and including the Guardian safeguards.

---

## 1. Application Architecture & Core Workflow

### 1.1 Core Philosophy: Human-on-Exception

The system defaults to “action first,” surfacing only edge cases for human review—e.g. unclear or duplicate tasks. Human intervention happens only within an 18-hour review window.&#x20;

### 1.2 Timezone Strategy

* **Backend (UTC):** All data storage and cron triggers run in UTC.
* **Frontend (Local):** UTC timestamps are converted client-side to the user’s browser locale.&#x20;

### 1.3 System Components & Data Flow

#### 1.3.1 Data Ingestion & Warehouse Build

* **Automated Backfill (every 15 min):**

  1. Compare local transcript count vs. Fireflies API.
  2. If behind, fetch a small batch of missing transcripts.
  3. Store raw JSON in a PostgreSQL JSONB column.
* **Daily Delta Sync (23:59 UTC):**

  1. Fetch recent transcripts.
  2. Insert only new `fireflies_id`s.&#x20;

#### 1.3.2 AI Processing & Task Management

* **AI Task Extraction (every 5 min):**

  1. Query unprocessed transcripts.
  2. Send to Gemini API + post-process (dedupe, enforce word counts, weekend-safe due dates).
  3. Save as `ActionItem` and mark transcript processed.
* **AI Daily Briefing (00:05 UTC):**

  1. Gather tasks from last 24h.
  2. Generate a high-level summary via Gemini.
  3. Save to `daily_reports` table.&#x20;

#### 1.3.3 Review & Autonomous Push

* **Human Review Window (18h):**
  Admins can **Edit**, **Approve**, or **Reject** each task via the dashboard.
* **Stale Task Alerts (Real-time UI):**
  Banner prompts review when tasks near 18h deadline.
* **Auto-Push Job (hourly):**
  Finds pending tasks >18h old and pushes them to Monday.com, logging every result.&#x20;

### 1.4 Deployment & Local Environment (No Docker)

* **Production (Render.com):**
  Defined in `render.yaml` for Web Service, PostgreSQL, and Cron jobs—push to GitHub → zero-downtime deploy.
* **Local Dev/Test:**

  1. Install PostgreSQL natively (e.g. Homebrew).
  2. Run `flask run` for the web UI.
  3. Launch APScheduler jobs via a standalone script.&#x20;

### 1.5 Software Testing

* **Unit Tests:** Isolate every function; mock external APIs.
* **Integration Tests:** Verify end-to-end Fireflies → AI → DB flows.
* *(Optionally)* End-to-End tests against a local staging database.&#x20;

---

## 2. Guardian Script: Safeguarding AI-Driven Changes

Wrap every automated or “AI agent” command in `guardian.sh`:

1. **Pre-check:** Ensure a clean Git state or abort.
2. **(Optional) Backup:** Snapshot via `scripts/create_snapshot.sh`.
3. **Run:** Execute the provided command.
4. **Post-check:** If tracked files changed, alarm—and, if configured, restore.&#x20;

**Example:**

```bash
./guardian.sh --backup --strict ai-agent generate-changes.patch
```

---

## 3. Development Workflow & AI-Agent Governance

1. **Patch-Only Mode:** Configure the agent to emit unified diffs, never write directly.
2. **Pull Request Workflow:** Agent opens a PR; humans must review/approve before merge.
3. **Commit Standards:** Every AI PR includes descriptive messages and references relevant ticket IDs.

---

## 4. CI/CD Pipeline

* **Lint & Type-Check:** ESLint, Flake8, mypy/TypeScript.
* **Automated Tests:** Full unit + integration suite.
* **Gated Merges:** Block any PR with failing checks (GitHub Actions or equivalent).

---

## 5. Feature Flags & Incremental Rollouts

* **Isolate New Features:** Wrap behind flags so they’re off by default.
* **Canary/Staging:** Deploy AI-agent changes to staging first; monitor before full rollout.

---

## 6. Environment Parity (No Docker)

Maintain as close to production as possible without containers:

* **Local DB = Prod DB** (same schema, version).
* **Same Python/runtime versions** locally and on Render (via `.python-version` or pyenv).&#x20;

---

## 7. Deployment & Rollback

* **Render Deployment:** Push to GitHub → Render auto-deploy.
* **One-Click Rollback:** Use the last known-good Git tag in Render’s UI or CLI.
* **Database Backups & Maintenance Mode:**

  1. `pg_dump $DATABASE_URL > backup.sql`
  2. Enable maintenance, run `flask db upgrade`, then re-enable traffic.&#x20;

---

## 8. Monitoring & Observability

* **Structured Logging & Rotation:** RotatingFileHandler, 10 MB chunks, 10 backups.&#x20;
* **Health Check Endpoint:** `/health` tests DB and external API connectivity.&#x20;
* **Performance Metrics:** Log request durations (`before_request`/`after_request`) and track in your APM.

---

## 9. Blameless Retrospectives

After any cascade of regressions:

1. Gather logs, PR history, and Guardian alerts.
2. Identify root cause (prompt ambiguity, missing tests, misconfig).
3. Update processes, tests, or prompts to close the loop.

---

With this map, you’ve got a clear, holistic view—from raw transcript ingest to safe AI-driven code changes, through rigorous CI, deployment, monitoring, and rollback—ensuring reliability and speed without Docker.
