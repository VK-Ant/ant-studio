"""Ant Studio Configuration."""
import os

class Settings:
    HOST: str = os.getenv("ANT_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("ANT_PORT", "8000"))
    DATA_DIR: str = os.getenv("ANT_DATA_DIR", "./data")
    OUTPUT_DIR: str = os.getenv("ANT_OUTPUT_DIR", "./output")
    TEMPLATES_DIR: str = os.getenv("ANT_TEMPLATES_DIR", "./templates")
    WORKFLOWS_DIR: str = os.getenv("ANT_WORKFLOWS_DIR", "./workflows")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    MAX_GPU_MEMORY_MB: float = float(os.getenv("ANT_MAX_GPU_MB", "6000"))
    LOG_LEVEL: str = os.getenv("ANT_LOG_LEVEL", "INFO")

settings = Settings()
