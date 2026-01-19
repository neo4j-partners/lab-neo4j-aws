"""
Shared configuration and utilities for workshop solutions.

This module provides common functionality for Neo4j connections,
AWS Bedrock integration, and configuration management.
"""

import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import BedrockEmbeddings
from neo4j_graphrag.llm import BedrockLLM
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from new-workshops/ directory
_root_env = Path(__file__).parent.parent / ".env"
load_dotenv(_root_env)


class Neo4jConfig(BaseSettings):
    """Neo4j configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    uri: str = Field(validation_alias="NEO4J_URI")
    username: str = Field(validation_alias="NEO4J_USERNAME")
    password: str = Field(validation_alias="NEO4J_PASSWORD")


class AWSConfig(BaseSettings):
    """AWS Bedrock configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    region: str = Field(default="us-east-1", validation_alias="AWS_REGION")
    bedrock_model_id: str = Field(
        default="anthropic.claude-3-5-sonnet-20241022-v2:0",
        validation_alias="AWS_BEDROCK_MODEL_ID",
    )
    bedrock_embedding_model_id: str = Field(
        default="amazon.titan-embed-text-v2:0",
        validation_alias="AWS_BEDROCK_EMBEDDING_MODEL_ID",
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


def get_aws_config() -> AWSConfig:
    """Get AWS configuration from environment."""
    return AWSConfig()


def get_embedder() -> BedrockEmbeddings:
    """
    Get embedder using AWS Bedrock.

    Uses boto3's default credential chain (env vars, ~/.aws/credentials, IAM role, etc.)
    Returns BedrockEmbeddings configured for Amazon Titan Text Embeddings V2.
    """
    config = get_aws_config()

    return BedrockEmbeddings(
        model_id=config.bedrock_embedding_model_id,
        region_name=config.region,
    )


def get_llm() -> BedrockLLM:
    """
    Get LLM using AWS Bedrock.

    Uses boto3's default credential chain (env vars, ~/.aws/credentials, IAM role, etc.)
    Returns BedrockLLM configured for Claude via the Converse API.
    """
    config = get_aws_config()

    return BedrockLLM(
        model_id=config.bedrock_model_id,
        region_name=config.region,
    )
