"""
Azure OpenAI 客户端

简化的 LLM 客户端，仅支持 Azure OpenAI。
支持结构化输出（Structured Outputs）功能。
"""
import json
from typing import Optional, TypeVar, Type

from pydantic import BaseModel

from docuflow.core.config import get_azure_config, get_model_config, get_settings

T = TypeVar('T', bound=BaseModel)


class AzureOpenAIClient:
    """Azure OpenAI LLM 客户端"""

    def __init__(self, temperature: float = 0.3, model_name: Optional[str] = None):
        """
        初始化客户端

        Args:
            temperature: 生成温度
            model_name: 指定模型名称（可选，默认使用配置中的主模型）
        """
        from openai import AzureOpenAI

        config = get_azure_config()
        settings = get_settings()

        # 如果指定了不同的模型，使用该模型的配置
        if model_name and model_name != settings.model_name:
            model_config = get_model_config(model_name)
            self.client = AzureOpenAI(
                api_key=config["api_key"],
                api_version=model_config["api_version"],
                azure_endpoint=model_config["endpoint"]
            )
            self.deployment = model_config["deployment"]
        else:
            self.client = AzureOpenAI(
                api_key=config["api_key"],
                api_version=config["api_version"],
                azure_endpoint=config["azure_endpoint"]
            )
            self.deployment = config["azure_deployment"]

        self.temperature = temperature

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """生成 LLM 响应（文本）"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message.content

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
    ) -> T:
        """
        生成结构化输出（使用 Azure OpenAI Structured Outputs）

        Args:
            prompt: 用户提示词
            response_model: Pydantic 模型类
            system_prompt: 系统提示词（可选）

        Returns:
            符合 response_model 的实例
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=self.temperature,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__.lower(),
                    "strict": True,
                    "schema": response_model.model_json_schema()
                }
            }
        )

        data = json.loads(response.choices[0].message.content)
        return response_model.model_validate(data)
