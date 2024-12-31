from dataclasses import dataclass
from typing import List, Literal, Optional

from .page_models import Figure, Paragraph, ParagraphWithTranslation, Table


@dataclass
class Section:
    """
    Section entity

    :ivar section_id: ID of the section.
    :vartype section_id: int
    :ivar paragraphs: List of paragraphs in the section.
    :vartype paragraphs: List[Paragraph]
    :ivar tables: List of tables in the section.
    :vartype tables: List[Table]
    :ivar figures: List of figures in the section.
    :vartype figures: List[Figure]
    """

    section_id: int
    paragraphs: List[Paragraph]
    paragraph_ids: List[int]
    tables: List[Table]
    table_ids: List[int]
    figures: List[Figure]
    figure_ids: List[int]

    def to_dict(self) -> dict:
        return dict(
            section_id=self.section_id,
            paragraphs=[paragraph.to_dict() for paragraph in self.paragraphs],
            paragraph_ids=self.paragraph_ids,
            tables=[table.to_dict() for table in self.tables],
            table_ids=self.table_ids,
            figures=[figure.to_dict() for figure in self.figures],
            figure_ids=self.figure_ids,
        )


@dataclass
class SectionWithTranslation:
    """
    Section with translation entity

    :ivar section_id: ID of the section.
    :vartype section_id: int
    :ivar paragraphs: List of paragraphs in the section.
    :vartype paragraphs: List[ParagraphWithTranslation]
    :ivar tables: List of tables in the section.
    :vartype tables: List[Table]
    :ivar figures: List of figures in the section.
    :vartype figures: List[Figure]
    """

    section_id: int
    paragraphs: List[ParagraphWithTranslation]
    paragraph_ids: List[int]
    tables: List[Table]
    table_ids: List[int]
    figures: List[Figure]
    figure_ids: List[int]

    def to_dict(self) -> dict:
        return dict(
            section_id=self.section_id,
            paragraphs=[paragraph.to_dict() for paragraph in self.paragraphs],
            paragraph_ids=self.paragraph_ids,
            tables=[table.to_dict() for table in self.tables],
            table_ids=self.table_ids,
            figures=[figure.to_dict() for figure in self.figures],
            figure_ids=self.figure_ids,
        )
