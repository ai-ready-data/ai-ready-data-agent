# The AI-Ready Data Framework

**Six factors that determine whether your data can reliably power AI systems.**

An open standard defining what "AI-ready data" actually means, plus portable assessment skills that any AI agent can use to evaluate your data infrastructure.

## Background

The contributors to this project include practicing data engineers, ML practitioners, and platform architects who have built and operated AI systems across industries. This document synthesizes our collective experience building data systems that power reliable and trustworthy AI systems.

The format is inspired by Martin Fowler's work on defining technical patterns, the 12-Factor App methodology, and the 12 Factor Agent.

## Who Should Read This

* **Data engineers** deploying pipelines that power AI systems.
* **Platform teams** designing infrastructure for ML and AI workloads.
* **Architects** evaluating whether their stack can support RAG, agents, or real-time inference.
* **Data leaders** who need to assess organizational AI readiness and communicate gaps to their teams.
* **Coding agents** building the infrastructure they'll eventually consume.

## The Three Workload Levels

Whether data is "AI-ready" depends on what you're building. Different use cases have different tolerance for issues, so the framework defines three workload levels. Every requirement and threshold is scoped to a level.

| Level | Workload | Tolerance for issues | What it means |
|-------|----------|----------------------|---------------|
| **L1** | Descriptive analytics and BI | Moderate | Humans are in the loop. An analyst can spot and compensate for a missing value or an undeclared relationship. |
| **L2** | RAG and retrieval systems | Low | Any chunk of data can become a model response. Ambiguity, staleness, or missing context propagates directly to the end user. |
| **L3** | ML model training and fine-tuning | Very low | Errors are not just retrieved — they are *learned*. Bad data becomes bad weights, silently and permanently. |

Levels are ordered by **strictness of requirements**, not by maturity. L3 is not "better" than L1 — it is a different use case with stricter demands. Meeting a stricter level implies meeting the less strict ones (additivity): if your data passes at L3 for a given requirement, it passes at L2 and L1 too.

Canonical definitions and rationale: [docs/definitions.md](docs/definitions.md).

---

## The 6 Factors

Each factor has requirements at all three workload levels. The factor docs in [`skills/factors/`](skills/factors/) are the single source of truth — each file includes requirements, numeric thresholds, assessment SQL, interpretation rules, remediation patterns, and stack capabilities.

| Factor | Name | Definition |
|--------|------|-------------|
| **0** | [**Clean**](skills/factors/0-clean.md) | Accurate, complete, valid, and free of errors |
| **1** | [**Contextual**](skills/factors/1-contextual.md) | Meaning is explicit and colocated with the data |
| **2** | [**Consumable**](skills/factors/2-consumable.md) | Right format and latencies for AI workloads |
| **3** | [**Current**](skills/factors/3-current.md) | Reflects the present state, freshness enforced |
| **4** | [**Correlated**](skills/factors/4-correlated.md) | Traceable from source to decisions |
| **5** | [**Compliant**](skills/factors/5-compliant.md) | Governed, secure, policy-enforced |

Factor document shape: [docs/specs/factor-spec.md](docs/specs/factor-spec.md).

---

## Skills

Portable, agent-agnostic knowledge for AI-ready data assessment. Organized in two layers:

**Portable knowledge** ([`skills/factors/`](skills/factors/), [`skills/platforms/`](skills/platforms/), [`skills/workflows/`](skills/workflows/)) — Self-contained markdown with everything an agent needs: factor definitions, SQL, thresholds, remediation patterns, and workflow guides. No CLI, no Python, no package install required. Any agent that can read markdown and execute SQL can follow these.

**CLI orchestration** ([`skills/cli/`](skills/cli/)) — For agents with the `aird` CLI available. Shell commands that automate each workflow step. References the portable layer for domain knowledge — never duplicates it. See the [CLI README](cli/README.md) for installation and usage.

Entry point: [`skills/SKILL.md`](skills/SKILL.md). Architecture details: [`skills/README.md`](skills/README.md).

---

## For Cortex Code Users

Install these skills to get AI-ready data assessment capabilities in Cortex Code.

### Option 1: Add to skills.json (recommended)

Add this to `~/.snowflake/cortex/skills.json`:

```json
{
  "remote": [
    {
      "source": "https://github.com/ai-ready-data/ai-ready-data-agent",
      "ref": "main",
      "skills": [
        { "name": "ai-ready-data" },
        { "name": "assess-data-cli" }
      ]
    }
  ]
}
```

### Option 2: Ask Cortex Code to install

Just tell Cortex Code:

> "Install skills from github.com/ai-ready-data/ai-ready-data-agent"

It will read this README and configure the skills for you.

### After installation

Use the skills with:
- `$ai-ready-data` — Universal assessment (works with any SQL connection, no CLI required)
- `$assess-data-cli` — CLI-based assessment (requires `aird` CLI installed)

---

## For Coding Agents

Start at **[AGENTS.md](AGENTS.md)** for the playbook. It outlines the workflow (discover, connect, assess, interpret, remediate, compare), stopping points, and where to find everything.

Skills live in [`skills/`](skills/) with a two-layer architecture:
- **Portable knowledge** — Factor definitions, thresholds, assessment SQL, remediation patterns, and workflow guides. Any agent with SQL access can follow these directly.
- **CLI orchestration** — Shell commands for the `aird` CLI that automate each step. References the portable layer for domain knowledge.

---

## Design & Specs

Specifications, design rationale, and architecture:

- [Project spec](docs/specs/project-spec.md) — purpose, layers, outcomes
- [CLI spec](docs/specs/cli-spec.md) — commands, artifacts, config
- [Factor spec](docs/specs/factor-spec.md) — factor document shape, requirement keys
- [Report spec](docs/specs/report-spec.md) — canonical report JSON schema and markdown rendering
- [Design log](docs/log/) — composability, architecture, analysis

## Contributing

Specs and design rationale live under [docs/specs](docs/specs/) and [docs/log](docs/log/). Contributions that align with the project spec and CLI spec are welcome.

## License

MIT
