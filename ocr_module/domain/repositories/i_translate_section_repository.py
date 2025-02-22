from abc import ABC, abstractmethod
from typing import List

from ocr_module.domain.entities import (
    Paragraph,
    ParagraphWithTranslation,
    Section,
    SectionWithTranslation,
)


class ITranslateSectionRepository(ABC):
    @abstractmethod
    def translate_section(
        self, section: Section, source_language: str | None, target_language: str
    ) -> SectionWithTranslation:
        """
        セクションを翻訳する

        Args:
            section (Section): セクション
            source_language (str | None): ソース言語(Noneの場合は自動翻訳)
            target_language (str): ターゲット言語

        Returns:
            SectionWithTranslation: 翻訳されたセクション
        """
        raise NotImplementedError

    @abstractmethod
    def translate_section_with_formula_id(
        self,
        section: Section,
        source_language: str | None,
        target_language: str,
    ) -> SectionWithTranslation:
        """
        セクションを翻訳する

        Args:
            section (Section): セクション
            source_language (str | None): ソース言語(Noneの場合は自動翻訳)
            target_language (str): ターゲット言語

        Returns:
            SectionWithTranslation: 翻訳されたセクション
        """
        raise NotImplementedError

    @abstractmethod
    def translate_paragraphs_with_formula_id(
        self,
        paragraphs: List[Paragraph],
        source_language: str | None,
        target_language: str,
    ) -> List[ParagraphWithTranslation]:
        """
        パラグラフを翻訳する（数式ID付き）

        Args:
            paragraphs (List[Paragraph]): パラグラフ
            source_language (str | None): ソース言語(Noneの場合は自動翻訳)
            target_language (str): ターゲット言語

        Returns:
            List[ParagraphWithTranslation]: 翻訳されたパラグラフ
        """
        ...

    @abstractmethod
    def translate_paragraphs(
        self,
        paragraphs: List[Paragraph],
        source_language: str | None,
        target_language: str,
    ) -> List[ParagraphWithTranslation]:
        """
        パラグラフを翻訳する

        Args:
            paragraphs (List[Paragraph]): パラグラフ
            source_language (str | None): ソース言語(Noneの場合は自動翻訳)
            target_language (str): ターゲット言語

        Returns:
            List[ParagraphWithTranslation]: 翻訳されたパラグラフ
        """
        ...
