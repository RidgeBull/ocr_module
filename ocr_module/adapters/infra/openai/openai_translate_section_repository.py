import os
import time
from logging import INFO, StreamHandler, getLogger
from typing import Any, Dict, List, Tuple

from openai import OpenAI

from ocr_module.domain.entities import (
    Paragraph,
    ParagraphWithTranslation,
    Section,
    SectionWithTranslation,
    TranslationUsageStatsConfig,
)
from ocr_module.domain.repositories.i_translate_section_repository import (
    ITranslateSectionRepository,
)


class OpenAITranslateSectionRepository(ITranslateSectionRepository):
    def __init__(
        self,
        client: OpenAI,
        model: str,
        context: str | None = None,
        retry_limit: int = 3,
        retry_delay: int = 10,
    ):
        """
        Initialize the OpenAITranslateSectionRepository

        Args:
            client (OpenAI, optional): _description_. Defaults to OpenAI(api_key=settings.OPENAI_API_KEY).
            model (str, optional): _description_. Defaults to "gpt-4o-2024-11-20".
            retry_limit (int, optional): _description_. Defaults to 3.
            retry_delay (int, optional): _description_. Defaults to 10.
        """
        self.client = client
        self.context = context
        self.model = model
        self.retry_limit = retry_limit
        self.retry_delay = retry_delay
        self.logger = getLogger(__name__)

    @staticmethod
    def build_batch_translate_request(
        paragraphs: List[Paragraph],
        source_language: str | None,
        target_language: str,
        context: str | None = None,
    ) -> List[dict[str, str]]:
        """
        Build a batch translate request for OpenAI API

        Args:
            paragraphs (List[TextParagraph]): List of paragraphs to translate
            source_language (str | None): Source language(None means auto translate)
            target_language (str): Target language

        Returns:
            List[dict[str, str]]: List of translate request
        """
        # combine paragraphs with sign
        combined_text = "\n\n".join(
            [
                f"### Paragraph {paragraph.paragraph_id} ###\n{paragraph.content}"
                for paragraph in paragraphs
            ]
        )
        if source_language is None:
            source_language = "automatically detect the source language and"
        # build translate request
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are only allowed to translate.\n"
                    f"You are a great translator. Please translate the following text from {source_language} to {target_language}.\n"
                    f"Each paragraph is prefixed with '### Paragraph n ###'. Please include the same prefixes in your translations to correspond each translation with the input text.\n"
                    f"Do not translate the '### Paragraph n ###' prefixes and :formula: placeholders.\n"
                    f"Do not add or remove :formula: placeholders.\n"
                    f"Do not add any other text or comments.\n"
                    f"Context: {context}\n"
                ),
            },
            {
                "role": "user",
                "content": combined_text,
            },
        ]
        return messages

    @staticmethod
    def build_batch_translate_with_formula_id_request(
        paragraphs: List[Paragraph],
        source_language: str | None,
        target_language: str,
        context: str | None = None,
    ) -> List[dict[str, str]]:
        """
        Build a batch translate request for OpenAI API

        Args:
            paragraphs (List[Paragraph]): List of paragraphs to translate
            source_language (str | None): Source language(None means auto translate)
            target_language (str): Target language

        Returns:
            List[dict[str, str]]: List of translate request
        """
        combined_text = "\n\n".join(
            [
                f"### Paragraph {paragraph.paragraph_id} ###\n{paragraph.content}"
                for paragraph in paragraphs
            ]
        )
        if source_language is None:
            source_language = "automatically detect the source language and"
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are only allowed to translate.\n"
                    f"You are a great translator. Please translate the following text from {source_language} to {target_language}.\n"
                    f"Each paragraph is prefixed with '### Paragraph n ###'. Please include the same prefixes in your translations to correspond each translation with the input text.\n"
                    f"Do not translate the '### Paragraph n ###' prefixes and <formula_n/> placeholders.\n"
                    f"Do not add or remove <formula_n/> placeholders.\n"
                    f"Do not add any other text or comments.\n"
                    f"Context: {context}\n"
                ),
            },
            {
                "role": "user",
                "content": combined_text,
            },
        ]
        return messages

    @staticmethod
    def parse_batch_translate_response(response: str) -> List[str]:
        """
        Parse the batch translate response from OpenAI API

        Args:
            response (str): Response from OpenAI API

        Returns:
            List[str]: List of translation
        """
        translations: List[str] = []
        # split response by '### Text n ###'
        parts = response.split("### Paragraph")
        for part in parts[1:]:
            text = part.split("###")[1].strip()
            translations.append(text)
        return translations

    def _request_translate(self, messages: List[dict[str, str]]) -> Dict[str, Any]:
        """
        Request translate from OpenAI API
        """
        retry_count = 0
        while retry_count < self.retry_limit:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=4096,
                    temperature=0.7,
                    top_p=1.0,
                )
                translated_text = response.choices[0].message.content
                self.logger.debug(translated_text)
                return {
                    "status": "success",
                    "data": translated_text,
                    "input_tokens": (
                        response.usage.prompt_tokens if response.usage else 0
                    ),
                    "output_tokens": (
                        response.usage.completion_tokens if response.usage else 0
                    ),
                }
            except Exception as e:
                retry_count += 1
                self.logger.warning(f"Failed to translate: {e}")
                time.sleep(self.retry_delay)
        raise Exception("Failed to translate")

    def translate_paragraphs(
        self,
        paragraphs: List[Paragraph],
        source_language: str | None,
        target_language: str,
    ) -> Tuple[List[ParagraphWithTranslation], TranslationUsageStatsConfig]:
        con_len = sum([p.content_length() for p in paragraphs])
        self.logger.debug(
            f"Start to translate {len(paragraphs)} paragraphs of {con_len:,} chars"
        )
        messages = self.build_batch_translate_request(
            paragraphs, source_language, target_language, self.context
        )
        response = self._request_translate(messages)
        translations = self.parse_batch_translate_response(response["data"])
        paragraphs_with_translation: List[ParagraphWithTranslation] = []
        # 翻訳のリクエスト自体は一度に一気に行われるため、responseのinput_tokensとoutput_tokensをそのまま使用する
        usage_stats = TranslationUsageStatsConfig(
            input_token_count=response["input_tokens"],
            output_token_count=response["output_tokens"],
        )
        for translation, paragraph in zip(translations, paragraphs):
            paragraphs_with_translation.append(
                ParagraphWithTranslation(
                    paragraph_id=paragraph.paragraph_id,
                    role=paragraph.role,
                    translation=translation,
                    content=paragraph.content,
                    bbox=paragraph.bbox,
                    page_number=paragraph.page_number,
                )
            )
            # 翻訳のリクエスト自体は一度に一気に行われるため、responseのinput_tokensとoutput_tokensをそのまま使用する
            usage_stats.input_character_count += len(paragraph.content)
            usage_stats.output_character_count += len(translation)
        return paragraphs_with_translation, usage_stats

    def translate_section(
        self,
        section: Section,
        source_language: str | None,
        target_language: str,
    ) -> Tuple[SectionWithTranslation, TranslationUsageStatsConfig]:
        self.logger.debug(f"Start to translate section {section}")
        paragraphs_with_translation, usage_stats = self.translate_paragraphs(
            section.paragraphs,
            source_language,
            target_language,
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

    def translate_paragraphs_with_formula_id(
        self,
        paragraphs: List[Paragraph],
        source_language: str | None,
        target_language: str,
    ) -> Tuple[List[ParagraphWithTranslation], TranslationUsageStatsConfig]:
        con_len = sum([p.content_length() for p in paragraphs])
        self.logger.debug(
            f"Start to translate {len(paragraphs)} paragraphs of {con_len:,} chars"
        )
        messages = self.build_batch_translate_with_formula_id_request(
            paragraphs, source_language, target_language, self.context
        )
        response = self._request_translate(messages)
        translations = self.parse_batch_translate_response(response["data"])
        # 翻訳のリクエスト自体は一度に一気に行われるため、responseのinput_tokensとoutput_tokensをそのまま使用する
        usage_stats = TranslationUsageStatsConfig(
            input_token_count=response["input_tokens"],
            output_token_count=response["output_tokens"],
        )
        paragraphs_with_translation: List[ParagraphWithTranslation] = []
        for translation, paragraph in zip(translations, paragraphs):
            paragraphs_with_translation.append(
                ParagraphWithTranslation(
                    paragraph_id=paragraph.paragraph_id,
                    role=paragraph.role,
                    translation=translation,
                    content=paragraph.content,
                    bbox=paragraph.bbox,
                    page_number=paragraph.page_number,
                )
            )
            # 翻訳のリクエスト自体は一度に一気に行われるため、responseのinput_tokensとoutput_tokensをそのまま使用する
            usage_stats.input_character_count += len(paragraph.content)
            usage_stats.output_character_count += len(translation)
        return paragraphs_with_translation, usage_stats

    def translate_section_with_formula_id(
        self,
        section: Section,
        source_language: str | None,
        target_language: str,
    ) -> Tuple[SectionWithTranslation, TranslationUsageStatsConfig]:
        paragraphs_with_translation, usage_stats = self.translate_paragraphs_with_formula_id(
            section.paragraphs, source_language, target_language
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
