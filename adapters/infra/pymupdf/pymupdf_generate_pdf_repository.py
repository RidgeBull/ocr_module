import pymupdf
import os
from ocr.domain.entities import Section, TextParagraph, Table
from ocr.domain.repositories import IPDFGeneratorRepository
from typing import List, Tuple
from logging import getLogger
import matplotlib.pyplot as plt


def convert_bbox_to_point(
    bbox: Tuple[float, float, float, float]
) -> Tuple[float, float, float, float]:
    return (
        bbox[0] * 72,
        bbox[1] * 72,
        bbox[2] * 72,
        bbox[3] * 72,
    )


class PyMuPDFGeneratePDFRepository(IPDFGeneratorRepository):
    def __init__(self):
        self.logger = getLogger(__name__)
        plt.rc("text", usetex=True)

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
                self._insert_latex_block(paragraph)

    def _insert_paragraph(self, paragraph: TextParagraph):
        page = self.doc[paragraph.page_number - 1]
        # paragraphのtext中の:fromula:を全て置換する
        text = paragraph.text
        for formula in paragraph.inline_formulas:
            text = text.replace(":formula:", formula, 1)
        # bboxはinch単位なので、pointに変換
        bbox = convert_bbox_to_point(paragraph.bbox)
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

    def _insert_latex_block(self, latex_block: TextParagraph):
        # paragraphのtext中の:fromula:を全て置換する
        text = latex_block.text
        for formula in latex_block.inline_formulas:
            text = text.replace(":formula:", formula, 1)
        # textをLaTeX形式に変換
        plt.text(0.5, 0.5, text, fontsize=12)
        plt.axis("off")
        plt.savefig(
            os.path.join(os.path.dirname(__file__), "temp.png"), bbox_inches="tight"
        )
        plt.close()
        page = self.doc[latex_block.page_number - 1]
        bbox = convert_bbox_to_point(latex_block.bbox)
        page.insert_image(
            bbox, filename=os.path.join(os.path.dirname(__file__), "temp.png")
        )
