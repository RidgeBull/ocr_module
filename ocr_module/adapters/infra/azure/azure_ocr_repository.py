import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Dict, List, Literal, Tuple

from azure.ai.documentintelligence.models import (
    DocumentFigure,
    DocumentFormula,
    DocumentPage,
    DocumentParagraph,
    DocumentSection,
    DocumentSpan,
    DocumentStyle,
    DocumentTable,
)

from ocr_module.domain.entities import (
    Caption,
    Cell,
    DisplayFormula,
    Figure,
    Section,
    Table,
    TextLine,
    TextParagraph,
)
from ocr_module.domain.repositories import IImageExtractorRepository, IOcrRepository
from utils.logger import setup_function_logger

from .azure_client import AzureDocumentIntelligenceClient


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
    bbox: tuple
    page_number: int


@dataclass
class _TextParagraphWithLatex:
    paragraph_index: int
    text: str
    inline_formulas: List[str]
    page_number: int
    bbox: tuple


@dataclass
class DocumentParagraphWithIndex:
    def __init__(self, paragraph: DocumentParagraph, index: int):
        self.paragraph = paragraph
        self.index = index


@dataclass
class _Page:
    text_lines: List[_TextLine]
    display_formulas: List[DisplayFormula]
    text_paragraphs: List[_TextParagraph]
    tables: List[Table]
    figures: List[Figure]


def _get_bounding_box(polygon: List[float]) -> tuple:
    x_coordinates = [polygon[i] for i in range(0, len(polygon), 2)]
    y_coordinates = [polygon[i] for i in range(1, len(polygon), 2)]
    return (
        min(x_coordinates),
        min(y_coordinates),
        max(x_coordinates),
        max(y_coordinates),
    )


class DevAzureOcrRepository(IOcrRepository):
    def __init__(self, image_extractor: IImageExtractorRepository):
        self.client = AzureDocumentIntelligenceClient()
        self.image_extractor = image_extractor
        self.logger = getLogger(__name__)
        self.analyze_section_logger = setup_function_logger("analyze_section")
        self.analyze_page_logger = setup_function_logger("analyze_page")
        self.analyze_paragraph_logger = setup_function_logger("analyze_paragraph")
        self.get_line_style_logger = setup_function_logger("get_line_style")
        self.get_textlines_logger = setup_function_logger("get_textlines")

        # ページ解析結果をキャッシュするための辞書
        # { page_number: {"text_lines": [...], "display_formulas": [...]} }
        self._page_cache = {}

    def get_sections(self, document_path: str) -> List[Section]:
        self.document_path = document_path
        pages, paragraphs, sections, tables, figures = self._ocr_document(document_path)
        self.page_number = len(pages)
        # (page_number, DocumentFormula)
        all_formulas: List[Tuple[int, DocumentFormula]] = []
        for page in pages:
            for formula in page.formulas or []:
                all_formulas.append((page.page_number, formula))
        self.display_formulas = [
            DisplayFormula(
                latex_value=formula.value,
                bbox=_get_bounding_box(formula.polygon or []),
                page_number=page_number,
            )
            for page_number, formula in all_formulas
        ]
        self.page_size = pages[0].width or 0, pages[0].height or 0
        # paragraphsのうちroleがないものを抽出
        paragraphs_without_role = [
            paragraph for paragraph in paragraphs if paragraph.role is None
        ]
        text_paragraphs_with_latex_list = self._convert_text_paragraphs_to_latex(
            paragraphs_without_role, pages
        )
        sections_list = []
        for section in sections:
            sections_list.append(
                self._analyze_section(
                    section, text_paragraphs_with_latex_list, tables, figures
                )
            )
        return sections_list

    def get_page_number(self) -> int:
        return self.page_number

    def get_display_formulas(self) -> List[DisplayFormula]:
        return self.display_formulas

    def get_page_size(self) -> Tuple[int, int]:
        return self.page_size

    def _ocr_document(self, document_path: str) -> Tuple[
        List[DocumentPage],
        List[DocumentParagraph],
        List[DocumentSection],
        List[DocumentTable],
        List[DocumentFigure],
    ]:
        """ドキュメントをOCR処理し、構造化されたデータを取得する

        Args:
            document_path (str): 処理対象のドキュメントパス

        Returns:
            Tuple[List[DocumentPage], ...]: ページ、パラグラフ、セクション、テーブル、図のリスト
        """
        result = self.client.analyze_document_from_document_path(document_path)
        return (
            result.pages or [],
            result.paragraphs or [],
            result.sections or [],
            result.tables or [],
            result.figures or [],
        )

    def _analyze_page_paragraphs(
        self, page: DocumentPage, paragraphs: List[DocumentParagraphWithIndex]
    ) -> List[_TextParagraphWithLatex]:
        """ページ内のパラグラフを解析し、LaTeX形式の数式を含むテキストに変換する

        Args:
            page (DocumentPage): 解析対象のページ
            paragraphs (List[DocumentParagraphWithIndex]): インデックス付きのパラグラフリスト

        Returns:
            List[_TextParagraphWithLatex]: LaTeX形式の数式を含むパラグラフのリスト
        """
        text_paragraphs_with_latex: List[_TextParagraphWithLatex] = []
        inline_formulas = [
            formula for formula in page.formulas if formula.kind == "inline"
        ]
        current_formula_index = 0
        for paragraph in paragraphs:
            text = paragraph.paragraph.content
            bbox = _get_bounding_box(paragraph.paragraph.bounding_regions[0].polygon)
            page_number = paragraph.paragraph.bounding_regions[0].page_number
            num_formulas = text.count(":formula:")
            line_formulas = inline_formulas[
                current_formula_index : current_formula_index + num_formulas
            ]
            current_formula_index += num_formulas
            text_paragraphs_with_latex.append(
                _TextParagraphWithLatex(
                    paragraph.index,
                    text,
                    [formula.value for formula in line_formulas],
                    page_number,
                    bbox,
                )
            )
        return text_paragraphs_with_latex

    def _convert_text_paragraphs_to_latex(
        self, text_paragraphs: List[DocumentParagraph], pages: List[DocumentPage]
    ) -> List[_TextParagraphWithLatex]:
        """全パラグラフをページごとにLaTeX形式に変換する

        Args:
            text_paragraphs (List[DocumentParagraph]): 変換対象のパラグラフリスト
            pages (List[DocumentPage]): ドキュメントのページリスト

        Returns:
            List[_TextParagraphWithLatex]: LaTeX形式パラグラフのリスト
        """
        text_paragraphs_with_latex_list: List[_TextParagraphWithLatex] = []
        document_paragraphs_with_index = [
            DocumentParagraphWithIndex(paragraph, index)
            for index, paragraph in enumerate(text_paragraphs)
        ]
        for page_number, page in enumerate(pages):
            page_paragraphs_with_index = [
                paragraph
                for paragraph in document_paragraphs_with_index
                if paragraph.paragraph.bounding_regions[0].page_number
                == page_number + 1
            ]
            text_paragraphs_with_latex = self._analyze_page_paragraphs(
                page, page_paragraphs_with_index
            )
            text_paragraphs_with_latex_list.extend(text_paragraphs_with_latex)
        return text_paragraphs_with_latex_list

    def _analyze_section(
        self,
        section: DocumentSection,
        text_paragraphs_with_latex_list: List[_TextParagraphWithLatex],
        tables: List[DocumentTable],
        figures: List[DocumentFigure],
    ) -> Section:
        """ドキュメントのセクションを解析する

        Args:
            section (DocumentSection): 解析対象のセクション
            text_paragraphs_with_latex_list (List[_TextParagraphWithLatex]): LaTeX形式パラグラフのリスト
            tables (List[DocumentTable]): ドキュメントのテーブルリスト
            figures (List[DocumentFigure]): ドキュメントの図リスト
            display_formulas (List[DocumentFormula]): ドキュメントの数式リスト

        Returns:
            Section: 解析済みのセクション
        """
        if not section.elements:
            return Section(paragraphs=[], formula_blocks=[], tables=[], figures=[])

        # 要素のID抽出
        elements = section.elements
        paragraph_ids = [
            int(element.split("/")[-1])
            for element in elements
            if element.startswith("/paragraphs/")
        ]
        figure_ids = [
            int(element.split("/")[-1])
            for element in elements
            if element.startswith("/figures/")
        ]
        table_ids = [
            int(element.split("/")[-1])
            for element in elements
            if element.startswith("/tables/")
        ]

        # パラグラフの処理
        paragraphs = [
            TextParagraph(
                text=text_paragraphs_with_latex.text,
                inline_formulas=text_paragraphs_with_latex.inline_formulas,
                lines=[],
                bbox=text_paragraphs_with_latex.bbox,
                page_number=text_paragraphs_with_latex.page_number,
            )
            for text_paragraphs_with_latex in text_paragraphs_with_latex_list
            if text_paragraphs_with_latex.paragraph_index in paragraph_ids
        ]

        # 図の処理
        section_figures: List[Figure] = []
        for fid in figure_ids:
            figure = figures[fid]
            if not figure.bounding_regions:
                continue

            bbox = _get_bounding_box(figure.bounding_regions[0].polygon)
            page_number = figure.bounding_regions[0].page_number

            # キャプションの処理
            caption = Caption(bbox=(0, 0, 0, 0), content="")
            if figure.caption and figure.caption.bounding_regions:
                caption = Caption(
                    bbox=_get_bounding_box(figure.caption.bounding_regions[0].polygon),
                    content=figure.caption.content,
                )

            # 画像データの抽出
            image_data = self.image_extractor.extract_image(
                self.document_path,
                page_number,
                bbox,
            )

            section_figures.append(
                Figure(
                    bbox=bbox,
                    page_number=page_number,
                    caption=caption,
                    image_data=image_data,
                )
            )

        # テーブルの処理
        section_tables: List[Table] = []
        for tid in table_ids:
            table = tables[tid]
            if not table.bounding_regions:
                continue

            bbox = _get_bounding_box(table.bounding_regions[0].polygon)
            page_number = table.bounding_regions[0].page_number

            # セルの処理
            cells = []
            for cell in table.cells:
                if not cell.bounding_regions:
                    continue
                cell_bbox = _get_bounding_box(cell.bounding_regions[0].polygon)
                cells.append(
                    Cell(
                        row_index=cell.row_index,
                        column_index=cell.column_index,
                        content=cell.content,
                        bbox=cell_bbox,
                    )
                )

            # キャプションの処理
            caption = Caption(bbox=(0, 0, 0, 0), content="")
            if table.caption and table.caption.bounding_regions:
                caption = Caption(
                    bbox=_get_bounding_box(table.caption.bounding_regions[0].polygon),
                    content=table.caption.content,
                )

            # 画像データの抽出
            image_data = self.image_extractor.extract_image(
                self.document_path,
                page_number,
                bbox,
            )

            section_tables.append(
                Table(
                    row_num=table.row_count,
                    col_num=table.column_count,
                    cells=cells,
                    bbox=bbox,
                    page_number=page_number,
                    caption=caption,
                    image_data=image_data,
                )
            )

        return Section(
            paragraphs=paragraphs,
            figures=section_figures,
            tables=section_tables,
            formula_blocks=[],  # 今回は空のまま
        )
