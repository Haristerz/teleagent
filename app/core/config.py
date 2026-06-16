from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # AWS
    aws_region: str
    claude_model: str
    embedding_model: str

    # Database (create later)
    db_host: str
    db_name: str
    db_user: str
    db_password: str
    db_port: int = 5432

    # Bedrock Guardrails
    bedrock_guardrail_id: str
    bedrock_guardrail_version: str
    
    # Langfuse (observability)
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_base_url: str

    # Email
    gmail_user: str
    gmail_password: str

    class Config:
        env_file = ".env"
        extra="ignore"  # ← ignore extra fields

settings = Settings()