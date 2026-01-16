"""
Azure OpenAI 客户端

简化的 LLM 客户端，仅支持 Azure OpenAI。
"""
from typing import Optional

from docuflow.core.config import get_azure_config


class AzureOpenAIClient:
    """Azure OpenAI LLM 客户端"""

    def __init__(self, temperature: float = 0.3):
        from openai import AzureOpenAI

        config = get_azure_config()
        self.client = AzureOpenAI(
            api_key=config["api_key"],
            api_version=config["api_version"],
            azure_endpoint=config["azure_endpoint"]
        )
        self.deployment = config["azure_deployment"]
        self.temperature = temperature

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """生成 LLM 响应"""
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
