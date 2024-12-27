from typing import List
from logging import getLogger
from ocr.domain.repositories import (
    ITranslateSectionRepository,
    IPDFGeneratorRepository,
    IOcrRepository,
)
from ocr.domain.entities import (
    Section,
    SectionWithTranslation,
    TextParagraphWithTranslation,
    TextParagraph,
)


class TranslatePDFUseCase:
    def __init__(
        self,
        translate_section_repository: ITranslateSectionRepository,
        pdf_generator_repository: IPDFGeneratorRepository,
        ocr_repository: IOcrRepository,
    ):
        self.translate_section_repository = translate_section_repository
        self.pdf_generator_repository = pdf_generator_repository
        self.ocr_repository = ocr_repository
        self.logger = getLogger(__name__)

    @staticmethod
    def _convert_translated_section_to_section(
        section: SectionWithTranslation,
    ) -> Section:
        translated_paragraphs: List[TextParagraph] = []
        for paragraph in section.paragraphs:
            translated_paragraphs.append(
                TextParagraph(
                    text=paragraph.translation,
                    inline_formulas=paragraph.inline_formulas,
                    lines=paragraph.lines,
                    bbox=paragraph.bbox,
                    page_number=paragraph.page_number,
                )
            )
        return Section(
            paragraphs=translated_paragraphs,
            formula_blocks=section.formula_blocks,
            tables=section.tables,
            figures=section.figures,
        )

    def execute(
        self,
        document_path: str,
        output_path: str,
        source_language: str,
        target_language: str,
    ):
        self.logger.info(f"Start to translate PDF file {document_path} to {output_path}")
        sections = self.ocr_repository.get_sections(document_path)
        self.logger.info(f"Sections are extracted from {document_path} successfully {sections}")
        translated_sections: List[SectionWithTranslation] = []
        for section in sections:
            translated_sections.append(
                self.translate_section_repository.translate_section(
                    section, source_language, target_language
                )
            )
        self.logger.info(f"Sections are translated successfully {translated_sections}")
        print(translated_sections)
        self.pdf_generator_repository.generate_pdf(
            sections=[self._convert_translated_section_to_section(section) for section in translated_sections],
            page_num=self.ocr_repository.get_page_number(),
            output_path=output_path,
            display_formulas=self.ocr_repository.get_display_formulas(),
            page_size=self.ocr_repository.get_page_size(),
        )
        self.logger.info(f"PDF file is generated at {output_path}")
        return output_path
