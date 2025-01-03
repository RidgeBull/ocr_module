from logging import getLogger
from typing import Dict, List

from ocr_module.domain.entities import (
    Page,
    PageWithTranslation,
    ParagraphWithTranslation,
    SectionWithTranslation,
)


class GetTranslatedPageUseCase:
    """sectionはpageをまたいだ情報になっているので、page単位の情報に分割しなおす

    Pageのlistを走査し、Page中のparagraph_idと一致する翻訳済みのparagraph(SectionWithTranslation)と入れ替える
    """

    def __init__(self):
        self.logger = getLogger(__name__)

    def execute(
        self, pages: List[Page], translated_sections: List[SectionWithTranslation]
    ) -> List[PageWithTranslation]:
        page_with_translations: List[PageWithTranslation] = []
        paragraph_dict = self._get_page_paragraphs(translated_sections)
        for page in pages:
            page_with_translation = self._convert_page_to_page_with_translation(
                page, paragraph_dict
            )
            page_with_translations.append(page_with_translation)
        return page_with_translations

    @staticmethod
    def _get_page_paragraphs(
        sections: List[SectionWithTranslation],
    ) -> Dict[int, ParagraphWithTranslation]:
        # key: paragraph_id , value: ParagraphWithTranslation の dict
        paragraph_dict: Dict[int, ParagraphWithTranslation] = {}
        for section in sections:
            for paragraph in section.paragraphs:
                paragraph_dict[paragraph.paragraph_id] = paragraph
        return paragraph_dict

    @staticmethod
    def _convert_page_to_page_with_translation(
        page: Page, paragraph_dict: Dict[int, ParagraphWithTranslation]
    ) -> PageWithTranslation:
        paragraphs_with_translation: List[ParagraphWithTranslation] = []
        for paragraph in page.paragraphs:
            if paragraph.paragraph_id in paragraph_dict:
                paragraphs_with_translation.append(
                    paragraph_dict[paragraph.paragraph_id]
                )
            else:
                paragraph_with_translation = ParagraphWithTranslation(
                    paragraph_id=paragraph.paragraph_id,
                    role=paragraph.role,
                    content=paragraph.content,
                    bbox=paragraph.bbox,
                    page_number=paragraph.page_number,
                    translation=paragraph.content,
                )
                paragraphs_with_translation.append(paragraph_with_translation)
        return PageWithTranslation(
            page_number=page.page_number,
            width=page.width,
            height=page.height,
            formulas=page.formulas,
            display_formulas=page.display_formulas,
            figures=page.figures,
            tables=page.tables,
            paragraphs=paragraphs_with_translation,
        )
