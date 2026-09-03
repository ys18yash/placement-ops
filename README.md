# PlacementOps

## Deterministic Placement Scheduling Engine

**PlacementOps is a constraint-aware interview scheduling and
deterministic replanning platform built for high-volume campus placement
operations.**

It models placement week across **students, companies, interviewer
panels, rooms, availability windows, and placement days**, then
generates a reproducible schedule and replans it when disruptions occur.

**[Live
Demo](https://placement-ops-final-qxu31vmcd-yashsharma23csds-2811s-projects.vercel.app/)
· [GitHub](https://github.com/ys18yash/placement-ops) · [API
Docs](https://placement-ops-final-qxu31vmcd-yashsharma23csds-2811s-projects.vercel.app/)**

### The System at a Glance

  Scale                            Result
  ------------------------ --------------
  Candidates                      **800**
  Companies                        **35**
  Interview Panels                 **85**
  Interview Rooms                  **20**
  Interview Requests              **859**
  Placement Days                    **4**
  Scheduled Interviews            **476**
  Unscheduled Interviews          **383**
  Completion Rate              **55.41%**
  Schedule Generation        **\~130 ms**
  Scheduling Conflicts              **0**

### What Makes PlacementOps Interesting

**Constraint-aware scheduling**\
Allocates interviews while respecting student availability, company day
constraints, interviewer-panel capacity, room capacity, operating
windows, and overlap rules.

**Deterministic execution**\
The same dataset and seed produce the same schedule, making results
reproducible, testable, and easy to reason about.

**Deterministic replanning**\
Operational disruptions such as room outages, panel unavailability,
company delays, and student withdrawals trigger a new valid schedule
without discarding the scheduling constraints.

**Performance-focused engine**\
The scheduler uses indexed resource occupancy, precomputed availability,
incremental scoring, and safe candidate pruning to avoid repeated linear
scans.

**Operations-focused interface**\
The frontend provides schedule exploration, a visual timeline,
operational analytics, disruption simulation, replanning impact
analysis, notifications, and a grounded Gemini assistant.

## The Problem

Scheduling a campus placement week is not simply a matter of assigning
interviews to available time slots.

With hundreds of candidates, multiple companies, interviewer panels,
rooms, placement days, and availability windows, every assignment
consumes several shared resources at once. A decision that is valid in
isolation can make a later interview impossible to schedule.

For PlacementOps, an interview can only be accepted when its complete
assignment is feasible across the relevant dimensions:

``` text
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
```

## The Solution

PlacementOps is designed as a deterministic scheduling system that
builds, validates, and continuously adapts a placement-week schedule.

Rather than treating an interview as an isolated calendar event,
PlacementOps assigns each interview across the full set of scheduling
dimensions:

``` text
Interview
   │
   ├── Candidate
   ├── Company
   ├── Placement Day
   ├── Time Window
   ├── Interview Panel
   └── Room
```

Each candidate assignment is evaluated against the constraints that
apply to all of these resources before it can become part of the
schedule.

## Key Capabilities

PlacementOps combines deterministic scheduling, disruption recovery, and
operational analysis into a single placement-week workflow.

### Disruption & Replanning

**Deterministic Replanning**\
Adapts the schedule to operational changes while preserving the same
scheduling constraints used during initial generation.

Supported disruptions:

  ---------------------------------------------------------------------
  Disruption                         Example
  ---------------------------------- ----------------------------------
  **Room Unavailable**               A scheduled interview room becomes
                                     unavailable.

  **Panel Unavailable**              An interviewer panel can no longer
                                     participate.

  **Company Delay**                  A company changes when its
                                     interviews can begin.

  **Student Withdrawal**             A candidate withdraws from the
                                     placement process.
  ---------------------------------------------------------------------

**Impact Classification**\
Every affected interview is explicitly classified as:

``` text
RESCHEDULED
UNSCHEDULED
UNCHANGED
```

**Before → After Analysis**\
For affected assignments, the system exposes the original assignment,
the replanned assignment, and the reason associated with the change
where the available data supports it.

**Post-Replan Validation**\
The resulting schedule is checked for assignment integrity,
resource/time conflicts, interview accounting, and disruption-specific
conditions before it is returned.

### AI Assistance

**Grounded Gemini Assistant**\
Ask natural-language questions about the current scheduling state,
including schedule counts, workload distribution, resource utilization,
interview details, and replanning results.

The assistant is grounded in structured PlacementOps data. Exact
operational facts are derived from the application's scheduling state
rather than invented by the language model.

**Streaming Responses**\
Gemini responses are delivered incrementally to the interface through
the application's streaming assistant pipeline.

## System Architecture

PlacementOps is organized as a layered system where the frontend, API,
scheduling engine, replanning logic, analytics, and AI assistant have
clear responsibilities.

``` text
                         ┌────────────────────────────┐
                         │     React Operations UI     │
                         │                            │
                         │  Schedule · Timeline       │
                         │  Analytics · Replanning    │
                         │  Assistant · Notifications │
                         └──────────────┬─────────────┘
                                        │
                              HTTP / SSE │
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
```

### Engineering Boundaries

  Boundary        Responsibility
  --------------- ------------------------------------------
  **Frontend**    Presentation and user interaction
  **API**         Validation and application orchestration
  **Scheduler**   Deterministic assignment decisions
  **Replanner**   Deterministic disruption recovery
  **Gemini**      Natural-language interpretation

This separation keeps the core scheduling system deterministic and
testable while still allowing the application to provide a modern
operational interface and natural-language assistant.

------------------------------------------------------------------------

## Scheduling Engine

The scheduling engine is the core of PlacementOps.

It builds the placement-week schedule incrementally by evaluating
feasible assignments, applying hard constraints, scoring valid
candidates, and selecting the result deterministically.

It is a **deterministic heuristic scheduler**, not a claim of globally
optimal scheduling.

### Performance Optimization

The original implementation spent substantial time repeatedly scanning
existing assignments and comparing large numbers of intervals.

Profiling identified repeated conflict checks and interval comparisons
as major cost centers.

The optimized implementation reduces this work through:

  ---------------------------------------------------------------------
  Optimization                       Effect
  ---------------------------------- ----------------------------------
  **Resource occupancy indexes**     Avoid repeated global schedule
                                     scans.

  **Precomputed availability**       Reuse static availability
                                     information.

  **Incremental counters**           Avoid repeatedly recomputing
                                     scheduling state.

  **Safe candidate pruning**         Remove impossible candidates
                                     before expensive checks.

  **Short-circuit checks**           Stop validation as soon as a
                                     constraint fails.

  **On-demand best-candidate         Avoid unnecessary materialization
  selection**                        and sorting of the complete
                                     feasible candidate set.
  ---------------------------------------------------------------------

### Deterministic Equivalence

The optimized scheduler was compared against the previous implementation
on the canonical dataset.

``` text
Assignment sequence      476 / 476 identical
Unscheduled interview IDs       identical
Candidate scoring         96,421 / 96,421 equivalent
Scheduling conflicts                    0
```

The resulting schedule therefore remains behaviorally identical while
the engine executes substantially faster.

## Replanning & Disruption Recovery

A placement schedule is not static.

During placement week, resources can become unavailable, interview
windows can change, or a candidate can withdraw after the schedule has
already been generated.

PlacementOps treats these events as **operational disruptions** and
produces a new deterministic schedule state while preserving the
scheduling constraints.

### Supported Disruptions

  ---------------------------------------------------------------------
  Disruption                         Effect
  ---------------------------------- ----------------------------------
  **Room Unavailable**               Removes a room from the affected
                                     scheduling period.

  **Panel Unavailable**              Removes an interviewer panel from
                                     the affected scheduling period.

  **Company Delay**                  Applies the configured timing
                                     restriction to affected company
                                     interviews.

  **Student Withdrawal**             Removes the student's scheduled
                                     interviews from the schedule.
  ---------------------------------------------------------------------

## Data Model & Dataset

PlacementOps uses a deterministic synthetic dataset to model a
high-volume campus placement week.

The dataset represents the participants, organizations, interviewer
resources, physical resources, interview demand, and time constraints
required by the scheduling engine.

### Canonical Result

The canonical workload produces the following baseline result:

  Metric                       Result
  ---------------------- ------------
  Interview Requests          **859**
  Scheduled                   **476**
  Unscheduled                 **383**
  Completion Rate          **55.41%**
  Scheduling Conflicts          **0**

These values describe the canonical workload and provide a stable
reference point for regression and performance testing.

## API Design

PlacementOps exposes a small FastAPI surface around the scheduling
domain.

HTTP handlers validate requests and delegate the actual scheduling and
replanning decisions to the backend services.

### API Surface

  -----------------------------------------------------------------------
  Method                  Endpoint                Purpose
  ----------------------- ----------------------- -----------------------
  `GET`                   `/health`               Backend health check

  `POST`                  `/schedule/generate`    Generate the initial
                                                  deterministic schedule

  `POST`                  `/schedule/replan`      Replan an existing
                                                  schedule after a
                                                  disruption

  `POST`                  `/assistant/query`      Return a grounded
                                                  Gemini response

  `POST`                  `/assistant/stream`     Stream Gemini responses
                                                  grounded in
                                                  PlacementOps data
  -----------------------------------------------------------------------

The API is intentionally small: the frontend interacts with a few
focused operations rather than depending on internal scheduler
implementation details.

### API Documentation

FastAPI provides interactive API documentation for development and
testing.

``` text
/docs
```

The generated documentation exposes the available endpoints, request
schemas, and response models without requiring a separate API
specification to be maintained manually.

## Performance Engineering

PlacementOps was optimized using a profile-driven approach.

The goal was not simply to make the scheduler faster, but to reduce
repeated work while preserving the exact scheduling behavior of the
canonical implementation.

### Optimization Techniques

  ---------------------------------------------------------------------
  Technique                          What Changed
  ---------------------------------- ----------------------------------
  **Resource occupancy indexes**     Existing assignments are indexed
                                     by resource and placement day
                                     instead of repeatedly scanning the
                                     full schedule.

  **Precomputed availability**       Static availability information is
                                     prepared once and reused during
                                     candidate evaluation.

  **Incremental state**              Company, panel, room, and student
                                     scheduling state is updated as
                                     assignments are accepted.

  **Safe candidate pruning**         Candidates that cannot satisfy
                                     known constraints are discarded
                                     before unnecessary checks.

  **Short-circuit validation**       Constraint evaluation stops as
                                     soon as a candidate is known to be
                                     invalid.

  **On-demand selection**            The scheduler tracks the best
                                     feasible candidate without
                                     unnecessarily materializing and
                                     sorting every candidate.
  ---------------------------------------------------------------------

These changes target the cost of candidate evaluation while leaving the
scheduling policy unchanged.

### Benchmark Result

The optimized scheduler was benchmarked against the canonical dataset
using the same deterministic input and configuration.

Five runs produced:

``` text
0.1275 s
0.1289 s
0.1306 s
0.1307 s
0.1338 s
```

Median runtime:

``` text
~130 ms
```

The measured runtime is more than **99% lower** than the earlier
implementation under the corresponding benchmark setup.

### Correctness During Optimization

A faster scheduler is only useful if it still produces the correct
result.

The optimized implementation was compared with the previous
implementation on the canonical dataset.

``` text
Scheduled assignments     476 / 476 identical
Unscheduled interview IDs      identical
Candidate scoring         96,421 / 96,421 equivalent
Scheduling conflicts                   0
```

This provides a stronger validation than a runtime comparison alone:

``` text
Performance Improvement
        +
Behavioral Equivalence
        ↓
Accepted Optimization
```

### Result

The final scheduler combines:

**Constraint correctness · deterministic behavior · reproducible
benchmarking · efficient candidate evaluation**

with a measured canonical runtime of approximately **130 ms**.

------------------------------------------------------------------------

## Correctness, Testing & Validation

Correctness is a core requirement of PlacementOps.

The system validates scheduling behavior at both the individual
constraint level and the complete schedule level, with automated tests
covering generation, replanning, API validation, and regression
behavior.

### Test Suite

The current backend test suite contains:

``` text
57 total tests
55 passed
2 skipped
```

The skipped cases were intentional and were not failing tests. The
repository should be re-run before release so these figures match the
exact published state.

## Frontend & Operations Console

PlacementOps includes a recruiter-facing operations console for
exploring and managing the placement schedule.

The interface is built around the state produced by the backend
scheduling system. It does not contain an independent scheduling model
or make scheduling decisions in the browser.

## AI Assistant & Gemini Integration

PlacementOps includes a Gemini-powered assistant that provides a
natural-language interface to the current scheduling state.

The assistant is deliberately separated from the scheduling engine:

> **PlacementOps makes scheduling decisions. Gemini helps operators
> understand them.**

## Project Structure & Code Organization

PlacementOps is organized so that scheduling logic, API behavior, data
generation, and frontend presentation remain separated.

``` text
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
```

## Technology Stack

PlacementOps uses a lightweight full-stack architecture with
Python/FastAPI on the backend and React/Vite on the frontend.

### Why This Stack

The stack is intentionally simple.

The project does not introduce a large framework ecosystem around the
scheduling engine. Each major technology has a focused responsibility:

``` text
React        → user interface
Vite         → frontend tooling
FastAPI      → application API
Python       → scheduling domain
Uvicorn      → application server
Gemini       → natural-language interface
unittest     → automated validation
Git          → source control
```

This keeps the implementation approachable while leaving the scheduling
engine independent from the presentation layer.

------------------------------------------------------------------------

## Local Development & Setup

PlacementOps can be run locally as two processes:

``` text
React / Vite Frontend
        │
        │ HTTP
        ▼
FastAPI Backend
        │
        ▼
PlacementOps Scheduling Engine
```

## API Usage & Example Workflow

PlacementOps can be used through the FastAPI endpoints independently of
the React frontend.

The main operational workflow is:

``` text
Generate
   ↓
Inspect
   ↓
Disrupt
   ↓
Replan
   ↓
Analyze
```

## Deployment & Production Configuration

PlacementOps is designed to separate the frontend deployment from the
FastAPI backend.

A practical production setup is:

``` text
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
```

## Future Improvements

PlacementOps is intentionally focused on the core placement scheduling
and replanning workflow.

Potential future improvements include:

### Scheduling

-   stronger optimization objectives beyond the current heuristic
    scoring
-   additional fairness constraints across candidates and resources
-   improved handling of multi-stage interview processes
-   larger-scale workload benchmarking
-   optional comparison with mathematical optimization approaches

### Operations

-   persistent schedule storage
-   user authentication and role-based access
-   audit logs for operational changes
-   richer export formats
-   calendar and notification integrations

### AI

-   broader natural-language exploration of scheduling state
-   configurable assistant actions with explicit approval
-   richer context selection for complex operational questions
-   evaluation of assistant responses against deterministic application
    facts

These improvements would extend the system while preserving its central
design principle:

``` text
deterministic scheduling state
        +
explicit operational controls
        +
AI-assisted interpretation
```

------------------------------------------------------------------------

## Project Links

**Live Demo:**
https://placement-ops-final-qxu31vmcd-yashsharma23csds-2811s-projects.vercel.app/\
**GitHub:** https://github.com/ys18yash/placement-ops  
**Video Walkthrough:** https://youtu.be/PpCkmrgLxgI\
**API Docs:**
https://placement-ops-final-qxu31vmcd-yashsharma23csds-2811s-projects.vercel.app/

------------------------------------------------------------------------

## License

This project is available under the license included in the repository.

------------------------------------------------------------------------

## Author

**Yash Sharma**

Software Engineering · Full-Stack Development · Backend · AI Integration

PlacementOps was built as an engineering-focused scheduling system
combining constraint-aware scheduling, deterministic replanning,
performance optimization, API design, operational visualization, and
grounded AI assistance.
