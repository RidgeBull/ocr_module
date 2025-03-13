from dataclasses import dataclass

@dataclass
class TranslationUsageStatsConfig:
    """TranslationUsageStatsConfig entity
    Args:
        model_name (str): Model name used for translation
        version (str): Version of the model used for translation
        api_endpoint (str): API endpoint used for translation
        input_character_count (int): Input character count used for translation
        output_character_count (int): Output character count used for translation
        input_token_count (int): Input token count used for translation
        output_token_count (int): Output token count used for translation

    Attributes:
        model_name (str): Model name used for translation
        version (str): Version of the model used for translation
        api_endpoint (str): API endpoint used for translation
        input_character_count (int): Input character count used for translation
        output_character_count (int): Output character count used for translation
        input_token_count (int): Input token count used for translation
        output_token_count (int): Output token count used for translation
    """
    model_name: str = ""
    version: str = ""
    api_endpoint: str = ""
    input_character_count: int = 0
    output_character_count: int = 0
    input_token_count: int = 0
    output_token_count: int = 0

    def to_dict(self) -> dict:
        return dict(
            model_name=self.model_name,
            version=self.version,
            api_endpoint=self.api_endpoint,
            input_character_count=self.input_character_count,
            output_character_count=self.output_character_count,
            input_token_count=self.input_token_count,
            output_token_count=self.output_token_count,
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
