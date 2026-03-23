from __future__ import annotations

"""
Shared configuration and utilities for workshop solutions.

This module provides common functionality for Neo4j connections,
LLM/embedder initialization, and configuration management.
Uses AWS Bedrock for LLM and embedding services.
"""

import json
from contextlib import contextmanager
from pathlib import Path

import boto3
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import BedrockNovaEmbeddings
from neo4j_graphrag.llm import BedrockLLM
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from financial_data_load directory
_root_env = Path(__file__).parent.parent / ".env"
load_dotenv(_root_env)


class Neo4jConfig(BaseSettings):
    """Neo4j configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    uri: str = Field(validation_alias="NEO4J_URI")
    username: str = Field(validation_alias="NEO4J_USERNAME")
    password: str = Field(validation_alias="NEO4J_PASSWORD")


class BedrockConfig(BaseSettings):
    """AWS Bedrock configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-6",
        validation_alias="MODEL_ID",
    )
    region: str = Field(default="us-east-1", validation_alias="AWS_REGION")
    embedding_dimensions: int = Field(
        default=1024, validation_alias="EMBEDDING_DIMENSIONS"
    )


@contextmanager
def get_neo4j_driver():
    """Context manager for Neo4j driver connection."""
    config = Neo4jConfig()
    driver = GraphDatabase.driver(
        config.uri,
        auth=(config.username, config.password),
    )
    try:
        yield driver
    finally:
        driver.close()


def get_embedder() -> BedrockNovaEmbeddings:
    """Get embedder using AWS Bedrock Nova Multimodal Embeddings.

    Returns a BedrockNovaEmbeddings object for use with neo4j-graphrag retrievers.
    For raw float arrays (e.g., for Cypher queries), use get_embedding() instead.
    """
    config = BedrockConfig()

    return BedrockNovaEmbeddings(
        region_name=config.region,
        embedding_dimension=config.embedding_dimensions,
    )


def get_llm() -> BedrockLLM:
    """Get LLM using AWS Bedrock."""
    config = BedrockConfig()

    return BedrockLLM(
        model_id=config.model_id,
        region_name=config.region,
    )


class _NovaEmbedding(BaseModel):
    embedding: list[float]


class _NovaEmbeddingResponse(BaseModel):
    embeddings: list[_NovaEmbedding]


_bedrock_client = None


def get_embedding(text: str) -> list[float]:
    """Generate an embedding vector for text using Bedrock Nova.

    Returns the raw float array for use in Cypher vector search queries.
    Unlike get_embedder(), this returns floats directly rather than a
    BedrockNovaEmbeddings object.
    """
    global _bedrock_client
    config = BedrockConfig()
    if _bedrock_client is None:
        _bedrock_client = boto3.client(
            "bedrock-runtime", region_name=config.region
        )
    request_body = {
        "taskType": "SINGLE_EMBEDDING",
        "singleEmbeddingParams": {
            "embeddingPurpose": "GENERIC_INDEX",
            "embeddingDimension": config.embedding_dimensions,
            "text": {
                "truncationMode": "END",
                "value": text,
            },
        },
    }
    response = _bedrock_client.invoke_model(
        modelId="amazon.nova-2-multimodal-embeddings-v1:0",
        body=json.dumps(request_body),
    )
    result = json.loads(response["body"].read())
    parsed = _NovaEmbeddingResponse.model_validate(result)
    return parsed.embeddings[0].embedding
