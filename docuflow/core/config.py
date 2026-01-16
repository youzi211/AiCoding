"""
配置管理

支持多模型配置和项目管理，按 项目/模型 分目录存储。
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from docuflow.core.models import AppConfig

load_dotenv()


# 支持的模型配置
MODEL_CONFIGS = {
    "gpt-5.2": {
        "prefix": "GPT5.2",
        "env_endpoint": "GPT5.2_AZURE_OPENAI_ENDPOINT",
        "env_deployment": "GPT5.2_AZURE_OPENAI_DEPLOYMENT",
        "env_api_version": "GPT5.2_AZURE_OPENAI_API_VERSION",
    },
    "gpt-5.1": {
        "prefix": "GPT5.1",
        "env_endpoint": "GPT5.1_AZURE_OPENAI_ENDPOINT",
        "env_deployment": "GPT5.1_AZURE_OPENAI_DEPLOYMENT",
        "env_api_version": "GPT5.1_AZURE_OPENAI_API_VERSION",
    },
    "deepseek-v3.2": {
        "prefix": "DeepSeek-V3.2",
        "env_endpoint": "DeepSeek-V3.2_AZURE_OPENAI_ENDPOINT",
        "env_deployment": "DeepSeek-V3.2_AZURE_OPENAI_DEPLOYMENT",
        "env_api_version": "DeepSeek-V3.2_AZURE_OPENAI_API_VERSION",
    },
}


class Settings(BaseSettings):
    """基于环境变量的配置"""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix='DOCUFLOW_',
        extra='ignore'
    )

    # Azure OpenAI 配置
    azure_openai_api_key: Optional[str] = None

    # 默认模型
    model_name: str = "gpt-5.2"

    # LLM 配置
    llm_temperature: float = 0.3

    # 处理配置
    chunk_size: int = 2000
    chunk_overlap: int = 200
    max_retries: int = 3
    step_by_step: bool = False

    # 检索配置
    retrieval_method: str = "keyword"
    top_k_chunks: int = 5


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的设置实例"""
    return Settings()


def get_available_models() -> list[str]:
    """获取所有可用模型"""
    return list(MODEL_CONFIGS.keys())


def get_model_config(model_name: str) -> dict:
    """根据模型名称获取对应的配置"""
    if model_name not in MODEL_CONFIGS:
        raise ValueError(
            f"不支持的模型: {model_name}。支持的模型: {', '.join(MODEL_CONFIGS.keys())}"
        )

    cfg = MODEL_CONFIGS[model_name]
    return {
        "prefix": cfg["prefix"],
        "endpoint": os.getenv(cfg["env_endpoint"]),
        "deployment": os.getenv(cfg["env_deployment"]),
        "api_version": os.getenv(cfg["env_api_version"]),
    }


def create_app_config(
    project_root: Path,
    project_name: str = "default",
    model_name: Optional[str] = None
) -> AppConfig:
    """
    创建 AppConfig

    目录结构:
        data/
        ├── input/                    # 输入文档（共享）
        └── {project_name}/
            └── {model_name}/
                ├── workspace/
                │   ├── 01_global/
                │   └── 02_modules/
                └── output/

    Args:
        project_root: 项目根目录
        project_name: 项目名称（用于区分不同文档）
        model_name: 模型名称（用于区分不同模型的输出）
    """
    settings = get_settings()
    model = model_name or settings.model_name

    # 构建目录路径
    data_dir = project_root / "data"
    input_dir = data_dir / "input" / project_name  # 按项目分输入
    project_model_dir = data_dir / project_name / model

    return AppConfig(
        project_root=project_root,
        input_dir=input_dir,
        workspace_dir=project_model_dir / "workspace",
        output_dir=project_model_dir / "output",
        llm_temperature=settings.llm_temperature,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        max_retries=settings.max_retries,
        step_by_step_mode=settings.step_by_step,
        retrieval_method=settings.retrieval_method,
        top_k_chunks=settings.top_k_chunks,
    )


def get_azure_config() -> dict:
    """获取 Azure OpenAI 配置"""
    settings = get_settings()
    api_key = settings.azure_openai_api_key
    
    if not api_key:
        raise ValueError(
            "未配置 Azure OpenAI API 密钥。"
            "请设置 DOCUFLOW_AZURE_OPENAI_API_KEY 环境变量。"
        )
    
    # 获取选择的模型配置
    model_config = get_model_config(settings.model_name)
    
    if not model_config["endpoint"]:
        raise ValueError(f"未配置 {model_config['prefix']}_AZURE_OPENAI_ENDPOINT")
    if not model_config["deployment"]:
        raise ValueError(f"未配置 {model_config['prefix']}_AZURE_OPENAI_DEPLOYMENT")
    if not model_config["api_version"]:
        raise ValueError(f"未配置 {model_config['prefix']}_AZURE_OPENAI_API_VERSION")

    return {
        "api_key": api_key,
        "azure_endpoint": model_config["endpoint"],
        "azure_deployment": model_config["deployment"],
        "api_version": model_config["api_version"],
        "model_name": settings.model_name,
    }