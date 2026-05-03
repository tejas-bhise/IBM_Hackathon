<p align="center">
  <img src="https://img.shields.io/badge/IBM%20Bob-Hackathon-052FAD?style=for-the-badge&logo=ibm&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-Frontend-000000?style=for-the-badge&logo=next.js&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
</p>

<h1 align="center">AI Project Intelligence Platform</h1>
<p align="center"><strong>Turn any codebase into a living, intelligent system for faster, safer development.</strong></p>

<p align="center">
  <a href="https://github.com/tejas-bhise/IBM_Hackathon">
    <img src="https://img.shields.io/badge/Repository-IBM__Hackathon-181717?style=flat-square&logo=github" />
  </a>
  &nbsp;
  <img src="https://img.shields.io/badge/Status-In%20Development-orange?style=flat-square" />
  &nbsp;
  <img src="https://img.shields.io/badge/Hackathon-IBM%20Bob%202025-052FAD?style=flat-square" />
</p>

***

## Overview

Software teams spend enormous amounts of time doing things that should be automatic — understanding new codebases, hunting for security issues, losing context between sprints, and explaining the same system to different stakeholders repeatedly. These are not edge cases; they are the daily friction that slows every serious engineering team.

**AI Project Intelligence Platform** eliminates that friction. Upload any GitHub repository or ZIP archive, and the platform produces a comprehensive, continuously updated intelligence layer over your codebase — security audit, architecture summary, project memory, workflow stage assessment, and an interactive AI assistant — all from a single submission.

> *"A system that turns any project into a continuously updated, secure, and understandable knowledge system."*

***

## Problem Statement

Modern software development teams face four compounding problems that collectively waste thousands of engineering hours per year:

**1. Codebase Comprehension Delay**  
New developers take days or weeks to understand a project's structure, data flow, and critical modules. There is no automated system that reads a repository and explains what it does, how it is organized, and where to start.

**2. Security & Privacy Blind Spots**  
Most teams lack dedicated security review cycles. PII exposure (emails, phone numbers, passwords), hardcoded secrets, API key leaks, and SQL injection patterns routinely ship to production because no automated, developer-facing tool flags them at the code level before deployment.

**3. Context Loss Over Time**  
Developers return from leave, context-switch between projects, or join mid-sprint with zero institutional memory of recent changes. Commit logs are a poor substitute for semantic understanding of *what* changed and *why*.

**4. Team Misalignment**  
Product managers, developers, and business stakeholders read the same codebase differently — or not at all. The absence of role-appropriate explanations means decisions are made on incomplete information, causing late-stage rejections and wasted effort.

No existing tool addresses all four problems together with AI-driven intelligence at the codebase level.

***

## Solution

A unified AI platform that ingests a codebase once and produces structured, actionable intelligence across five dimensions:

| Dimension | What it delivers |
|---|---|
| **Security Audit** | Automated detection of PII, secrets, SQL injection, unsafe patterns with per-issue fix suggestions |
| **Project Understanding** | Architecture summary, tech stack detection, entry point identification, module-level explanation |
| **Project Memory** | Semantic tracking of recent work, features, refactors, and active development areas |
| **Workflow Intelligence** | Stage classification (prototype → production-ready), risk level, blockers, recommended next actions |
| **AI Chat Assistant** | Natural language Q&A over the codebase with RAG-powered context retrieval |

The result is a platform that functions simultaneously as a **Project Brain**, a **Security Auditor**, and a **Memory System** — serving developers, product managers, and technical leads from a single interface.

***

## Core Features

### Security & Privacy Auditor
The primary feature of the platform. The scanner ingests all source files and runs a multi-layer detection pipeline covering:

- **PII Detection** — email addresses, phone numbers, password fields embedded in source
- **Secret Detection** — hardcoded API keys, tokens, credentials, and environment variable misuse  
- **Vulnerability Patterns** — SQL injection via string concatenation, unsafe query construction, unvalidated inputs
- **Mock Data Generator** — when PII is found, the system generates safe synthetic replacement data to assist remediation

Each issue is returned with severity classification (CRITICAL / HIGH / MEDIUM / LOW), file path, line number, code snippet, explanation, and a concrete fix suggestion.

### Project Memory
A deterministic + AI-augmented memory system that tracks what the team has been working on. Given a repository, it:

- Parses Git commit history (when available) and categorizes commits by feature area
- Scores and ranks source files by architectural importance
- Infers active development areas, last focus, and development phase
- Returns structured memory across four buckets: Recent Work, Features, Security, Refactors

This enables the "vacation use case" — a developer returning after time off can immediately answer *"What did I work on last?"* without reading through commit logs.

### Project Understanding
Automated architecture analysis that produces:

- One-paragraph natural language description of what the project does
- Tech stack detection (frameworks, languages, databases)
- Entry point identification
- Architecture type classification (Layered Monolith, Microservices, MVC, etc.)
- Module-level data flow summary

### AI Alerts & Review System
Beyond the static scanner, an LLM-powered review layer generates contextual alerts — flagging risky patterns, suggesting architectural improvements, and explaining *why* a pattern is dangerous rather than just flagging it.

### Role-Based Workflow Intelligence
The workflow engine classifies projects along a deployment readiness axis and generates role-appropriate outputs:

- **Developer view** — technical blockers, refactor suggestions, security debt
- **PM view** — feature completion status, risk level, recommended actions
- **Investor/stakeholder view** — plain-language project health summary

***

## IBM Bob Integration

IBM Bob serves as the primary AI reasoning engine powering the platform's intelligence layer.

**Bob is used for:**

- **Code summarization** — Bob reads source files and generates architectural summaries, module descriptions, and data flow explanations that would be impossible to produce with rule-based systems alone
- **Security reasoning** — Beyond pattern matching, Bob interprets *why* a code pattern is risky and generates contextual fix suggestions tailored to the specific codebase
- **Memory generation** — Bob processes file importance rankings and commit history to produce natural language project memory narratives
- **Workflow assessment** — Bob evaluates overall project health, classifies development stage, and recommends concrete next actions
- **Conversational Q&A** — Bob powers the chat interface, maintaining codebase context across multi-turn conversations via RAG retrieval

The system is built with a `smart_llm_call` routing layer that directs tasks to Bob as the primary model, with Gemini and Groq as fallback providers when needed to ensure availability during high-load hackathon demonstration.

> **Note on watsonx.ai / Orchestrate:** The architecture is designed to integrate with watsonx.ai as a deployment target. The `smart_llm_call` abstraction layer allows the LLM backend to be swapped per task type, enabling watsonx.ai to be substituted or augmented as IBM infrastructure access is provisioned. This integration is the immediate next step post-hackathon.

***

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│              Next.js 15 + React + Tailwind CSS                  │
│   Upload → Dashboard → Security → Memory → Workflow → Chat     │
└─────────────────────┬───────────────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────────────────┐
│                       BACKEND (FastAPI)                         │
│                                                                 │
│  /api/upload    /api/analysis    /api/workflow                  │
│  /api/memory    /api/chat        /api/mock     /api/summary     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   PROCESSING PIPELINE                    │  │
│  │  Ingestion → Scanning → Summarization → Memory →         │  │
│  │  Workflow Engine → Embedding → Chat Engine               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
  ┌──────────┐  ┌──────────┐  ┌──────────────┐
  │ IBM Bob  │  │ MongoDB  │  │ Vector Store │
  │ (Primary │  │ (Project │  │ (Embeddings  │
  │   LLM)   │  │  State)  │  │  for RAG)    │
  └──────────┘  └──────────┘  └──────────────┘
        │
  ┌─────▼──────────────┐
  │  Gemini / Groq     │
  │  (Fallback LLMs)   │
  └────────────────────┘
```

***

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 15, React, TypeScript, Tailwind CSS |
| **Backend** | FastAPI (Python 3.11+) |
| **Primary AI** | IBM Bob |
| **Fallback LLMs** | Google Gemini, Groq |
| **Database** | MongoDB (project state), PostgreSQL (structured data) |
| **Vector Store** | Embedding-based RAG for chat context |
| **Deployment** | IBM Cloud |

***

## Repository Structure

```
IBM_Hackathon/
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── routes/
│   │   ├── upload.py            # GitHub URL + ZIP upload handling
│   │   ├── analysis.py          # Security analysis results
│   │   ├── workflow.py          # Workflow stage & risk assessment
│   │   ├── memory.py            # Project memory API
│   │   ├── chat.py              # AI chat interface
│   │   ├── summary.py           # Project summary
│   │   └── mock.py              # Mock data generation
│   ├── services/
│   │   ├── scanner.py           # PII + vulnerability detection engine
│   │   ├── summarizer.py        # LLM-powered code summarization
│   │   ├── memory.py            # Memory build & Git analysis
│   │   ├── workflow_engine.py   # Stage classification & risk scoring
│   │   ├── embedder.py          # Vector embedding for RAG
│   │   ├── chat_engine.py       # Conversational AI with context
│   │   ├── ingestion.py         # File parsing & preprocessing
│   │   ├── pipeline.py          # End-to-end analysis orchestration
│   │   ├── ai_client.py         # LLM routing (Bob → Gemini → Groq)
│   │   ├── alert_builder.py     # Structured alert generation
│   │   └── mock_generator.py    # Synthetic PII replacement data
│   └── db/
│       └── mongo.py             # MongoDB collections
├── frontend/
│   ├── app/
│   │   ├── dashboard/
│   │   │   ├── page.tsx         # Dashboard entry (SSR wrapper)
│   │   │   └── DashboardClient.tsx  # Main dashboard UI
│   │   └── upload/
│   │       └── page.tsx         # Upload interface
│   └── lib/
│       ├── api.ts               # Typed API client
│       └── store.ts             # Client state (project ID)
└── README.md
```

***

## User Flow

```
1. Upload          →   Paste GitHub repo URL or upload ZIP archive
2. Analysis        →   Platform ingests, scans, and analyzes the codebase
                       (security audit + summarization + memory + workflow)
3. Dashboard       →   View security score, issue breakdown, tech stack,
                       architecture summary, and project description
4. Deep Dive       →   Drill into individual security issues with
                       file path, line number, code snippet, and fix suggestion
5. Workflow        →   Review deployment stage, risk level, blockers,
                       and recommended next actions
6. Memory          →   Inspect recent work, features, security history,
                       and refactors tracked over time
7. Chat            →   Ask natural language questions about the codebase
                       ("Where is auth handled?", "What changed recently?")
```

***

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB instance (local or Atlas)
- IBM Bob API key

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add: BOB_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, MONGO_URI

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Configure environment
cp .env.example .env.local
# Add: NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

***

## Submission Checklist

| Item | Status |
|---|---|
| GitHub Repository | ✅ [github.com/tejas-bhise/IBM_Hackathon](https://github.com/tejas-bhise/IBM_Hackathon) |
| Problem + Solution (≤ 500 words) | ✅ Documented above |
| IBM Bob Usage Explanation | ✅ Documented above |
| Video Demonstration | 🔄 *To be added — YouTube link pending upload* |
| watsonx.ai / Orchestrate Integration | 🔄 *Architecture prepared; integration in progress* |

***

## Problem + Solution (Hackathon Submission — ≤ 500 words)

**Problem:** Every software team wastes time on four recurring bottlenecks. Developers spend days understanding new codebases instead of contributing. Security vulnerabilities — PII leaks, hardcoded secrets, SQL injection — go undetected until production because no lightweight, developer-facing tool flags them continuously. Context is lost whenever developers switch projects or return from leave, forcing them to re-read commit histories and documentation that rarely exists. And across roles — developer, PM, stakeholder — the same project is explained differently and understood inconsistently, causing misalignment that results in rejected work and wasted effort.

**Why it matters:** These are not niche problems. Every team above five people experiences all four. The cost is measurable: slower onboarding, delayed deployments, security incidents, and re-work cycles that compound over time. Enterprise teams lose weeks per quarter to problems that a sufficiently intelligent system could eliminate.

**Solution:** The AI Project Intelligence Platform accepts any GitHub repository or ZIP archive and, in a single pipeline run, produces: a scored security audit with per-issue fixes; a plain-language architecture summary with tech stack detection and data flow explanation; a semantic project memory tracking recent work, features, and refactors; a workflow stage assessment with blockers and recommended actions; and a RAG-powered chat interface for natural language codebase queries. IBM Bob drives the reasoning layer — interpreting code patterns, generating contextual fix suggestions, building memory narratives, and powering conversational Q&A. The platform reduces codebase onboarding from days to minutes, surfaces security debt before it reaches production, and gives every team member — regardless of role — the exact level of project understanding they need.

***

## License

This project was built for the IBM Bob Hackathon. All rights reserved by the authors.

***

