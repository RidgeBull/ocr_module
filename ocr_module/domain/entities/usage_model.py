from dataclasses import dataclass

@dataclass
class TranslationUsageStatsConfig:
    """TranslationUsageStatsConfig entity
    Args:
        model_name (str): Model name used for translation
        version (str): Version of the model used for translation
        api_endpoint (str): API endpoint used for translation
        billed_character_count (int): Billed character count used for translation
        input_token_count (int): Input token count used for translation
        output_token_count (int): Output token count used for translation

    Attributes:
        model_name (str): Model name used for translation
        version (str): Version of the model used for translation
        api_endpoint (str): API endpoint used for translation
        billed_character_count (int): Billed character count used for translation
        input_token_count (int): Input token count used for translation
        output_token_count (int): Output token count used for translation
    """
    model_name: str = ""
    version: str = ""
    api_endpoint: str = ""
    billed_characters_count: int = 0
    input_tokens_count: int = 0
    output_tokens_count: int = 0

    def to_dict(self) -> dict:
        return dict(
            model_name=self.model_name,
            version=self.version,
            api_endpoint=self.api_endpoint,
            billed_characters_count=self.billed_characters_count,
            input_token_count=self.input_tokens_count,
            output_token_count=self.output_tokens_count,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "TranslationUsageStatsConfig":
        return cls(**data)


@dataclass
class OCRUsageStatsConfig:
    """OCRUsageStatsConfig entity
    Args:
        model_name (str): Model name used for OCR
        page_count (int): Page count

    Attributes:
        model_name (str): Model name used for OCR
        page_count (int): Page count
    """
    model_name: str = ""
    page_count: int = 0

    def to_dict(self) -> dict:
        return dict(
            model_name=self.model_name,
            page_count=self.page_count,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "OCRUsageStatsConfig":
        return cls(**data)
