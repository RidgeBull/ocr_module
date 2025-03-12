import json
from dataclasses import dataclass, field
from typing import List, Dict, Any

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


@dataclass
class Document:
    pages: List[Page]
    sections: List[Section]

    def to_dict(self) -> dict[str, Any]:
        return dict(
            pages=[page.to_dict() for page in self.pages],
            sections=[section.to_dict() for section in self.sections],
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class TranslatedDocument:
    pages: List[PageWithTranslation]
    sections: List[SectionWithTranslation]
    usage_stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(
            pages=[page.to_dict() for page in self.pages],
            sections=[section.to_dict() for section in self.sections],
            usage_stats=self.usage_stats,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
