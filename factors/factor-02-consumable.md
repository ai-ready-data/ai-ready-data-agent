# Factor 2: Consumable

**Definition:** Data is served in the right format and at the right latencies for AI workloads.

## The Shift

AI workloads have fundamentally different access patterns than BI. Traditional analytics tolerates query times measured in seconds or minutes — a dashboard refresh, a report generation. AI workloads cannot.

- **Vector retrieval** must return in milliseconds for interactive experiences
- **Feature serving** requires sub-100ms latency for real-time inference
- **Inference chains** make multiple round-trips, multiplying any latency

Beyond latency, AI systems require data in specific formats:
- **Embeddings** for semantic search and similarity
- **Pre-chunked documents** sized for context windows
- **Feature vectors** materialized for both training and serving
- **Native formats** (Parquet, JSON, vectors) without conversion overhead

A format mismatch or latency miss isn't a degraded experience — it's a failed prediction, a timeout, a broken agent.

### Per-workload tolerance

**L1 (Descriptive analytics and BI)** — **Tolerance for format/latency issues: High.** Humans wait for dashboards. Data can be transformed at query time. Formats are flexible.

**L2 (RAG and retrieval systems)** — **Tolerance for format/latency issues: Low.** Retrieval must complete in milliseconds. Documents must be pre-chunked. Embeddings must exist. Query-time transformation breaks SLAs.

**L3 (ML model training and fine-tuning)** — **Tolerance for format/latency issues: Very low.** Training processes terabytes repeatedly. Features must exist in both batch (columnar) and serving (row-oriented) formats. Any inefficiency multiplies across epochs.

## Requirements

What must be true about the data for each workload. The full vision includes AI-native formats (embeddings, chunks, vectors). Current implementation focuses on what we can measure in database platforms today.

### Format & Structure

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **AI-consumable format** | Standard table formats are sufficient | Data exists as vectors, chunks, or features without query-time transformation | All AI-serving data is in native consumption formats |
| **Pre-transformed** | Query-time joins and aggregations acceptable | Data is pre-joined, pre-aggregated for consumption patterns | Zero query-time transformation for training pipelines |

### Latency & Performance

| Requirement | L1 | L2 | L3 |
|-------------|----|----|-----|
| **Query optimization** | Acceptable query times for interactive use | Sub-second retrieval for AI-serving tables | Optimized scan performance for training data |
| **Search capability** | Basic text search sufficient | Optimized text/semantic search for retrieval workloads | Full search optimization for any text-based access |

## Required Stack Capabilities

| Capability | L1 | L2 | L3 |
|------------|----|----|-----|
| **Vector storage** | — | Native vector data type; similarity search | Quantization options for scale |
| **Clustering** | Basic indexing | Clustering keys on AI-serving tables | Automatic reclustering |
| **Search optimization** | — | Text search optimization (substring, equality, semantic) | — |
| **Dual-layer storage** | — | Columnar + row-oriented for features | Automated sync between formats |
| **Document processing** | — | Chunking pipelines; metadata extraction | — |

## Requirement keys (for tests and remediation)

Current implementation focuses on performance aspects measurable via information_schema:

| Dimension | Requirement (name) | Key |
|-----------|-------------------|-----|
| Performance | Query optimization | `clustering_coverage` |
| Performance | Search capability | `search_optimization_coverage` |

## Not Yet Implemented

These requirements from `/factors.md` are not yet testable via automated SQL checks:

- **AI-consumable format:** Existence of vector columns, embedding indices
- **Retrieval-optimized chunking:** Document chunk sizes appropriate for context windows
- **Workload-optimized embeddings:** Embedding dimensions match workload tradeoffs
- **Dual-format features:** Features materialized in both columnar and row formats
- **Materialized query results:** Frequent patterns pre-computed as data products

Implementation status by suite and platform: [docs/coverage/README.md](../docs/coverage/README.md).
