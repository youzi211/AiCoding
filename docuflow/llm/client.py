"""
Azure OpenAI 客户端

完全基于 LangChain 框架的 LLM 客户端，仅支持 Azure OpenAI。
支持结构化输出（Structured Outputs）功能。
带有全局并发控制（Semaphore）、请求超时和 LangChain 速率限制。

已完全迁移到 LangChain：
- 使用 AzureChatOpenAI.invoke() 进行文本生成
- 使用 .with_structured_output() 进行结构化输出
- 统一错误处理和速率限制
"""
import threading
from typing import Optional, TypeVar, Type

from pydantic import BaseModel
from langchain_openai import AzureChatOpenAI
from langchain_core.rate_limiters import InMemoryRateLimiter

from docuflow.core.config import get_azure_config, get_model_config, get_settings
from docuflow.utils import get_logger

T = TypeVar('T', bound=BaseModel)

logger = get_logger()

# 全局并发信号量 —— 限制同时进行的 LLM API 请求数
# 防止多用户/多任务同时打满 Azure 的 RPM/TPM 配额
_semaphore: Optional[threading.Semaphore] = None
_semaphore_lock = threading.Lock()


def _get_semaphore(max_concurrent: int = 3) -> threading.Semaphore:
    """获取或创建全局信号量（线程安全的懒初始化）"""
    global _semaphore
    if _semaphore is None:
        with _semaphore_lock:
            if _semaphore is None:
                _semaphore = threading.Semaphore(max_concurrent)
    return _semaphore


def reset_semaphore(max_concurrent: int = 3) -> None:
    """重置信号量（用于配置变更时）"""
    global _semaphore
    with _semaphore_lock:
        _semaphore = threading.Semaphore(max_concurrent)


class AzureOpenAIClient:
    """Azure OpenAI LLM 客户端（带超时、并发控制和速率限制）

    完全基于 LangChain 实现：
    - 使用 LangChain AzureChatOpenAI 客户端处理所有请求
    - generate() 使用 invoke() 进行文本生成
    - generate_structured() 使用 with_structured_output() 进行结构化输出
    - 全局 Semaphore 并发控制（限制同时进行的请求数）
    - LangChain InMemoryRateLimiter 速率限制（限制每秒请求数）
    """

    def __init__(
        self,
        temperature: float = 0.3,
        model_name: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
        max_concurrent: int = 3,
        rate_limiter: Optional[InMemoryRateLimiter] = None,
    ):
        """
        初始化客户端

        Args:
            temperature: 生成温度
            model_name: 指定模型名称（可选，默认使用配置中的主模型）
            timeout: 请求超时秒数（默认120秒）
            max_retries: SDK 内部重试次数（默认3次，处理429等瞬态错误）
            max_concurrent: 最大并发请求数（全局共享信号量）
            rate_limiter: 可选的自定义速率限制器，未指定时根据配置自动创建
        """
        config = get_azure_config()
        settings = get_settings()

        # 创建或使用传入的速率限制器
        if rate_limiter is None and settings.llm_rate_limit_enabled:
            rate_limiter = InMemoryRateLimiter(
                requests_per_second=settings.llm_rate_limit_requests_per_second,
                check_every_n_seconds=settings.llm_rate_limit_check_every_n_seconds,
                max_bucket_size=settings.llm_rate_limit_max_bucket_size,
            )
            logger.debug(
                f"已启用速率限制: {settings.llm_rate_limit_requests_per_second} req/s, "
                f"max_bucket={settings.llm_rate_limit_max_bucket_size}"
            )

        # 如果指定了不同的模型，使用该模型的配置
        if model_name and model_name != settings.model_name:
            model_config = get_model_config(model_name)
            # LangChain 客户端（用于所有 LLM 调用）
            self.llm = AzureChatOpenAI(
                deployment_name=model_config["deployment"],
                api_key=config["api_key"],
                api_version=model_config["api_version"],
                azure_endpoint=model_config["endpoint"],
                temperature=temperature,
                timeout=timeout,
                max_retries=max_retries,
                rate_limiter=rate_limiter,
            )
            self.deployment = model_config["deployment"]
        else:
            # LangChain 客户端（用于所有 LLM 调用）
            self.llm = AzureChatOpenAI(
                deployment_name=config["azure_deployment"],
                api_key=config["api_key"],
                api_version=config["api_version"],
                azure_endpoint=config["azure_endpoint"],
                temperature=temperature,
                timeout=timeout,
                max_retries=max_retries,
                rate_limiter=rate_limiter,
            )
            self.deployment = config["azure_deployment"]

        self.temperature = temperature
        self._semaphore = _get_semaphore(max_concurrent)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """生成 LLM 响应（文本），带并发控制

        使用 LangChain 的 invoke() 方法进行文本生成。
        """
        # 构建消息
        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("human", prompt))

        # 通过信号量控制并发，防止超出 Azure 速率限制
        self._semaphore.acquire()
        try:
            logger.debug(f"LLM 请求开始 (deployment={self.deployment})")
            # 使用 LangChain 的 invoke 方法
            response = self.llm.invoke(messages)
            # 安全地获取内容
            if response and response.content:
                return response.content
            return ""
        except Exception as e:
            self._handle_api_error(e)
        finally:
            self._semaphore.release()

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
    ) -> T:
        """
        生成结构化输出（使用 LangChain 的 with_structured_output），带并发控制

        Args:
            prompt: 用户提示词
            response_model: Pydantic 模型类
            system_prompt: 系统提示词（可选）

        Returns:
            符合 response_model 的实例
        """
        # 通过信号量控制并发
        self._semaphore.acquire()
        try:
            logger.debug(f"LLM 结构化请求开始 (deployment={self.deployment}, model={response_model.__name__})")

            # 使用 LangChain 的 with_structured_output 自动处理结构化输出
            structured_llm = self.llm.with_structured_output(response_model)

            # 构建消息
            messages = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("human", prompt))

            # 调用 LangChain，自动返回 Pydantic 实例
            result = structured_llm.invoke(messages)
            return result
        except Exception as e:
            self._handle_api_error(e)
        finally:
            self._semaphore.release()

    def _handle_api_error(self, e: Exception) -> None:
        """统一处理 API 错误，转换为 LLMGenerationError

        支持 OpenAI 原生异常和 LangChain 异常处理。
        """
        from docuflow.llm import LLMGenerationError
        from openai import RateLimitError, APITimeoutError, APIConnectionError

        if isinstance(e, RateLimitError):
            logger.warning(f"Azure API 速率限制: {e}")
            raise LLMGenerationError(
                f"Azure API 速率限制，请稍后重试: {e}", retryable=True
            ) from e
        elif isinstance(e, APITimeoutError):
            logger.warning(f"Azure API 请求超时: {e}")
            raise LLMGenerationError(
                f"LLM 请求超时: {e}", retryable=True
            ) from e
        elif isinstance(e, APIConnectionError):
            logger.warning(f"Azure API 连接错误: {e}")
            raise LLMGenerationError(
                f"LLM 连接失败: {e}", retryable=True
            ) from e
        elif isinstance(e, LLMGenerationError):
            raise
        else:
            # LangChain 可能会包装异常，尝试提取原始 OpenAI 异常
            if hasattr(e, '__cause__') and e.__cause__:
                # 递归处理原始异常
                self._handle_api_error(e.__cause__)
            else:
                logger.error(f"LLM 调用未知错误: {e}")
                raise LLMGenerationError(
                    f"LLM 调用失败: {e}", retryable=False
                ) from e
