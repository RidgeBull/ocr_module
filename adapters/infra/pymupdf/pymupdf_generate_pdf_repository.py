import pymupdf
import os
from ocr.domain.entities import Section, TextParagraph
from ocr.domain.repositories import IPDFGeneratorRepository
from typing import List, Tuple
from logging import getLogger


class PyMuPDFGeneratePDFRepository(IPDFGeneratorRepository):
    def __init__(self):
        self.logger = getLogger(__name__)

    def generate_pdf(self, sections: List[Section], page_num: int, output_path: str):
        self.doc = pymupdf.Document()
        for i in range(page_num):
            self.doc.new_page(i)

        for section in sections:
            self._insert_section(section)

        self.doc.save(os.path.join(output_path), garbage=4, deflate=True, clean=True)
        self.doc.close()
        return output_path

    def _insert_section(self, section: Section):
        if section.paragraphs:
            self.logger.info(f"Inserting {len(section.paragraphs)} paragraphs")
            for paragraph in section.paragraphs:
                self._insert_paragraph(paragraph)

    def _insert_paragraph(self, paragraph: TextParagraph):
        page = self.doc[paragraph.page_number - 1]
        # paragraphのtext中の:fromula:を全て置換する
        text = paragraph.text
        for formula in paragraph.inline_formulas:
            text = text.replace(":formula:", formula, 1)
        # bboxはinch単位なので、pointに変換
        bbox = (
            paragraph.bbox[0] * 72,
            paragraph.bbox[1] * 72,
            paragraph.bbox[2] * 72,
            paragraph.bbox[3] * 72,
        )
        if paragraph.lines:
            css = f"*{{font-family: {paragraph.lines[0].font}; color: {paragraph.lines[0].color_hex}; font-weight: {paragraph.lines[0].font_weight}; background-color: {paragraph.lines[0].background_color_hex};}}"
            page.insert_htmlbox(
                rect=bbox,
                text=text,
                css=css,
            )
        else:
            page.insert_htmlbox(
                rect=bbox,
                text=text,
            )
