import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=True)


class Settings:
    def __init__(self) -> None:
        # Application
        self.APP_NAME = "CloudConform"
        self.APP_VERSION = "0.1.0"
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
        self.ALLOWED_ORIGINS = [
            origin.strip() for origin in os.getenv(
                "ALLOWED_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
            ).split(",") if origin.strip()
        ]

        # Database and cache
        self.DATABASE_URL = self._required("DATABASE_URL")
        self.REDIS_URL = self._required("REDIS_URL")

        # Authentication
        self.JWT_SECRET_KEY = self._required("JWT_SECRET_KEY")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "1"))

        # Grounded, read-only security agent
        self.SECURITY_AGENT_MODE = os.getenv("SECURITY_AGENT_MODE", "preview").lower()
        self.BEDROCK_MODEL_ID = os.getenv(
            "BEDROCK_MODEL_ID",
            "us.amazon.nova-pro-v1:0",
        )
        self.SECURITY_AGENT_DEMO_DAILY_LIMIT = int(
            os.getenv("SECURITY_AGENT_DEMO_DAILY_LIMIT", "3")
        )
        self.SECURITY_AGENT_GLOBAL_DAILY_LIMIT = int(
            os.getenv("SECURITY_AGENT_GLOBAL_DAILY_LIMIT", "30")
        )

        if len(self.JWT_SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters.")

        if self.SECURITY_AGENT_MODE not in {"preview", "strands"}:
            raise ValueError("SECURITY_AGENT_MODE must be 'preview' or 'strands'.")

        if self.SECURITY_AGENT_DEMO_DAILY_LIMIT < 0:
            raise ValueError("SECURITY_AGENT_DEMO_DAILY_LIMIT must be non-negative.")

        if self.SECURITY_AGENT_GLOBAL_DAILY_LIMIT < 0:
            raise ValueError("SECURITY_AGENT_GLOBAL_DAILY_LIMIT must be non-negative.")

        # Azure credentials
        self.AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")
        self.AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
        self.AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
        self.AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
        self.AZURE_DISCOVERY_ENABLED = (
            os.getenv("AZURE_DISCOVERY_ENABLED", "false").lower() == "true"
        )

        # Google Cloud configuration
        self.GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
        self.GCP_DISCOVERY_ENABLED = (
            os.getenv("GCP_DISCOVERY_ENABLED", "false").lower() == "true"
        )

        # AWS credentials
        self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN", "")
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
        self.AWS_DISCOVERY_ENABLED = (
            os.getenv("AWS_DISCOVERY_ENABLED", "false").lower() == "true"
        )

    @staticmethod
    def _required(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"{name} is missing from the .env file.")
        return value


settings = Settings()
