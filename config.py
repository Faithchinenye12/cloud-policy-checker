import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=True)


class Settings:
    def __init__(self) -> None:
        # Application
        self.APP_NAME = "Cloud Policy Checker"
        self.APP_VERSION = "0.1.0"
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"

        # Database and cache
        self.DATABASE_URL = self._required("DATABASE_URL")
        self.REDIS_URL = self._required("REDIS_URL")

        # Authentication
        self.JWT_SECRET_KEY = self._required("JWT_SECRET_KEY")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "1"))

        if len(self.JWT_SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters.")

        # Azure credentials
        self.AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")
        self.AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
        self.AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
        self.AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")

        # AWS credentials
        self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    @staticmethod
    def _required(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"{name} is missing from the .env file.")
        return value


settings = Settings()