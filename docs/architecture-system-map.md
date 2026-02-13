# AI-Ready Data Assessment — System Map

A conceptual map of the entire system: framework, agent playbook, skills, and how they relate to the CLI (in the separate [ai-ready-data-cli](https://github.com/ai-ready-data/ai-ready-data-cli) repo).

---

## 1. High-Level Architecture (Two Repos)

```mermaid
flowchart TB
  subgraph framework ["ai-ready-data-agent (this repo)"]
    direction TB
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
      Factors["skills/factors/*.md"]
    end

    subgraph layer2 [Layer 2: Agentic Skills]
      direction TB
      Playbook[AGENTS.md<br/>Playbook]
      ParentSkill["skills/SKILL.md<br/>Parent: assess-data"]
      Workflows["skills/workflows/"]
      Platforms["skills/platforms/"]
      Playbook --> ParentSkill
      ParentSkill --> Workflows
      ParentSkill --> Platforms
    end

    layer1 --> layer2
  end

  subgraph cli ["ai-ready-data-cli (separate repo)"]
    direction TB
    subgraph layer3 [Layer 3: CLI Tool]
      direction TB
      CLI[aird CLI]
      Suites[Test Suites]
      PlatformAdapters[Platform Adapters]
      CLI --> Suites
      CLI --> PlatformAdapters
    end

    CLISkills["CLI Agent Skills"]
    CLISkills --> CLI
  end

  User[Data Engineer / Coding Agent] --> layer2
  CLISkills -.->|references| layer1
  layer3 --> Report[Report / History]
  Report --> User
```

---

## 2. Agent Playbook & Skills Hierarchy

```mermaid
flowchart TB
  subgraph Playbook [AGENTS.md — Agent Playbook]
    Role[Role: Read-only assessor]
    Workflow[Workflow: 5 steps]
    Constraints[Constraints: No write SQL, suggest only]
  end

  subgraph Parent [Parent Skill]
    AssessData["skills/SKILL.md<br/>assess-data"]
    Intent[Intent routing table]
    Forbidden[Forbidden actions]
  end

  subgraph WorkflowSkills [Workflow Skills]
    W1[discover]
    W2[assess]
    W3[interpret]
    W4[remediate]
  end

  subgraph FactorSkills [Factor Skills]
    F0[0-clean]
    F1[1-contextual]
    F2[2-consumable]
    F3[3-current]
    F4[4-correlated]
    F5[5-compliant]
  end

  subgraph PlatformSkills [Platform Skills]
    P1[snowflake]
  end

  Playbook --> Parent
  Parent --> W1 & W2 & W3 & W4
  W2 & W3 & W4 --> FactorSkills
  W1 & W2 --> PlatformSkills
```

---

## 3. Workflow & Stopping Points

```mermaid
flowchart LR
  subgraph Phase1 [Phase 1]
    I1["1. Understand data<br/>workflows/discover"]
    I1 --> STOP1
    STOP1[STOP]
  end

  subgraph Phase2 [Phase 2]
    D["2. Discover schema<br/>platforms/*.md"]
    STOP2[STOP]
    D --> STOP2
  end

  subgraph Phase3 [Phase 3]
    A["3. Assess<br/>factors/*.md"]
    STOP3[STOP]
    A --> STOP3
  end

  subgraph Phase4 [Phase 4]
    IN["4. Interpret<br/>workflows/interpret"]
    STOP4[STOP]
    IN --> STOP4
  end

  subgraph Phase5 [Phase 5]
    REM["5. Suggest fixes<br/>workflows/remediate"]
    STOP5[STOP]
    REM --> STOP5
  end

  STOP1 --> D
  STOP2 --> A
  STOP3 --> IN
  STOP4 --> REM
```

---

## 4. Full System Overview (Compact)

```mermaid
flowchart TB
  User[User / Coding Agent]
  Playbook[AGENTS.md]
  Skills[Skills Layer]
  Factors[6 Factors × 3 Levels]
  Platforms[Platform SQL Patterns]
  Report[Assessment Results]

  User --> Playbook
  Playbook --> Skills
  Skills --> Factors
  Skills --> Platforms
  Factors --> Report
  Report --> User

  CLI["aird CLI<br/>(separate repo)"]
  Skills -.->|optional| CLI
  CLI --> Report
```

---

## Key Files Reference

| Component | Location |
|-----------|----------|
| Playbook | `AGENTS.md` |
| Parent skill | `skills/SKILL.md` |
| Workflow skills | `skills/workflows/{discover,assess,interpret,remediate}.md` |
| Factor skills | `skills/factors/{0-clean,1-contextual,2-consumable,3-current,4-correlated,5-compliant}.md` |
| Platform skills | `skills/platforms/snowflake.md` |
| Audit skill | `skills/audit/SKILL.md` |
| CLI tool | [ai-ready-data-cli](https://github.com/ai-ready-data/ai-ready-data-cli) repo |
