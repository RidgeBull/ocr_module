from .framework.resolver import (
    AzureOcrClient,
    GeneratePDFClient,
    OpenAITranslateClient,
    AzureOpenAITranslateClient,
    DeepLTranslateClient,
    TranslateClient,
    PyMuPDFOcrClient,
    OCRClient,
)
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
    Document,
    TranslatedDocument,
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
    "Document",
    "TranslatedDocument",
    "TranslateClient",
    "PyMuPDFOcrClient",
    "OCRClient",
]
