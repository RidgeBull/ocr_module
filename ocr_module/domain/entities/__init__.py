import json
from dataclasses import dataclass
from typing import List

from .page_models import (
    DisplayFormula,
    Figure,
    Formula,
    Page,
    PageWithTranslation,
    Paragraph,
    ParagraphWithTranslation,
    Table,
)
from .section_models import Section, SectionWithTranslation


@dataclass
class Document:
    pages: List[Page]
    sections: List[Section]

    def to_dict(self) -> str:
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

    def to_dict(self) -> str:
        return dict(
            pages=[page.to_dict() for page in self.pages],
            sections=[section.to_dict() for section in self.sections],
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
