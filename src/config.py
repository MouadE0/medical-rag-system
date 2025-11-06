from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", 
        env="OPENAI_EMBEDDING_MODEL"
    )
    openai_embedding_dimensions: int = Field(default=1536)
    
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    cocoa_pdf_path: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "data" / "CoCoA.pdf"
    )
    chroma_persist_dir: str = Field(
        default="./data/chroma_db", 
        env="CHROMA_PERSIST_DIR"
    )
    
    chunk_size: int = 600
    chunk_overlap: int = 100
    top_k_retrieval: int = 10
    top_k_rerank: int = 5
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3

    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()