import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import INFO, StreamHandler, getLogger
from typing import List

from ocr_module.domain.entities import Section, SectionWithTranslation
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
    ) -> List[SectionWithTranslation]:
        """Sectionの内容を翻訳する（数式ID付き）

        Args:
            sections (List[Section]): 翻訳するSectionのリスト
            source_language (str | None): 翻訳元の言語(None means auto translate)
            target_language (str): 翻訳先の言語

        Returns:
            List[SectionWithTranslation]: 翻訳されたSectionWithTranslationのリスト
        """
        section_with_translations: List[SectionWithTranslation] = []
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
                section_with_translation = future.result()
                section_with_translations.append(section_with_translation)
        return section_with_translations

    async def execute_async(
        self,
        sections: List[Section],
        source_language: str | None,
        target_language: str,
    ) -> List[SectionWithTranslation]:
        """Sectionの内容を非同期で翻訳する（数式ID付き）

        Args:
            sections (List[Section]): 翻訳するSectionのリスト
            source_language (str | None): 翻訳元の言語(None means auto translate)
            target_language (str): 翻訳先の言語
        """
        LIMIT = 1500
        async def get_result_task(section: Section) -> SectionWithTranslation:
            # logging
            start_time = time.time()
            i = f"{section.section_id:03d}"
            self._logger.info(f"[{i}]" + "=" * 30)
            self._logger.info(f"[{i}]  start translate_section_with_formula_id")
            if section.content_length() == 0:
                self._logger.info(f"[{i}]  content length is 0")
                ret = SectionWithTranslation(
                    section_id=section.section_id,
                    paragraphs=section.paragraphs,
                    paragraph_ids=section.paragraph_ids,
                    table_ids=section.table_ids,
                    figure_ids=section.figure_ids,
                    tables=section.tables,
                    figures=section.figures,
                )
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
                para_rets = await asyncio.gather(*tasks)
                # para_rets は List[List[ParagraphWithTranslation]] なので flatten
                para_rets = [para for para_list in para_rets for para in para_list]
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
            return ret

        # contentが多い順にrequestを投げる

        sections.sort(key=lambda x: x.content_length(), reverse=True)
        tasks = [get_result_task(section) for section in sections]
        results = await asyncio.gather(*tasks)
        results: List[SectionWithTranslation] = list(results)
        results.sort(key=lambda x: x.section_id)

        return results
