from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import getLogger
from typing import List

from ocr_module.domain.entities import Section, SectionWithTranslation
from ocr_module.domain.repositories import ITranslateSectionRepository


class TranslateSectionUseCase:
    def __init__(self, translate_section_repository: ITranslateSectionRepository):
        self.translate_section_repository = translate_section_repository
        self.logger = getLogger(__name__)

    def execute(
        self,
        sections: List[Section],
        source_language: str,
        target_language: str,
    ) -> List[SectionWithTranslation]:
        section_with_translations: List[SectionWithTranslation] = []
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    self.translate_section_repository.translate_section,
                    section,
                    source_language,
                    target_language,
                )
                for section in sections
            ]
            for future in as_completed(futures):
                section_with_translation = future.result()
                section_with_translations.append(section_with_translation)
        return section_with_translations
