from logging import DEBUG, INFO, getLogger
from typing import List, Tuple

import pymupdf

from ocr_module.domain.entities import Page, PageWithTranslation
from ocr_module.domain.repositories import IPDFGeneratorRepository


def _convert_inch_bbox_to_pt(
    inch_bbox: Tuple[float, float, float, float]
) -> Tuple[float, float, float, float]:
    return (inch_bbox[0] * 72, inch_bbox[1] * 72, inch_bbox[2] * 72, inch_bbox[3] * 72)


class PyMuPDFGeneratePDFRepository(IPDFGeneratorRepository):
    def __init__(self):
        self._logger = getLogger(__name__)
        self._logger.setLevel(INFO)

    def generate_pdf(self, page: Page, output_path: str):
        """PDFを生成する

        Args:
            page (Page): ページ
            output_path (str): 出力パス
        """
        self._logger.debug(f"Generating PDF with page: {page}")
        paragraphs = page.paragraphs
        document = pymupdf.Document()
        pymupdf_page = document.new_page(width=page.width * 72, height=page.height * 72)
        for paragraph in paragraphs:
            pymupdf_page.insert_htmlbox(
                _convert_inch_bbox_to_pt(paragraph.bbox),
                text=paragraph.content,
            )
        self._logger.debug(f"Inserted {len(paragraphs)} paragraphs")
        for figure in page.figures:
            pymupdf_page.insert_image(
                _convert_inch_bbox_to_pt(figure.bbox),
                stream=figure.image_data,
            )
        self._logger.debug(f"Inserted {len(page.figures)} figures")
        for table in page.tables:
            pymupdf_page.insert_image(
                _convert_inch_bbox_to_pt(table.bbox),
                stream=table.image_data,
            )
        self._logger.debug(f"Inserted {len(page.tables)} tables")
        for display_formula in page.display_formulas:
            pymupdf_page.insert_image(
                _convert_inch_bbox_to_pt(display_formula.bbox),
                stream=display_formula.image_data,
            )
        self._logger.debug(f"Inserted {len(page.display_formulas)} display formulas")
        document.save(output_path, garbage=4, deflate=True, clean=True)

    def generate_pdf_with_translation(
        self, page: PageWithTranslation, output_path: str
    ):
        self._logger.debug(f"Generating PDF with page: {page}")
        paragraphs = page.paragraphs
        document = pymupdf.Document()
        pymupdf_page = document.new_page(width=page.width * 72, height=page.height * 72)
        for paragraph in paragraphs:
            pymupdf_page.insert_htmlbox(
                _convert_inch_bbox_to_pt(paragraph.bbox),
                text=paragraph.translation,
            )
        self._logger.debug(f"Inserted {len(paragraphs)} paragraphs")
        for figure in page.figures:
            pymupdf_page.insert_image(
                _convert_inch_bbox_to_pt(figure.bbox),
                stream=figure.image_data,
            )
        self._logger.debug(f"Inserted {len(page.figures)} figures")
        for table in page.tables:
            pymupdf_page.insert_image(
                _convert_inch_bbox_to_pt(table.bbox),
                stream=table.image_data,
            )
        self._logger.debug(f"Inserted {len(page.tables)} tables")
        for display_formula in page.display_formulas:
            pymupdf_page.insert_image(
                _convert_inch_bbox_to_pt(display_formula.bbox),
                stream=display_formula.image_data,
            )
        self._logger.debug(f"Inserted {len(page.display_formulas)} display formulas")
        document.save(output_path, garbage=4, deflate=True, clean=True)

    def generate_pdf_with_formula_id(self, page: PageWithTranslation, output_path: str):
        paragraphs = page.paragraphs
        document = pymupdf.Document()
        pymupdf_page = document.new_page(width=page.width * 72, height=page.height * 72)
        for paragraph in paragraphs:
            pymupdf_page.insert_htmlbox(
                _convert_inch_bbox_to_pt(paragraph.bbox),
                text=paragraph.translation,
            )
        self._logger.debug(f"Inserted {len(paragraphs)} paragraphs")
        for figure in page.figures:
            pymupdf_page.insert_image(
                _convert_inch_bbox_to_pt(figure.bbox),
                stream=figure.image_data,
            )
        self._logger.debug(f"Inserted {len(page.figures)} figures")
        for table in page.tables:
            pymupdf_page.insert_image(
                _convert_inch_bbox_to_pt(table.bbox),
                stream=table.image_data,
            )
        self._logger.debug(f"Inserted {len(page.tables)} tables")
        for display_formula in page.display_formulas:
            pymupdf_page.insert_image(
                _convert_inch_bbox_to_pt(display_formula.bbox),
                stream=display_formula.image_data,
            )
        self._logger.debug(f"Inserted {len(page.display_formulas)} display formulas")
        document.save(output_path, garbage=4, deflate=True, clean=True)
