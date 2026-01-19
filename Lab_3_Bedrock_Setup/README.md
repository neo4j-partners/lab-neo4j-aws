# Lab 3 - Amazon Bedrock Setup

In this lab, you will set up Amazon Bedrock and verify access to the foundation models needed for the remaining labs. Amazon Bedrock is AWS's fully managed service for accessing foundation models from leading AI companies.

## Prerequisites

Before starting, make sure you have:
- Completed **Lab 0** (AWS sign-in)
- Completed **Lab 1** (Neo4j Aura setup with backup restored)
- Completed **Lab 2** (Aura Agents - to understand the agent patterns)

## What is Amazon Bedrock?

Amazon Bedrock provides:

- **Foundation Models** - Access to Claude (Anthropic), Titan (Amazon), Llama (Meta), and more
- **Playground** - Test models with prompts before building applications
- **Bedrock Agents** - Build AI agents that can use external tools
- **Knowledge Bases** - Connect agents to your data sources for RAG
- **Guardrails** - Content filtering and safety controls

In this lab, you'll:
- Navigate to Amazon Bedrock in the AWS Console
- Complete the one-time Anthropic use case form (required for Claude models)
- Test the models in the Bedrock Playground
- Understand the models you'll use in later labs

---

## How Model Access Works (Updated October 2025)

> **Important Change:** As of October 2025, Amazon Bedrock **automatically enables** all serverless foundation models by default. The previous "Model Access" page and manual enablement process have been retired.

### What This Means for You

| Provider | Access Status | Additional Requirement |
|----------|---------------|------------------------|
| **Amazon** (Titan) | Auto-enabled | None |
| **Meta** (Llama) | Auto-enabled | None |
| **Mistral AI** | Auto-enabled | None |
| **Anthropic** (Claude) | Auto-enabled | One-time use case form |

**Anthropic models require a one-time use case form submission** before first use. This form takes less than a minute to complete and grants immediate access.

### Access Control

Model access is now managed through standard AWS mechanisms:
- **IAM Policies** - Control which users/roles can invoke specific models
- **Service Control Policies (SCPs)** - Restrict model access at the organization level
- **AWS Marketplace** - Claude models are billed through AWS Marketplace

---

## Part 1: Complete the Anthropic Use Case Form

Before using Claude models, you need to submit a one-time use case form.

### Step 1: Navigate to Amazon Bedrock

1. Sign in to the [AWS Console](https://console.aws.amazon.com)
2. In the search bar, type **Bedrock** and select **Amazon Bedrock**

![Find Bedrock](images/find_bedrock.png)

3. You should see the Amazon Bedrock welcome page

![Bedrock Console](images/bedrock_console.png)

### Step 2: Access the Chat Playground

1. In the left sidebar, click **Playgrounds** under "Getting started"
2. Select **Chat playground**

![Playground Menu](images/playground_menu.png)

### Step 3: Select an Anthropic Model

1. In the playground, click **Select model**
2. Choose **Anthropic** as the provider
3. Select **Claude Sonnet 4.5** (or any Claude model)

![Select Playground Model](images/select_playground_model.png)

### Step 4: Complete the Use Case Form

If this is your first time using an Anthropic model in this account, you'll see a form requesting use case details.

Fill out the form with details relevant to this workshop's SEC filings analysis use case:

| Field | Suggested Value |
|-------|-----------------|
| **Use Case Description** | Building AI agents for SEC 10-K filings analysis - querying a Neo4j knowledge graph to analyze company risk factors, asset manager ownership patterns, and financial disclosures |
| **Industry** | Financial Services |
| **Expected Usage** | Select based on your workshop/testing needs (low volume is fine for this lab) |

1. Enter your **Use Case Description** (example above or similar)
2. Select **Financial Services** as the industry
3. Estimate your monthly token usage
4. Review and accept the **End User License Agreement (EULA)**
5. Click **Submit**

> **Note:** Access is granted immediately after submission. If using AWS Organizations, submitting from the management account grants access to all member accounts.

![Anthropic Form](images/anthropic_form.png)

### Step 5: Verify Access

After form submission, you should be able to use Claude in the playground immediately. If you see an error, wait a few seconds and try again.

---

## Part 2: Explore the Bedrock Playground

The Bedrock Playground lets you test models before building applications.

### Step 6: Test Claude

With Claude Sonnet 4.5 selected, try these prompts:

**Prompt 1: General knowledge**
```
What information is typically found in an SEC 10-K filing?
```

![Playground Test 1](images/playground_test_1.png)

**Prompt 2: Financial analysis**
```
What are common risk factors that technology companies disclose in their 10-K filings?
```

**Prompt 3: Cypher query (preview for later labs)**
```
Write a Cypher query to find all companies and their risk factors in a Neo4j graph database where companies have a HAS_RISK relationship to RiskFactor nodes.
```

### Step 7: Adjust Model Parameters (Optional)

Click the **Configuration** panel to adjust:

| Parameter | Description | Recommended |
|-----------|-------------|-------------|
| **Temperature** | Randomness (0=focused, 1=creative) | 0.3 for analysis |
| **Top P** | Nucleus sampling threshold | 0.9 |
| **Max tokens** | Maximum response length | 4096 |

![Model Configuration](images/model_configuration.png)

---

## Part 3: Verify Titan Embeddings Access

Amazon Titan models are auto-enabled with no additional requirements.

### Step 8: Test Titan Embeddings (Optional)

1. In the left sidebar, click **Playgrounds**
2. Select **Text playground**
3. Select **Amazon** as the provider
4. Choose **Titan Text Embeddings V2**
5. Enter a test phrase:

```
Apple Inc faces risks related to global supply chain disruptions
```

6. Click **Run**

You'll see a vector of 1024 floating-point numbers - this is how text is converted to embeddings for semantic search.

![Embeddings Test](images/embeddings_test.png)

---

## Part 4: Understand the Models

### Models You'll Use in This Workshop

| Model | Use Case | Context Window | Cost | Labs |
|-------|----------|----------------|------|------|
| **Claude Sonnet 4.5** | Agent reasoning, text generation, Cypher queries | 200K tokens (1M preview) | ~$3/M input tokens | 4, 8 |
| **Claude Haiku 4.5** | Fast, cost-effective responses | 200K tokens | ~$0.80/M input tokens | Alternative |
| **Titan Text Embeddings V2** | Vector embeddings (1024 dimensions) | N/A | ~$0.02/M tokens | 6-7 |

### Claude 4.5 Model Family

| Model | Best For | Performance |
|-------|----------|-------------|
| **Claude Opus 4.5** | Production code, complex agents | Highest capability |
| **Claude Sonnet 4.5** | Balanced performance, rapid iteration | Best cost/performance |
| **Claude Haiku 4.5** | Sub-agents, high-volume tasks | Fastest, lowest cost |

All Claude 4.5 models support:
- **Extended thinking** - Deeper reasoning for complex problems
- **1M token context** (preview) - Process very long documents
- **Hybrid reasoning** - Near-instant or extended thinking modes

### Titan Embeddings Best Practices

For the coding labs, you'll use Titan Text Embeddings V2 with these settings:

- **Dimensions**: 1024 (optimized for performance)
- **Normalize**: true (for cosine similarity)
- **Document segmentation**: 512 tokens recommended

---

## Troubleshooting

### "Access Denied" Error for Claude Models

If you see an access error when trying to use Claude:

1. **Verify form completion**: Ensure you completed the Anthropic use case form
2. **Check IAM permissions**: Your role needs `bedrock:InvokeModel` permission
3. **Check AWS Marketplace permissions**: For first-time account setup, you may need:
   - `aws-marketplace:Subscribe`
   - `aws-marketplace:ViewSubscriptions`
4. **Wait and retry**: Access propagation can take a few minutes

### IAM Policy for Bedrock Access

If you need to create an IAM policy for Bedrock access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "*"
        },
        {
            "Sid": "MarketplaceAccess",
            "Effect": "Allow",
            "Action": [
                "aws-marketplace:ViewSubscriptions",
                "aws-marketplace:Subscribe"
            ],
            "Resource": "*"
        }
    ]
}
```

Or use the AWS managed policy: `AmazonBedrockFullAccess`

---

## Summary

You have now set up Amazon Bedrock with:
- **Anthropic use case form** completed for Claude access
- **Playground experience** testing Claude's capabilities
- **Understanding** of the models you'll use in later labs

## Model Access Checklist

Before proceeding, verify you can use:

- [ ] Claude Sonnet 4.5 (or Claude Haiku 4.5)
- [ ] Titan Text Embeddings V2

## What's Next

Continue to [Lab 4 - AI Agent Builder](../Lab_4_GAAB_Agents/) to create an AI agent that can query your Neo4j knowledge graph using the pre-deployed MCP server.

---

## References

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/)
- [Amazon Bedrock Model Access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
- [Simplified Model Access (AWS Blog)](https://aws.amazon.com/blogs/security/simplified-amazon-bedrock-model-access/)
- [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Claude on Amazon Bedrock](https://aws.amazon.com/bedrock/anthropic/)
- [Titan Embeddings Best Practices](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)
