import openai
from typing import Dict
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type


class LLMClient:
    """
    Wrapper for a single LLM endpoint (OpenAI, AzureOpenAI, etc.)
    """

    def __init__(self, config: Dict):
        self.client = openai.OpenAI(
            base_url=config["api_base"],
            api_key=config["api_key"],
            timeout=config["timeout"],
            max_retries=config["max_retries"],
        )
        self.name = config["name"]
        self.model_name = config["model_name"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(
            (
                openai.APITimeoutError,
                openai.APIConnectionError,
                openai.RateLimitError,
                openai.InternalServerError,
            )
        ),
    )
    def chat_completion(self, messages, temperature=0.7) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content
