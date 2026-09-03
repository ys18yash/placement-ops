# PlacementOps

## Deterministic Placement Scheduling Engine

**PlacementOps is a constraint-aware interview scheduling and deterministic
replanning platform built for high-volume campus placement operations.**

It models placement week as a multi-resource scheduling problem across
**students, companies, interviewer panels, rooms, availability windows, and
placement days** — then generates a reproducible schedule and safely replans
it when real-world disruptions occur.

**[Live Demo](YOUR_LIVE_LINK) · [GitHub](YOUR_GITHUB_LINK) · [API Docs](YOUR_API_LINK)**

---

### The System at a Glance

| Scale | Result |
|---|---:|
| Candidates | **800** |
| Companies | **35** |
| Interview Panels | **85** |
| Interview Rooms | **20** |
| Interview Requests | **859** |
| Placement Days | **4** |
| Scheduled Interviews | **476** |
| Unscheduled Interviews | **383** |
| Completion Rate | **55.41%** |
| Schedule Generation | **~130 ms** |
| Scheduling Conflicts | **0** |

---

### What Makes PlacementOps Interesting

**Constraint-aware scheduling**  
Allocates interviews while respecting student availability, company day
constraints, interviewer-panel capacity, room capacity, operating windows,
and overlap rules.

**Deterministic execution**  
The same dataset and seed produce the same schedule, making results
reproducible, testable, and easy to reason about.

**Deterministic replanning**  
Operational disruptions such as room outages, panel unavailability, company
delays, and student withdrawals trigger a new valid schedule without
discarding the scheduling constraints.

**Performance-focused engine**  
The scheduler uses indexed resource occupancy, precomputed availability,
incremental scoring, and safe candidate pruning to avoid repeated linear
scans.

**Operations-focused interface**  
The frontend provides schedule exploration, a visual timeline, operational
analytics, disruption simulation, replanning impact analysis, notifications,
and a grounded Gemini assistant.

---

### Core Workflow

```text
Placement Data
      ↓
Constraint-Aware Scheduling
      ↓
Validated Deterministic Schedule
      ↓
Inspect / Analyze
      ↓
Operational Disruption
      ↓
Deterministic Replanning
      ↓
Impact Analysis

## The Problem

Scheduling a campus placement week is not simply a matter of assigning
interviews to available time slots.

With hundreds of candidates, multiple companies, interviewer panels, rooms,
placement days, and availability windows, every assignment consumes several
shared resources at once. A decision that is valid in isolation can make a
later interview impossible to schedule.

For PlacementOps, an interview can only be accepted when its complete
assignment is feasible across the relevant dimensions:

```text
                 Interview Request
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
      Candidate      Company       Resources
      availability   day rules     panel + room
          │             │             │
          └─────────────┼─────────────┘
                        ↓
                 Time-window check
                        ↓
                Conflict validation
                        ↓
                 Valid assignment


## The Solution

PlacementOps is designed as a deterministic scheduling system that builds,
validates, and continuously adapts a placement-week schedule.

Rather than treating an interview as an isolated calendar event, PlacementOps
assigns each interview across the full set of scheduling dimensions:

```text
Interview
   │
   ├── Candidate
   ├── Company
   ├── Placement Day
   ├── Time Window
   ├── Interview Panel
   └── Room   

## Key Capabilities

PlacementOps combines deterministic scheduling, disruption recovery, and
operational analysis into a single placement-week workflow.

### Schedule Generation

**Constraint-Aware Scheduling**  
Builds interview assignments across candidates, companies, interviewer panels,
rooms, placement days, availability windows, interview durations, and overlap
constraints.

**Deterministic Execution**  
Uses stable interview ordering, deterministic candidate scoring, and
consistent tie-breaking so the same dataset and seed produce the same schedule.

**Resource-Aware Allocation**  
Tracks shared student, panel, and room occupancy while the schedule is being
constructed, preventing conflicting assignments.

**Explicit Unscheduled Outcomes**  
When no feasible assignment remains, the interview is kept explicitly
unscheduled rather than forcing an invalid placement.

---

### Disruption & Replanning

**Deterministic Replanning**  
Adapts the schedule to operational changes while preserving the same scheduling
constraints used during initial generation.

Supported disruptions:

| Disruption | Example |
|---|---|
| **Room Unavailable** | A scheduled interview room becomes unavailable. |
| **Panel Unavailable** | An interviewer panel can no longer participate. |
| **Company Delay** | A company changes when its interviews can begin. |
| **Student Withdrawal** | A candidate withdraws from the placement process. |

**Impact Classification**  
Every affected interview is explicitly classified as:

```text
RESCHEDULED
UNSCHEDULED
UNCHANGED 

## System Architecture

PlacementOps is organized as a layered system where the frontend, API, scheduling
engine, replanning logic, analytics, and AI assistant have clear
responsibilities.

```text
                         ┌────────────────────────────┐
                         │     React Operations UI     │
                         │                            │
                         │  Schedule · Timeline       │
                         │  Analytics · Replanning    │
                         │  Assistant · Notifications │
                         └──────────────┬─────────────┘
                                        │
                              HTTP / SSE│
                                        ▼
                         ┌────────────────────────────┐
                         │       FastAPI Backend      │
                         │                            │
                         │  Validation · Services     │
                         │  Schedule APIs · Assistant │
                         └───────┬─────────┬──────────┘
                                 │         │
                    ┌────────────┘         └─────────────┐
                    ▼                                    ▼
          ┌───────────────────┐                ┌───────────────────┐
          │ Scheduling Engine │                │ Replanning Engine │
          │                   │                │                   │
          │ Ordering          │                │ Disruptions       │
          │ Candidate search  │                │ Affected jobs     │
          │ Constraints       │                │ Rescheduling      │
          │ Scoring           │                │ Validation        │
          └─────────┬─────────┘                └─────────┬─────────┘
                    │                                    │
                    └────────────────┬───────────────────┘
                                     ▼
                           ┌────────────────────┐
                           │ Placement Dataset  │
                           │                    │
                           │ Students           │
                           │ Companies          │
                           │ Panels             │
                           │ Rooms              │
                           │ Interviews         │
                           │ Availability       │
                           └────────────────────┘

                                      AI
                                       │
                                       ▼
                              ┌─────────────────┐
                              │   Google Gemini │
                              │                 │
                              │ Natural-language│
                              │ assistance      │
                              └─────────────────┘

                              
## Scheduling Engine

The scheduling engine is the core of PlacementOps.

It builds the placement-week schedule incrementally by evaluating feasible
assignments, applying hard constraints, scoring valid candidates, and selecting
the result deterministically.

It is a **deterministic heuristic scheduler**, not a claim of globally optimal
scheduling.

### Scheduling Flow

```text
Interview Requests
        │
        ▼
Deterministic Ordering
        │
        ▼
Generate Assignment Candidates
        │
        ▼
Hard Constraint Checks
        │
        ├── invalid ──────────► reject
        │
        ▼
Score Feasible Candidates
        │
        ▼
Deterministic Tie-Breaking
        │
        ▼
Assign Best Candidate
        │
        ▼
Update Scheduling State
        │
        └────────────────────► next interview

## Replanning & Disruption Recovery

A placement schedule is not static.

During placement week, resources can become unavailable, interview windows can
change, or a candidate can withdraw after the schedule has already been
generated.

PlacementOps treats these events as **operational disruptions** and produces a
new deterministic schedule state while preserving the scheduling constraints.

### Supported Disruptions

| Disruption | Effect |
|---|---|
| **Room Unavailable** | Removes a room from the affected scheduling period. |
| **Panel Unavailable** | Removes an interviewer panel from the affected scheduling period. |
| **Company Delay** | Applies the configured timing restriction to affected company interviews. |
| **Student Withdrawal** | Removes the student's scheduled interviews from the schedule. |

### Replanning Flow

```text
Existing Schedule
       │
       ▼
Disruption Detected
       │
       ▼
Identify Affected Assignments
       │
       ▼
Preserve Unaffected Assignments
       │
       ▼
Release Affected Resources
       │
       ▼
Search for Feasible Alternatives
       │
       ▼
Deterministic Reassignment
       │
       ▼
Validate Final Schedule
       │
       ▼
Replanned Schedule

## Data Model & Dataset

PlacementOps uses a deterministic synthetic dataset to model a high-volume
campus placement week.

The dataset represents the participants, organizations, interviewer resources,
physical resources, interview demand, and time constraints required by the
scheduling engine.

### Core Model

```text
┌────────────┐
│  Student   │
└─────┬──────┘
      │
      │ interview request
      ▼
┌────────────┐       ┌────────────┐
│ Interview  │──────►│  Company   │
│   Request  │       └────────────┘
└─────┬──────┘
      │
      ├──────────────► Placement Day
      │
      ├──────────────► Time Window
      │
      ├──────────────► Interview Panel
      │
      └──────────────► Interview Room

## API Design

PlacementOps exposes a small FastAPI surface around the scheduling domain.
HTTP handlers validate requests and delegate the actual scheduling and
replanning decisions to the backend services.

### API Surface

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Backend health check |
| `POST` | `/schedule/generate` | Generate the initial deterministic schedule |
| `POST` | `/schedule/replan` | Replan an existing schedule after a disruption |
| `POST` | `/assistant/stream` | Stream Gemini responses grounded in PlacementOps data |

The API is intentionally small: the frontend interacts with a few focused
operations rather than depending on internal scheduler implementation details.

### Schedule Generation

```text
POST /schedule/generate
        │
        ▼
Request Validation
        │
        ▼
Scheduling Service
        │
        ▼
Deterministic Scheduler
        │
        ▼
Schedule Validation
        │
        ▼
Structured Result

## Performance Engineering

PlacementOps was optimized using a profile-driven approach.

The goal was not simply to make the scheduler faster, but to reduce repeated
work while preserving the exact scheduling behavior of the canonical
implementation.

### From Profiling to Optimization

The baseline scheduler repeatedly scanned existing assignments and performed
large numbers of interval-overlap checks during candidate evaluation.

Profiling identified these operations as the dominant sources of execution
cost:

```text
Candidate Evaluation
        │
        ├── repeated resource scans
        │
        ├── interval-overlap checks
        │
        └── repeated state / scoring work
                ↓
          scheduling overhead

## Correctness, Testing & Validation

Correctness is a core requirement of PlacementOps.

The system validates scheduling behavior at both the individual constraint level
and the complete schedule level, with automated tests covering generation,
replanning, API validation, and regression behavior.

### Validation Layers

```text
Constraint Checks
        ↓
Schedule Integrity
        ↓
Replanning Validation
        ↓
API Tests
        ↓
End-to-End Scenarios
        ↓
Deterministic Regression

## Frontend & Operations Console

PlacementOps includes a recruiter-facing operations console for exploring and
managing the placement schedule.

The interface is built around the state produced by the backend scheduling
system. It does not contain an independent scheduling model or make scheduling
decisions in the browser.

### Operations Workspace

The console is organized around the main placement operations workflow:

```text
Overview
   ↓
Schedule
   ↓
Timeline
   ↓
Analytics
   ↓
Replanning
   ↓
Assistant

## AI Assistant & Gemini Integration

PlacementOps includes a Gemini-powered assistant that provides a natural-language
interface to the current scheduling state.

The assistant is deliberately separated from the scheduling engine:

> **PlacementOps makes scheduling decisions. Gemini helps operators understand
> them.**

### Assistant Flow

```text
User Question
      ↓
React Assistant
      ↓
FastAPI
      ↓
PlacementOps Context
      ↓
Gemini
      ↓
SSE Stream
      ↓
React

## Project Structure & Code Organization

PlacementOps is organized so that scheduling logic, API behavior, data
generation, and frontend presentation remain separated.

```text
placement-ops/
│
├── backend/
│   └── placementops/
│       ├── api/
│       │   ├── routes.py
│       │   └── service.py
│       │
│       ├── dataset/
│       │   └── generator.py
│       │
│       ├── scheduling/
│       │   ├── scheduler.py
│       │   ├── constraints.py
│       │   ├── replanner.py
│       │   └── metrics.py
│       │
│       └── app.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── ...
│   │
│   ├── package.json
│   └── vite.config.*
│
├── tests/
│   ├── test_api.py
│   ├── test_scheduling_replanner.py
│   └── test_scheduling_replanning_metrics.py
│
├── requirements.txt
├── .gitignore
└── README.md

## Technology Stack

PlacementOps uses a lightweight full-stack architecture with Python/FastAPI on
the backend and React/Vite on the frontend.

### Stack Overview

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | React 19 | Operations console and interactive scheduling views |
| **Build Tool** | Vite | Frontend development and production builds |
| **Frontend Language** | JavaScript | UI logic and application behavior |
| **Styling** | CSS | Responsive layout, themes, timeline, and dashboard styling |
| **Backend** | Python | Scheduling and application logic |
| **API Framework** | FastAPI | HTTP API, validation, and streaming responses |
| **ASGI Server** | Uvicorn | Runs the FastAPI application |
| **AI** | Google Gemini | Natural-language scheduling assistant |
| **Testing** | Python `unittest` | Backend and scheduling validation |
| **Version Control** | Git / GitHub | Source control and project hosting |

### Backend

The backend is built with:

```text
Python
   ↓
FastAPI
   ↓
Uvicorn
   ↓
PlacementOps Scheduling Domain

## Local Development & Setup

PlacementOps can be run locally as two processes:

    React / Vite Frontend
            │
            │ HTTP
            ▼
    FastAPI Backend
            │
            ▼
    PlacementOps Scheduling Engine

### Prerequisites

Install:

- Python 3.x
- Node.js and npm
- Git

The exact supported versions should match the versions documented by the
repository's dependency files.

### Clone the Repository

    git clone <YOUR_GITHUB_REPOSITORY>
    cd placement-ops

### Backend Setup

Create a Python virtual environment:

    python -m venv .venv

Windows:

    .venv\Scripts\activate

macOS / Linux:

    source .venv/bin/activate

Install backend dependencies:

    pip install -r requirements.txt

Start the FastAPI server from the repository root:

    python -m uvicorn placementops.app:app --reload --app-dir backend

The backend will be available at:

    http://127.0.0.1:8000

Health check:

    http://127.0.0.1:8000/health

Interactive API documentation:

    http://127.0.0.1:8000/docs

### Frontend Setup

Open a second terminal:

    cd frontend

Install dependencies:

    npm install

Start the Vite development server:

    npm run dev

The frontend will be available at the local URL printed by Vite.

### Development API Connection

During local development, the frontend communicates with the FastAPI backend
through the configured API base URL / Vite proxy.

    Browser
       ↓
    Vite Development Server
       ↓
    FastAPI :8000
       ↓
    PlacementOps

This keeps frontend development separate from the backend process while
allowing the operations console to use the live scheduling APIs.

### Gemini Configuration

Gemini credentials must remain server-side.

Configure the backend with the environment variables expected by the
application:

    GEMINI_API_KEY=<your-key>
    GEMINI_MODEL=<configured-model>

Do not commit API credentials or local environment files to Git.

### Running the Full Application

Start both processes:

    Terminal 1
    ──────────
    FastAPI
      ↓
    http://127.0.0.1:8000

    Terminal 2
    ──────────
    React / Vite
      ↓
    Local frontend URL

Open the frontend in a browser to generate schedules, inspect assignments,
simulate disruptions, run replanning, and use the assistant.

### Running Tests

From the repository root:

    python -m unittest discover -s tests -p "test_*.py"

The test suite validates the backend scheduling and operational workflows.

### Canonical Dataset

The canonical dataset uses:

    Seed: 20260829

The fixed seed provides a reproducible workload for local testing,
benchmarking, and regression comparisons.

### Development Workflow

A typical development cycle is:

    Modify Code
        ↓
    Run Tests
        ↓
    Run Backend
        ↓
    Run Frontend
        ↓
    Exercise Scheduling Workflow
        ↓
    Validate Result
        ↓
    Commit Changes

The frontend and backend can therefore be developed independently while
sharing the same scheduling API contract.

## API Usage & Example Workflow

PlacementOps can be used through the FastAPI endpoints independently of the
React frontend.

The main operational workflow is:

    Generate
       ↓
    Inspect
       ↓
    Disrupt
       ↓
    Replan
       ↓
    Analyze

### Generate a Schedule

Send a request to:

    POST /schedule/generate

The endpoint generates the schedule from the configured placement dataset and
returns the scheduling result.

Conceptually:

    Client
      ↓
    /schedule/generate
      ↓
    Scheduler
      ↓
    Validated Schedule
      ↓
    JSON Response

Example:

    curl -X POST http://127.0.0.1:8000/schedule/generate

The exact request body should match the request schema exposed by the FastAPI
documentation.

### Replan After a Disruption

Send a request to:

    POST /schedule/replan

The request specifies the disruption and the information required to apply it
to the current scheduling state.

Supported disruption types:

    ROOM_UNAVAILABLE
    PANEL_UNAVAILABLE
    COMPANY_DELAY
    STUDENT_WITHDRAWAL

The replanning response contains the resulting scheduling state and the
information required to understand the operational impact.

### Health Check

Verify that the backend is running:

    curl http://127.0.0.1:8000/health

### Interactive API Documentation

FastAPI exposes interactive documentation at:

    http://127.0.0.1:8000/docs

The documentation is the authoritative reference for the current request and
response schemas.

### Example Operational Workflow

A typical API-driven workflow is:

    1. Generate the baseline schedule.
    2. Inspect scheduled and unscheduled interviews.
    3. Apply an operational disruption.
    4. Run deterministic replanning.
    5. Validate the resulting schedule.
    6. Compare the original and replanned state.

This makes it possible to operate PlacementOps without relying on the React
frontend.

---

## Deployment & Production Configuration

PlacementOps is designed to separate the frontend deployment from the
FastAPI backend.

A practical production setup is:

    GitHub
      │
      ├──────────────► Vercel
      │                 React / Vite Frontend
      │
      └──────────────► Render
                        FastAPI Backend
                            │
                            ▼
                         Gemini

### Frontend Deployment

The React application can be deployed from the `frontend` directory.

Typical Vercel configuration:

    Root Directory: frontend
    Build Command: npm run build
    Output Directory: dist

The production frontend should point to the deployed FastAPI backend through
the configured API base URL.

Example:

    VITE_API_BASE_URL=https://<your-backend>.onrender.com

### Backend Deployment

The FastAPI application can be deployed as a Python web service.

Typical Render configuration:

    Root Directory: /
    Build Command: pip install -r requirements.txt

Start command:

    uvicorn placementops.app:app --host 0.0.0.0 --port $PORT --app-dir backend

Production deployments should not use:

    --reload

The deployed service should expose:

    /health
    /docs

### Environment Variables

Backend-only configuration should be supplied through environment variables.

Example:

    GEMINI_API_KEY=<your-key>
    GEMINI_MODEL=<configured-model>

Frontend configuration may include:

    VITE_API_BASE_URL=<deployed-backend-url>

Secrets must never be committed to the repository or embedded in frontend
source code.

### CORS

The FastAPI backend must allow requests from the deployed frontend origin.

For production, CORS should be configured for the actual frontend origin
rather than using an unnecessarily broad wildcard policy.

Conceptually:

    Vercel Frontend
          │
          │ HTTPS
          ▼
    Render FastAPI
          │
          ▼
    PlacementOps

### Production Request Flow

    Browser
       ↓
    Vercel
       ↓
    FastAPI API
       ↓
    Scheduling / Replanning
       ↓
    Response

For assistant requests:

    Browser
       ↓
    FastAPI
       ↓
    Gemini
       ↓
    SSE Stream
       ↓
    Browser

This keeps provider credentials and scheduling logic on the server side.

### Deployment Checklist

Before publishing the live application:

    Backend
    ├── production start command configured
    ├── /health responds successfully
    ├── /docs responds successfully
    ├── environment variables configured
    └── CORS restricted to the frontend origin

    Frontend
    ├── production build succeeds
    ├── API base URL points to the deployed backend
    └── no local development URLs remain

    Repository
    ├── secrets excluded
    ├── environment files ignored
    ├── generated build artifacts ignored
    └── tests pass

---

## Future Improvements

PlacementOps is intentionally focused on the core placement scheduling and
replanning workflow.

Potential future improvements include:

### Scheduling

    • stronger optimization objectives beyond the current heuristic scoring
    • additional fairness constraints across candidates and resources
    • improved handling of multi-stage interview processes
    • larger-scale workload benchmarking
    • optional comparison with mathematical optimization approaches

### Replanning

    • richer disruption combinations
    • configurable replan objectives
    • priority-aware preservation of critical assignments
    • historical disruption tracking
    • operator approval before committing a replan

### Operations

    • persistent schedule storage
    • user authentication and role-based access
    • audit logs for operational changes
    • richer export formats
    • calendar and notification integrations

### Analytics

    • historical utilization trends
    • resource bottleneck forecasting
    • company-level capacity analysis
    • what-if simulation for additional staffing or rooms

### AI

    • broader natural-language exploration of scheduling state
    • configurable assistant actions with explicit approval
    • richer context selection for complex operational questions
    • evaluation of assistant responses against deterministic application facts

These improvements would extend the system while preserving its central design
principle:

    deterministic scheduling state
            +
    explicit operational controls
            +
    AI-assisted interpretation

---

## Project Links

    Live Demo:  YOUR_LIVE_LINK
    GitHub:     YOUR_GITHUB_LINK
    API Docs:   YOUR_API_LINK

---

## License

This project is available under the license included in the repository.

---

## Author

**Yash Sharma**

Software Engineering · Full-Stack Development · Backend · AI Integration

PlacementOps was built as an engineering-focused scheduling system combining
constraint-aware scheduling, deterministic replanning, performance
optimization, API design, operational visualization, and grounded AI
assistance.