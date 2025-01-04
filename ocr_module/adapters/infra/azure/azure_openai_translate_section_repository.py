import os
import time
from logging import getLogger, INFO
from typing import Any, Dict, List

from openai import AzureOpenAI

from ocr_module.domain.entities import (
    Paragraph,
    ParagraphWithTranslation,
    Section,
    SectionWithTranslation,
)
from ocr_module.domain.repositories.i_translate_section_repository import (
    ITranslateSectionRepository,
)


class AzureOpenAITranslateSectionRepository(ITranslateSectionRepository):
    def __init__(
        self,
        client: AzureOpenAI = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        ),
        model: str = "gpt-4o-2024-11-20",
        retry_limit: int = 3,
        retry_delay: int = 10,
    ):
        self._client = client
        self._model = model
        self._retry_limit = retry_limit
        self._retry_delay = retry_delay
        self._logger = getLogger(__name__)
        self._logger.setLevel(INFO)

    @staticmethod
    def build_batch_translate_request(
        paragraphs: List[Paragraph], source_language: str, target_language: str
    ) -> List[dict[str, str]]:
        """
        Build a batch translate request for AzureOpenAI API

        Args:
            paragraphs (List[TextParagraph]): List of paragraphs to translate
            source_language (str): Source language
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
        paragraphs: List[Paragraph], source_language: str, target_language: str
    ) -> List[dict[str, str]]:
        """
        Build a batch translate request for OpenAI API

        Args:
            paragraphs (List[Paragraph]): List of paragraphs to translate
            source_language (str): Source language
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
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are only allowed to translate.\n"
                    f"You are a great translator. Please translate the following text from {source_language} to {target_language}.\n"
                    f"Each paragraph is prefixed with '### Paragraph n ###'. Please include the same prefixes in your translations to correspond each translation with the input text.\n"
                    f"Do not translate the '### Paragraph n ###' prefixes and <<formula_n>> placeholders.\n"
                    f"Do not add or remove <<formula_n>> placeholders.\n"
                    f"Do not add any other text or comments.\n"
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
        Request translate from AzureOpenAI API
        """
        retry_count = 0
        while retry_count < self._retry_limit:
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    max_tokens=4096,
                    temperature=0.7,
                    top_p=1.0,
                )
                return {
                    "status": "success",
                    "data": response.choices[0].message.content,
                }
            except Exception as e:
                retry_count += 1
                time.sleep(self._retry_delay)
        raise Exception("Failed to translate")

    def translate_section(
        self, section: Section, source_language: str, target_language: str
    ) -> SectionWithTranslation:
        self._logger.debug(f"Start to translate section {section}")
        messages = self.build_batch_translate_request(
            section.paragraphs, source_language, target_language
        )
        response = self._request_translate(messages)
        self._logger.debug(f"Response from OpenAI API: {response}")
        translations = self.parse_batch_translate_response(response["data"])
        self._logger.debug(f"Translations: {translations}")
        paragraphs_with_translation: List[ParagraphWithTranslation] = []
        for translation, paragraph in zip(translations, section.paragraphs):
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
        return SectionWithTranslation(
            section_id=section.section_id,
            paragraphs=paragraphs_with_translation,
            paragraph_ids=section.paragraph_ids,
            table_ids=section.table_ids,
            figure_ids=section.figure_ids,
            tables=section.tables,
            figures=section.figures,
        )

    def translate_section_with_formula_id(
        self, section: Section, source_language: str, target_language: str
    ) -> SectionWithTranslation:
        messages = self.build_batch_translate_with_formula_id_request(
            section.paragraphs, source_language, target_language
        )
        response = self._request_translate(messages)
        self._logger.debug(f"Response from OpenAI API: {response}")
        translations = self.parse_batch_translate_response(response["data"])
        self._logger.debug(f"Translations: {translations}")
        paragraphs_with_translation: List[ParagraphWithTranslation] = []
        for translation, paragraph in zip(translations, section.paragraphs):
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
        return SectionWithTranslation(
            section_id=section.section_id,
            paragraphs=paragraphs_with_translation,
            paragraph_ids=section.paragraph_ids,
            table_ids=section.table_ids,
            figure_ids=section.figure_ids,
            tables=section.tables,
            figures=section.figures,
        )