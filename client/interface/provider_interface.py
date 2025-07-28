from enum import Enum
from typing import Protocol
from returns.result import Result

from core.enum import error


class AIClientInterface(Protocol):
    def generate_content(self, prompt: str) -> Result[str, error.ClientError]:
        """
        Method to generate content from the AI provider.
        """
        ...

    def send_message(self, message: str) -> Result[str, error.ClientError]:
        """
        Method to send a message to the AI provider.
        """
        ...
