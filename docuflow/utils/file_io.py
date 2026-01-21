"""文件操作工具"""
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional, Type, TypeVar

import yaml
from pydantic import BaseModel

from docuflow.utils.logging import get_logger

T = TypeVar('T', bound=BaseModel)


def safe_read_text(file_path: Path, default: str = "") -> str:
    """安全读取文本文件"""
    try:
        if file_path.exists():
            return file_path.read_text(encoding='utf-8')
        return default
    except Exception as e:
        get_logger().warning(f"读取失败 {file_path}: {e}")
        return default


def safe_write_text(file_path: Path, content: str) -> bool:
    """安全写入文本文件（原子操作）"""
    temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(content, encoding='utf-8')
        temp_path.replace(file_path)
        return True
    except Exception as e:
        get_logger().error(f"写入失败 {file_path}: {e}")
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        return False


def safe_read_yaml(file_path: Path, model_class: Type[T]) -> Optional[T]:
    """安全读取 YAML 文件为 Pydantic 模型"""
    try:
        if not file_path.exists():
            return None
        content = file_path.read_text(encoding='utf-8')
        data = yaml.safe_load(content)
        if data is None:
            return None
        return model_class.model_validate(data)
    except Exception as e:
        get_logger().error(f"解析 YAML 失败 {file_path}: {e}")
        return None


def safe_write_yaml(file_path: Path, model: BaseModel) -> bool:
    """安全写入 Pydantic 模型为 YAML"""
    try:
        data = model.model_dump(mode='json')
        content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return safe_write_text(file_path, content)
    except Exception as e:
        get_logger().error(f"写入 YAML 失败 {file_path}: {e}")
        return False


def safe_read_json(file_path: Path, model_class: Type[T]) -> Optional[T]:
    """安全读取 JSON 文件为 Pydantic 模型"""
    try:
        if not file_path.exists():
            return None
        content = file_path.read_text(encoding='utf-8')
        data = json.loads(content)
        return model_class.model_validate(data)
    except Exception as e:
        get_logger().error(f"解析 JSON 失败 {file_path}: {e}")
        return None


def safe_write_json(file_path: Path, model: BaseModel, indent: int = 2) -> bool:
    """安全写入 Pydantic 模型为 JSON"""
    try:
        content = model.model_dump_json(indent=indent)
        return safe_write_text(file_path, content)
    except Exception as e:
        get_logger().error(f"写入 JSON 失败 {file_path}: {e}")
        return False


def ensure_directory_structure(config: 'AppConfig') -> bool:
    """创建项目目录结构"""
    directories = [
        config.input_dir,                    # 使用配置的路径
        config.workspace_dir / "01_global",
        config.workspace_dir / "02_modules",
        config.workspace_dir / "03_output",
        config.workspace_dir / "04_critique_logs",  # 批判日志目录
        config.output_dir,
    ]
    try:
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        get_logger().error(f"创建目录失败: {e}")
        return False


def get_input_files(input_dir: Path) -> list[Path]:
    """获取输入目录中支持的文件"""
    supported_extensions = {'.pdf', '.docx', '.doc', '.md', '.markdown', '.txt'}
    files = []
    if input_dir.exists():
        for file_path in input_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files.append(file_path)
    return sorted(files)


def sanitize_module_name(name: str) -> str:
    """将模块名称转换为安全的文件名"""
    name = unicodedata.normalize('NFKC', name)
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    name = name.strip('_')
    return name or "unnamed_module"


def module_name_to_filename(name: str) -> str:
    """将模块名称转换为 Markdown 文件名"""
    return f"module_{sanitize_module_name(name)}.md"


def get_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
