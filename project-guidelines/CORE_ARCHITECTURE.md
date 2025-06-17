# TaskForge Core Architecture

## 1. Application Architecture & Core Workflow

### 1.1 Core Philosophy: Human-on-Exception

The system defaults to "action first," surfacing only edge cases for human review—e.g. unclear or duplicate tasks. Human intervention happens only within an 18-hour review window.

### 1.2 Timezone Strategy

* **Backend (UTC):** All data storage and cron triggers run in UTC.
* **Frontend (Local):** UTC timestamps are converted client-side to the user's browser locale.

### 1.3 System Components & Data Flow

#### 1.3.1 Data Ingestion & Warehouse Build

* **Automated Backfill (every 15 min):**
  1. Compare local transcript count vs. Fireflies API.
  2. If behind, fetch a small batch of missing transcripts.
  3. Store raw JSON in a PostgreSQL JSONB column.
* **Daily Delta Sync (23:59 UTC):**
  1. Fetch recent transcripts.
  2. Insert only new `fireflies_id`s.

#### 1.3.2 AI Processing & Task Management

* **AI Task Extraction (every 5 min):**
  1. Query unprocessed transcripts.
  2. Send to Gemini API + post-process (dedupe, enforce word counts, weekend-safe due dates).
  3. Save as `ActionItem` and mark transcript processed.
* **AI Daily Briefing (00:05 UTC):**
  1. Gather tasks from last 24h.
  2. Generate a high-level summary via Gemini.
  3. Save to `daily_reports` table.

#### 1.3.3 Review & Autonomous Push

* **Human Review Window (18h):**
  Admins can **Edit**, **Approve**, or **Reject** each task via the dashboard.
* **Stale Task Alerts (Real-time UI):**
  Banner prompts review when tasks near 18h deadline.
* **Auto-Push Job (hourly):**
  Finds pending tasks >18h old and pushes them to Monday.com, logging every result.

### 1.4 Deployment & Local Environment (No Docker)

* **Production (Render.com):**
  Defined in `render.yaml` for Web Service, PostgreSQL, and Cron jobs—push to GitHub → zero-downtime deploy.
* **Local Dev/Test:**
  1. Install PostgreSQL natively (e.g. Homebrew).
  2. Run `python manage.py runserver` for the web UI.
  3. Launch Celery workers for background jobs.

### 1.5 Software Testing

* **Unit Tests:** Isolate every function; mock external APIs.
* **Integration Tests:** Verify end-to-end Fireflies → AI → DB flows.
* *(Optionally)* End-to-End tests against a local staging database.

## Database Schema

### Core Tables
- `transcripts` - Raw Fireflies data (JSONB)
- `action_items` - Processed tasks
- `daily_reports` - AI-generated summaries
- `user_reviews` - Human review decisions

## External Integrations

### APIs Required
- **Fireflies API** - Transcript ingestion
- **Gemini API** - AI processing
- **Monday.com API** - Task delivery

### Rate Limiting
- Fireflies: Batch processing, 15-min intervals
- Gemini: Queue-based processing
- Monday.com: Retry logic with exponential backoff

## Performance Requirements

- **15-minute ingestion cycles**
- **5-minute AI processing cycles**
- **18-hour human review window**
- **Real-time UI updates**
- **Zero-downtime deployments** 