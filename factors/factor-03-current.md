# Factor 3: Current

**Definition:** Data reflects the present state, with freshness enforced by infrastructure rather than assumed by convention.

## The Shift

Models have no concept of time. Every input is treated as ground truth. When a model receives stale data, it doesn't produce a "stale answer" — it produces a confident, wrong one. The staleness is invisible in the output.

Traditional analytics tolerates staleness through convention: "this dashboard refreshes nightly," "that report uses yesterday's data." Humans adjust their interpretation accordingly. AI systems cannot. An agent answering "what's my current balance?" will state yesterday's number as fact.

Freshness must be enforced by infrastructure:
- **Change tracking** captures when data changes
- **Streams** propagate changes incrementally
- **Dynamic tables** maintain derived data automatically
- **Freshness monitoring** alerts when data falls outside SLA

Without these mechanisms, freshness depends on pipeline schedules holding, jobs not failing, and upstream sources behaving — a chain of assumptions that eventually breaks.

### Per-workload tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for stale data: Moderate.** Dashboards and reports often show historical data by design. Users understand "as of yesterday" or "refreshed hourly."

**L2 (RAG and retrieval systems)** — **Tolerance for stale data: Low.** Users expect current information. A support agent citing outdated policies or a knowledge base returning superseded procedures creates real harm.

**L3 (ML model training and fine-tuning)** — **Tolerance for stale data: Very low.** Training on stale data teaches the model outdated patterns. Feature stores must maintain point-in-time correctness — the features at inference must match what was available at training.

## Requirements

What must be true about the data for each workload. These requirements focus on the **infrastructure** for freshness that we can measure in database platforms.

### Change Detection

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Change tracking** | Change tracking enabled on key tables for audit; not required everywhere | Change tracking on tables in the retrieval scope for incremental updates | Change tracking on all assessed tables; full CDC coverage for training pipelines |
| **Stream coverage** | Streams on tables that feed downstream pipelines | Streams on tables that feed RAG indices for near-real-time updates | Streams on all tables with downstream dependencies |

### Freshness

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Data freshness** | Most tables updated within a reasonable window (days to weeks) | Tables in retrieval scope updated within SLA (hours to days) | All tables updated within strict SLA; stale training data is blocked |
| **Automatic refresh** | Static views acceptable for most derived data | Dynamic tables for data that feeds retrieval systems | Dynamic tables for all derived data to eliminate staleness windows |

## Required Stack Capabilities

What the platform must support to consistently meet these requirements.

| Capability | L1 | L2 | L3 |
|------------|----|----|-----|
| **Change tracking** | Platform tracks row-level changes with timestamps | — | — |
| **Streams/CDC** | Platform supports streams for change data capture | Streams support append-only and full CDC modes | — |
| **Dynamic tables** | Platform supports automatically refreshed derived tables | Target lag configurable per table | Downstream cascade support |
| **Freshness monitoring** | Platform exposes last_altered timestamps | — | Freshness SLA alerting |

## Requirement keys (for tests and remediation)

Stable identifiers for use in test definitions, threshold config, and remediation templates.

| Dimension | Requirement (name) | Key |
|-----------|-------------------|-----|
| Change Detection | Change tracking | `change_tracking_coverage` |
| Change Detection | Stream coverage | `stream_coverage` |
| Freshness | Data freshness | `data_freshness_pass_rate` |
| Freshness | Automatic refresh | `dynamic_table_coverage` |

## Future Requirements

The full vision of current data (from the AI-Ready Data framework) includes requirements we do not yet test:

- **Event timestamps:** Data carries explicit timestamps distinguishing event time from processing time
- **Declared freshness contracts:** Data carries its freshness SLA as metadata
- **Staleness metadata:** Data carries computed currency scores for prioritized refresh
- **Point-in-time correctness:** Feature values at inference match those available at training
- **Staleness blocking:** Circuit breakers block consumption when freshness contracts are violated

These are documented in `/factors.md` and will be implemented as the framework matures.

Implementation status by suite and platform: [docs/coverage/README.md](../docs/coverage/README.md).
