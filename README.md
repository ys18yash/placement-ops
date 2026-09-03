# PlacementOps

## Deterministic Placement Scheduling Engine

**PlacementOps is a constraint-aware interview scheduling and deterministic replanning platform built for high-volume campus placement operations.**

It models placement week as a multi-resource scheduling problem across **students, companies, interviewer panels, rooms, availability windows, and placement days** — then generates a reproducible schedule and safely replans it when real-world disruptions occur.

**[Watch the PlacementOps Demo](https://youtu.be/PpCkmrgLxgI)**

> Recommended: watch in **720p** for the best viewing experience.
**[Live Demo](YOUR_LIVE_LINK) · [GitHub](https://github.com/ys18yash/placement-ops) · [API Docs](YOUR_API_LINK)**

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

### What Makes PlacementOps Interesting

**Constraint-aware scheduling**  
Allocates interviews while respecting student availability, company day constraints, interviewer-panel capacity, room capacity, operating windows, and overlap rules.

**Deterministic execution**  
The same dataset and seed produce the same schedule, making results reproducible, testable, and easy to reason about.

**Deterministic replanning**  
Operational disruptions such as room outages, panel unavailability, company delays, and student withdrawals trigger a new valid schedule without discarding the scheduling constraints.

**Performance-focused engine**  
The scheduler uses indexed resource occupancy, precomputed availability, incremental scoring, and safe candidate pruning to avoid repeated linear scans.

**Operations-focused interface**  
The frontend provides schedule exploration, a visual timeline, operational analytics, disruption simulation, replanning impact analysis, notifications, and a grounded Gemini assistant.

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
```

> **Deterministic:** identical input data and seed produce identical scheduling results.

> **Validated:** assignments are checked against the project's scheduling constraints before they are accepted.

---

## The Problem

Scheduling a campus placement week is not simply a matter of assigning interviews to available time slots.

With hundreds of candidates, multiple companies, interviewer panels, rooms, placement days, and availability windows, every assignment consumes several shared resources at once. A decision that is valid in isolation can make a later interview impossible to schedule.

For PlacementOps, an interview can only be accepted when its complete assignment is feasible across the relevant dimensions:

```text
                 Interview Request
                        
          
          ↓             ↓             ↓
      Candidate      Company       Resources
      availability   day rules     panel + room
                                    
          
                        ↓
                 Time-window check
                        ↓
                Conflict validation
                        ↓
                 Valid assignment
```

### Constraints That Interact

| Constraint | Example |
|---|---|
| **Candidate availability** | A student cannot be assigned outside an available window. |
| **Student conflicts** | A candidate cannot have overlapping interviews. |
| **Company day rules** | A company may only interview on authorized placement days. |
| **Panel availability** | An interviewer panel cannot be double-booked or exceed its concurrency limit. |
| **Room availability** | A room cannot host overlapping interviews and must be operational. |
| **Interview duration** | The selected time window must contain the complete interview. |
| **Operating hours** | Interviews must remain within the placement-day schedule. |

These constraints are coupled.

For example, assigning one interview to a particular panel and room does not just satisfy that interview — it also consumes capacity that may be required by another candidate later in the schedule.

### The Replanning Problem

The challenge does not end once the initial schedule is generated.

Placement operations can change during the week:

- a room can become unavailable
- an interviewer panel can drop out
- a company can delay its interviews
- a student can withdraw

The system must then determine what can remain unchanged, what must move, and what can no longer be scheduled — while continuing to respect the same constraints.

> **Replanning must recover from disruption without turning the schedule into an invalid state.**

### Engineering Requirements

**Correctness**  
Accept an assignment only when the relevant scheduling constraints are satisfied.

**Determinism**  
Given the same dataset and seed, produce the same scheduling result.

**Resilience**  
Replan around operational disruptions while preserving schedule validity.

**Performance**  
Evaluate a large search space efficiently enough for the scheduler to remain practical.

PlacementOps is built around these requirements from the beginning rather than treating scheduling, validation, and disruption handling as separate afterthoughts.

---

## The Solution

PlacementOps is designed as a deterministic scheduling system that builds, validates, and continuously adapts a placement-week schedule.

Rather than treating an interview as an isolated calendar event, PlacementOps assigns each interview across the full set of scheduling dimensions:

```text
Interview
   
    Candidate
    Company
    Placement Day
    Time Window
    Interview Panel
    Room
```

Each candidate assignment is evaluated against the constraints that apply to all of these resources before it can become part of the schedule.

### 1. Build the Initial Schedule

PlacementOps begins with the placement dataset and prioritizes interview requests using the scheduler's deterministic ordering strategy.

It then evaluates feasible combinations of:

```text
Placement Day
      ↓
Time Window
      ↓
Interview Panel
      ↓
Room
```

For each interview, feasible candidates are validated and scored. The selected assignment is added to the schedule, and the state of occupied resources is updated before the next interview is evaluated.

This process continues until every interview is either:

- assigned a valid slot, or
- left explicitly unscheduled because no feasible assignment remains.

### 2. Validate the Result

A generated schedule is not considered complete simply because every row has a time and resource.

Assignments are validated against the scheduling constraints to ensure that the resulting schedule remains internally consistent and conflict-free.

The system therefore produces a schedule together with a measurable outcome:

```text
Scheduled Interviews
Unscheduled Interviews
Resource Utilization
Schedule Span
Constraint Validation
```

### 3. Adapt to Operational Disruptions

Placement schedules can change after the initial schedule has been generated.

PlacementOps supports deterministic replanning for disruptions such as:

```text
Room Unavailable
        
Panel Unavailable
        
Company Delay
        
Student Withdrawal
        ↓
Affected Schedule State
        ↓
Replanning
        ↓
Revalidated Schedule
```

The replanner determines which assignments are affected, attempts feasible alternatives, and records the resulting changes.

Each affected interview can be classified as:

```text
UNCHANGED
RESCHEDULED
UNSCHEDULED
```

### 4. Inspect and Analyze

The resulting schedule is exposed through a recruiter-facing operations interface.

PlacementOps provides:

- schedule exploration and filtering
- visual schedule timeline
- resource utilization analysis
- operational analytics
- unscheduled-interview inspection
- disruption simulation
- replanning impact analysis
- notifications
- a grounded Gemini assistant

The interface is designed to make the state of the scheduling system understandable, not just display raw scheduling records.

### The Result

The final system follows a simple operational loop:

```text
UNDERSTAND
    ↓
SCHEDULE
    ↓
VALIDATE
    ↓
INSPECT
    ↓
DISRUPTION
    ↓
REPLAN
    ↓
VALIDATE AGAIN
    ↓
ANALYZE
```

This turns PlacementOps from a static interview calendar into a **deterministic, constraint-aware scheduling and replanning system**.

---

## Key Capabilities

PlacementOps combines deterministic scheduling, disruption recovery, and operational analysis into a single placement-week workflow.

### Schedule Generation

**Constraint-Aware Scheduling**  
Builds interview assignments across candidates, companies, interviewer panels, rooms, placement days, availability windows, interview durations, and overlap constraints.

**Deterministic Execution**  
Uses stable interview ordering, deterministic candidate scoring, and consistent tie-breaking so the same dataset and seed produce the same schedule.

**Resource-Aware Allocation**  
Tracks shared student, panel, and room occupancy while the schedule is being constructed, preventing conflicting assignments.

**Explicit Unscheduled Outcomes**  
When no feasible assignment remains, the interview is kept explicitly unscheduled rather than forcing an invalid placement.

### Disruption & Replanning

**Deterministic Replanning**  
Adapts the schedule to operational changes while preserving the same scheduling constraints used during initial generation.

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
```

**Before → After Analysis**  
For affected assignments, the system exposes the original assignment, the replanned assignment, and the reason associated with the change where the available data supports it.

**Post-Replan Validation**  
The resulting schedule is checked for assignment integrity, resource/time conflicts, interview accounting, and disruption-specific conditions before it is returned.

### Schedule Exploration

**Operations Table**  
Search, filter, sort, paginate, inspect, and export scheduled interviews.

**Visual Timeline**  
View the schedule across placement days and time windows using room- or panel-based resource lanes.

**Unscheduled Inspector**  
Inspect the interviews that remain without feasible assignments.

**Assignment Details**  
Open an individual interview to inspect its candidate, company, panel, room, day, time, and duration.

### Operational Analytics

**Workload Analysis**  
Understand scheduled versus unscheduled demand and how interviews are distributed across placement days and time windows.

**Resource Utilization**  
Analyze room and interviewer-panel utilization to identify how the available capacity is being used.

**Company Workload**  
Compare interview demand across participating companies.

**Replanning Impact**  
Compare the schedule before and after a disruption through affected, rescheduled, newly unscheduled, and unchanged outcomes.

### Operational Controls

**Disruption Simulator**  
Trigger supported placement-week disruptions directly from the interface and observe the resulting deterministic replan.

**Notifications**  
Receive concise feedback for meaningful scheduling and replanning events, including successful runs, warnings, and failures.

**CSV Export**  
Export schedule data for offline analysis and operational workflows.

### AI Assistance

**Grounded Gemini Assistant**  
Ask natural-language questions about the current scheduling state, including schedule counts, workload distribution, resource utilization, interview details, and replanning results.

The assistant is grounded in structured PlacementOps data. Exact operational facts are derived from the application's scheduling state rather than invented by the language model.

**Streaming Responses**  
Gemini responses are delivered incrementally to the interface through the application's streaming assistant pipeline.

### Interface

**Recruiter-Facing Operations Console**  
A purpose-built interface for understanding, exploring, and operating the placement schedule.

**Timeline + Analytics Views**  
Separate focused workspaces keep operational analysis available without overloading the primary overview.

**Light & Dark Themes**  
A consistent PlacementOps visual system is available in both light and dark modes.

**Responsive Design**  
The application adapts across desktop, tablet, and mobile layouts.

---

## System Architecture

PlacementOps is organized as a layered system where the frontend, API, scheduling engine, replanning logic, analytics, and AI assistant have clear responsibilities.

```text
                         
                              React Operations UI     
                                                     
                           Schedule · Timeline       
                           Analytics · Replanning    
                           Assistant · Notifications 
                         
                                        
                              HTTP / SSE 
                                        
                         
                                FastAPI Backend      
                                                     
                           Validation · Services     
                           Schedule APIs · Assistant 
                         
                                          
                             
                                                        
                          
           Scheduling Engine                  Replanning Engine 
                                                                
           Ordering                           Disruptions       
           Candidate search                   Affected jobs     
           Constraints                        Rescheduling      
           Scoring                            Validation        
                          
                                                        
                    
                                     
                           
                            Placement Dataset  
                                               
                            Students           
                            Companies          
                            Panels             
                            Rooms              
                            Interviews         
                            Availability       
                           

                                      AI
                                       
                                       
                              
                                 Google Gemini 
                                               
                               Natural-language
                               assistance      
                              
```

### Frontend

The React frontend is the operations layer for interacting with the generated schedule.

It is responsible for:

- overview and scheduling KPIs
- schedule exploration
- search, filtering, sorting, and pagination
- visual schedule timeline
- operational analytics
- disruption simulation
- replanning impact visualization
- notifications
- assignment inspection
- Gemini assistant interaction
- light/dark themes

The frontend does not contain scheduling decisions. Scheduling and replanning remain backend responsibilities.

### Backend

FastAPI provides the application boundary between the UI and the scheduling system.

Core responsibilities include:

- request validation
- scheduling and replanning orchestration
- schedule validation
- operational metric generation
- assistant context preparation
- streaming assistant responses

### Scheduling Engine

The scheduling engine is responsible for constructing the initial schedule.

Its pipeline is:

```text
Interview Requests
        ↓
Deterministic Ordering
        ↓
Candidate Generation
        ↓
Constraint Checks
        ↓
Candidate Scoring
        ↓
Deterministic Selection
        ↓
Resource State Update
```

The engine tracks the shared resources required by each interview and rejects assignments that violate the scheduling constraints.

### Replanning Engine

The replanning engine starts from an existing schedule and responds to operational disruptions.

```text
Existing Schedule
       ↓
Disruption
       ↓
Affected Assignments
       ↓
Feasible Alternatives
       ↓
Deterministic Replanning
       ↓
Validation
       ↓
Replanned Schedule
```

### Analytics

Operational metrics are derived from the scheduling state rather than maintained as independent UI values.

This supports views such as:

```text
Schedule Completion
Day Distribution
Time Distribution
Room Utilization
Panel Utilization
Company Workload
Replanning Impact
```

### AI Assistant

The Gemini assistant is intentionally outside the scheduling decision path.

Its flow is:

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
Streaming Response
      ↓
React Assistant
```

PlacementOps remains the source of truth for operational data.

The application derives scheduling facts from its own state and provides that context to Gemini, allowing the model to explain and interact with the data without becoming responsible for scheduling decisions.

### Engineering Boundaries

| Boundary | Responsibility |
|---|---|
| **Frontend** | Presentation and user interaction |
| **API** | Validation and application orchestration |
| **Scheduler** | Deterministic assignment decisions |
| **Replanner** | Deterministic disruption recovery |
| **Gemini** | Natural-language interpretation |

This separation keeps the core scheduling system deterministic and testable while still allowing the application to provide a modern operational interface and natural-language assistant.

---

## Scheduling Engine

The scheduling engine is the core of PlacementOps.

It builds the placement-week schedule incrementally by evaluating feasible assignments, applying hard constraints, scoring valid candidates, and selecting the result deterministically.

It is a **deterministic heuristic scheduler**, not a claim of globally optimal scheduling.

### Scheduling Flow

```text
Interview Requests
        
        
Deterministic Ordering
        
        
Generate Assignment Candidates
        
        
Hard Constraint Checks
        
         invalid  reject
        
        
Score Feasible Candidates
        
        
Deterministic Tie-Breaking
        
        
Assign Best Candidate
        
        
Update Scheduling State
        
         next interview
```

### Hard Constraints

An assignment is considered feasible only when all applicable constraints pass.

| Constraint | Rule |
|---|---|
| **Student availability** | The complete interview must fit inside the student's available window. |
| **Student conflicts** | A student cannot have overlapping interviews. |
| **Company day eligibility** | The company must be allowed to interview on the selected placement day. |
| **Panel availability** | The selected panel must be available for the interval. |
| **Panel conflicts** | The panel cannot receive conflicting assignments or exceed its supported concurrency. |
| **Room availability** | The selected room must be operational and available for the interval. |
| **Room conflicts** | A room cannot host overlapping interviews. |
| **Interview duration** | The full interview duration must fit within the selected slot. |
| **Operating hours** | The assignment must remain inside the placement-day operating window. |

Constraint evaluation is short-circuited: once a candidate is known to be invalid, the remaining checks are not performed.

### Candidate Selection

For each interview request, the scheduler evaluates combinations of:

```text
Placement Day
      ×
Time Window
      ×
Interview Panel
      ×
Room
```

Candidates that violate hard constraints are discarded.

The remaining candidates are scored according to the scheduler's deterministic allocation policy, and the best candidate is selected.

This creates an important separation:

```text
Hard Constraints
      ↓
"What is allowed?"
      ↓
Scoring
      ↓
"What is preferred?"
```

The scheduler therefore never sacrifices validity simply to obtain a better score.

### Determinism

Determinism is built into the scheduling process rather than added afterward.

The engine uses stable interview ordering, deterministic candidate evaluation, and stable tie-breaking.

Therefore:

```text
Same Input Dataset
        +
Same Seed
        +
Same Configuration
        ↓
Same Schedule
```

This makes the scheduler reproducible across runs and provides a stable basis for testing, debugging, benchmarking, and replanning.

### Incremental State

Scheduling is stateful: every accepted assignment changes the resources available to later interviews.

PlacementOps maintains scheduling state incrementally for:

```text
Students
Panels
Rooms
Companies
Placement Days
```

Resource occupancy is indexed by resource and placement day, allowing the scheduler to evaluate relevant intervals without repeatedly scanning the entire schedule.

Static availability is also precomputed before the main candidate-evaluation loop.

### Performance Optimization

The original implementation spent substantial time repeatedly scanning existing assignments and comparing large numbers of intervals.

Profiling identified repeated conflict checks and interval comparisons as major cost centers.

The optimized implementation reduces this work through:

| Optimization | Effect |
|---|---|
| **Resource occupancy indexes** | Avoid repeated global schedule scans. |
| **Precomputed availability** | Reuse static availability information. |
| **Incremental counters** | Avoid repeatedly recomputing scheduling state. |
| **Safe candidate pruning** | Remove impossible candidates before expensive checks. |
| **Short-circuit checks** | Stop validation as soon as a constraint fails. |
| **On-demand best-candidate selection** | Avoid unnecessary materialization and sorting of the complete feasible candidate set. |

### Deterministic Equivalence

The optimized scheduler was compared against the previous implementation on the canonical dataset.

```text
Assignment sequence      476 / 476 identical
Unscheduled interview IDs       identical
Candidate scoring         96,421 / 96,421 equivalent
Scheduling conflicts                    0
```

The resulting schedule therefore remains behaviorally identical while the engine executes substantially faster.

### When No Valid Assignment Exists

An interview is not forced into an invalid slot.

When the candidate search produces no feasible assignment, the request is recorded explicitly as unscheduled:

```text
Interview Request
       
       
Feasible Assignment?
      / \
    Yes  No
         
         
  Scheduled
           Unscheduled
```

This keeps the schedule valid and makes incomplete capacity or constraint coverage visible to the operations layer.

---

## Replanning & Disruption Recovery

A placement schedule is not static.

During placement week, resources can become unavailable, interview windows can change, or a candidate can withdraw after the schedule has already been generated.

PlacementOps treats these events as **operational disruptions** and produces a new deterministic schedule state while preserving the scheduling constraints.

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
       
       
Disruption Detected
       
       
Identify Affected Assignments
       
       
Preserve Unaffected Assignments
       
       
Release Affected Resources
       
       
Search for Feasible Alternatives
       
       
Deterministic Reassignment
       
       
Validate Final Schedule
       
       
Replanned Schedule
```

The replanner does not simply regenerate the entire schedule blindly.

It first determines which existing assignments are affected by the disruption, preserves assignments that remain valid, and then attempts to recover the affected interviews using the scheduling engine's constraints.

### Impact Classification

Each affected interview is classified according to its result:

```text
UNCHANGED
RESCHEDULED
UNSCHEDULED
```

This creates an explicit before-and-after view of the disruption.

For example:

```text
Original Assignment
        
        
Room Becomes Unavailable
        
        
Alternative Feasible Slot?
       / \
     Yes  No
          
          
RESCHEDULED  UNSCHEDULED
```

Unaffected assignments remain classified as **UNCHANGED**.

### Deterministic Replanning

Replanning follows the same deterministic principles as initial scheduling.

Given the same:

```text
Initial Schedule
      +
Disruption
      +
Scheduling Configuration
```

the replanner produces the same resulting schedule.

### Constraint Preservation

A successful replan must continue to satisfy the scheduling constraints.

The final schedule is checked for:

- assignment integrity
- student overlaps
- panel conflicts
- room conflicts
- availability violations
- placement-day rules
- disruption-specific conditions
- interview accounting

The objective is therefore:

```text
Valid Original Schedule
        +
Real-World Disruption
        ↓
Valid Replanned Schedule
```

rather than simply maximizing the number of rescheduled interviews.

### Student Withdrawal

Student withdrawal is treated differently from resource disruptions.

When a student withdraws:

```text
Student Withdrawal
        ↓
Find all scheduled interviews
        ↓
Remove those assignments
        ↓
Do not reschedule the withdrawn student
        ↓
Update schedule accounting
```

This prevents the system from incorrectly attempting to reassign interviews for a candidate who is no longer participating.

### Before → After Comparison

The replanning result exposes the operational impact of the disruption.

The interface can compare:

```text
Original Schedule
      ↓
Replanned Schedule
      ↓
Changed Assignments
      ↓
Operational Impact
```

This allows an operator to see which interviews moved, which were lost, and which remained unaffected.

### Replanning Guarantees

PlacementOps treats these properties as part of replanning correctness:

**No invalid assignments**  
A replan must not introduce scheduling conflicts or violate the applicable constraints.

**Explicit outcomes**  
Affected interviews are classified instead of silently disappearing or being overwritten.

**Minimal unnecessary change**  
Assignments that remain valid are preserved rather than being needlessly changed.

**Deterministic results**  
The same starting state and disruption produce the same replanned outcome.

**Post-replan validation**  
The resulting schedule is validated before it is returned to the application.

### Example

A room outage can be represented as:

```text
Before

Room R07
09:00  Interview A
09:30  Interview B
10:00  Interview C


Disruption

R07 becomes unavailable


Replan

Interview A  unchanged / alternative room
Interview B  rescheduled
Interview C  rescheduled / unscheduled


After

Final schedule
       
       
Constraint validation
       
       
Operational impact
```

The exact outcome depends on the available alternative resources and the constraints of the affected interviews.

### Why Replanning Matters

The key distinction is that PlacementOps is not only a schedule generator.

It is designed to maintain a **valid scheduling state as operational conditions change**.

That turns the system from a one-time planning algorithm into a deterministic placement operations workflow:

```text
PLAN
  ↓
OPERATE
  ↓
DISRUPTION
  ↓
REPLAN
  ↓
VALIDATE
  ↓
CONTINUE
```

---

## Data Model & Dataset

PlacementOps uses a deterministic synthetic dataset to model a high-volume campus placement week.

The dataset represents the participants, organizations, interviewer resources, physical resources, interview demand, and time constraints required by the scheduling engine.

### Core Model

```text

  Student   

      
       interview request
      
       
 Interview    Company   
   Request         

      
       Placement Day
       Time Window
       Interview Panel
       Interview Room
```

A scheduled interview is a concrete assignment across:

```text
Student
  +
Company
  +
Placement Day
  +
Time Window
  +
Panel
  +
Room
```

The scheduler must find a combination that satisfies the applicable constraints across all of these dimensions.

### Canonical Dataset

The repository uses the following canonical workload:

| Entity | Count |
|---|---:|
| Students | **800** |
| Companies | **35** |
| Interview Panels | **85** |
| Rooms | **20** |
| Interview Requests | **859** |
| Placement Days | **4** |

The workload is intentionally large enough to create meaningful contention between shared resources while remaining reproducible for local development, testing, and benchmarking.

### Entity Responsibilities

| Entity | Scheduling Role |
|---|---|
| **Student** | Candidate availability and student-level overlap constraints |
| **Company** | Interview demand and placement-day eligibility |
| **Interview Request** | Unit of work that must be scheduled or explicitly left unscheduled |
| **Panel** | Interviewer availability and concurrency capacity |
| **Room** | Physical interview capacity and occupancy |
| **Placement Day** | Day-level scheduling horizon and company constraints |

### Interview Request → Assignment

An interview request contains the information needed to construct a scheduling decision.

```text
Interview Request
      
       Student
       Company
       Scheduling constraints
               
               
        Candidate Assignment
               
                Placement Day
                Start Time
                End Time
                Panel
                Room
```

If no feasible assignment exists, the request remains explicitly **unscheduled** rather than being placed in a conflicting slot.

### Availability Model

Availability is represented across the resources that participate in an interview:

```text
Student Availability
        +
Panel Availability
        +
Room Availability
        +
Placement-Day Rules
        +
Operating Hours
        ↓
Feasible Assignment Window
```

This allows the scheduler to evaluate the complete assignment instead of treating time availability as a property of only one resource.

### Deterministic Generation

The synthetic workload is generated from a fixed seed.

```text
Canonical Seed
20260829
```

Using the same seed reproduces the same underlying scheduling workload.

This provides a controlled basis for:

```text
Correctness Tests
Performance Benchmarks
Regression Testing
Replanning Scenarios
Debugging
```

It also means that scheduler changes can be evaluated against a stable input rather than a newly generated workload.

### Canonical Result

The canonical workload produces the following baseline result:

| Metric | Result |
|---|---:|
| Interview Requests | **859** |
| Scheduled | **476** |
| Unscheduled | **383** |
| Completion Rate | **55.41%** |
| Scheduling Conflicts | **0** |

These values describe the canonical workload and provide a stable reference point for regression and performance testing.

### Why Synthetic Data?

The project uses generated data rather than real candidate or recruiter records.

This makes the workload:

- reproducible
- safe to share
- suitable for automated testing
- suitable for performance benchmarking
- suitable for controlled disruption experiments

The dataset is therefore a **repeatable engineering workload**, not production placement data.

---

## API Design

PlacementOps exposes a small FastAPI surface around the scheduling domain.

HTTP handlers validate requests and delegate the actual scheduling and replanning decisions to the backend services.

### API Surface

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Backend health check |
| `POST` | `/schedule/generate` | Generate the initial deterministic schedule |
| `POST` | `/schedule/replan` | Replan an existing schedule after a disruption |
| `POST` | `/assistant/stream` | Stream Gemini responses grounded in PlacementOps data |

The API is intentionally small: the frontend interacts with a few focused operations rather than depending on internal scheduler implementation details.

### Schedule Generation

```text
POST /schedule/generate
        
        
Request Validation
        
        
Scheduling Service
        
        
Deterministic Scheduler
        
        
Schedule Validation
        
        
Structured Result
```

The generation endpoint starts a scheduling run and returns the resulting scheduling state, including scheduled and unscheduled interview information and the metrics required by the operations interface.

The HTTP layer does not implement the scheduling algorithm.

### Replanning

```text
POST /schedule/replan
        
        
Validate Disruption
        
        
Replanning Service
        
        
Identify Affected Assignments
        
        
Recover Feasible Assignments
        
        
Validate Result
        
        
Replanned Schedule + Impact
```

The endpoint accepts a supported disruption and the information required to apply it to the existing scheduling state.

Supported disruption types are:

```text
ROOM_UNAVAILABLE
PANEL_UNAVAILABLE
COMPANY_DELAY
STUDENT_WITHDRAWAL
```

The replanning workflow rejects invalid operational inputs before they reach the core replanning logic.

### Validation

PlacementOps performs both structural and domain-level validation.

```text
HTTP Request
     
     
Schema Validation
     
     
Domain Validation
     
     
Scheduling Operation
```

Structural validation handles malformed request bodies and invalid field shapes.

Domain validation handles scheduling-specific conditions such as:

- unsupported disruption types
- invalid placement days
- invalid resource references
- invalid effective times
- disruption parameters that do not match the available scheduling state

This separation keeps transport-level validation distinct from scheduling rules.

### Error Contract

The API distinguishes malformed requests from valid requests that violate an application rule.

```text
Malformed Request
        422

Valid Request
      
       invalid domain operation  400

Valid Request
       scheduling workflow
```

This gives the frontend enough information to present meaningful operational feedback.

### Schedule Result

The schedule APIs return structured scheduling data rather than frontend-specific markup.

Conceptually:

```text
Schedule Result
      
       Scheduled Interviews
       Unscheduled Interviews
       Schedule Metrics
       Resource State
       Replanning Impact
```

This allows the same backend result to drive the overview, schedule table, timeline, analytics, and replanning views.

### Assistant Streaming

The assistant uses a separate server-side streaming path:

```text
POST /assistant/stream
        
        
Validate Request
        
        
Build PlacementOps Context
        
        
Gemini Streaming Request
        
        
Server-Sent Events
        
        
React Assistant
```

The browser does not call Gemini directly.

Instead, the backend:

1. receives the user question
2. builds structured context from the current PlacementOps state
3. sends that context to Gemini
4. streams the generated response back to the frontend

This keeps provider credentials outside the browser and keeps PlacementOps as the source of truth for scheduling facts.

### Separation of Concerns

The API follows a thin-controller design:

```text
HTTP Layer
    ↓
Application Service
    ↓
Scheduling / Replanning Domain Logic
    ↓
Validated Scheduling State
```

The API is therefore responsible for transport, validation, and orchestration, while the scheduler and replanner remain responsible for scheduling decisions.

### API Documentation

FastAPI provides interactive API documentation for development and testing.

```text
/docs
```

The generated documentation exposes the available endpoints, request schemas, and response models without requiring a separate API specification to be maintained manually.

### Design Goals

PlacementOps keeps the API intentionally focused around the core operational workflow:

```text
GENERATE
   ↓
INSPECT
   ↓
DISRUPT
   ↓
REPLAN
   ↓
ANALYZE
```

The result is a small API surface with a clear boundary between HTTP concerns and the deterministic scheduling domain.

---

## Performance Engineering

PlacementOps was optimized using a profile-driven approach.

The goal was not simply to make the scheduler faster, but to reduce repeated work while preserving the exact scheduling behavior of the canonical implementation.

### From Profiling to Optimization

The baseline scheduler repeatedly scanned existing assignments and performed large numbers of interval-overlap checks during candidate evaluation.

Profiling identified these operations as the dominant sources of execution cost:

```text
Candidate Evaluation
        
         repeated resource scans
        
         interval-overlap checks
        
         repeated state / scoring work
                ↓
          scheduling overhead
```

### Optimization Techniques

| Technique | What Changed |
|---|---|
| **Resource occupancy indexes** | Existing assignments are indexed by resource and placement day instead of repeatedly scanning the full schedule. |
| **Precomputed availability** | Static availability information is prepared once and reused during candidate evaluation. |
| **Incremental state** | Company, panel, room, and student scheduling state is updated as assignments are accepted. |
| **Safe candidate pruning** | Candidates that cannot satisfy known constraints are discarded before unnecessary checks. |
| **Short-circuit validation** | Constraint evaluation stops as soon as a candidate is known to be invalid. |
| **On-demand selection** | The scheduler tracks the best feasible candidate without unnecessarily materializing and sorting every candidate. |

These changes target the cost of candidate evaluation while leaving the scheduling policy unchanged.

### Benchmark Result

The optimized scheduler was benchmarked against the canonical dataset using the same deterministic input and configuration.

Five runs produced:

```text
0.1275 s
0.1289 s
0.1306 s
0.1307 s
0.1338 s
```

Median runtime:

```text
~130 ms
```

The measured runtime is more than **99% lower** than the earlier implementation under the corresponding benchmark setup.

### Correctness During Optimization

A faster scheduler is only useful if it still produces the correct result.

The optimized implementation was compared with the previous implementation on the canonical dataset.

```text
Scheduled assignments     476 / 476 identical
Unscheduled interview IDs      identical
Candidate scoring         96,421 / 96,421 equivalent
Scheduling conflicts                   0
```

This provides a stronger validation than a runtime comparison alone:

```text
Performance Improvement
        +
Behavioral Equivalence
        ↓
Accepted Optimization
```

### Benchmarking Strategy

The benchmark uses a fixed dataset and deterministic configuration so that performance and behavioral changes can be compared against a stable workload.

```text
Fixed Seed
   ↓
Fixed Dataset
   ↓
Fixed Scheduler Configuration
   ↓
Benchmark
   ↓
Compare Runtime + Schedule
```

This makes the benchmark useful for regression testing as the scheduler evolves.

### Engineering Trade-off

PlacementOps deliberately does not claim global mathematical optimality.

The scheduler uses a deterministic heuristic that prioritizes:

```text
Valid Assignment
      ↓
Deterministic Selection
      ↓
Efficient Execution
```

The optimization work therefore improves the implementation of the existing decision process rather than changing the scheduling objective or introducing a general-purpose optimization solver.

### Result

The final scheduler combines:

**Constraint correctness · deterministic behavior · reproducible benchmarking · efficient candidate evaluation**

with a measured canonical runtime of approximately **130 ms**.

---

## Correctness, Testing & Validation

Correctness is a core requirement of PlacementOps.

The system validates scheduling behavior at both the individual constraint level and the complete schedule level, with automated tests covering generation, replanning, API validation, and regression behavior.

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
```

### Constraint Validation

Every accepted assignment must satisfy the applicable scheduling constraints.

The validation covers:

| Area | Validation |
|---|---|
| **Student** | Availability and overlap safety |
| **Panel** | Availability, conflicts, and concurrency |
| **Room** | Availability and overlap safety |
| **Company** | Placement-day eligibility |
| **Interview** | Duration and operating-hour compliance |

An assignment that violates a hard constraint is rejected rather than repaired after it has entered the schedule.

### Schedule Integrity

The final schedule is validated independently of candidate selection.

Checks include:

```text
Valid entity references
        +
Valid assignment fields
        +
No duplicate assignments
        +
Scheduled / unscheduled accounting
        +
No resource-time conflicts
```

This ensures that a scheduler run cannot be considered successful merely because it returned a result.

### Replanning Validation

Replanning adds another validation layer because it starts from an existing schedule.

After a disruption, PlacementOps verifies:

```text
Affected assignments
        ↓
Replanned assignments
        ↓
Constraint validity
        ↓
Interview accounting
        ↓
Disruption-specific postconditions
```

Supported disruption scenarios include:

```text
ROOM_UNAVAILABLE
PANEL_UNAVAILABLE
COMPANY_DELAY
STUDENT_WITHDRAWAL
```

Student withdrawal is validated separately: interviews belonging to a withdrawn candidate are removed and are not reassigned.

### Deterministic Regression

The canonical dataset provides a stable reference for regression testing.

```text
Canonical Dataset
       ↓
Reference Scheduler
       ↓
Reference Result
       ↓
Implementation Change
       ↓
Compare Against Reference
```

For the scheduler optimization, the comparison showed:

```text
Scheduled assignments     476 / 476 identical
Unscheduled interview IDs      identical
Candidate scoring         96,421 / 96,421 equivalent
Scheduling conflicts                   0
```

This verifies behavioral equivalence rather than checking only aggregate metrics.

### End-to-End Validation

Complete operational workflows are also tested:

```text
Generate Schedule
       ↓
Apply Disruption
       ↓
Replan
       ↓
Validate Result
       ↓
Compare Before / After
```

A representative canonical student-withdrawal scenario produced:

| Metric | Result |
|---|---:|
| Baseline scheduled | **476** |
| Replanned scheduled | **473** |
| Affected interviews | **3** |
| Withdrawn student's remaining assignments | **0** |
| Newly unscheduled | **3** |

This validates the behavior of the complete generate → disrupt → replan workflow.

### API Validation

API tests verify both successful requests and invalid inputs.

```text
Valid Request
     ↓
Scheduling Workflow

Malformed Request
     ↓
422 Validation Error

Invalid Domain Input
     ↓
400 Bad Request
```

This keeps malformed or invalid operational commands from reaching the core scheduling logic.

### Test Suite

At the previously validated Phase 2 checkpoint, the backend suite contained:

```text
49 total tests
47 passed
2 skipped
```

The skipped cases were intentional and were not failing tests. The repository should be re-run before release so these figures match the exact published state.

### Correctness Principles

PlacementOps treats the following as invariants:

**Valid assignments**  
Hard scheduling constraints cannot be violated.

**Consistent accounting**  
Every interview is either scheduled or explicitly unscheduled.

**Deterministic behavior**  
The same input state produces the same scheduling result.

**Safe replanning**  
Disruptions cannot introduce invalid assignments.

**Regression safety**  
Performance improvements must preserve established scheduling behavior.

---

## Frontend & Operations Console

PlacementOps includes a recruiter-facing operations console for exploring and managing the placement schedule.

The interface is built around the state produced by the backend scheduling system. It does not contain an independent scheduling model or make scheduling decisions in the browser.

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
```

Each workspace answers a different operational question without forcing the entire scheduling system into a single dashboard.

### Overview

The overview provides the current state of placement week at a glance.

It surfaces the most important operational metrics, including:

```text
Scheduled Interviews
Unscheduled Interviews
Completion Rate
Resource Utilization
Schedule Span
Placement-Day Distribution
```

The objective is simple:

> **Understand the current schedule before taking action.**

### Schedule

The schedule workspace is the primary record-level view.

Operators can:

- search interviews
- filter scheduling records
- sort results
- paginate through assignments
- inspect individual interviews
- export schedule data as CSV

An assignment can be inspected through its scheduling dimensions:

```text
Student
Company
Placement Day
Start / End Time
Panel
Room
Duration
```

### Timeline

The timeline provides a visual representation of assignments across time and resources.

```text
             09:00   10:00   11:00   12:00   13:00   14:00   15:00   16:00   17:00

Room R01               
Room R02                    
Room R03                        
Panel P01            
...
```

Each interview appears as a time-based assignment within its resource lane.

This view makes resource utilization, scheduling density, and temporal relationships easier to inspect than a table alone.

The visible timeline range is a presentation choice and does not alter the backend scheduling horizon.

### Analytics

The analytics workspace turns the current scheduling state into operational views.

Examples include:

```text
Scheduled vs. Unscheduled
Interviews by Placement Day
Interviews by Time Window
Room Utilization
Panel Utilization
Company Workload
```

The visualizations are derived from scheduling data returned by the backend, so the dashboard remains consistent with the actual schedule.

### Replanning

The replanning workspace connects operational disruption with its resulting schedule impact.

```text
Disruption
    ↓
Run Replan
    ↓
Replanned Schedule
    ↓
Impact Review
```

The interface makes changed assignments explicit:

```text
UNCHANGED
RESCHEDULED
UNSCHEDULED
```

Operators can therefore compare the before-and-after scheduling state instead of losing the original assignment information.

### Unscheduled Work

Interviews without feasible assignments remain visible as a separate workload.

This gives operators a clear distinction between:

```text
Scheduled Work
      +
Unscheduled Demand
```

The frontend presents the information available from the scheduling system rather than inventing reasons for why an interview could not be placed.

### Assignment Inspection

Individual interview details can be opened from the schedule workspace.

The detail view presents the complete assignment context in one place:

```text
Candidate
Company
Day
Time
Panel
Room
Duration
```

This supports quick operational checks without requiring the user to inspect raw API responses.

### Notifications

The console provides lightweight feedback for meaningful system events such as:

```text
Schedule Generated
Replan Completed
Validation Warning
Operation Failed
```

Notifications are intentionally secondary to the scheduling workspace so that operational feedback does not overwhelm the primary information.

### Navigation & Responsive Layout

The desktop interface uses a collapsible navigation rail so that the main workspace can expand when navigation is not needed.

On smaller screens, navigation adapts to the available viewport while preserving access to the core scheduling workflows.

The layout is designed around:

```text
Navigation
   +
Focused Workspace
   +
Dense Scheduling Information
```

rather than placing every feature on a single screen.

### Visual System

PlacementOps uses a consistent **Midnight Cobalt + Ice** visual system across the application.

The design emphasizes:

```text
Strong information hierarchy
Scheduling-oriented grid structure
Readable tables
Clear time-based visualization
Restrained status colors
Light / Dark themes
```

The visual language is intentionally operational rather than decorative.

### Frontend / Backend Boundary

The frontend is responsible for:

```text
Presentation
Interaction
Filtering
Visualization
User Feedback
```

The backend remains responsible for:

```text
Scheduling Decisions
Constraint Validation
Replanning
Operational State
```

This keeps the browser focused on interacting with scheduling state while the core scheduling logic remains centralized and testable.

### Design Goal

The frontend is built around one principle:

> **Make a complex scheduling system easy to inspect and operate.**

The result is an operations console that lets a recruiter or placement operator move from:

```text
What is happening?
        ↓
Where is the pressure?
        ↓
What changed?
        ↓
What should be replanned?
        ↓
What is the resulting state?
```

without needing to understand the internal scheduling implementation.

---

## AI Assistant & Gemini Integration

PlacementOps includes a Gemini-powered assistant that provides a natural-language interface to the current scheduling state.

The assistant is deliberately separated from the scheduling engine:

> **PlacementOps makes scheduling decisions. Gemini helps operators understand them.**

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
```

The browser communicates only with the PlacementOps backend. Gemini is called server-side.

### Grounded Scheduling Context

The backend builds the context supplied to Gemini from the current PlacementOps state.

```text
Current Schedule
      +
Schedule Metrics
      +
Resource State
      +
Replanning Results
      +
Relevant Interview Data
      ↓
Structured Assistant Context
```

This gives the model application-specific information instead of relying only on general model knowledge.

Example questions include:

```text
"How many interviews are scheduled?"

"Which company has the highest interview workload?"

"Which room is most utilized?"

"What changed after the room outage?"

"Show me this interview's details."
```

### Deterministic Facts

For questions that can be answered directly from scheduling state, the application remains responsible for computing the underlying value.

```text
PlacementOps State
      ↓
Deterministic Calculation
      ↓
Exact Fact
      ↓
Gemini
      ↓
Natural-Language Response
```

This is used for operational information such as:

```text
Counts
Utilization
Totals
Day-level statistics
Interview assignments
Replanning impact
```

The model therefore acts as the conversational layer rather than the source of truth for scheduling data.

### Streaming

Assistant responses are streamed from the backend using Server-Sent Events.

```text
Gemini
   
    response chunks
   
FastAPI
   
    SSE
   
React
   
   
Incremental UI Update
```

This allows the response to appear progressively in the assistant interface.

### Security Boundary

The Gemini credential is kept server-side.

```text
Browser
   
     no Gemini credential
   
   
FastAPI
   
   
Gemini API
```

Provider configuration is supplied through backend environment variables rather than embedded in frontend code or committed to the repository.

### AI Responsibility Boundary

| Concern | System Responsible |
|---|---|
| **Scheduling decisions** | PlacementOps Scheduler |
| **Constraint validation** | PlacementOps Backend |
| **Disruption recovery** | PlacementOps Replanner |
| **Operational facts** | PlacementOps Scheduling State |
| **Natural-language interaction** | Gemini |

This boundary keeps the core scheduling workflow deterministic and testable while still providing a conversational interface.

### Failure Isolation

Gemini is an optional interface layer.

A provider failure should not prevent the core system from generating, validating, or replanning schedules.

```text
             PlacementOps
                  
        
                           
 Scheduling / Replanning   Gemini
                           
                            optional interface
        
 Core scheduling workflow
```

### Design Principle

The AI integration follows a simple rule:

> **Use AI for interpretation and interaction, not for authoritative scheduling decisions.**

This keeps PlacementOps deterministic where correctness matters while using Gemini where natural-language interaction provides the most value.

---

## Project Structure & Code Organization

PlacementOps is organized so that scheduling logic, API behavior, data generation, and frontend presentation remain separated.

```text
placement-ops/

 backend/
    placementops/
        api/
           routes.py
           service.py
       
        dataset/
           generator.py
       
        scheduling/
           scheduler.py
           constraints.py
           replanner.py
           metrics.py
       
        app.py

 frontend/
    src/
       components/
       ...
   
    package.json
    vite.config.*

 tests/
    test_api.py
    test_scheduling_replanner.py
    test_scheduling_replanning_metrics.py

 requirements.txt
 .gitignore
 README.md
```

### Backend

The backend is divided around the scheduling domain.

| Path | Responsibility |
|---|---|
| `backend/placementops/api/` | HTTP routes and application-level service orchestration |
| `backend/placementops/dataset/` | Deterministic synthetic dataset generation |
| `backend/placementops/scheduling/` | Scheduling, constraints, replanning, and metrics |
| `backend/placementops/app.py` | FastAPI application entry point |

The most important separation is inside `scheduling/`:

```text
scheduler.py
    ↓
Creates the initial schedule

constraints.py
    ↓
Defines / evaluates scheduling feasibility

replanner.py
    ↓
Handles disruption recovery

metrics.py
    ↓
Derives scheduling and replanning metrics
```

This keeps the core scheduling logic independent from HTTP transport and UI concerns.

### Frontend

The React frontend is responsible for presenting and interacting with the scheduling state.

The frontend contains the application shell and focused workspaces for:

```text
Schedule
Timeline
Analytics
Replanning
Notifications
Assistant
```

UI components remain separate from the backend scheduling implementation.

### Dataset Generation

`dataset/generator.py` creates the synthetic placement workload used by the application and tests.

The generator is seed-driven so that the same canonical seed can recreate the same scheduling input.

```text
Seed
 ↓
Students
Companies
Panels
Rooms
Interview Requests
Availability
 ↓
Canonical Placement Dataset
```

### Tests

The `tests/` directory covers the backend scheduling and operational behavior.

Tests are organized around the major system boundaries:

```text
API
 ↓
Scheduling
 ↓
Replanning
 ↓
Metrics
```

This structure makes it possible to test the scheduling domain independently from the frontend.

### Dependency Direction

The project follows a simple dependency direction:

```text
Frontend
   ↓
FastAPI API
   ↓
Application Services
   ↓
Scheduling Domain
   ↓
Dataset / Scheduling State
```

The scheduling engine does not depend on the React application, which keeps the core algorithm reusable and independently testable.

### Why the Structure Matters

The repository is intentionally organized around **responsibilities rather than features alone**.

A scheduling change should primarily live in the scheduling layer.

An API change should primarily affect the API layer.

A frontend visualization should not require changes to the scheduling algorithm.

This separation makes the project easier to test, profile, debug, and extend.

---

## Technology Stack

PlacementOps uses a lightweight full-stack architecture with Python/FastAPI on the backend and React/Vite on the frontend.

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
```

Python is used for the scheduling engine, constraint evaluation, replanning, metrics, dataset generation, and backend services.

FastAPI provides the HTTP boundary and request validation, while Uvicorn serves the application.

### Frontend

The frontend uses:

```text
React 19
    +
Vite
    +
JavaScript
    +
CSS
```

React provides the component model for the operations console.

Vite provides the development server and production build pipeline.

CSS is used for the responsive dashboard, scheduling timeline, light/dark themes, tables, forms, and other visual elements.

### AI Layer

Google Gemini is integrated through the backend rather than directly from the browser.

```text
React
  ↓
FastAPI
  ↓
Gemini
```

This keeps the provider credential server-side and allows PlacementOps to prepare the scheduling context before requesting a response.

### Testing

The backend uses Python's built-in `unittest` framework.

The test suite covers the core application boundaries, including:

```text
API
Scheduling
Constraints
Replanning
Metrics
Regression Behavior
```

The deterministic dataset also provides a stable workload for benchmarking and regression comparison.

### Why This Stack

The stack is intentionally simple.

The project does not introduce a large framework ecosystem around the scheduling engine. Each major technology has a focused responsibility:

```text
React        → user interface
Vite         → frontend tooling
FastAPI      → application API
Python       → scheduling domain
Uvicorn      → application server
Gemini       → natural-language interface
unittest     → automated validation
Git          → source control
```

This keeps the implementation approachable while leaving the scheduling engine independent from the presentation layer.

---

## Local Development & Setup

PlacementOps can be run locally as two processes:

```text
React / Vite Frontend
        
         HTTP
        
FastAPI Backend
        
        
PlacementOps Scheduling Engine
```

### Prerequisites

Install:

- Python 3.x
- Node.js and npm
- Git

The exact supported versions should match the versions documented by the repository's dependency files.

### Clone the Repository

```bash
git clone https://github.com/ys18yash/placement-ops.git
cd placement-ops
```

### Backend Setup

Create a Python virtual environment:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server from the repository root:

```bash
python -m uvicorn placementops.app:app --reload --app-dir backend
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### Frontend Setup

Open a second terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The frontend will be available at the local URL printed by Vite.

### Development API Connection

During local development, the frontend communicates with the FastAPI backend through the configured API base URL / Vite proxy.

```text
Browser
   ↓
Vite Development Server
   ↓
FastAPI :8000
   ↓
PlacementOps
```

This keeps frontend development separate from the backend process while allowing the operations console to use the live scheduling APIs.

### Gemini Configuration

Gemini credentials must remain server-side.

Configure the backend with the environment variables expected by the application:

```text
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Do not commit API credentials or local environment files to Git.

### Running the Full Application

Start both processes:

```text
Terminal 1

FastAPI
  ↓
http://127.0.0.1:8000

Terminal 2

React / Vite
  ↓
Local frontend URL
```

Open the frontend in a browser to generate schedules, inspect assignments, simulate disruptions, run replanning, and use the assistant.

### Running Tests

From the repository root:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Because the backend package lives under `backend/`, if Python cannot resolve `placementops` in a fresh shell, set the module path explicitly before running the suite:

```powershell
$env:PYTHONPATH="backend"
python -m unittest discover -s tests -p "test_*.py"
```

The test suite validates the backend scheduling and operational workflows.

### Canonical Dataset

The canonical dataset uses:

```text
Seed: 20260829
```

The fixed seed provides a reproducible workload for local testing, benchmarking, and regression comparisons.

### Development Workflow

A typical development cycle is:

```text
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
```

The frontend and backend can therefore be developed independently while sharing the same scheduling API contract.

---

## API Usage & Example Workflow

PlacementOps can be used through the FastAPI endpoints independently of the React frontend.

The main operational workflow is:

```text
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

### Generate a Schedule

Send a request to:

```text
POST /schedule/generate
```

The endpoint generates the schedule from the configured placement dataset and returns the scheduling result.

Conceptually:

```text
Client
  ↓
/schedule/generate
  ↓
Scheduler
  ↓
Validated Schedule
  ↓
JSON Response
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/schedule/generate
```

The exact request body should match the request schema exposed by the FastAPI documentation.

### Replan After a Disruption

Send a request to:

```text
POST /schedule/replan
```

The request specifies the disruption and the information required to apply it to the current scheduling state.

Supported disruption types:

```text
ROOM_UNAVAILABLE
PANEL_UNAVAILABLE
COMPANY_DELAY
STUDENT_WITHDRAWAL
```

The replanning response contains the resulting scheduling state and the information required to understand the operational impact.

### Health Check

Verify that the backend is running:

```bash
curl http://127.0.0.1:8000/health
```

### Interactive API Documentation

FastAPI exposes interactive documentation at:

```text
http://127.0.0.1:8000/docs
```

The documentation is the authoritative reference for the current request and response schemas.

### Example Operational Workflow

A typical API-driven workflow is:

1. Generate the baseline schedule.
2. Inspect scheduled and unscheduled interviews.
3. Apply an operational disruption.
4. Run deterministic replanning.
5. Validate the resulting schedule.
6. Compare the original and replanned state.

This makes it possible to operate PlacementOps without relying on the React frontend.

---

## Deployment & Production Configuration

PlacementOps is designed to separate the frontend deployment from the FastAPI backend.

A practical production setup is:

```text
GitHub
  
   Vercel
                   React / Vite Frontend
  
   Render
                    FastAPI Backend
                        
                        
                       Gemini
```

### Frontend Deployment

The React application can be deployed from the `frontend` directory.

Typical Vercel configuration:

```text
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
```

The production frontend should point to the deployed FastAPI backend through the configured API base URL.

Example:

```text
VITE_API_BASE_URL=https://<your-backend>.onrender.com
```

### Backend Deployment

The FastAPI application can be deployed as a Python web service.

Typical Render configuration:

```text
Root Directory: /
Build Command: pip install -r requirements.txt
```

Start command:

```bash
uvicorn placementops.app:app --host 0.0.0.0 --port $PORT --app-dir backend
```

Production deployments should not use:

```text
--reload
```

The deployed service should expose:

```text
/health
/docs
```

### Environment Variables

Backend-only configuration should be supplied through environment variables.

Example:

```text
GEMINI_API_KEY=<your-key>
GEMINI_MODEL=<configured-model>
```

Frontend configuration may include:

```text
VITE_API_BASE_URL=<deployed-backend-url>
```

Secrets must never be committed to the repository or embedded in frontend source code.

### CORS

The FastAPI backend must allow requests from the deployed frontend origin.

For production, CORS should be configured for the actual frontend origin rather than using an unnecessarily broad wildcard policy.

Conceptually:

```text
Vercel Frontend
      
       HTTPS
      
Render FastAPI
      
      
PlacementOps
```

### Production Request Flow

```text
Browser
   ↓
Vercel
   ↓
FastAPI API
   ↓
Scheduling / Replanning
   ↓
Response
```

For assistant requests:

```text
Browser
   ↓
FastAPI
   ↓
Gemini
   ↓
SSE Stream
   ↓
Browser
```

This keeps provider credentials and scheduling logic on the server side.

### Deployment Checklist

Before publishing the live application:

```text
Backend
 production start command configured
 /health responds successfully
 /docs responds successfully
 environment variables configured
 CORS restricted to the frontend origin

Frontend
 production build succeeds
 API base URL points to the deployed backend
 no local development URLs remain

Repository
 secrets excluded
 environment files ignored
 generated build artifacts ignored
 tests pass
```

---

## Future Improvements

PlacementOps is intentionally focused on the core placement scheduling and replanning workflow.

Potential future improvements include:

### Scheduling

- stronger optimization objectives beyond the current heuristic scoring
- additional fairness constraints across candidates and resources
- improved handling of multi-stage interview processes
- larger-scale workload benchmarking
- optional comparison with mathematical optimization approaches

### Replanning

- richer disruption combinations
- configurable replan objectives
- priority-aware preservation of critical assignments
- historical disruption tracking
- operator approval before committing a replan

### Operations

- persistent schedule storage
- user authentication and role-based access
- audit logs for operational changes
- richer export formats
- calendar and notification integrations

### Analytics

- historical utilization trends
- resource bottleneck forecasting
- company-level capacity analysis
- what-if simulation for additional staffing or rooms

### AI

- broader natural-language exploration of scheduling state
- configurable assistant actions with explicit approval
- richer context selection for complex operational questions
- evaluation of assistant responses against deterministic application facts

These improvements would extend the system while preserving its central design principle:

```text
deterministic scheduling state
        +
explicit operational controls
        +
AI-assisted interpretation
```

---

## Project Links

**Live Demo:** YOUR_LIVE_LINK  
**GitHub:** https://github.com/ys18yash/placement-ops  
**API Docs:** YOUR_API_LINK

---

## License

This project is available under the license included in the repository.

---

## Author

**Yash Sharma**

Software Engineering · Full-Stack Development · Backend · AI Integration

PlacementOps was built as an engineering-focused scheduling system combining constraint-aware scheduling, deterministic replanning, performance optimization, API design, operational visualization, and grounded AI assistance.
