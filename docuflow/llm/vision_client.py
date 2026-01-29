"""
视觉模型客户端

支持使用 Azure OpenAI GPT-4 Vision 或其他视觉模型生成图片描述。
使用 LangChain 的 AzureChatOpenAI 实现。
"""
from typing import Optional

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage

from docuflow.core.config import get_azure_config, get_model_config, get_settings


class VisionClient:
    """视觉模型客户端，用于生成图片描述"""

    # 默认的图片描述提示词
    DEFAULT_PROMPT = """请详细描述这张图片的内容（500字以内）。
        如果是架构图、流程图、图表或界面截图，请描述：
        1. 图片的主要内容和目的
        2. 关键元素和它们之间的关系
        3. 任何可见的文字、标签或数值
        4. 设计模式、结构或流程的重要细节

        请用简洁、专业的中文描述，保留所有重要的技术细节。"""

    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.3,
                 timeout: int = 120, max_retries: int = 3):
        """
        初始化视觉模型客户端

        Args:
            model_name: 视觉模型名称（如 "gpt-5.2"），None 表示使用默认模型
            temperature: 生成温度
            timeout: 请求超时秒数
            max_retries: SDK 内部重试次数
        """
        config = get_azure_config()
        settings = get_settings()

        # 如果指定了模型，使用该模型的配置
        if model_name and model_name != settings.model_name:
            model_config = get_model_config(model_name)
            self.llm = AzureChatOpenAI(
                deployment_name=model_config["deployment"],
                api_key=config["api_key"],
                api_version=model_config["api_version"],
                azure_endpoint=model_config["endpoint"],
                temperature=temperature,
                timeout=timeout,
                max_retries=max_retries,
            )
        else:
            # 使用默认配置
            self.llm = AzureChatOpenAI(
                deployment_name=config["azure_deployment"],
                api_key=config["api_key"],
                api_version=config["api_version"],
                azure_endpoint=config["azure_endpoint"],
                temperature=temperature,
                timeout=timeout,
                max_retries=max_retries,
            )

        self.temperature = temperature

    def describe_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        max_tokens: int = 2000,
    ) -> str:
        """
        为图片生成描述

        Args:
            image_bytes: 图片二进制数据
            prompt: 自定义提示词（可选）
            max_tokens: 最大生成 token 数

        Returns:
            图片描述文本
        """
        import base64

        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        user_prompt = prompt or self.DEFAULT_PROMPT

        # 使用 LangChain 的 HumanMessage 构建包含图片和文本的消息
        message = HumanMessage(
            content=[
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        )

        # 调用 LangChain 的 invoke 方法
        response = self.llm.invoke(
            [message],
            max_completion_tokens=max_tokens,
        )

        # 安全地获取内容，处理可能的 None 响应
        if response and response.content:
            content = response.content
            # 打印调试信息
            print("图片描述生成成功。token数量：", len(content))
            return content

        # 如果响应为空，返回默认消息
        return "[图片描述生成失败：模型返回空响应]"

    def describe_images_batch(
        self,
        images: list[bytes],
        prompt: Optional[str] = None,
        show_progress: bool = False,
    ) -> list[str]:
        """
        批量生成图片描述

        Args:
            images: 图片二进制数据列表
            prompt: 自定义提示词（可选）
            show_progress: 是否显示进度
        Returns:
            图片描述列表
        """
        descriptions = []
        length = len(images)
        for i ,img in enumerate(images):
            if show_progress:
                print(f"正在处理图片 {i + 1}/{length}...")
            try:
                description=self.describe_image(img,prompt)
                descriptions.append(description)
            except Exception as e:
                print(f"图片 {i + 1} 描述生成失败: {e}")
                descriptions.append("[图片描述生成失败]")

        return descriptions


def create_vision_description_function(
    model_name: Optional[str] = None,
    prompt: Optional[str] = None,
    max_tokens: int = 2000,
):
    """
    创建图片描述函数，用于传递给 ImageExtractor

    Args:
        model_name: 视觉模型名称
        prompt: 自定义提示词
        max_tokens: 最大生成 token 数

    Returns:
        接受图片二进制数据，返回描述文本的函数
    """
    # 创建一个共享的客户端，避免每次调用都重新创建
    client = VisionClient(model_name=model_name)

    def describe_func(image_bytes: bytes) -> str:
        return client.describe_image(image_bytes, prompt=prompt, max_tokens=max_tokens)

    return describe_func
