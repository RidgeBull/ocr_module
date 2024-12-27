from abc import ABC, abstractmethod
from typing import List
from ocr.domain.entities import SectionWithTranslation, Section


class ITranslateSectionRepository(ABC):
    @abstractmethod
    def translate_section(self, section: Section, source_language: str, target_language: str) -> SectionWithTranslation:
        pass
