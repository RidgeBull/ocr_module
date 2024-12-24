from .azure_client import AzureDocumentIntelligenceClient
from ocr.domain.entities import *
from ocr.domain.repositories import IOcrRepository
from typing import List, Tuple
from logging import getLogger

from azure.ai.documentintelligence.models import (
    DocumentPage,
    DocumentParagraph,
    DocumentStyle,
    DocumentSpan,
    DocumentFormula,
    DocumentSection,
    DocumentFigure,
    DocumentTable,
)


@dataclass
class _TextLine:
    text: str
    inline_formulas: List[DocumentFormula]
    bbox: tuple  # (xmin, ymin, xmax, ymax)
    font: str
    color_hex: str
    font_weight: Literal["bold", "normal"]
    background_color_hex: str
    span: DocumentSpan


@dataclass
class _TextParagraph:
    text: str
    inline_formulas: List[DocumentFormula]
    lines: List[TextLine]
    bbox: tuple
    page_number: int


def _get_line_style(line_span: DocumentSpan, styles: List[DocumentStyle]) -> dict:
    style_attributes = {
        "font": None,
        "color": None,
        "font_weight": None,
        "background_color": None,
    }

    for style in styles:
        spans = style.spans
        for span in spans:
            if span.offset <= line_span.offset < span.offset + span.length:
                if style.similar_font_family:
                    style_attributes["font"] = style.similar_font_family
                if style.color:
                    style_attributes["color"] = style.color
                if style.font_weight:
                    style_attributes["font_weight"] = style.font_weight
                if style.background_color:
                    style_attributes["background_color"] = style.background_color

    return style_attributes


def _get_bounding_box(polygon: List[float]) -> tuple:
    """_summary_

    Args:
        polygon (List[float]): ポリゴン座標

    Returns:
        tuple: (xmin, ymin, xmax, ymax): バウンディングボックス座標
    """
    x_coordinates = [polygon[i] for i in range(0, len(polygon), 2)]
    y_coordinates = [polygon[i] for i in range(1, len(polygon), 2)]
    return (
        min(x_coordinates),
        min(y_coordinates),
        max(x_coordinates),
        max(y_coordinates),
    )


def _get_textlines_in_paragraph(
    paragraph: DocumentParagraph, text_lines: List[_TextLine]
) -> List[_TextLine]:
    paragraph_span = paragraph.spans[0]
    paragraph_text_lines = [
        text_line
        for text_line in text_lines
        if paragraph_span.offset
        <= text_line.span.offset
        < paragraph_span.offset + paragraph_span.length
    ]
    return paragraph_text_lines


class AzureOcrRepository(IOcrRepository):
    def __init__(self):
        self.client = AzureDocumentIntelligenceClient()
        self.logger = getLogger(__name__)

    def get_sections(self, document_path: str) -> List[Section]:
        print(f"Reading document from path: {document_path}")
        self._read_document(document_path)
        sections = self._get_sections()
        return sections

    def get_page_number(self) -> int:
        return len(self.pages)

    def _read_document(self, document_path: str):
        self.result = self.client.analyze_document_from_document_path(document_path)
        if self.result.sections:
            print(f"Sections: {self.result.sections}")
            self.sections = self.result.sections
        if self.result.paragraphs:
            print(f"Paragraphs: {self.result.paragraphs}")
            self.paragraphs = self.result.paragraphs
        if self.result.figures:
            print(f"Figures: {self.result.figures}")
            self.figures = self.result.figures
        if self.result.tables:
            print(f"Tables: {self.result.tables}")
            self.tables = self.result.tables
        if self.result.pages:
            print(f"Pages: {self.result.pages}")
            self.pages = self.result.pages
        if self.result.styles:
            print(f"Styles: {self.result.styles}")
            self.styles = self.result.styles

    def _analyze_page(
        self, document_page: DocumentPage
    ) -> Tuple[List[_TextLine], List[DocumentFormula]]:
        # ページ内のformulaを取得
        formulas: List[DocumentFormula] = document_page.formulas if document_page.formulas else []

        # inline formulaを取得
        inline_formulas: List[DocumentFormula] = [
            formula for formula in formulas if formula.kind == "inline"
        ]

        # display formulaを取得
        display_formulas: List[DocumentFormula] = [
            formula for formula in formulas if formula.kind == "display"
        ]

        # ページ内のlinesを取得する
        lines = document_page.lines

        # text_linesを取得する
        text_lines: List[_TextLine] = []

        # inline formulaのindexを取得
        current_inline_formula_idx = 0

        # 各lineに対して、styleを取得する
        for line in lines:
            style = _get_line_style(line.spans[0], self.styles)
            num_formula = line.content.count(":formula:")
            line_formulas = inline_formulas[
                current_inline_formula_idx : current_inline_formula_idx + num_formula
            ]
            current_inline_formula_idx += num_formula
            line = _TextLine(
                text=line.content,
                inline_formulas=line_formulas,
                bbox=_get_bounding_box(line.polygon),
                font=style["font"],
                color_hex=style["color"],
                font_weight=style["font_weight"],
                background_color_hex=style["background_color"],
                span=line.spans[0],
            )
            self.logger.info(f"Line: {line.text} with style: {style}")
            text_lines.append(line)

        return text_lines, display_formulas

    @staticmethod
    def _analyze_paragraph(
        paragraph: DocumentParagraph, text_lines: List[_TextLine]
    ) -> _TextParagraph:
        if not paragraph.bounding_regions:
            return _TextParagraph(
                text="",
                inline_formulas=[],
                lines=[],
                bbox=(0, 0, 0, 0),
                page_number=0,
            )
        paragraph_text_lines = _get_textlines_in_paragraph(paragraph, text_lines)
        paragraph_text = "".join([line.text for line in paragraph_text_lines])
        text_paragraph = _TextParagraph(
            text=paragraph_text,
            inline_formulas=[
                formula
                for text_line in paragraph_text_lines
                for formula in text_line.inline_formulas
            ],
            lines=[
                TextLine(
                    text=line.text,
                    inline_formulas=[formula.value for formula in line.inline_formulas],
                    bbox=line.bbox,
                    font=line.font,
                    color_hex=line.color_hex,
                    font_weight=line.font_weight,
                    background_color_hex=line.background_color_hex,
                )
                for line in paragraph_text_lines
            ],
            bbox=_get_bounding_box(paragraph.bounding_regions[0].polygon),
            page_number=paragraph.bounding_regions[0].page_number,
        )
        return text_paragraph

    @staticmethod
    def _analyze_figure(figure: DocumentFigure) -> Figure:
        if not figure.bounding_regions:
            return Figure(
                bbox=(0, 0, 0, 0),
                page_number=0,
                caption=Caption(bbox=(0, 0, 0, 0), content=""),
            )
        bbox = _get_bounding_box(figure.bounding_regions[0].polygon)
        page_number = figure.bounding_regions[0].page_number
        if not figure.caption:
            return Figure(
                bbox=bbox,
                page_number=page_number,
                caption=Caption(bbox=(0, 0, 0, 0), content=""),
            )
        caption = Caption(
            bbox=_get_bounding_box(figure.caption.bounding_regions[0].polygon),
            content=figure.caption.content,
        )
        return Figure(
            bbox=bbox,
            page_number=page_number,
            caption=caption,
        )

    @staticmethod
    def _analyze_table(table: DocumentTable) -> Table:
        if not table.bounding_regions:
            return Table(
                row_num=0,
                col_num=0,
                cells=[],
                bbox=(0, 0, 0, 0),
                page_number=0,
                caption=Caption(bbox=(0, 0, 0, 0), content=""),
            )
        bbox = _get_bounding_box(table.bounding_regions[0].polygon)
        page_number = table.bounding_regions[0].page_number
        cells = [
            Cell(
                row_index=cell.row_index,
                column_index=cell.column_index,
                content=cell.content,
                bbox=_get_bounding_box(cell.bounding_regions[0].polygon),
            )
            for cell in table.cells
        ]
        if not table.caption:
            return Table(
                row_num=table.row_count,
                col_num=table.column_count,
                cells=cells,
                bbox=bbox,
                page_number=page_number,
                caption=Caption(bbox=(0, 0, 0, 0), content=""),
            )
        caption = Caption(
            bbox=_get_bounding_box(table.caption.bounding_regions[0].polygon),
            content=table.caption.content,
        )
        return Table(
            row_num=table.row_count,
            col_num=table.column_count,
            cells=cells,
            bbox=bbox,
            page_number=page_number,
            caption=caption,
        )

    def _analyze_section(self, section: DocumentSection) -> Section:
        if not section.elements:
            return Section(
                paragraphs=[],
                formula_blocks=[],
                tables=[],
                figures=[],
            )
        elements = section.elements
        paragraph_ids = [
            element.split("/")[-1]
            for element in elements
            if element.startswith("/paragraphs/")
        ]
        figure_ids = [
            element.split("/")[-1]
            for element in elements
            if element.startswith("/figures/")
        ]
        table_ids = [
            element.split("/")[-1]
            for element in elements
            if element.startswith("/tables/")
        ]

        paragraphs: List[TextParagraph] = []
        for paragrapj_id in paragraph_ids:
            paragraph = self.paragraphs[int(paragrapj_id)]
            if not paragraph.bounding_regions:
                continue
            page_number = paragraph.bounding_regions[0].page_number
            page = self.pages[page_number - 1]
            text_lines, display_formulas = self._analyze_page(page)
            paragraph = self._analyze_paragraph(paragraph, text_lines)
            paragraphs.append(
                TextParagraph(
                    text=paragraph.text,
                    inline_formulas=[
                        formula.value for formula in paragraph.inline_formulas
                    ],
                    lines=[
                        TextLine(
                            text=line.text,
                            inline_formulas=line.inline_formulas,
                            bbox=line.bbox,
                            font=line.font,
                            color_hex=line.color_hex,
                            font_weight=line.font_weight,
                            background_color_hex=line.background_color_hex,
                        )
                        for line in paragraph.lines
                    ],
                    bbox=paragraph.bbox,
                    page_number=paragraph.page_number,
                )
            )

        figures: List[Figure] = []
        for figure_id in figure_ids:
            figure = self.figures[int(figure_id)]
            figure = self._analyze_figure(figure)
            figures.append(
                Figure(
                    bbox=figure.bbox,
                    page_number=figure.page_number,
                    caption=figure.caption,
                )
            )

        tables: List[Table] = []
        for table_id in table_ids:
            table = self.tables[int(table_id)]
            table = self._analyze_table(table)
            tables.append(
                Table(
                    row_num=table.row_num,
                    col_num=table.col_num,
                    cells=table.cells,
                    bbox=table.bbox,
                    page_number=table.page_number,
                    caption=table.caption,
                )
            )

        return Section(
            paragraphs=paragraphs,
            formula_blocks=[],
            tables=tables,
            figures=figures,
        )

    def _get_sections(self) -> List[Section]:
        sections: List[Section] = []
        for section in self.sections:
            print(f"Analyzing section: {section}")
            try:
                section = self._analyze_section(section)
                sections.append(section)
            except Exception as e:
                self.logger.error(f"Failed to analyze section: {section}", exc_info=True)
        return sections
