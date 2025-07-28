import os
import re
import logging

from google import genai
from google.genai import types


from returns.result import Result, Success, Failure

from core.enum import error
from core.enum import model
from client.interface import provider_interface
from client.google.schema import GeminiResponseSchema

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class GoogleClient(provider_interface.AIClientInterface):
    """
    Google Client for interacting with the Google GenAI API.
    """

    def __init__(self):
        self.client = genai.Client()
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.chat = self.client.chats.create(
            model=self.model,
            config={
                "system_instruction": "以繁體中文回答問題，語氣保持專業與嚴謹\n請僅提供 JSON 物件，嚴格遵循所提供的結構描述，不包含任何額外文字或格式。",
                "max_output_tokens": int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", 5000)),
                "top_k": float(os.getenv("GEMINI_TOP_K", 2.0)),
                "top_p": float(os.getenv("GEMINI_TOP_P", 0.5)),
                "temperature": float(os.getenv("GEMINI_TEMPERATURE", 0.5)),
                "stop_sequences": os.getenv("GEMINI_STOP_SEQUENCES", "\n").split(","),
                "seed": int(os.getenv("GEMINI_SEED", 1)),
                # "response_mime_type": "application/json",
                # "response_schema": GeminiResponseSchema,
            },
        )

    def generate_content(self, prompt: str) -> Result[str, error.ClientError]:
        """
        Generate content based on the provided prompt.
        """
        response: types.GenerateContentResponse = self.client.models.generate_content(
            model=self.model,
            config=self.config,
            prompt=prompt,
        )
        schemaResponse: GeminiResponseSchema = response.parsed
        # TODO: improve handle multiple candidates
        finish_reason: types.FinishReason = response.candidates[0].finish_reason
        client_error: error.ClientError | None = self.__handle_finish_reason(
            finish_reason
        )
        if client_error is None:
            return Success(schemaResponse.result)
        else:
            return Failure(client_error)

    def send_message(self, message: str) -> Result[str, error.ClientError]:
        """
        Send a message to the AI provider.
        """
        response: types.GenerateContentResponse = self.chat.send_message(
            message=message,
            config={
                "response_mime_type": "application/json",
                "response_schema": GeminiResponseSchema,
            },
        )
        schemaResponse: GeminiResponseSchema | None = response.parsed

        # 沒有解析到 schemaResponse，則使用原始文本
        result = None
        if schemaResponse is None:
            result = response.text
        else:
            result = schemaResponse.result

        # TODO: improve handle multiple candidates
        finish_reason: types.FinishReason = response.candidates[0].finish_reason
        client_error: error.ClientError | None = self.__handle_finish_reason(
            finish_reason
        )
        if client_error is None:
            return Success(result)
        else:
            return Failure(client_error)

    def __is_valid_response_reason(self, reason: types.FinishReason) -> bool:
        return reason in [
            types.FinishReason.STOP,
        ]

    def __handle_finish_reason(
        self, reason: types.FinishReason
    ) -> error.ClientError | None:
        """
        Handle the finish reason from the response.
        """
        if self.__is_valid_response_reason(reason):
            return None
        else:
            logging.error(f"Unexpected finish reason: {reason}")
            return error.ClientError.UNKNOWN
