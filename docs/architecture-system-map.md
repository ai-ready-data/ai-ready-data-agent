# AI-Ready Data Assessment — System Map

A conceptual map of the entire system: framework, agent playbook, skills, CLI, and components.

---

## 1. High-Level Architecture (Three Layers)

```mermaid
flowchart TB
  subgraph layer1 [Layer 1: Factors Framework]
    direction TB
    F0[Clean]
    F1[Contextual]
    F2[Consumable]
    F3[Current]
    F4[Correlated]
    F5[Compliant]
    L1[L1 Analytics]
    L2[L2 RAG]
    L3[L3 Training]
    Factors[factors/*.md]
  end

  subgraph layer2 [Layer 2: Agentic System]
    direction TB
    Playbook[AGENTS.md<br/>Playbook]
    ParentSkill[skills/SKILL.md<br/>Parent: assess-data]
    SubSkills[Sub-skills]
    Refs[references/*.md]
    Playbook --> ParentSkill
    ParentSkill --> SubSkills
    SubSkills --> Refs
  end

  subgraph layer3 [Layer 3: Executable Tests]
    direction TB
    CLI[aird CLI]
    Suites[Suites]
    Platforms[Platform Adapters]
    CLI --> Suites
    CLI --> Platforms
  end

  User[Data Engineer / Coding Agent] --> layer2
  layer1 --> layer2
  layer2 --> layer3
  layer3 --> Report[Report / History]
  Report --> User
```

---

## 2. Agent Playbook & Skills Hierarchy

```mermaid
flowchart TB
  subgraph Playbook [AGENTS.md — Agent Playbook]
    Role[Role: Read-only assessor]
    Workflow[Workflow: 8 steps]
    Constraints[Constraints: No write SQL, suggest only]
  end

  subgraph Parent [Parent Skill]
    AssessData[skills/SKILL.md<br/>assess-data]
    Intent[Intent routing table]
    Forbidden[Forbidden actions]
  end

  subgraph SubSkills [Sub-skills]
    S1[connect]
    S2[discover]
    S3[assess]
    S4[interpret]
    S5[interview]
    S6[remediate]
    S7[compare]
    S8[report]
    S9[add-platform]
  end

  subgraph Refs [References]
    R1[platforms.md]
    R2[cli-commands.md]
    R3[context-file.md]
    R4[connections-manifest.md]
  end

  Playbook --> Parent
  Parent --> S1 & S2 & S3 & S4 & S5 & S6 & S7 & S8 & S9
  S1 & S2 & S3 & S4 & S5 & S6 & S7 & S8 --> Refs
```

---

## 3. Workflow & Stopping Points

```mermaid
flowchart LR
  subgraph Phase1 [Phase 1]
    I1[1. Understand data<br/>interview/SKILL]
    I1 --> STOP1
    STOP1[STOP]
  end

  subgraph Phase2 [Phase 2]
    C[2. Connect<br/>connect/SKILL]
    D[3. Discover & scope<br/>discover/SKILL]
    STOP2[STOP]
    C --> D --> STOP2
  end

  subgraph Phase3 [Phase 3]
    A[4. Assess<br/>assess/SKILL]
    STOP3[STOP]
    A --> STOP3
  end

  subgraph Phase4 [Phase 4]
    IN[5. Interpret<br/>interpret/SKILL]
    STOP4[STOP]
    IN --> STOP4
  end

  subgraph Phase5 [Phase 5]
    REM[6. Suggest fixes<br/>remediate/SKILL]
    STOP5[STOP]
    REM --> STOP5
  end

  subgraph Phase6 [Phase 6 Optional]
    COMP[7. Compare<br/>compare/SKILL]
    BENCH[8. Benchmark]
  end

  STOP1 --> C
  STOP2 --> A
  STOP3 --> IN
  STOP4 --> REM
  STOP5 --> COMP
  COMP --> BENCH
```

---

## 4. CLI Commands & Pipeline

```mermaid
flowchart TB
  subgraph CLI [aird CLI]
    Init[init]
    Assess[assess]
    Discover[discover]
    Run[run]
    Report[report]
    Save[save]
    History[history]
    Diff[diff]
    Suites[suites]
    Compare[compare]
    Rerun[rerun]
    Benchmark[benchmark]
  end

  subgraph Pipeline [Full Pipeline]
    D[discover]
    R[run]
    Rep[report]
    S[save]
    D --> R --> Rep --> S
  end

  subgraph Composable [Composable Path]
    D2[aird discover]
    R2[aird run]
    Rep2[aird report]
    S2[aird save]
    D2 --> R2 --> Rep2 --> S2
  end

  Assess --> Pipeline
  Init -.-> Assess
  Compare --> History
  Rerun --> Run
  Benchmark --> Assess
```

---

## 5. Assessment Pipeline Internals

```mermaid
flowchart TB
  subgraph Input [Input]
    Conn[Connection string]
    Context[Context file]
    Inv[Inventory]
  end

  subgraph Discovery [Discovery]
    Disc[discovery.discover]
    Schemas[Schemas]
    Tables[Tables]
    Columns[Columns]
    Disc --> Schemas & Tables & Columns
  end

  subgraph Run [Test Execution]
    Loader[suite loader]
    Exec[platform executor]
    RunTests[run.run_tests]
    Loader --> Exec --> RunTests
  end

  subgraph Report [Report]
    Build[report.build_report]
    Markdown[report_to_markdown]
    Rich[render_rich_report]
    Build --> Markdown
    Build --> Rich
  end

  subgraph Storage [Storage]
    DB[(~/.aird/assessments.db)]
    Audit[Audit log]
  end

  Conn --> Disc
  Inv --> RunTests
  Disc --> Inv
  RunTests --> Build
  Build --> DB
  Build --> Audit
```

---

## 6. Platform & Suite Architecture

```mermaid
flowchart TB
  subgraph Platforms [Platform Adapters]
    DuckDB[DuckDB]
    SQLite[SQLite]
    Snowflake[Snowflake]
    Registry[platform/registry]
    DuckDB & SQLite & Snowflake --> Registry
  end

  subgraph Suites [Test Suites]
    Common[common]
    CommonSQLite[common_sqlite]
    CleanSnowflake[clean_snowflake]
    ContextualSnowflake[contextual_snowflake]
    CommonSnowflake[common_snowflake]
  end

  subgraph Definitions [Suite Definitions / agent/suites/definitions/]
    CleanCommon[clean_common.yaml]
    CleanSqlite[clean_sqlite.yaml]
    CleanSnowflakeY[clean_snowflake.yaml]
    ContextualY[contextual_snowflake.yaml]
    SnowflakeCommon[snowflake_common.yaml]
  end

  subgraph Factors [Factor Coverage]
    Clean[Clean]
    Contextual[Contextual]
  end

  DuckDB --> Common
  SQLite --> CommonSQLite
  Snowflake --> CleanSnowflake & ContextualSnowflake
  CleanSnowflake --> CommonSnowflake
  ContextualSnowflake --> CommonSnowflake
  Definitions --> Suites
  Suites --> Factors
```

---

## 7. UI Components

```mermaid
flowchart TB
  subgraph Interactive [Interactive Flow -i]
    Flow[ui/flow.InteractiveAssessFlow]
    Welcome[Welcome panel]
    DiscoverSpinner[Discovery spinner]
    ScopeSelect[Scope selection]
    Preview[Test preview]
    Progress[Progress bar]
    Summary[Summary panel]
    Flow --> Welcome --> DiscoverSpinner --> ScopeSelect --> Preview --> Progress --> Summary
  end

  subgraph Console [Console]
    RichConsole[Rich console]
    Confirm[confirm]
    isInteractive[is_interactive]
    Themes[themes]
  end

  subgraph ReportUI [Report Rendering]
    RichReport[render_rich_report]
    Markdown[report_to_markdown]
    RichReport --> SummaryPanel
    RichReport --> FactorTables
    RichReport --> Footer
  end

  subgraph Other [Other UI]
    BenchmarkUI[benchmark UI]
    CompareUI[compare UI]
    SurveyUI[survey prompts]
  end
```

---

## 8. Full System Overview (Compact)

```mermaid
flowchart TB
  User[User / Coding Agent]
  Playbook[AGENTS.md]
  Skills[Skills Layer]
  CLI[aird CLI]
  Factors[6 Factors × 3 Levels]
  Platforms[DuckDB / SQLite / Snowflake]
  Suites[Test Suites]
  Report[Report JSON/MD]
  History[History DB]

  User --> Playbook
  Playbook --> Skills
  Skills --> CLI
  CLI --> Factors
  CLI --> Platforms
  CLI --> Suites
  Suites --> Report
  Report --> History
  Report --> User
  History --> User
```

---

## Key Files Reference

| Component | Location |
|-----------|----------|
| Playbook | `AGENTS.md` |
| Parent skill | `skills/SKILL.md` |
| Sub-skills | `skills/workflows/{discover,assess,interpret,remediate}.md`, `skills/cli/{connect,discover,assess,interpret,remediate,compare}.md` |
| References | `skills/cli/references/{platforms,cli-commands,context-file,connections-manifest}.md` |
| Factors | `skills/factors/0-clean.md`, `1-contextual.md`, `2-consumable.md`, `3-current.md`, `4-correlated.md`, `5-compliant.md` |
| CLI entry | `agent/cli.py` |
| Pipeline | `agent/pipeline.py` |
| Suites | `agent/suites/definitions/*.yaml` |
| UI flow | `agent/ui/flow.py` |
| Rich report | `agent/ui/report.py` |
