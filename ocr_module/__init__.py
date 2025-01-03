from .framework.resolver import AzureOcrClient, GeneratePDFClient, OpenAITranslateClient
from ocr_module.domain.entities import (
    Formula,
    DisplayFormula,
    Paragraph,
    ParagraphWithTranslation,
    Figure,
    Table,
    Page,
    PageWithTranslation,
    Section,
    SectionWithTranslation,
)

__all__ = [
    "Formula",
    "DisplayFormula",
    "Paragraph",
    "ParagraphWithTranslation",
    "Figure",
    "Table",
    "Page",
    "PageWithTranslation",
    "Section",
    "SectionWithTranslation",
]
