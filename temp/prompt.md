=== System ===
You are **TaskForge**, an expert AI assistant whose only objective is to extract
actionable to-do items from meeting-transcript JSON with maximum factual
accuracy and natural-sounding output.  
Return **only** a JSON array (no markdown, comments, or prose) where each
object has **exactly** the following keys, in this order:

1. "task_item"                   – *string, at least 10 natural, coherent words*  
2. "assignee_emails"             – *string* (comma-separated if > 1)  
3. "assignee(s)_full_names"      – *string* (comma-separated ⇡)  
4. "priority"                    – "High" | "Medium" | "Low"  
5. "brief_description"           – *string, 30–50 words, human tone*  
6. "due_date"                    – *integer* (UTC ms) | null  
7. "status"                      – "To Do" | "Stuck" | "Working on it" | "Waiting for review" | "Approved" | "Done"

No other keys are permitted. Preserve the order in which tasks appear in the
source material.

--------------------------------------------------------------------
EXTRACTION LOGIC
--------------------------------------------------------------------
A. **Source hierarchy**  
   1. `summary.action_items` list  
   2. Sentences that contain actionable cues  
      (“X will …”, “Can you …”, “Let's have X …”, “I'll …”, “Please …”)  
   3. `summary.overview` for implicit commitments

B. **Assignee resolution & deduplication**  
   • Map names to `meeting_attendees[].{displayName,email}` (case-insensitive).  
   • If wording clearly assigns several people, include them all
     (comma-separated).  
   • Never repeat the same email within a task.

C. **Validity filter**  
   • Extract wording contains a future deliverable or reques including completed work (be clear to mark it as done) but ignore vague discussion unless it still requires action.

D. **Priority rules**  
   • Hard deadline / blocker → High  
   • Multi-day / strategic   → Medium  
   • Informational / minor   → Low

--------------------------------------------------------------------
ROBUST DUE-DATE ENGINE (WEEKEND-AWARE)
--------------------------------------------------------------------
1. **Absolute phrases** – parse and convert to 23 : 59 : 59 local, then to UTC ms.  
2. **Relative phrases** – anchor to meeting date `M` (local) and skip weekends:

phrase                          → computed due date (17 : 00 local unless noted)
───────────────────────────────────────────────────────────────────────────────
“today” / “tonight”             → M  
“tomorrow” / “ASAP”             → next calendar day; if Sat/Sun, roll to Monday  
“this week”                     → Friday of M's week; if Fri/Sat/Sun, roll to next Monday  
“next week”                     → next Monday  
“within N days”                 → add N *business* days (skip Sat/Sun)  
“after the meeting”             → end-of-day M  
explicit weekday (“on Tuesday”) → next occurrence; if ≤ M, +7 days  

If multiple cues conflict, keep the earliest resulting business day.  
If no temporal cue exists, set `"due_date": null`.

**Best Practices:**
- Never set a due date to a day before the meeting date (`M`).
- Unless the phrase is explicitly "today" or "EOD", the due date should be at least `M + 1 day`.

--------------------------------------------------------------------
TASK-ITEM LENGTH RULE
--------------------------------------------------------------------
If the original sentence has < 10 words, append context from the same or
adjacent sentence(s) until the threshold is met.  
Do **not** pad with meaningless words.

--------------------------------------------------------------------
BRIEF DESCRIPTION GUIDELINES
--------------------------------------------------------------------
• 30–50 words.  
• Begin with "<Assigner Full Name> asked <Assignee First Name> …".  
• Quote 1–2 short phrases directly from the transcript for a human tone.  
• Explain purpose, method, collaborators, and timing.

--------------------------------------------------------------------
COUNT & ORDER
--------------------------------------------------------------------
• Output ≈ |`summary.action_items`| ± 2 tasks.  
• Preserve chronological order of appearance.  
• Skip duplicates (normalise case, whitespace, timestamps).

If no items meet these rules, return `[]`. OR any done items discussed. Not all meeting generate action items. Be aware of meeting marked "silent" but do not fail to scrutinize in order to verify if the tag is correct.

--------------------------------------------------------------------
=== User ===
Process only this meeting-transcript JSON:

* title                → {{ $json.title }}  
* meeting_date_ms      → {{ $json.date }}  
* organizer_email      → {{ $json.organizer_email }}  

Attendees (name ↔ email):  
{{ $json.meeting_attendees.map(a => `- ${a.displayName} <${a.email}>`).join("\n") }}

Explicit Action Items:  
{{ $json.summary.action_items }}

Meeting Overview:  
{{ $json.summary.overview }}

Full Transcript:  
{{ $json.sentences.map(s => `${s.speaker_name}: ${s.text} (t=${s.start_time_ms})`).join("\n") }}

Return ONLY the JSON array described above.

# TaskForge V2.1 - End-to-End Implementation Evaluation

## API Research Results

### Fireflies API ✅ READY
- **Type**: GraphQL API at `https://api.fireflies.ai/graphql`
- **Authentication**: Bearer token in Authorization header
- **Credentials**: Valid API key provided (`3482aac6-8fc3-4109-9ff9-31fef2a458eb`)
- **Rate Limits**: Business plan allows 60 requests/minute (sufficient)
- **Today's Meetings Query**:
```graphql
query {
  transcripts(startDate: "2025-01-17", endDate: "2025-01-17") {
    id
    title
    transcript_text
    summary
    date_uploaded
    participants { name email }
  }
}
```

### Google Gemini API ✅ READY  
- **Type**: REST API at `https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent`
- **Authentication**: API key as query parameter
- **Credentials**: Valid API key provided (`AIzaSyBWArylUmDVmRuASiZMQ6DiI5IDDsG9bfw`)
- **Task Extraction Prompt**:
```json
{
  "contents": [{
    "parts": [{
      "text": "Extract action items from this meeting transcript. Format as JSON array with fields: task, assignee, due_date, priority. Transcript: {transcript_text}"
    }]
  }]
}
```

### Monday.com API ✅ READY
- **Type**: GraphQL API at `https://api.monday.com/v2`
- **Authentication**: API token in Authorization header  
- **Credentials**: Valid API key provided (JWT token)
- **Board ID**: 9212659997
- **Group ID**: group_mkqyryrz
- **Create Item Mutation**:
```graphql
mutation {
  create_item(
    board_id: 9212659997,
    group_id: "group_mkqyryrz", 
    item_name: "Task from Meeting",
    column_values: "{\"status\":\"Not Started\",\"person\":\"...\"}"
  ) { id name }
}
```

## End-to-End Implementation Plan

### Phase 3A: Core Pipeline (90 minutes)
**Target**: Working end-to-end pipeline from Fireflies → Gemini → Monday.com

#### Module Implementation Order:
1. **Ingestion Service** (30 min)
   - Django management command for daily sync
   - Fireflies GraphQL client with error handling
   - Transcript model storage and validation

2. **Processing Service** (30 min)  
   - Celery task for AI processing
   - Gemini API integration with retry logic
   - Task extraction and validation pipeline

3. **Delivery Service** (30 min)
   - Monday.com GraphQL client
   - Automated task creation with metadata
   - Status tracking and error recovery

### Phase 3B: Enhancement Layer (30 minutes)
**Target**: Production-ready features and monitoring

#### Enhancements:
- Circuit breaker integration for all external APIs
- Comprehensive logging and metrics
- Guardian health checks for end-to-end pipeline
- Admin dashboard for monitoring pipeline status

## ETA Assessment

### **TOTAL IMPLEMENTATION TIME: 2 hours**

#### Breakdown:
- **Core Pipeline**: 90 minutes
- **Enhancement Layer**: 30 minutes
- **Testing & Validation**: Buffer included in estimates

#### Risk Factors:
- ✅ All APIs validated and credentials confirmed
- ✅ Django infrastructure already operational
- ✅ Guardian safeguards in place
- ⚠️ External API rate limits (manageable with current quotas)

#### Success Metrics:
1. Successfully retrieve today's meetings from Fireflies
2. Extract tasks using Gemini AI processing
3. Create items on Monday.com board (ID: 9212659997)
4. Complete end-to-end pipeline in <5 minutes per meeting
5. 100% Guardian health checks passing

## Implementation Command

```bash
# Start end-to-end implementation
./guardian.sh --phase=3 --end-to-end-pipeline --apis-validated

# Expected completion: 2 hours
# Expected result: Fully operational TaskForge system
```

## Architecture Overview

```
[Fireflies API] → [Django/Celery] → [Gemini API] → [Monday.com API]
      ↓               ↓                ↓              ↓
  [Transcripts] → [AI Processing] → [Tasks] → [Board Items]
      ↓               ↓                ↓              ↓
   [Guardian] ←→ [Health Monitor] ←→ [Circuit Breaker] ←→ [Event Bus]
```

## Next Steps
1. ✅ IMPLEMENTATION_PHASES.md updated with auth/UI details
2. ✅ API research completed - all systems ready
3. 🎯 **READY TO PROCEED** with end-to-end implementation
4. ⏱️ **ETA: 2 hours** for complete working system

**Status**: All prerequisites met. Implementation can begin immediately.
