import os
from pydantic import BaseModel


class Settings(BaseModel):
    project_name: str = "NurseShift API"
    version: str = "0.1.0-beta"
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "nurseshift-local")
    firestore_emulator_host: str = os.getenv("FIRESTORE_EMULATOR_HOST", "localhost:8080")
    auto_seed: bool = os.getenv("AUTO_SEED", "true").lower() in ("true", "1", "yes")
    auth_dev_mode: bool = os.getenv("AUTH_DEV_MODE", "true").lower() in ("true", "1", "yes")
    azure_tenant_id: str = os.getenv("AZURE_TENANT_ID", "hospital-tenant-id")
    azure_client_id: str = os.getenv("AZURE_CLIENT_ID", "hospital-client-id")
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY", "nurseshift-dev-secret-key-change-in-prod"
    )
    jwt_algorithm: str = "HS256"


settings = Settings()
