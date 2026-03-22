# GPT-5.4-nano as a Replacement for GPT-4o in Entity Extraction

The `SimpleKGPipeline` that builds this project's knowledge graph from SEC 10-K filings currently runs on GPT-4o. The GPT-5.4 model family, released on March 17, 2026, offers smaller models that cost significantly less, accept longer inputs, produce longer outputs, and carry nearly two years of additional training data. GPT-5.4-nano in particular is positioned by OpenAI for exactly this kind of workload: classification, entity extraction, and structured output at high throughput [1][4].

The case for switching is primarily economic and practical. Reasoning capability is a secondary benefit that helps at the margins, not the headline argument.

## Cost

The pricing difference is the strongest reason to move off GPT-4o.

| Model | Input (per M tokens) | Cached Input (per M tokens) | Output (per M tokens) |
|---|---|---|---|
| GPT-4o (global standard) | $2.50 | — | $10.00 |
| GPT-4o-mini | $0.15 | — | $0.60 |
| GPT-5.4-mini | $0.75 | $0.075 | $4.50 |
| GPT-5.4-nano | $0.20 | $0.02 | $1.25 |

GPT-5.4-nano costs 92% less on input and 87.5% less on output compared to GPT-4o global standard [4][5]. GPT-5.4-mini sits in between at 70% and 55% reductions respectively.

Both GPT-5.4 models support cached input pricing. This matters for the pipeline: when processing multiple chunks from the same filing, the system prompt and schema definition are identical across calls. Cached input at $0.02/M tokens (nano) or $0.075/M tokens (mini) reduces the effective per-filing cost substantially beyond the headline rate.

## Context Window and Output Ceiling

| Feature | GPT-4o | GPT-5.4-mini | GPT-5.4-nano |
|---|---|---|---|
| Context window (input) | 128K tokens | 272K tokens | 272K tokens |
| Max output tokens | 16K | 128K | 128K |
| Training data cutoff | October 2023 | August 2025 | August 2025 |

GPT-4o's 16K output ceiling constrains how many entities and relationships can be extracted per call. When the pipeline processes a dense chunk full of companies, executives, financial metrics, and risk factors, 16K tokens of structured JSON output fills up quickly. GPT-5.4-nano's 128K output limit removes that constraint entirely [3].

The 272K input window also provides headroom. SEC 10-K filings routinely exceed 100 pages. While the pipeline processes filings in chunks rather than whole documents, the larger window allows for bigger chunks with more surrounding context, which improves extraction quality without requiring architectural changes.

## Training Data Recency

GPT-4o's training data cuts off at October 2023. GPT-5.4-nano's extends to August 2025 [3]. For entity extraction from SEC filings, this means the model has seen nearly two additional years of financial documents, regulatory language, and corporate terminology. It will handle current company names, recently adopted accounting standards, and evolving disclosure patterns more reliably than GPT-4o without needing few-shot examples to compensate.

## Structured Output and Function Calling

Both GPT-4o and GPT-5.4-nano support structured outputs and function calling, so the `SimpleKGPipeline` requires no interface changes. The schema definition for `Company`, `Executive`, `FinancialMetric`, `RiskFactor`, `Product`, and `AssetManager` node types works identically across models [3][4].

## Where Reasoning Fits (and Where It Doesn't)

GPT-5.4-nano and GPT-5.4-mini are reasoning models with adjustable thinking levels: minimal, low, medium, and high [6]. This is an architectural difference from GPT-4o, which has no reasoning mechanism.

Entity extraction is primarily pattern recognition with structured output. Identifying "John Smith, CEO" as an `Executive` entity, or "$4.2 billion" as a `FinancialMetric`, does not require chain-of-thought reasoning. A well-prompted model with a good schema handles these cases through instruction following, and GPT-4o does this adequately. Spending thinking tokens on straightforward extraction adds latency and cost with marginal benefit.

Where reasoning provides a genuine edge is relationship classification: deciding whether a company mentioned in a passage is a customer, competitor, subsidiary, or partner. SEC filings reference the same entity in different roles across sections, and relationship type assignment is closer to reading comprehension than pattern matching. Reasoning can also help with coreference resolution across passages and reconciling conflicting entity attributes (an executive whose role changed mid-filing period).

These harder cases represent a minority of total extraction work. The practical impact of reasoning on overall extraction quality is incremental, not transformational. Setting the thinking level to low minimizes the overhead for the majority of straightforward extraction while preserving some reasoning capacity for ambiguous cases.

One constraint worth noting: parallel tool calls are not supported at the minimal reasoning level. Since the pipeline uses function calling for structured output, the minimum usable thinking level is low [6].

## Benchmark Context

| Benchmark | GPT-5.4-mini | GPT-5.4 (full) | GPT-5-mini |
|---|---|---|---|
| SWE-Bench Pro (coding) | 54.4% | 57.7% | 45.7% |
| GPQA Diamond (reasoning) | 88.0% | 93.0% | 81.6% |
| OSWorld Verified (tool use) | 72.1% | 75.0% | 42.0% |
| Toolathlon (function calling) | 42.9% | 54.6% | 26.9% |

These benchmarks measure coding, graduate-level reasoning, and agentic tool use [1][2]. None directly measure entity extraction quality. They confirm that GPT-5.4-mini is a capable model that approaches its full-size sibling, but they don't predict how well it identifies `RiskFactor` nodes from SEC prose. Published nano benchmarks are not yet available on the same suite. Extraction quality should be validated empirically against a sample of filings before committing to either model.

## Recommendation

**Start with GPT-5.4-nano.** The cost savings are dramatic, the context window and output ceiling are substantially larger, the training data is nearly two years newer, and OpenAI positions the model specifically for entity extraction workloads. Set thinking level to low to keep reasoning overhead minimal while preserving function calling support.

**Validate before committing.** Process a representative sample of filings (3-4 covering different company sizes and industries) and compare extracted entities and relationships against GPT-4o output. The likely outcome is that nano handles the vast majority of extraction correctly, with possible degradation on complex relationship classification in dense passages.

**Fall back to GPT-5.4-mini if needed.** If nano's extraction quality drops below acceptable thresholds on relationship types or entity disambiguation, GPT-5.4-mini provides deeper reasoning at $0.75/$4.50 per M tokens — still 55-70% cheaper than GPT-4o. Mini's 88% GPQA Diamond score reflects genuine reasoning capability that can help with the harder classification cases, though for most extraction work the difference will be marginal.

## References

1. [OpenAI: Introducing GPT-5.4 mini and nano](https://openai.com/index/introducing-gpt-5-4-mini-and-nano/)
2. [The Decoder: OpenAI ships GPT-5.4 mini and nano, faster and more capable but up to 4x pricier](https://the-decoder.com/openai-ships-gpt-5-4-mini-and-nano-faster-and-more-capable-but-up-to-4x-pricier/)
3. [Microsoft: Azure OpenAI model availability — GPT-5.4](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure#gpt-54)
4. [Microsoft Tech Community: Introducing OpenAI's GPT-5.4 mini and GPT-5.4 nano for low-latency AI](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/introducing-openai%E2%80%99s-gpt-5-4-mini-and-gpt-5-4-nano-for-low-latency-ai/4500569)
5. [Azure OpenAI Service Pricing](https://azure.microsoft.com/en-us/pricing/details/azure-openai/)
6. [Microsoft: GPT-5 vs GPT-4.1 model choice guide](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/model-choice-guide)
