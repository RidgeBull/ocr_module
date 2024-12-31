from abc import ABC, abstractmethod
from typing import List

from domain.entities import Section, SectionWithTranslation


class ITranslateSectionRepository(ABC):
    @abstractmethod
    def translate_section(
        self, section: Section, source_language: str, target_language: str
    ) -> SectionWithTranslation:
        """
        セクションを翻訳する

        Args:
            section (Section): セクション
            source_language (str): ソース言語
            target_language (str): ターゲット言語

        Returns:
            SectionWithTranslation: 翻訳されたセクション
        """
        raise NotImplementedError

    @abstractmethod
    def translate_section_with_formula_id(
        self,
        section: Section,
        source_language: str,
        target_language: str,
    ) -> SectionWithTranslation:
        """
        セクションを翻訳する

        Args:
            section (Section): セクション
            source_language (str): ソース言語
            target_language (str): ターゲット言語

        Returns:
            SectionWithTranslation: 翻訳されたセクション
        """
        raise NotImplementedError
