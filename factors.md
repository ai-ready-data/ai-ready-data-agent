> **Reference input.** This file is used to guide factor file creation and test development. It is NOT the canonical factor documentation. For canonical factor docs with requirements, thresholds, assessment SQL, and remediation, see [skills/factors/](skills/factors/).

## Factors of AI-Ready Data

| Factor | Factor Name | Definition | Topic Areas | Reasoning | Snowflake Capabilities |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 0 | Clean | Is the data accurate, complete, consistent, and valid? | Quality, Testing, Monitoring | Models are statistical functions \-- they optimize on whatever signal is present in the input distribution, including noise. Dirty data doesn't just degrade output quality, it gets encoded into weights and embeddings as learned patterns, making errors systematic and hard to detect downstream. | Data Quality Monitoring, Data Metric Functions (DMFs), Horizon |
| 1 | Contextual | Is the data's meaning explicit and co-located with canonical semantics? | Semantics, Metadata, Knowledge Representation | LLMs and agents resolve ambiguity through inference, not lookup. Without explicit semantics (types, enums, relationships, business definitions), the model fills gaps with priors from training data \-- producing plausible but wrong interpretations that are invisible at query time. | Horizon Catalog, Tags, Object Comments, Universal Search |
| 2 | Consumable | Is the data served in the right format and at the right latencies for AI workloads? | Accessibility, Interoperability, Performance | AI workloads have fundamentally different access patterns than BI: vector retrieval, feature serving, and inference chains require sub-second latency, native format compatibility (embeddings, JSON, Parquet), and elastic throughput. A format mismatch or latency miss isn't a degraded experience \-- it's a bad prediction. | Iceberg Tables, Dynamic Tables, Cortex AI, Feature Store |
| 3 | Current | Does the data reflect the present state, with freshness enforced by systems? | Freshness, Pipeline Reliability, Temporal Awareness | Models have no concept of time \-- they treat every input as ground truth. Stale data doesn't produce a "stale answer," it produces a confident, wrong one. Freshness must be enforced by infrastructure (CDC, streaming, SLA monitoring), not assumed by convention. | Streams, Tasks, Dynamic Tables, Snowpipe, Snowpipe Streaming |
| 4 | Correlated | Is the data traceable from source to every decision it informs? | Observability, Reproducibility, Cost transparency | AI systems are compositional: data flows through transformations, feature engineering, model inference, and post-processing before producing an output. Without end-to-end lineage, a bad output is a black box \-- you can't isolate whether the failure was in the source data, a transformation, or the model itself. | ACCESS\_HISTORY, OBJECT\_DEPENDENCIES, Time Travel, Query History |
| 5 | Compliant | Is the data governed with explicit ownership, enforced access boundaries, and AI-specific safeguards? | Governance, Privacy, Responsible use | AI introduces novel governance surface area: PII can leak through embeddings, bias can be encoded in training distributions, and model outputs can constitute regulated decisions (credit, hiring, healthcare). Traditional RBAC and audit logs are necessary but insufficient \-- AI-specific controls (consent tracking, bias monitoring, use-case policies) are required to meet emerging regulation. | Masking Policies, Row Access Policies, Governance, Trust Center |

# Curated

## Requirements

| Requirement | What | Why | Target | Use Cases | Maturity |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Semantic type annotations | Fields carry machine-readable semantic type definitions from a governed ontology, specifying business meaning, scope, and context. | AI understands field purpose without ambiguity. Semantic types must be structured, scoped, and machine-actionable. | 100% of key data assets have semantic types | Text-to-SQL, BI agents, analytical AI | Foundation |
| Canonical metric definitions | Authoritative definitions for business metrics stored in version-controlled glossaries with documented formulas, calculation logic, and effective dates. | Different AI systems produce consistent answers to identical questions. | 95%+ metric definition coverage | Text-to-SQL, BI agents, reporting automation | Foundation |
| Schema contracts | Schemas specify semantic relationships, nullability rules, domain constraints, and evolution compatibility modes. | Prevents AI from receiving malformed or semantically invalid data. Semantic validation catches errors that pass schema checks. | Schema contracts on all production data products | All AI workloads | Foundation |
| Entity resolution & relationships | Entity links defined with confidence scores for probabilistic matches, not just deterministic foreign keys.  Entities may exist in multiple states simultaneously. Relationships are scoped, not flattened. | AI understands entity relationships with appropriate uncertainty. | All key entities have documented resolution rules with confidence thresholds; resolution snapshots retained for audit | Knowledge graphs, cross-domain analytics, entity-aware AI | Intermediate |
| Semantic chunk metadata | Document chunks carry LLM-generated summaries, extracted keywords/entities, language codes, and quality confidence scores.  Metadata is versioned. Accuracy targets are explicit. | AI understands chunk content without processing full text. | All indexed documents have semantic metadata; accuracy audited against sample | RAG, document search, chatbots | Advanced |

## Platform Capabilities

| Capability | What It Enables | Snowflake Product | Partner Ecosystem |
| :---- | :---- | :---- | :---- |
| Semantic layer | Centralized metric definitions; NL-to-SQL translation; version-controlled business logic accessible to BI, LLMs, and agents | Semantic Views | dbt Semantic Layer, Cube, AtScale |
| Schema registry | Automated compatibility checking; schema validation at ingestion; evolution tracking (backward, forward, full) | Iceberg schema evolution | Confluent Schema Registry |
| Data catalog | ML-powered metadata discovery; sensitive data classification; natural language search over metadata | Horizon Catalog, Universal Search | Alation, Atlan, Collibra |
| Feature registry | Feature documentation with lineage, ownership, access controls; online/offline sync | Feature Store | Tecton, Feast, Databricks Feature Store |
| Lineage tracking | End-to-end visualization; column-level granularity; automated extraction from SQL and ETL | Horizon Lineage, ACCESS\_HISTORY | Monte Carlo, Atlan, Alation |
| Vector metadata store | Embeddings with metadata; hybrid queries (semantic \+ keyword \+ filtering); filtering operators | Cortex Search | Pinecone, Weaviate, Qdrant |
| Federated governance | Global policy enforcement with domain autonomy; data contracts; API-based metadata access | Horizon Data Governance, Data Clean Rooms | Immuta, Privacera |

# Accessible

## Requirements

| Requirement | What | Why | Maturity | Use Cases | Target |
| :---- | :---- | :---- | :---- | :---- | :---- |
| AI-consumable format | Data exists in formats directly consumable by AI systems—vectors, features, structured chunks—without conversion or transformation at query time | AI systems operate under strict latency budgets; format conversion adds latency and complexity | Foundation | All AI workloads | All AI-serving data is in native consumption formats |
| Pre-transformed for serving | Data is pre-joined, pre-aggregated, and formatted for the consumption pattern; no transformation happens at query time | Query-time transformation adds latency and complexity; pre-transformation shifts cost to write time | Foundation | RAG, real-time ML, chatbots, fraud detection | All AI-serving data requires zero query-time transformation |
| Retrieval-optimized chunking | Document chunks are sized for retrieval quality and context window utilization (typically 256-512 tokens; varies by model architecture) | Chunk size directly impacts retrieval quality and context fragmentation | Foundation | RAG, document search | All indexed corpora use chunk sizes validated against retrieval benchmarks |
| Chunk-level metadata | Each chunk carries: unique ID, source provenance with version, timestamp, pre-computed query representations | Enables filtering, versioning, and debugging of retrieval results | Foundation | RAG, document search | All indexed content has complete chunk metadata |
| Workload-optimized embeddings | Embedding dimensions and quantization match workload tradeoffs: 384 (speed) → 1536+ (quality); int8/float8 quantization where quality loss \<1% | Balances retrieval quality against storage/compute costs | Intermediate | RAG, semantic search, similarity matching | All embedding indices are optimized for their access pattern |
| Dual-format features | Features exist in both columnar format (batch/training) and row-oriented format (real-time serving) | ML features need both batch access (training) and real-time access (inference) from the same source | Intermediate | ML training, real-time inference, feature stores | All ML features are materialized in both formats with consistency guarantees |
| Dual-indexed retrieval | Content is indexed for both dense (vector) and sparse (BM25/keyword) retrieval; hybrid search via reciprocal rank fusion | Pure vector search misses keyword matches; pure keyword misses semantic similarity | Intermediate | RAG, enterprise search | All RAG corpora support hybrid retrieval |
| Materialized query results | Frequent query patterns exist as pre-computed data products; semantically similar queries resolve from cached results | Repeated/similar queries are common; materialization shifts cost from read time to write time | Advanced | RAG, chatbots, high-volume applications | High-frequency query patterns are materialized as data products |
| Multiple embedding representations | Content exists as original text plus rephrased/summarized versions; hierarchical embeddings at document and chunk levels | Different query types match different representations; improves recall coverage | Advanced | RAG, document search | Key corpora have multiple indexed representations |

## Platform Capabilities

| Capability | What It Enables | Snowflake Product | Partner Ecosystem |
| :---- | :---- | :---- | :---- |
| Data lakehouse | Unified storage for structured \+ unstructured; ACID transactions; time travel; schema evolution | Iceberg Tables, Snowflake Managed Iceberg | Databricks, Apache Iceberg |
| AI-native transformation | Embedding generation; feature computation; format conversion to AI-consumable representations | Cortex Embed, Snowpark ML, Dynamic Tables | LangChain, LlamaIndex, Tecton |
| Document processing | Chunking pipelines with configurable strategies; metadata extraction; provenance and versioning through transformation | Cortex Parse, Document AI | LangChain, LlamaIndex, Unstructured |
| Dual-layer storage | Columnar offline stores \+ row-oriented online stores; automated materialization between formats | Dynamic Tables, Hybrid Tables | Redis, DynamoDB, Cassandra |
| Vector infrastructure | Dense and sparse indexing; hybrid search with rank fusion; quantization; pre/post-filtering; multi-representation storage | Cortex Search, VECTOR data type | Pinecone, Weaviate, Milvus, Qdrant |
| Query materialization | Pre-computed results as data products; semantic caching; incremental refresh | Dynamic Tables, Materialized Views | Redis, Momento |
| Multi-modal storage | Single platform for structured data, documents, images, audio, video with unified governance | Unstructured data support, Directory Tables | \- |
| Serving APIs | REST \+ native connectors; access patterns optimized for AI consumption; Snowpark for programmatic access | Snowflake Connector, Snowpark, Hybrid Tables | \- |
| Agent data access | Query decomposition; parallel execution; context assembly from multiple sources | Cortex Analyst, Cortex Search | LangChain, LlamaIndex |

# Current

## Requirements

| Requirement | What | Why | Maturity | Use Cases | Target |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Event timestamps | Data carries timestamps indicating when it was captured or last updated; event time is distinct from processing time | Freshness cannot be calculated without knowing data age; event time is the source of truth for currency | Foundation | All AI workloads | All AI-serving data carries event timestamps |
| Declared freshness contracts | Data carries its freshness requirements as metadata—maximum acceptable age per workload, error budgets for tolerated staleness | Different workloads have different tolerances; contracts make requirements explicit and enforceable | Foundation | All AI workloads | All AI data products have declared freshness contracts |
| Staleness metadata | Data carries computed currency scores based on (time since last update) / (acceptable update frequency); enables corpus-wide staleness tracking | Different content types decay at different rates; staleness scores enable prioritized refresh and consumption decisions | Intermediate | RAG, knowledge bases, document search | All indexed corpora carry staleness scores |
| Point-in-time correctness | Feature values at inference match those available during training; online and offline stores maintain temporal parity | Training-serving skew causes silent model degradation; data leakage inflates training metrics | Intermediate | ML training, real-time inference | All ML features have validated point-in-time correctness |
| Continuous currency | Data is updated incrementally as changes occur, not in batches that create staleness windows | Batch windows create gaps where data is known-stale; incremental updates maintain continuous freshness | Intermediate | Streaming pipelines, RAG, feature stores | All AI-critical data sources support incremental updates |
| Staleness blocking | Stale data is blocked from consumption when freshness contracts are violated; the system refuses to serve data it cannot vouch for | If stale data can reach AI consumers, it will; enforcement prevents silent degradation | Advanced | Real-time ML, fraud detection, high-stakes decisions | Circuit breakers block stale data for all critical AI paths |

## Platform Capabilities

| Capability | What It Enables | Snowflake Product | Partner Ecosystem |
| :---- | :---- | :---- | :---- |
| Timestamp infrastructure | Event time capture distinct from processing time; watermarks for late data handling; time travel for point-in-time queries | Time Travel, METADATA$START\_SCAN\_TIME | Apache Kafka (event time), Flink (watermarks) |
| Freshness contract metadata | Declared freshness SLAs stored as metadata on data products; contract validation at consumption | Data Quality Monitoring (preview), Tags | Monte Carlo, Atlan |
| Streaming ingestion | Event streaming with ordering guarantees; millions of events/second | Snowpipe Streaming, Kafka Connector | Confluent, Apache Kafka, Amazon Kinesis |
| Stream processing | Low-latency transformations; exactly-once semantics; continuous updates | Dynamic Tables, Streams and Tasks | Apache Flink, Spark Structured Streaming |
| Change Data Capture | Log-based CDC with minimal source impact; SCD Type 2 for history; incremental propagation | Streams, Time Travel | Fivetran, Airbyte, Debezium |
| Feature store sync | Dual writes to offline \+ online stores; temporal parity between training and serving | Feature Store (preview), Dynamic Tables | Tecton, Feast |
| Staleness computation | Currency score calculation based on update frequency and age; corpus-wide staleness tracking | Dynamic Tables, UDFs | Custom implementation |
| Circuit breakers | Auto-block consumption when freshness contracts violated; closed/open/half-open states | Task error handling, Alerts | Monte Carlo, Great Expectations |
| Vector incremental updates | Continuous writes without blocking reads; add/update/delete without full reindex | Cortex Search incremental refresh | Pinecone, Weaviate |

# Observable

## Requirements

| Requirement | What | Why | Maturity | Use Cases | Target |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Data quality signals | Data carries computed quality metadata: completeness scores, freshness vs. SLA, volume relative to baseline, distribution profiles; quality signals are queryable and versioned | Quality issues cause silent degradation; signals must be on the data, not just in dashboards | Foundation | All AI workloads | All AI-serving data carries quality metadata |
| Drift baselines | Data has stored reference distributions for comparison; baseline snapshots are versioned and refreshed on known-good states | Drift detection requires a baseline; without stored references, shift detection is impossible | Foundation | ML models, RAG, recommendations | All production models have versioned baseline distributions |
| Decision traces | Every AI decision exists as a linked trace: inputs (prompts, context) → retrieved data (docs, scores) → intermediate steps → outputs (response, latency); traces are immutable and queryable | Problems surface weeks after root cause; without traces, debugging and audit are impossible | Foundation | All AI workloads | All production AI decisions have complete trace records |
| Data lineage | Data carries provenance showing origin, transformations, and dependencies; lineage enables temporal reconstruction of any past state | Impact analysis and root cause debugging require knowing what data flowed where | Foundation | All AI workloads | All AI-serving data has queryable lineage |
| Retrieval quality metadata | Retrieved chunks carry relevance scores, ranking signals, and match explanations; retrieval quality is logged per query | Retrieval degradation is invisible without per-query quality signals; metadata enables debugging | Intermediate | RAG, document search, chatbots | All RAG queries log retrieval quality metadata |
| Faithfulness signals | AI outputs carry verification metadata: claim support scores, source attribution, confidence indicators | Hallucinations erode trust; faithfulness must be measured and attached to outputs, not just sampled | Advanced | RAG, chatbots, content generation | All customer-facing AI outputs carry faithfulness metadata |

## Platform Capabilities

| Capability | What It Enables | Snowflake Product | Partner Ecosystem |
| :---- | :---- | :---- | :---- |
| Quality metadata computation | Automated profiling; quality scores computed and attached to data; versioned quality snapshots | Data Quality Monitoring (preview), Dynamic Tables | Great Expectations, dbt tests, Soda, Monte Carlo |
| Drift baseline storage | Reference distribution snapshots; versioned baselines; streaming and batch drift calculation | Snowpark ML (model monitoring), Time Travel | Evidently, NannyML, Arize |
| Retrieval quality logging | Per-query logging of relevance scores, ranking signals, match explanations; queryable retrieval history | Cortex Search logs, Query History | LangSmith, Weights & Biases |
| Faithfulness evaluation | LLM-as-judge; claim verification; faithfulness/relevance scoring attached to outputs | Cortex (evaluation functions) | TruLens, Weights & Biases, MLflow |
| Decision trace storage | OpenTelemetry-compatible tracing; immutable trace records; span correlation across LLM calls and tools | Query History, QUERY\_HISTORY view | Datadog, New Relic, Honeycomb, LangSmith |
| Data lineage capture | Automated lineage from SQL; column-level granularity; bi-temporal reconstruction; impact analysis | Horizon Lineage, ACCESS\_HISTORY | Monte Carlo, Atlan, Alation |

# Compliant

## Requirements

### Ownership & Access

| Requirement | What | Why | Maturity | Use Cases | Target |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Ownership metadata | Data carries its owner, steward, domain, and escalation path as queryable metadata attached to the asset | Ownership gaps create accountability vacuums; when AI produces unexpected results, the data must identify who owns the investigation | Foundation | All AI workloads | 100% of AI-serving data carries ownership metadata |
| Access classification | Data carries a sensitivity tier (public, internal, confidential, restricted) that determines which policies apply and what approvals are required | Classification drives policy; without explicit tiers on the data, access decisions are ad-hoc and inconsistent | Foundation | All AI workloads | All AI-serving data carries access classification |
| Permission boundaries | Data carries declared access scope specifying which roles, which AI systems, and for which purposes access is permitted | Implicit permissions create shadow access; declared boundaries on the data make access auditable and enforceable | Foundation | RAG, agents, ML pipelines | All sensitive data carries explicit permission boundaries |
| Identity attribution | Data access events carry the identity of the accessor (human or machine) with purpose context; access logs are immutable and queryable | Shared accounts obscure accountability; attributed access on the data enables audit and anomaly detection | Foundation | All AI workloads | All AI data access is identity-attributed |
| Delegation chain | Derived data carries inherited ownership and access obligations from source data; lineage determines the responsibility chain | Transformations don't eliminate accountability; derived data must inherit governance metadata from its sources | Intermediate | ML features, RAG indices, aggregations | All derived data carries inherited governance metadata |
| Access expiration | Data access grants carry time bounds, review triggers, and automatic revocation dates as metadata | Permanent grants accumulate risk; time-bound access on the data forces periodic revalidation | Intermediate | All AI workloads | All AI data access grants carry expiration metadata |

### Legal & Regulatory

| Requirement | What | Why | Maturity | Use Cases | Target |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Legal basis metadata | Data carries documented legal basis (consent, legitimate interest, contract), purpose limitations, and usage rights as queryable metadata | GDPR/CCPA require lawful basis; without metadata on the data, compliance cannot be verified at consumption | Foundation | All AI using personal data | All personal data carries legal basis metadata |
| Training data provenance | Training datasets carry documented sources, preprocessing steps, annotation methods, and statistical properties; provenance is immutable and auditable | EU AI Act requires documented, representative datasets; undocumented training data creates liability | Foundation | ML training, high-risk AI | All training datasets have complete provenance records |
| Erasure-ready identifiers | Data carries identifiers enabling targeted deletion; personal data can be located and removed across training sets, vector stores, and logs upon valid request | GDPR Article 17 applies to AI systems; erasure requires knowing where data lives | Intermediate | RAG, personalization, any system with PII | All personal data has erasure-ready identifiers |
| Decision reconstruction | Every AI decision links to the inputs, model version, and context that produced it; decisions can be fully reconstructed for any point in time | Regulators require explanation of automated decisions; reconstruction is how you prove what happened | Foundation | Credit scoring, hiring, fraud detection, content moderation | All high-impact decisions are reconstructable |
| Retention metadata | Data carries retention period, legal hold status, and expiration timestamps; retention is enforced automatically | Cannot retain indefinitely; EU AI Act requires 6+ months for high-risk AI logs; retention must be on the data | Foundation | All AI systems | All AI data has retention metadata with automated enforcement |

### Protection & Safety

| Requirement | What | Why | Maturity | Use Cases | Target |
| :---- | :---- | :---- | :---- | :---- | :---- |
| PII protection | Personal data is masked, tokenized, hashed, or anonymized before AI consumption; protection is applied at ingestion, not query time | Technical safeguards reduce breach impact; protection must be on the data, not just access controls | Foundation | All AI with personal data | All AI-serving data has PII protection applied |
| Bias assessment metadata | Data and models carry bias assessment results: error rates across demographic groups, mitigation measures applied, assessment timestamps | EU AI Act requires bias identification and mitigation; assessments must be documented and auditable | Advanced | High-risk AI, hiring, lending, content | All high-risk AI has bias assessment metadata |

## Platform Capabilities

### Ownership & Access Control

| Capability | What It Enables | Snowflake Product | Partner Ecosystem |
| :---- | :---- | :---- | :---- |
| Data ownership registry | Owner, steward, domain assignment on data assets; contact information; responsibility tracking | Horizon Catalog (ownership), Tags | Atlan, Alation, Collibra |
| Domain management | Bounded contexts for data products; cross-domain visibility with local autonomy | Databases/Schemas, Object Tagging | Atlan (data mesh), Collibra |
| Machine identity | Service accounts for AI workloads; OAuth for external systems; key-pair authentication | Service Users, OAuth, Key-Pair Auth | Okta, Azure AD |
| Role-based access control | Hierarchical roles; role grants; privilege inheritance; role activation | RBAC, Database Roles, Role Hierarchy | Privacera, Immuta |
| Fine-grained access | Row-level and column-level policies; conditional access based on context | Row Access Policies, Column Masking, Conditional Masking | Privacera, Immuta |
| Access governance workflows | Request, approval, and provisioning automation; time-bound access; periodic reviews | Access Requests (preview), Access History | Sailpoint, Saviynt, Veza |
| Ownership lineage | Ownership propagation through transformations; responsibility chain visualization | Horizon Lineage, Tags | Monte Carlo, Atlan |

### Legal & Regulatory Compliance

| Capability | What It Enables | Snowflake Product | Partner Ecosystem |
| :---- | :---- | :---- | :---- |
| Consent and legal basis tracking | Legal basis metadata stored with data; purpose limitation enforcement; consent status queryable at consumption | Tags, Row Access Policies | OneTrust, TrustArc, Collibra |
| Training data documentation | Provenance capture for training datasets; source, preprocessing, and annotation tracking; immutable audit records | Horizon Lineage, Dataset Versioning | Weights & Biases, MLflow, DVC |
| Erasure infrastructure | Personal data discovery across tables and vector stores; targeted deletion workflows; deletion verification | Object Dependencies, Cortex Search deletion | BigID, OneTrust |
| Decision reconstruction | Point-in-time snapshots; dataset \+ model \+ config linkage; immutable decision logs | Time Travel, Zero-Copy Cloning, Query History | MLflow, Weights & Biases |
| Retention enforcement | Retention metadata on data objects; automated expiration; legal hold support | Data Retention Policies, Time Travel | Collibra, Alation |

### Protection & Safety

| Capability | What It Enables | Snowflake Product | Partner Ecosystem |
| :---- | :---- | :---- | :---- |
| PII detection and protection | NER for 50+ PII types; masking, tokenization, and anonymization at ingestion; protection applied before AI consumption | Dynamic Data Masking, Classification | Presidio, Private AI, Nightfall |
| Bias assessment tracking | Fairness metrics stored with models; demographic error rate tracking; assessment versioning | Snowflake Model Registry | Weights & Biases, Fiddler, Arthur |

# 
