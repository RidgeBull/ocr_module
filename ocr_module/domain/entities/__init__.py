import json
from dataclasses import dataclass, field
from typing import List, Any

from .page_models import (
    Formula,
    DisplayFormula,
    Paragraph,
    ParagraphWithTranslation,
    Figure,
    Table,
    Page,
    PageWithTranslation,
)
from .section_models import Section, SectionWithTranslation
from .usage_model import TranslationUsageStatsConfig, OCRUsageStatsConfig

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
    "TranslationUsageStatsConfig",
    "OCRUsageStatsConfig",
]


@dataclass
class Document:
    pages: List[Page]
    sections: List[Section]
    ocr_usage_stats: OCRUsageStatsConfig = field(default_factory=OCRUsageStatsConfig)

    def to_dict(self) -> dict[str, Any]:
        return dict(
            pages=[page.to_dict() for page in self.pages],
            sections=[section.to_dict() for section in self.sections],
            ocr_usage_stats=self.ocr_usage_stats.to_dict(),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class TranslatedDocument:
    pages: List[PageWithTranslation]
    sections: List[SectionWithTranslation]
    translation_usage_stats: TranslationUsageStatsConfig = field(default_factory=TranslationUsageStatsConfig)

    def to_dict(self) -> dict[str, Any]:
        return dict(
            pages=[page.to_dict() for page in self.pages],
            sections=[section.to_dict() for section in self.sections],
            translation_usage_stats=self.translation_usage_stats.to_dict(),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
