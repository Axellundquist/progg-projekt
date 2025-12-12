from pydantic import BaseModel, BaseSettings, Field


class Settings(BaseSettings):
    api_key: str = Field(..., env="API_KEY")
    basic_auth_user: str | None = Field(None, env="BASIC_AUTH_USER")
    basic_auth_password: str | None = Field(None, env="BASIC_AUTH_PASSWORD")
    upload_max_mb: int = Field(50, env="UPLOAD_MAX_MB")
    video_process_timeout: int = Field(120, env="VIDEO_PROCESS_TIMEOUT")
    static_cache_seconds: int = Field(31536000, env="STATIC_CACHE_SECONDS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()


class VideoAnalysisResult(BaseModel):
    filename: str
    duration_seconds: float
    labels: list[str]
