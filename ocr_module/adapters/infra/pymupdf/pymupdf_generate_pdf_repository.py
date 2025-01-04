from ocr_module.domain.repositories import IPDFGeneratorRepository
from pymupdf import Document
import pymupdf
from logging import getLogger, INFO
from typing import Tuple, List
from ocr_module.domain.entities import (
    Page,
    PageWithTranslation,
    Paragraph,
    ParagraphWithTranslation,
)


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
        document = pymupdf.open()
        document.new_page(width=page.width*72, height=page.height*72)
        for paragraph in paragraphs:
            document = self._insert_paragraph(paragraph, document)
        self._logger.debug(f"Inserted {len(paragraphs)} paragraphs")
        for figure in page.figures:
            document = self._insert_graphic(figure.image_data, document, figure.bbox)
        self._logger.debug(f"Inserted {len(page.figures)} figures")
        for table in page.tables:
            document = self._insert_graphic(table.image_data, document, table.bbox)
        self._logger.debug(f"Inserted {len(page.tables)} tables")
        for display_formula in page.display_formulas:
            document = self._insert_graphic(display_formula.image_data, document, display_formula.bbox)
        self._logger.debug(f"Inserted {len(page.display_formulas)} display formulas")
        document.save(output_path)

    def generate_pdf_with_translation(self, page: PageWithTranslation, output_path: str):
        self._logger.debug(f"Generating PDF with page: {page}")
        paragraphs = page.paragraphs
        document = pymupdf.open()
        document.new_page(width=page.width*72, height=page.height*72)
        for paragraph in paragraphs:
            document = self._insert_paragraph_with_translation(paragraph, document)
        self._logger.debug(f"Inserted {len(paragraphs)} paragraphs")
        for figure in page.figures:
            document = self._insert_graphic(figure.image_data, document, figure.bbox)
        self._logger.debug(f"Inserted {len(page.figures)} figures")
        for table in page.tables:
            document = self._insert_graphic(table.image_data, document, table.bbox)
        for display_formula in page.display_formulas:
            document = self._insert_graphic(display_formula.image_data, document, display_formula.bbox)
        self._logger.debug(f"Inserted {len(page.display_formulas)} display formulas")
        document.save(output_path)

    def generate_pdf_with_formula_id(self, page: PageWithTranslation, output_path: str):
        paragraphs = page.paragraphs
        document = pymupdf.open()
        document.new_page(width=page.width*72, height=page.height*72)
        for paragraph in paragraphs:
            document = self._insert_paragraph_with_formula_id(paragraph, document)
        self._logger.debug(f"Inserted {len(paragraphs)} paragraphs")
        for figure in page.figures:
            document = self._insert_graphic(figure.image_data, document, figure.bbox)
        self._logger.debug(f"Inserted {len(page.figures)} figures")
        for table in page.tables:
            document = self._insert_graphic(table.image_data, document, table.bbox)
        self._logger.debug(f"Inserted {len(page.tables)} tables")
        for display_formula in page.display_formulas:
            document = self._insert_graphic(display_formula.image_data, document, display_formula.bbox)
        self._logger.debug(f"Inserted {len(page.display_formulas)} display formulas")
        document.save(output_path)

    def _insert_paragraph(self, paragraph: Paragraph, document: Document) -> Document:
        self._logger.debug(f"Inserting paragraph: {paragraph}")
        page = document.load_page(0)
        page.insert_htmlbox(
            _convert_inch_bbox_to_pt(paragraph.bbox),
            text=paragraph.content,
        )
        return document
    
    def _insert_paragraph_with_translation(self, paragraph: ParagraphWithTranslation, document: Document) -> Document:
        self._logger.debug(f"Inserting paragraph: {paragraph}")
        page = document.load_page(0)
        page.insert_htmlbox(
            _convert_inch_bbox_to_pt(paragraph.bbox),
            text=paragraph.translation,
        )
        return document

    def _insert_graphic(
        self,
        image_bytes: bytes,
        document: Document,
        inch_bbox: Tuple[float, float, float, float],
    ) -> Document:
        self._logger.debug(f"Inserting graphic: {inch_bbox}")
        page = document.load_page(0)
        page.insert_image(
            _convert_inch_bbox_to_pt(inch_bbox),
            stream=image_bytes,
        )
        return document
