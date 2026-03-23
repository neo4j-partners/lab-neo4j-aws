"""AWS Bedrock Nova embedding provider using neo4j-graphrag."""

from __future__ import annotations


def create_embedder():
    """Create a BedrockNovaEmbeddings instance via neo4j-graphrag.

    Reads AWS_REGION and EMBEDDING_DIMENSIONS from .env via AgentConfig.
    AWS credentials are resolved by the default boto3 credential chain.
    """
    from neo4j_graphrag.embeddings import BedrockNovaEmbeddings

    from ..config import AgentConfig

    config = AgentConfig()

    kwargs: dict = {}
    if config.aws_region:
        kwargs["region_name"] = config.aws_region
    if config.embedding_dimensions:
        kwargs["embedding_dimension"] = config.embedding_dimensions
    return BedrockNovaEmbeddings(**kwargs)
