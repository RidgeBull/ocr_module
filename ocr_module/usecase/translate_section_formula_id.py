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
        self._logger.setLevel(INFO)
        if self._logger.hasHandlers():
            self._logger.handlers.clear()
        self._logger.addHandler(StreamHandler())

    def execute(
        self, sections: List[Section], source_language: str, target_language: str
    ) -> List[SectionWithTranslation]:
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
        self, sections: List[Section], source_language: str, target_language: str
    ) -> List[SectionWithTranslation]:

        def request_task(section: Section) -> SectionWithTranslation:
            if section.content_length() == 0:
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
                paras = self._translate_section_repository.translate_paragraphs_with_formula_id(
                    section.paragraphs,
                    source_language,
                    target_language,
                )
                ret = SectionWithTranslation(
                    section_id=section.section_id,
                    paragraphs=paras,
                    paragraph_ids=section.paragraph_ids,
                    table_ids=section.table_ids,
                    figure_ids=section.figure_ids,
                    tables=section.tables,
                    figures=section.figures,
                )

            return ret

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
                        para_list,
                        source_language,
                        target_language,
                    )
                    for para_list in para_list
                ]
                para_rets = await asyncio.gather(*tasks)
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
