import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import INFO, StreamHandler, getLogger
from typing import List, Tuple

from ocr_module.domain.entities import (
    Paragraph,
    ParagraphWithTranslation,
    Section,
    SectionWithTranslation,
    TranslationUsageStatsConfig,
)
from ocr_module.domain.repositories import ITranslateSectionRepository


class TranslateSectionFormulaIdUseCase:
    """Sectionの内容を翻訳する（数式ID付き）"""

    def __init__(self, translate_section_repository: ITranslateSectionRepository):
        self._translate_section_repository = translate_section_repository
        self._logger = getLogger(__name__)
        if not self._logger.hasHandlers():
            self._logger.setLevel(INFO)
            self._logger.addHandler(StreamHandler())

    def execute(
        self,
        sections: List[Section],
        source_language: str | None,
        target_language: str,
    ) -> Tuple[List[SectionWithTranslation], TranslationUsageStatsConfig]:
        """Sectionの内容を翻訳する（数式ID付き）

        Args:
            sections (List[Section]): 翻訳するSectionのリスト
            source_language (str | None): 翻訳元の言語(None means auto translate)
            target_language (str): 翻訳先の言語

        Returns:
            List[SectionWithTranslation]: 翻訳されたSectionWithTranslationのリスト
        """
        section_with_translations: List[SectionWithTranslation] = []
        usage_stats: TranslationUsageStatsConfig = TranslationUsageStatsConfig()
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    self._translate_section_repository.translate_section_with_formula_id,
                    section,
                    source_language,
                    target_language,
                )
                for section in sections
            ]
            for future in as_completed(futures):
                section_with_translation, section_usage_stats = future.result()
                section_with_translations.append(section_with_translation)
                # usage_stats を更新する
                usage_stats.model_name = section_usage_stats.model_name
                usage_stats.version = section_usage_stats.version
                usage_stats.api_endpoint = section_usage_stats.api_endpoint
                usage_stats.input_character_count += (
                    section_usage_stats.input_character_count
                )
                usage_stats.output_character_count += (
                    section_usage_stats.output_character_count
                )
                usage_stats.input_token_count += section_usage_stats.input_token_count
                usage_stats.output_token_count += section_usage_stats.output_token_count
        return section_with_translations, usage_stats

    async def execute_async(
        self,
        sections: List[Section],
        source_language: str | None,
        target_language: str,
    ) -> Tuple[List[SectionWithTranslation], TranslationUsageStatsConfig]:
        """Sectionの内容を非同期で翻訳する（数式ID付き）

        Args:
            sections (List[Section]): 翻訳するSectionのリスト
            source_language (str | None): 翻訳元の言語(None means auto translate)
            target_language (str): 翻訳先の言語

        Returns:
            Tuple[List[SectionWithTranslation], TranslationUsageStatsConfig]: 翻訳されたセクションと使用統計情報
        """
        LIMIT = 1500
        usage_stats = TranslationUsageStatsConfig()

        async def get_result_task(
            section: Section,
        ) -> Tuple[SectionWithTranslation, TranslationUsageStatsConfig]:
            # logging
            start_time = time.time()
            i = f"{section.section_id:03d}"
            self._logger.info(f"[{i}]" + "=" * 30)
            self._logger.info(f"[{i}]  start translate_section_with_formula_id")

            section_usage_stats = TranslationUsageStatsConfig()

            if section.content_length() == 0:
                self._logger.info(f"[{i}]  content length is 0")
                ret = SectionWithTranslation(
                    section_id=section.section_id,
                    paragraphs=[],  # 空のリストを渡す
                    paragraph_ids=section.paragraph_ids,
                    table_ids=section.table_ids,
                    figure_ids=section.figure_ids,
                    tables=section.tables,
                    figures=section.figures,
                )
                return ret, section_usage_stats
            else:
                # paragraphs を chunk に分割する
                para_list = []
                current_paragraphs = []
                current_length = 0

                for paragraph in section.paragraphs:
                    paragraph_len = paragraph.content_length()
                    if current_length + paragraph_len > LIMIT and current_paragraphs:
                        para_list.append(current_paragraphs)
                        current_paragraphs = []
                        current_length = 0
                    current_paragraphs.append(paragraph)
                    current_length += paragraph_len

                # 残りのparagraphsがある場合、最後のチャンクを作成
                if current_paragraphs:
                    para_list.append(current_paragraphs)

                # 分割した paragraph を翻訳する
                tasks = [
                    asyncio.to_thread(
                        self._translate_section_repository.translate_paragraphs_with_formula_id,
                        paras,
                        source_language,
                        target_language,
                    )
                    for paras in para_list
                ]
                para_results = await asyncio.gather(*tasks)

                # 翻訳結果と使用統計を集計
                para_rets = []
                for paras, stats in para_results:
                    para_rets.extend(paras)
                    # 使用統計を更新
                    section_usage_stats.model_name = stats.model_name
                    section_usage_stats.version = stats.version
                    section_usage_stats.api_endpoint = stats.api_endpoint
                    section_usage_stats.input_character_count += (
                        stats.input_character_count
                    )
                    section_usage_stats.output_character_count += (
                        stats.output_character_count
                    )
                    section_usage_stats.input_token_count += stats.input_token_count
                    section_usage_stats.output_token_count += stats.output_token_count

                ret = SectionWithTranslation(
                    section_id=section.section_id,
                    paragraphs=para_rets,
                    paragraph_ids=section.paragraph_ids,
                    table_ids=section.table_ids,
                    figure_ids=section.figure_ids,
                    tables=section.tables,
                    figures=section.figures,
                )

            self._logger.info(
                f"[{i}]  {len(section.paragraphs)} paragraphs of {section.content_length():,} chars"
            )
            self._logger.info(f"[{i}]  end translate_section_with_formula_id")
            self._logger.info(
                f"[{i}]  elapsed time: {time.time() - start_time:.2f} sec"
            )
            self._logger.info(f"[{i}]" + "=" * 30)
            return ret, section_usage_stats

        # contentが多い順にrequestを投げる
        sections.sort(key=lambda x: x.content_length(), reverse=True)
        tasks = [get_result_task(section) for section in sections]
        results = await asyncio.gather(*tasks)

        # 結果と使用統計を分離
        sections_with_translation = []
        for section_result, section_stats in results:
            sections_with_translation.append(section_result)
            # 全体の使用統計を更新
            usage_stats.model_name = section_stats.model_name
            usage_stats.version = section_stats.version
            usage_stats.api_endpoint = section_stats.api_endpoint
            usage_stats.input_character_count += section_stats.input_character_count
            usage_stats.output_character_count += section_stats.output_character_count
            usage_stats.input_token_count += section_stats.input_token_count
            usage_stats.output_token_count += section_stats.output_token_count

        # セクションIDでソート
        sections_with_translation.sort(key=lambda x: x.section_id)

        return sections_with_translation, usage_stats
