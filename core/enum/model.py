import enum


class Gemini(enum.Enum):
    GEMINI_25_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_25_FLASH = "gemini-2.5-flash"
    GEMINI_25_PRO = "gemini-2.5-pro"


class Provider(enum.Enum):
    """
    Enum for model providers.
    """

    GOOGLE = "google"
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"

    def __str__(self):
        return self.value
