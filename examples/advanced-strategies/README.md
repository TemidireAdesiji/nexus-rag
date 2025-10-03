# Advanced Retrieval Strategies

NexusRAG supports four retrieval strategies, each with different trade-offs between latency, recall, and accuracy. This guide compares them with example queries and provides guidance on when to use each.

---

## Strategy Overview

| Strategy     | LLM Calls Before Retrieval | Retrieval Passes | Typical Latency | Best For                          |
|------------- |---------------------------|------------------|-----------------|-----------------------------------|
| vector       | 0                         | 1                | ~1-2s           | Direct factual questions          |
| combined     | 0                         | 2 (vector + BM25)| ~2-3s          | Terminology-specific queries      |
| expanded     | 1 (query expansion)       | 3+               | ~4-6s           | Short or vague queries            |
| decomposed   | 1 (query decomposition)   | N (per sub-query)| ~6-10s          | Multi-part comparative questions  |

---

## Strategy 1: Vector Search

Vector search embeds the query and performs approximate nearest-neighbor search against the vector store. It is the fastest strategy and works well when the query is semantically close to the stored content.

### Example

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What programming languages does the team specialize in?",
    "strategy": "vector"
  }'
```

### When to Use

- The query is a clear, self-contained question.
- The expected answer exists in the corpus in similar wording.
- Latency is the primary concern.

### When to Avoid

- The query uses technical jargon that may not appear verbatim in the documents.
- The query is very short (one or two words) and semantically ambiguous.

---

## Strategy 2: Combined Search

Combined search runs both vector search and keyword-based BM25 search, then merges results using reciprocal rank fusion (RRF). This captures both semantic similarity and exact keyword matches.

### Example

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ISO 27001 compliance audit results for Q3",
    "strategy": "combined"
  }'
```

This query contains specific terminology ("ISO 27001", "Q3") that BM25 excels at matching, combined with semantic meaning that vector search handles well.

### When to Use

- The query contains specific names, codes, dates, or acronyms.
- You want robust retrieval without extra latency from LLM calls.
- The corpus contains structured or semi-structured content.

### When to Avoid

- The corpus is small (under 100 chunks) -- BM25 adds little value.
- All queries are conversational with no specific terminology.

### Tuning

Adjust the fusion weights via `BM25_WEIGHT`:

```bash
# Give more weight to keyword matching (useful for technical corpora)
BM25_WEIGHT=0.5

# Give more weight to semantic matching (default)
BM25_WEIGHT=0.3
```

---

## Strategy 3: Expanded Search

Expanded search uses the LLM to generate alternative phrasings of the query before retrieval. Each expanded query is searched independently, and the results are deduplicated and merged.

### Example

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cloud stuff",
    "strategy": "expanded"
  }'
```

For this vague query, the LLM might generate expansions like:

- "What cloud computing services and platforms does the team work with?"
- "Cloud infrastructure capabilities including AWS, Azure, and GCP"
- "Cloud migration, deployment, and managed services expertise"

Each expansion retrieves chunks that the original two-word query would have missed.

### When to Use

- The user query is short, vague, or colloquial.
- You want to maximize recall and are willing to accept higher latency.
- The corpus covers a topic broadly and the user may not know the right terminology.

### When to Avoid

- The query is already specific and well-formed.
- Latency budget is under 3 seconds.

### Tuning

```bash
# Number of expanded queries to generate (default: 3)
QUERY_EXPANSION_COUNT=5

# More expansions = broader recall but higher latency and cost
```

---

## Strategy 4: Decomposed Search

Decomposed search uses the LLM to break a complex query into independent sub-questions, retrieves context for each, then synthesizes a unified answer that addresses all parts.

### Example

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare the teams experience in healthcare versus financial services, including project count, technologies used, and key outcomes.",
    "strategy": "decomposed"
  }'
```

The LLM decomposes this into sub-questions:

1. "How many projects has the team completed in the healthcare vertical?"
2. "What technologies were used in healthcare projects?"
3. "What were the key outcomes of healthcare engagements?"
4. "How many projects has the team completed in the financial services vertical?"
5. "What technologies were used in financial services projects?"
6. "What were the key outcomes of financial services engagements?"

Each sub-question retrieves its own context. The final generation step receives all retrieved chunks organized by sub-question, enabling a structured comparative answer.

### When to Use

- The query asks for a comparison between two or more topics.
- The query has multiple distinct parts that each require different evidence.
- Thoroughness matters more than speed.

### When to Avoid

- The query is simple and single-faceted.
- Latency budget is under 5 seconds.
- Cost is a concern (this strategy uses the most LLM tokens).

---

## Side-by-Side Comparison

The following query is sent to all four strategies to illustrate the differences:

**Query:** "What experience does the team have with machine learning?"

### Vector

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -d '{"query": "What experience does the team have with machine learning?", "strategy": "vector"}'
```

- Retrieves chunks containing "machine learning" and semantically similar phrases.
- Fast response (~1.5s).
- May miss chunks that discuss ML under different terminology (e.g., "predictive modeling", "neural networks").

### Combined

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -d '{"query": "What experience does the team have with machine learning?", "strategy": "combined"}'
```

- Retrieves via both semantic and keyword search.
- Catches chunks with the exact phrase "machine learning" even if semantically distant.
- Moderate response time (~2.5s).

### Expanded

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -d '{"query": "What experience does the team have with machine learning?", "strategy": "expanded"}'
```

- Generates expansions like "deep learning experience", "AI and ML project history", "data science capabilities".
- Retrieves chunks that the original query missed.
- Higher response time (~5s).

### Decomposed

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -d '{"query": "What experience does the team have with machine learning?", "strategy": "decomposed"}'
```

- Decomposes into sub-questions: "What ML projects has the team completed?", "What ML frameworks does the team use?", "What outcomes were achieved with ML?"
- Produces the most comprehensive answer.
- Highest response time (~8s).

---

## Choosing a Default Strategy

Set the platform default via `DEFAULT_SEARCH_MODE`:

```bash
# For general-purpose use
DEFAULT_SEARCH_MODE=combined

# For applications where users type natural questions
DEFAULT_SEARCH_MODE=vector

# For research-oriented applications where thoroughness matters
DEFAULT_SEARCH_MODE=expanded
```

Individual requests can always override the default by specifying `"strategy"` in the request body.

---

## Monitoring Strategy Performance

Check the Gateway logs (with `LOG_LEVEL=debug`) to see per-strategy timing:

```
DEBUG retrieval.vector: query_embedding_ms=12 search_ms=45 chunks=10
DEBUG retrieval.combined: vector_ms=45 bm25_ms=30 fusion_ms=5 chunks=10
DEBUG retrieval.expanded: expansion_ms=800 searches=3 total_chunks=25 dedup_chunks=15
DEBUG retrieval.decomposed: decomposition_ms=900 sub_questions=4 total_chunks=32 dedup_chunks=20
```

Use these timings to decide which strategy fits your latency budget.
