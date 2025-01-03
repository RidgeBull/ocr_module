import logging
from logging import getLogger
from typing import Dict, List

from ocr_module.domain.entities import Page, Paragraph, Section


class ChangeFormulaIdUseCase:
    """文中の`:formula:`を`<<formula_i>>`に変換する"""

    def __init__(self):
        self.logger = getLogger(__name__)
        # 既存のハンドラを削除
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        # 新しいハンドラを追加
        self.logger.addHandler(logging.StreamHandler())
        # ファイルにログを出力
        self.logger.addHandler(logging.FileHandler("change_formula_id.log", mode="w"))
        self.logger.setLevel(logging.INFO)

    def execute(self, pages: List[Page], sections: List[Section]) -> List[Section]:
        processed_pages: List[Page] = []
        processed_paragraphs: Dict[int, Paragraph] = {}
        # 各ページのパラグラフの内容を結合
        page_text = "\n".join(
            [paragraph.content for page in pages for paragraph in page.paragraphs]
        )
        self.logger.info(f"Before processed pages: {page_text}")
        for page in pages:
            processed_page = self.change_formula_tag_in_page(page)
            processed_pages.append(processed_page)
            for paragraph in processed_page.paragraphs:
                processed_paragraphs[paragraph.paragraph_id] = paragraph

        for section in sections:
            for paragraph in section.paragraphs:
                if paragraph.paragraph_id in processed_paragraphs:
                    paragraph.content = processed_paragraphs[
                        paragraph.paragraph_id
                    ].content
                    self.logger.info(
                        f"Changed formula tag in paragraph {paragraph.paragraph_id}: {paragraph.content}"
                    )
        self.logger.info(f"Processed sections: {sections}")

        return sections

    def change_formula_tag_in_page(self, page: Page) -> Page:
        current_formula_id = 0
        for paragraph in page.paragraphs:
            num_formula = paragraph.content.count(":formula:")
            for i in range(num_formula):
                formula_tag = f"<<formula_{current_formula_id}>>"
                paragraph.content = paragraph.content.replace(
                    f":formula:", formula_tag, 1
                )
                self.logger.info(
                    f"Changed formula tag in paragraph {paragraph.paragraph_id}: {formula_tag}"
                )
                self.logger.info(f"Paragraph content: {paragraph.content}")
                current_formula_id += 1
        return page
