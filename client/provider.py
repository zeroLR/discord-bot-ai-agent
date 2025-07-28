from typing import Protocol, Generic, TypeVar, Optional

from core.enum import model
from client.interface import provider_interface
from client.google.GoogleClient import GoogleClient


class AIProvider:
    """
    Factory class for AI provider clients.
    Usage:
        client = AIProviderClient.factory(ModelProvider.GOOGLE)
    """

    @classmethod
    def get_client(
        cls, provider: model.Provider
    ) -> Optional[provider_interface.AIClientInterface]:
        match provider:
            case model.Provider.GOOGLE:
                return GoogleClient()
            case model.Provider.OPENAI:
                print("OpenAI client is not implemented yet.")
                return None
            case model.Provider.AZURE:
                print("Azure client is not implemented yet.")
                return None
            case model.Provider.ANTHROPIC:
                print("Anthropic client is not implemented yet.")
                return None
