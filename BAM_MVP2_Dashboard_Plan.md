# AntiGravity BAM — Part 2: Web Dashboard & Lead Feedback Platform

## Goal

Build a **production-ready web dashboard** that:
1. Lets leads (Accenture client teams) **view BAM results** interactively — not just Excel files
2. Collects **structured feedback** from leads on taxonomy accuracy and association quality
3. Allows analysts to **upload data, run the pipeline, and review AI taxonomy suggestions** through a UI
4. Deploys on **Vercel** (frontend) with a lightweight Python API backend

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    VERCEL (Frontend)                 │
│                                                     │
│   Next.js App (App Router)                          │
│   ├── / (Landing / Login)                           │
│   ├── /dashboard (Association Maps + Charts)        │
│   ├── /taxonomy (AI Suggestions Review UI)          │
│   ├── /feedback (Lead Feedback Collection)          │
│   ├── /upload (Data Upload + Pipeline Trigger)      │
│   └── /api/... (Next.js API routes → proxy to API)  │
│                                                     │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────┐
│              RAILWAY / RENDER (Backend API)          │
│                                                     │
│   FastAPI (Python)                                  │
│   ├── POST /api/run-pipeline                        │
│   ├── POST /api/generate-taxonomy                   │
│   ├── GET  /api/results/{run_id}                    │
│   ├── POST /api/feedback                            │
│   ├── GET  /api/clients                             │
│   └── The full BAM Python engine from Part 1        │
│                                                     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              SUPABASE (Database + Auth + Storage)    │
│                                                     │
│   PostgreSQL:                                       │
│   ├── clients (client configs)                      │
│   ├── pipeline_runs (run history + results)         │
│   ├── taxonomy_suggestions (AI suggestions queue)   │
│   ├── feedback (lead feedback entries)              │
│   └── users (auth — analyst vs lead roles)          │
│                                                     │
│   Storage:                                          │
│   ├── uploads/ (raw Excel input files)              │
│   └── outputs/ (generated Excel results)            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Why not pure Vercel?** The BAM Python engine uses pandas, spaCy, NLTK — these are too heavy for Vercel serverless functions (250MB limit, 10s timeout). The Python backend runs on Railway (free tier available, $5/mo hobby) or Render, which supports long-running Python processes. The Next.js frontend on Vercel proxies API calls to it.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | **Next.js 14** (App Router) | Vercel-native, RSC, great DX |
| Styling | **Tailwind CSS** + **shadcn/ui** | Premium look with minimal effort |
| Charts | **Recharts** or **Nivo** | Interactive association heat maps |
| Auth | **Supabase Auth** | Simple, free, role-based (analyst vs lead) |
| Database | **Supabase PostgreSQL** | Free tier, real-time, great SDK |
| File Storage | **Supabase Storage** | Upload/download Excel files |
| Backend API | **FastAPI** (Python) | Wraps the BAM engine, async, auto-docs |
| Backend Host | **Railway** | Easy Python deploy, $5/mo, persistent |
| Frontend Host | **Vercel** | Free tier, automatic deploys from Git |
| NVIDIA NIM | API calls from FastAPI | Taxonomy generation |

---

## Database Schema (Supabase PostgreSQL)

### `users`
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
email         TEXT UNIQUE NOT NULL
role          TEXT NOT NULL CHECK (role IN ('analyst', 'lead', 'admin'))
name          TEXT
company       TEXT
created_at    TIMESTAMPTZ DEFAULT now()
```

### `clients`
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
name          TEXT NOT NULL (e.g., "JLR", "Nike")
brand         TEXT NOT NULL (e.g., "Jaguar", "Nike Running")
config_json   JSONB NOT NULL (the full client config from Part 1)
bigram_taxonomy_url   TEXT (Supabase storage path)
monogram_taxonomy_url TEXT
created_by    UUID REFERENCES users(id)
created_at    TIMESTAMPTZ DEFAULT now()
```

### `pipeline_runs`
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
client_id     UUID REFERENCES clients(id)
status        TEXT CHECK (status IN ('pending', 'running', 'completed', 'failed'))
input_file_url    TEXT (Supabase storage path)
output_file_url   TEXT (generated Excel download link)
results_json      JSONB (summary stats for dashboard rendering)
total_messages    INT
total_bigrams     INT
tagged_pct        FLOAT
run_duration_sec  FLOAT
created_by    UUID REFERENCES users(id)
created_at    TIMESTAMPTZ DEFAULT now()
completed_at  TIMESTAMPTZ
```

### `results_data`
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
run_id        UUID REFERENCES pipeline_runs(id)
level         TEXT CHECK (level IN ('word', 't2', 't3', 't4'))
attribute_t1  TEXT
attribute_t2  TEXT
attribute_t3  TEXT
attribute_t4  TEXT
word1         TEXT
word2         TEXT
mentions      INT
positive      INT
negative      INT
total         INT
positive_pct  FLOAT
negative_pct  FLOAT
mentions_assoc    TEXT
sentiment_assoc   TEXT
overall_assoc     TEXT
```

### `taxonomy_suggestions`
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
run_id        UUID REFERENCES pipeline_runs(id)
word1         TEXT
word2         TEXT
suggested_t1  TEXT
suggested_t2  TEXT
suggested_t3  TEXT
suggested_t4  TEXT
status        TEXT CHECK (status IN ('pending', 'approved', 'rejected', 'edited'))
reviewed_by   UUID REFERENCES users(id)
reviewed_at   TIMESTAMPTZ
analyst_notes TEXT
```

### `feedback`
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
run_id        UUID REFERENCES pipeline_runs(id)
user_id       UUID REFERENCES users(id)
category      TEXT CHECK (category IN ('accuracy', 'completeness', 'usefulness', 'general'))
rating        INT CHECK (rating BETWEEN 1 AND 5)
comment       TEXT
attribute_ref TEXT (optional — which T1/T2 the feedback refers to)
created_at    TIMESTAMPTZ DEFAULT now()
```

---

## Page-by-Page UI Specification

### Page 1: `/` — Landing Page

**For:** Unauthenticated visitors / leads receiving a link

**Content:**
- AntiGravity brand hero section with tagline: *"AI-Powered Brand Association Intelligence"*
- Brief explainer: what BAM does (3-step visual: Upload → Analyse → Insights)
- "Sign In" button → Supabase Auth (magic link email for leads, password for analysts)
- Clean, dark-themed, premium aesthetic — glassmorphism cards, subtle animations

---

### Page 2: `/dashboard` — Association Map Dashboard

**For:** Leads + Analysts (authenticated)

**Content:**
- **Client selector** dropdown at top (for analysts with multi-client access)
- **Latest run summary cards:** total mentions, total bigrams, tagged %, positive/negative split
- **Association Heat Map** (main visual): 
  - X-axis: T2 themes
  - Y-axis: T1 pillars
  - Cell colour: Association strength (Strong=green, Moderate=yellow, Weak=orange, Negligible=red)
  - Cell size: proportional to mention count
  - Click a cell → drill down to T3/T4 detail
- **Sentiment Distribution** bar chart: stacked positive/negative per T1
- **Top 20 Associations** table: sortable by mentions, sentiment, association strength
- **Download Excel** button: downloads the full output file from Supabase storage
- **"Give Feedback"** floating button → opens feedback modal

**Data source:** `results_data` table filtered by `run_id` of the latest completed run

---

### Page 3: `/taxonomy` — AI Taxonomy Review (Analyst Only)

**For:** Analysts

**Content:**
- Table of AI-suggested taxonomy entries from `taxonomy_suggestions` where `status = 'pending'`
- Columns: word1, word2, Suggested T1, T2, T3, T4, Action buttons
- **Actions per row:**
  - ✅ Approve — sets status to 'approved'
  - ✏️ Edit — inline edit T1–T4 values, then approve
  - ❌ Reject — marks as 'rejected' with optional note
- **Bulk actions:** "Approve All", "Reject All Noise"
- **Stats bar:** X pending, Y approved, Z rejected
- **"Merge to Taxonomy"** button: takes all approved suggestions and appends them to the client's taxonomy file in Supabase storage

---

### Page 4: `/upload` — Data Upload & Pipeline Run (Analyst Only)

**For:** Analysts

**Content:**
- **Client selector** (or "Create New Client" flow)
- **File upload** dropzone: accepts `.xlsx` files
- **Config preview:** shows the loaded client JSON config (editable for overrides)
- **"Run Pipeline"** button → POST to FastAPI backend
- **Progress indicator:** pending → running (with stage updates) → completed
- **Run history** table below: past runs with status, date, download link
- Checkbox: "Also generate AI taxonomy for untagged bigrams"

---

### Page 5: `/feedback` — Feedback Collection

**For:** Leads

**Content:**
- **Overall rating** (1–5 stars): "How useful was this BAM analysis?"
- **Category-specific ratings:**
  - Accuracy: "How accurate are the brand associations?"
  - Completeness: "Are there associations missing that you expected?"
  - Usefulness: "How actionable are these insights for your team?"
- **Open comment** text area
- **Specific attribute feedback:** optional — select a T1/T2 from dropdown and comment on it
- **Submit** → saves to `feedback` table
- **Thank you** screen with AntiGravity branding

---

### Page 6: `/admin` — Feedback Dashboard (Admin Only) 

**For:** AntiGravity team

**Content:**
- Aggregated feedback across all clients and runs
- Average ratings by category (accuracy, completeness, usefulness)
- Recent comments feed
- Filter by client, date range
- Export feedback to CSV

---

## FastAPI Backend Endpoints

### `POST /api/run-pipeline`
```json
Request:
{
  "client_id": "uuid",
  "input_file_url": "supabase-storage-path",
  "generate_taxonomy": true/false
}

Response:
{
  "run_id": "uuid",
  "status": "running"
}
```

### `GET /api/results/{run_id}`
```json
Response:
{
  "status": "completed",
  "summary": {
    "total_messages": 10000,
    "total_bigrams": 4523,
    "tagged_pct": 78.5,
    "positive_pct": 56.2
  },
  "results": {
    "word_level": [...],
    "t2": [...],
    "t3": [...],
    "t4": [...]
  },
  "output_file_url": "https://..."
}
```

### `POST /api/feedback`
```json
Request:
{
  "run_id": "uuid",
  "category": "accuracy",
  "rating": 4,
  "comment": "Mostly accurate but missed some sustainability mentions",
  "attribute_ref": "Brand Love > Rebranding & Marketing"
}
```

### `POST /api/generate-taxonomy`
Triggers NVIDIA NIM taxonomy generation for untagged bigrams of a given run.

### `POST /api/taxonomy/approve`
Bulk approve/reject taxonomy suggestions.

### `GET /api/clients`
List all configured clients.

---

## Deployment Plan

### Step 1: Supabase Setup
1. Create Supabase project (free tier)
2. Run SQL migrations to create all tables above
3. Enable Auth (magic link for leads, email/password for analysts)
4. Create storage buckets: `uploads`, `outputs`, `taxonomies`
5. Set up Row Level Security (RLS): leads see only their client's data

### Step 2: FastAPI Backend on Railway
1. Create `backend/` folder with FastAPI app
2. Include all `src/` modules from Part 1 as importable packages
3. Add Supabase Python client for DB reads/writes
4. Add file upload handling (receive from Vercel → store in Supabase Storage)
5. Dockerfile for Railway deployment
6. Environment variables: `SUPABASE_URL`, `SUPABASE_KEY`, `NVIDIA_API_KEY`

### Step 3: Next.js Frontend on Vercel
1. `npx create-next-app@latest` with App Router, TypeScript, Tailwind
2. Install: `@supabase/supabase-js`, `recharts` or `@nivo/core`, `shadcn/ui`
3. Build pages in order: Landing → Dashboard → Upload → Taxonomy → Feedback → Admin
4. API routes in `/app/api/` proxy to Railway backend
5. Connect to Git repo → auto-deploy on Vercel

### Step 4: Connect & Test
1. Analyst uploads Input_Data_1.xlsx via `/upload`
2. Pipeline runs on Railway, results stored in Supabase
3. Dashboard renders the association heat map
4. Share dashboard link with a test lead
5. Lead views results, submits feedback
6. Verify feedback appears in `/admin`

---

## Build Order (for execution)

| Step | What | Est. Time |
|---|---|---|
| 1 | Supabase project + schema + auth + storage | 2 hours |
| 2 | FastAPI backend wrapping Part 1 engine | 4 hours |
| 3 | Deploy FastAPI on Railway | 1 hour |
| 4 | Next.js scaffold + Tailwind + shadcn setup | 1 hour |
| 5 | Landing page (`/`) | 2 hours |
| 6 | Auth flow (login/signup) | 2 hours |
| 7 | Upload page (`/upload`) | 3 hours |
| 8 | Dashboard page (`/dashboard`) + charts | 6 hours |
| 9 | Taxonomy review page (`/taxonomy`) | 4 hours |
| 10 | Feedback page (`/feedback`) | 2 hours |
| 11 | Admin feedback dashboard (`/admin`) | 3 hours |
| 12 | Vercel deployment + domain setup | 1 hour |
| 13 | End-to-end test with real data | 3 hours |
| **Total** | | **~34 hours** |

---

## Open Questions

1. **Custom domain?** Do you want this on something like `bam.antigravity.ai` or just the default Vercel URL for now?
2. **Lead access model:** Should leads get a unique link per report (no login needed), or must they create an account? Magic links (email-based, no password) are the smoothest UX for leads.
3. **Railway vs Render:** Railway has a $5/mo hobby plan with always-on containers. Render has a free tier but containers spin down after inactivity (cold starts). Preference?
4. **Do you want the Part 1 (Python engine) built first and tested before we start the UI, or should we build both in parallel?**
