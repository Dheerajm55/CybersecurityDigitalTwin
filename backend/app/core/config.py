"""
Central application configuration.

All values are read from environment variables (see /.env.example).
Nothing here should ever contain a real secret — defaults are safe
placeholders for local development only.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core ---
    ENVIRONMENT: str = "development"
    APP_NAME: str = "CDT2"

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./cyber_twin.db"

    # --- Neo4j (optional — Phase 2 graph mirror; NetworkX is the default engine) ---
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = ""

    # --- Auth ---
    JWT_SECRET: str = "dev-only-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- LLM / RAG (Phase 7-8, unused until configured) ---
    LLM_PROVIDER: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Threat intelligence (Phase 6) ---
    MITRE_DATA_PATH: str = "./data/threat_intelligence/mitre_attack.json"
    NVD_API_KEY: str = ""

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173"

    # --- Demo data ---
    SEED_DEMO_DATA: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
