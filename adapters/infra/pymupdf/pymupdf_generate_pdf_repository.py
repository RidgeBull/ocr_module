import pymupdf
import os
from ocr.domain.entities import Section, TextParagraph, Table
from ocr.domain.repositories import IPDFGeneratorRepository
from typing import List, Tuple
from logging import getLogger
import matplotlib as mpl

mpl.use("pgf")
import matplotlib.pyplot as plt
import japanize_matplotlib
from pylatex import Document, Subsection, Command, Math, TikZ, Axis, Plot, Figure, Matrix, Alignat
from pylatex.utils import bold, italic, NoEscape
from pdf2image import convert_from_path


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
            print(f"formula: {formula}")
            text = text.replace(":formula:", f"${formula}$", 1)
        print(f"compiling {text} to LaTeX")
        output_path = f"output_{latex_block.page_number}_{len(latex_block.lines)}.png"
        self.compile_latex_to_image(text, output_path, (latex_block.bbox[2] - latex_block.bbox[0]), (latex_block.bbox[3] - latex_block.bbox[1]))
        # bboxはinch単位なので、pointに変換
        bbox = convert_bbox_to_point(latex_block.bbox)
        page = self.doc[latex_block.page_number - 1]
        page.insert_image(
            rect=bbox,
            filename=output_path,
        )

    def compile_latex_to_image(
        self, latex: str, output_path: str, width: float, height: float
    ):
        geometry_options = {
            "margin": "0.0in",
        }
        # LaTeXコードをPDFにコンパイル
        doc = Document()
        doc.packages.append(NoEscape(r"\usepackage{amsmath,amssymb,mathrsfs}"))
        doc.append(NoEscape(latex))
        pdf_path = "output.pdf"
        try:
            doc.generate_pdf("output", clean_tex=False)
        except Exception as e:
            self.logger.error(f"Error compiling LaTeX: {e}")
            return
        # PDFを画像に変換
        images = convert_from_path(pdf_path)
        images[0].save(output_path, "PNG")
        return output_path
