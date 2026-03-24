from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "LawFi"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://lawfi:lawfi@localhost:5433/lawfi"

    # Auth
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "rulings"

    # Anthropic (Claude)
    anthropic_api_key: str = ""

    # Google Cloud
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"
    gcs_bucket: str = ""

    # Cloudflare R2
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "lawfi-pdfs"
    r2_endpoint: str = ""

    # Vertex AI Embedding
    embedding_model: str = "text-multilingual-embedding-002"
    embedding_dimension: int = 768

    # Search
    search_results_limit: int = 20
    semantic_search_weight: float = 0.6
    keyword_search_weight: float = 0.4

    # Subscription limits
    free_daily_searches: int = 10
    pro_daily_searches: int = -1  # unlimited
    enterprise_daily_searches: int = -1  # unlimited

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
