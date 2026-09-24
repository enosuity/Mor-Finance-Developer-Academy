from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str 
    cors_origins: List[str] = ["http://localhost:5173", "https://mor-finance-developer-academy.onrender.com" , "https://morfinance.ai"]
    mongodb_uri: str
    secret_key: str
    jwt_algorithm: str

    github_client_id: str 
    github_client_secret: str 
    github_redirect_uri: str 

    default_llm: str = "openclaw" 
    claude_api_key: str = ""
    hermes_api_url: str = "http://localhost:11434/v1"
    hermes_model: str = "hermes-3-llama-3.1-8b"
    mentor_api_url: str = "https://frontend-v2-eta-red.vercel.app/api/agents/mentors/ask"
    mentor_bearer_token: str = "60d6b55053548bd64ce97ebaba3ae09b5574f744655b3a44ef254158eda41899"
    web3_career_api_key: str = "X9q3WrJhceDrdb3oYt2xXeF8Aukh1YsZ"
    web3_career_token: str = "X9q3WrJhceDrdb3oYt2xXeF8Aukh1YsZ"

    # ─── Leaderboard (testnet activity submissions) ───────────────────────────
    chains: List[str] = ["sepolia", "base-sepolia", "arbitrum-sepolia", "optimism-sepolia"]
    verify_onchain: bool = False
    rpc_url_sepolia: str = ""
    rpc_url_base_sepolia: str = ""
    rpc_url_arbitrum_sepolia: str = ""
    rpc_url_optimism_sepolia: str = ""

    # ─── Payment callback (sandbox/test-mode only) ────────────────────────────
    payment_countries: List[str] = ["NG", "KE", "TZ", "BW", "ZA", "GH", "RW"]
    allow_mock_payment_callback: bool = False

    # ─── Job aggregator (alternate to the live-fetch /api/jobs; see /api/jobs-aggregated) ────
    user_agent: str = "mor-finance-academy/1.0"
    cryptojobslist_rss_url: str = "https://api.cryptojobslist.com/jobs.rss"
    web3_career_url: str = "https://web3.career/api/v1"
    web3_career_tags: List[str] = ["intern", "entry-level"]
    job_ttl_days: int = 30
    aggregate_every_minutes: int = 30
    cron_secret: str = ""


settings = Settings()
