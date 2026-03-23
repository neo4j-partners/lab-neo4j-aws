"""AWS Bedrock embedding provider using neo4j-graphrag BedrockEmbeddings."""

from __future__ import annotations


def create_embedder():
    """Create a Bedrock embedder via neo4j-graphrag.

    Uses Amazon Titan Text Embeddings V2 by default (1024 dimensions).
    Reads AWS_REGION and EMBEDDING_MODEL_ID from .env via AgentConfig.
    AWS credentials are resolved by the default boto3 credential chain.
    """
    from neo4j_graphrag.embeddings import BedrockEmbeddings

    from ..config import AgentConfig

    config = AgentConfig()

    kwargs: dict = {}

    if config.aws_region:
        kwargs["region_name"] = config.aws_region

    if config.embedding_model_id:
        kwargs["model_id"] = config.embedding_model_id

    return BedrockEmbeddings(**kwargs)
