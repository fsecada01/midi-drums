# Multi-Model Routing Configuration

This document defines the model routing strategy for cost-optimized agentic workflows in the MIDI Drums Generator AI system.

## Model Tier Definitions

### Tier 1: Fast
**Purpose**: Simple classification, validation, quick decisions

| Provider | Model | Tokens/min | Cost/1M tokens |
|----------|-------|------------|----------------|
| Anthropic | claude-3-5-haiku-20241022 | ~100K | $0.25 in / $1.25 out |
| OpenAI | gpt-4o-mini | ~150K | $0.15 in / $0.60 out |
| Groq | llama-3.1-8b-instant | ~300K | $0.05 in / $0.08 out |
| Cohere | command-light | ~100K | $0.30 in / $0.60 out |

**Configuration**:
```python
FAST_CONFIG = {
    "max_tokens": 256,
    "temperature": 0.3,
    "timeout": 5.0,
}
```

**Use Cases**:
- Intent classification
- Parameter validation
- Genre/style validation
- Yes/no decisions
- Simple extractions

### Tier 2: Balanced
**Purpose**: Standard generation tasks, pattern analysis

| Provider | Model | Tokens/min | Cost/1M tokens |
|----------|-------|------------|----------------|
| Anthropic | claude-sonnet-4-20250514 | ~80K | $3.00 in / $15.00 out |
| OpenAI | gpt-4o | ~30K | $2.50 in / $10.00 out |
| Groq | llama-3.3-70b-versatile | ~100K | $0.59 in / $0.79 out |
| Cohere | command-r | ~50K | $0.50 in / $1.50 out |

**Configuration**:
```python
BALANCED_CONFIG = {
    "max_tokens": 1024,
    "temperature": 0.7,
    "timeout": 30.0,
}
```

**Use Cases**:
- Pattern characteristic analysis
- Single pattern generation
- Template selection
- Drummer style mapping
- Modification suggestions

### Tier 3: Advanced
**Purpose**: Complex composition, multi-step reasoning

| Provider | Model | Tokens/min | Cost/1M tokens |
|----------|-------|------------|----------------|
| Anthropic | claude-sonnet-4-20250514 | ~80K | $3.00 in / $15.00 out |
| OpenAI | gpt-4o | ~30K | $2.50 in / $10.00 out |
| Groq | llama-3.3-70b-versatile | ~100K | $0.59 in / $0.79 out |
| Cohere | command-r-plus | ~30K | $2.50 in / $10.00 out |

**Configuration**:
```python
ADVANCED_CONFIG = {
    "max_tokens": 2048,
    "temperature": 0.8,
    "timeout": 60.0,
}
```

**Use Cases**:
- Multi-section song composition
- Pattern variation generation
- Style blending decisions
- Complex fill sequences
- Creative suggestions

### Tier 4: Expert
**Purpose**: Complex analysis, specialized tasks

| Provider | Model | Tokens/min | Cost/1M tokens |
|----------|-------|------------|----------------|
| Anthropic | claude-opus-4-5-20251101 | ~15K | $15.00 in / $75.00 out |
| OpenAI | gpt-4o | ~30K | $2.50 in / $10.00 out |
| Groq | llama-3.3-70b-versatile | ~100K | $0.59 in / $0.79 out |
| Cohere | command-r-plus | ~30K | $2.50 in / $10.00 out |

**Configuration**:
```python
EXPERT_CONFIG = {
    "max_tokens": 4096,
    "temperature": 0.7,
    "timeout": 120.0,
}
```

**Use Cases**:
- Audio file analysis
- Pattern evolution algorithms
- Multi-genre style blending
- Complex polyrhythm generation
- Musical theory application

## Workflow Patterns

### Pattern 1: Single-Shot Generation
```
User Request
    │
    ▼
┌─────────────────┐
│ Fast: Classify  │  (5-10 tokens, ~$0.000001)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Balanced: Gen   │  (500-800 tokens, ~$0.005)
└────────┬────────┘
         │
         ▼
    Pattern Output

Total cost: ~$0.005 per pattern
```

### Pattern 2: Song Composition
```
User Request
    │
    ▼
┌─────────────────┐
│ Fast: Classify  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Advanced: Plan  │  (800-1200 tokens)
└────────┬────────┘
         │
    ┌────┴────┬────────┐
    ▼         ▼        ▼
┌────────┐ ┌────────┐ ┌────────┐
│Balanced│ │Balanced│ │Balanced│  (parallel section gen)
│Section1│ │Section2│ │Section3│
└────┬───┘ └────┬───┘ └────┬───┘
     │         │         │
     └────┬────┴────┬────┘
          ▼
┌─────────────────┐
│Advanced: Combine│
└────────┬────────┘
          ▼
     Song Output

Total cost: ~$0.03-0.05 per song
```

### Pattern 3: Audio Analysis
```
Audio File
    │
    ▼
┌─────────────────┐
│ Expert: Analyze │  (1500-2500 tokens)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Balanced: Gen   │  (generate matching patterns)
└────────┬────────┘
         │
         ▼
    Pattern(s) Output

Total cost: ~$0.15-0.25 per analysis
```

### Pattern 4: Iterative Refinement
```
User Request
    │
    ▼
┌─────────────────┐
│ Balanced: Init  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Fast: Validate  │  (check constraints)
└────────┬────────┘
         │
    ┌────┴────┐
    │ Pass?   │
    │ Yes  No │
    │    │    │
    ▼    └────┼───┐
Pattern       │   │
              ▼   │
┌─────────────────┐
│ Balanced: Fix   │
└────────┬────────┘
         │
         └──────────▶ (loop max 3x)

Total cost: ~$0.01-0.02 per pattern
```

## Cost Optimization Strategies

### 1. Cascade Classification
Always start with fast tier for intent classification before routing to more expensive models.

**Savings**: 50-80% on simple requests that can be handled by fast tier alone.

### 2. Response Caching
Cache common analysis results:
- Pattern characteristic analyses
- Genre/style templates
- Drummer modification mappings

**Implementation**:
```python
CACHE_CONFIG = {
    "pattern_analysis": {"ttl": 3600, "max_size": 1000},
    "template_selection": {"ttl": 86400, "max_size": 500},
    "modification_map": {"ttl": 86400, "max_size": 100},
}
```

**Savings**: 30-50% on repeated similar requests.

### 3. Batch Processing
Group multiple pattern requests into single API call when possible.

**Savings**: 20-30% on token overhead.

### 4. Token Budgeting
Strict max_tokens per task prevents runaway costs:

| Task Type | Max Tokens | Typical Usage |
|-----------|------------|---------------|
| Classification | 256 | 50-100 |
| Pattern gen | 1024 | 400-600 |
| Song comp | 2048 | 1200-1600 |
| Analysis | 4096 | 2000-3000 |

### 5. Provider Fallbacks
Define fallback chains for reliability and cost:

```python
FALLBACK_CHAINS = {
    "anthropic": ["groq", "openai"],  # Groq is cheaper fallback
    "openai": ["anthropic", "groq"],
    "groq": ["openai", "anthropic"],  # Fallback to paid if Groq fails
    "cohere": ["openai", "anthropic"],
}
```

### 6. Time-of-Day Routing
Route to cheaper providers during off-peak hours if latency is acceptable.

## Monitoring and Alerts

### Metrics to Track
- Cost per request (by tier)
- Token usage (input/output)
- Latency percentiles (p50, p95, p99)
- Cache hit rate
- Fallback frequency

### Alert Thresholds
- Cost per request > $0.10: Warning
- Cost per request > $0.50: Critical
- Latency p95 > 30s: Warning
- Fallback rate > 10%: Warning
- Cache hit rate < 20%: Review caching strategy

## Environment Variables

```bash
# Provider selection
AI_PROVIDER=anthropic

# Model overrides (optional)
AI_MODEL_FAST=claude-3-5-haiku-20241022
AI_MODEL_BALANCED=claude-sonnet-4-20250514
AI_MODEL_ADVANCED=claude-sonnet-4-20250514
AI_MODEL_EXPERT=claude-opus-4-5-20251101

# Tier overrides (optional)
AI_DEFAULT_TIER=balanced
AI_MAX_TIER=advanced  # Cap at advanced, never use expert

# Cost controls
AI_MAX_COST_PER_REQUEST=0.10
AI_MONTHLY_BUDGET=100.00

# Caching
AI_CACHE_ENABLED=true
AI_CACHE_TTL=3600

# Timeouts
AI_TIMEOUT_FAST=5
AI_TIMEOUT_BALANCED=30
AI_TIMEOUT_ADVANCED=60
AI_TIMEOUT_EXPERT=120
```

## Best Practices

1. **Start small**: Use fast tier classification before escalating
2. **Cache aggressively**: Common analyses don't need re-computation
3. **Parallel when possible**: Section generation can run concurrently
4. **Set budgets**: Per-request and monthly limits prevent surprises
5. **Monitor costs**: Track and alert on unusual patterns
6. **Test fallbacks**: Ensure graceful degradation works
7. **Review regularly**: Adjust routing based on actual usage patterns
