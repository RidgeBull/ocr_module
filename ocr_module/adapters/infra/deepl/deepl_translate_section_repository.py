import os
from logging import INFO, getLogger
from typing import List, Tuple

from ocr_module.domain.entities import (
    Paragraph,
    ParagraphWithTranslation,
    Section,
    SectionWithTranslation,
    TranslationUsageStatsConfig,
)
from ocr_module.domain.repositories import ITranslateSectionRepository

import deepl


class DeepLTranslateSectionRepository(ITranslateSectionRepository):
    def __init__(
        self,
        api_key: str,
        retry_limit: int = 3,
        glossary_id: str | None = None,
    ):
        deepl.http_client.max_network_retries = retry_limit
        self._client = deepl.Translator(auth_key=api_key)
        self._logger = getLogger(__name__)
        self._logger.setLevel(INFO)
        self._glossary_id = glossary_id

    def _batch_translation_with_formula_placeholder(
        self,
        paragraphs: List[Paragraph],
        source_language: str | None,
        target_language: str,
    ) -> Tuple[List[ParagraphWithTranslation], int]:
        """Batch translation with formula placeholder

        Args:
            paragraphs (List[Paragraph]): List of paragraphs to translate
            source_language (str | None): Source language(None means auto translate)
            target_language (str): Target language

        Returns:
            List[ParagraphWithTranslation]: List of paragraphs with translation
        """
        original_texts: List[str] = [paragraph.content for paragraph in paragraphs]
        # <formula_{id}/>を無視するようにする
        self._logger.debug(f"Translating from {source_language} to {target_language}")
        try:
            translated_texts = self._client.translate_text(
                text=original_texts,
                source_lang=source_language,
                target_lang=target_language,
                tag_handling="xml",
                ignore_tags=["formula"],
                glossary=self._glossary_id,
            )
            self._logger.debug(f"Translations: {translated_texts}")
        except Exception as e:
            self._logger.error(f"Error Translating with DeepL: {e}", exc_info=True)
            raise e
        billed_characters_count = 0
        paragraphs_with_translation: List[ParagraphWithTranslation] = []
        for i, paragraph in enumerate(paragraphs):
            paragraph_with_translation = ParagraphWithTranslation(
                paragraph_id=paragraph.paragraph_id,
                role=paragraph.role,
                content=paragraph.content,
                bbox=paragraph.bbox,
                page_number=paragraph.page_number,
                translation=translated_texts[i].text,
            )
            billed_characters_count += translated_texts[i].billed_characters
            paragraphs_with_translation.append(paragraph_with_translation)
        return paragraphs_with_translation, billed_characters_count

    def _batch_translation(
        self,
        paragraphs: List[Paragraph],
        source_language: str | None,
        target_language: str,
    ) -> Tuple[List[ParagraphWithTranslation], int]:
        """Batch translation

        Args:
            paragraphs (List[Paragraph]): List of paragraphs to translate
            source_language (str | None): Source language(None means auto translate)
            target_language (str): Target language
        """
        original_texts: List[str] = [paragraph.content for paragraph in paragraphs]
        self._logger.debug(f"Original texts: {original_texts}")
        try:
            translated_texts = self._client.translate_text(
                original_texts,
                source_lang=source_language,
                target_lang=target_language,
                glossary=self._glossary_id,
            )
            self._logger.debug(f"Translations: {translated_texts}")
        except Exception as e:
            self._logger.error(f"Error Translating with DeepL: {e}", exc_info=True)
            raise e
        paragraphs_with_translation: List[ParagraphWithTranslation] = []
        billed_characters_count = 0
        for i, paragraph in enumerate(paragraphs):
            paragraph_with_translation = ParagraphWithTranslation(
                paragraph_id=paragraph.paragraph_id,
                role=paragraph.role,
                content=paragraph.content,
                bbox=paragraph.bbox,
                page_number=paragraph.page_number,
                translation=translated_texts[i].text,
            )
            billed_characters_count += translated_texts[i].billed_characters
            paragraphs_with_translation.append(paragraph_with_translation)
        return paragraphs_with_translation, billed_characters_count

    def translate_paragraphs_with_formula_id(
        self,
        paragraphs: List[Paragraph],
        source_language: str | None,
        target_language: str,
    ) -> Tuple[List[ParagraphWithTranslation], TranslationUsageStatsConfig]:
        """Translate section with formula placeholder

        Args:
            section (Section): Section to translate
            source_language (str | None): Source language(None means auto translate)
            target_language (str): Target language

        Returns:
            Tuple[List[ParagraphWithTranslation], TranslationUsageStatsConfig]: Section with translation
        """

        paragraphs_with_translation, billed_characters_count = (
            self._batch_translation_with_formula_placeholder(
                paragraphs, source_language, target_language
            )
        )
        usage_stats = TranslationUsageStatsConfig(
            billed_characters_count=billed_characters_count,
        )
        return paragraphs_with_translation, usage_stats

    def translate_section_with_formula_id(
        self, section: Section, source_language: str | None, target_language: str
    ) -> Tuple[SectionWithTranslation, TranslationUsageStatsConfig]:
        # もしPargraphsが空の場合は、空のSectionWithTranslationを返す
        if len(section.paragraphs) <= 0:
            usage_stats = TranslationUsageStatsConfig()
            return (
                SectionWithTranslation(
                    section_id=section.section_id,
                    paragraphs=[
                        ParagraphWithTranslation(
                            paragraph_id=paragraph.paragraph_id,
                            role=paragraph.role,
                            content=paragraph.content,
                            bbox=paragraph.bbox,
                            page_number=paragraph.page_number,
                            translation=paragraph.content,
                        )
                        for paragraph in section.paragraphs
                    ],
                    paragraph_ids=section.paragraph_ids,
                    table_ids=section.table_ids,
                    figure_ids=section.figure_ids,
                    tables=section.tables,
                    figures=section.figures,
                ),
                usage_stats,
            )

        paragraphs_with_translation, usage_stats = (
            self.translate_paragraphs_with_formula_id(
                section.paragraphs, source_language, target_language
            )
        )
        return (
            SectionWithTranslation(
                section_id=section.section_id,
                paragraphs=paragraphs_with_translation,
                paragraph_ids=section.paragraph_ids,
                table_ids=section.table_ids,
                figure_ids=section.figure_ids,
                tables=section.tables,
                figures=section.figures,
            ),
            usage_stats,
        )

    def translate_paragraphs(
        self,
        paragraphs: List[Paragraph],
        source_language: str | None,
        target_language: str,
    ) -> Tuple[List[ParagraphWithTranslation], TranslationUsageStatsConfig]:
        """Translate section

        Args:
            section (Section): Section to translate
            source_language (str | None): Source language(None means auto translate)
            target_language (str): Target language

        Returns:
            List[ParagraphWithTranslation]: List of paragraphs with translation
        """
        # もしPargraphsが空の場合は、空のSectionWithTranslationを返す

        paragraphs_with_translation, billed_characters_count = self._batch_translation(
            paragraphs, source_language, target_language
        )
        usage_stats = TranslationUsageStatsConfig(
            billed_characters_count=billed_characters_count,
        )
        return paragraphs_with_translation, usage_stats

    def translate_section(
        self,
        section: Section,
        source_language: str | None,
        target_language: str,
    ) -> Tuple[SectionWithTranslation, TranslationUsageStatsConfig]:
        if len(section.paragraphs) <= 0:
            usage_stats = TranslationUsageStatsConfig()
            return (
                SectionWithTranslation(
                    section_id=section.section_id,
                    paragraphs=[
                        ParagraphWithTranslation(
                        paragraph_id=paragraph.paragraph_id,
                        role=paragraph.role,
                        content=paragraph.content,
                        bbox=paragraph.bbox,
                        page_number=paragraph.page_number,
                        translation=paragraph.content,
                    )
                    for paragraph in section.paragraphs
                ],
                    paragraph_ids=section.paragraph_ids,
                    table_ids=section.table_ids,
                    figure_ids=section.figure_ids,
                    tables=section.tables,
                    figures=section.figures,
                ),
                usage_stats,
            )
        paragraphs_with_translation, usage_stats = self.translate_paragraphs(
            section.paragraphs, source_language, target_language
        )
        self._logger.debug(f"Translations: {paragraphs_with_translation}")
        return (
            SectionWithTranslation(
                section_id=section.section_id,
                paragraphs=paragraphs_with_translation,
                paragraph_ids=section.paragraph_ids,
                table_ids=section.table_ids,
                figure_ids=section.figure_ids,
                tables=section.tables,
                figures=section.figures,
            ),
            usage_stats,
        )
