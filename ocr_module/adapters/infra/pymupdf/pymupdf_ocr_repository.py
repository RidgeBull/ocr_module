from typing import Tuple, List, Dict, Any, Optional
from ocr_module.domain.repositories import IOCRRepository
from ocr_module.domain.entities import (
    Document,
    Figure,
    Page,
    Paragraph,
    Section,
    Table,
    OCRUsageStatsConfig,
)
import pymupdf
from logging import DEBUG, getLogger

class PyMuPDFOCRRepository(IOCRRepository):
    """PyMuPDFを使用したOCRリポジトリクラス
    
    PyMuPDFライブラリを使用してPDFや画像からテキストやテーブルなどの要素を抽出し、
    ドメインエンティティに変換するリポジトリ実装。
    """
    def __init__(self):
        self._logger = getLogger(__name__)
        self._logger.setLevel(DEBUG)  # DEBUGレベルに設定して詳細なログを出力

    def get_document(self, document_path: str) -> Tuple[Document, OCRUsageStatsConfig]:
        """ドキュメントを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            Tuple[Document, OCRUsageStatsConfig]: ドキュメントと使用統計情報
        """

        # 1. ドキュメントを開く
        document = pymupdf.open(document_path)
        self._logger.debug(f"ドキュメントを開きました: {document_path}, ページ数: {len(document)}")

        # データを格納する変数を定義
        pages: List[Page] = []
        sections: List[Section] = []
        paragraphs: List[Paragraph] = []
        paragraph_id: int = 0
        figures: List[Figure] = []
        figure_id: int = 0
        tables: List[Table] = []
        table_id: int = 0
        page_number: int = 1

        # ページごとに処理を行う
        for page in document:
            text_page = page.get_textpage()

            # 段落と図のリストを取得
            paragraphs, figures = self._get_paragraphs_figures_from_text_page(
                text_page,
                page.rect.width,
                page.rect.height,
                page_number,
                paragraph_id,
                figure_id,
            )
            paragraphs.extend(paragraphs)
            figures.extend(figures)
            paragraph_id += len(paragraphs)
            figure_id += len(figures)

            tables = self._get_tables_from_page(
                page,
                page_number,
                table_id,
            )
            tables.extend(tables)
            table_id += len(tables)

            # ページエンティティを作成
            page_entity = Page(
                width=page.rect.width,
                height=page.rect.height,
                page_number=page_number,
                paragraphs=paragraphs,
                figures=figures,
                tables=tables,
                formulas=[],
                display_formulas=[],
            )

            # セクションエンティティを作成
            section_entity = Section(
                section_id=page_number,
                paragraphs=paragraphs,
                paragraph_ids=[p.paragraph_id for p in paragraphs],
                tables=tables,
                table_ids=[t.table_id for t in tables],
                figures=figures,
                figure_ids=[f.figure_id for f in figures],
            )

            sections.append(section_entity)
            pages.append(page_entity)
            page_number += 1

        # ドキュメントエンティティを作成
        document_entity = Document(
            pages=pages,
            sections=sections,
        )

        return document_entity, OCRUsageStatsConfig(page_count=len(pages))

    def get_pages(self, document_path: str) -> Tuple[List[Page], OCRUsageStatsConfig]:
        """ページを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            Tuple[List[Page], OCRUsageStatsConfig]: ページのリストと使用統計情報
        """

        document_entity, ocr_usage_stats_config = self.get_document(document_path)
        return document_entity.pages, ocr_usage_stats_config

    def get_sections(self, document_path: str) -> Tuple[List[Section], OCRUsageStatsConfig]:
        """セクションを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            Tuple[List[Section], OCRUsageStatsConfig]: セクションのリストと使用統計情報
        """
        document_entity, ocr_usage_stats_config = self.get_document(document_path)
        return document_entity.sections, ocr_usage_stats_config

    # テキストページからテーブルのリストを取得する
    @staticmethod
    def _get_tables_from_page(
        page: pymupdf.Page,
        page_number: int,
        current_table_id: int,
    ) -> List[Table]:
        """テーブルのリストを取得する

        Args:
            page: pymupdf.Page
            page_number: ページ番号
            current_table_id: 現在のテーブルID

        Returns:
            List[Table]: テーブルのリスト
        """
        tables: List[Table] = []
        table_finder = page.find_tables(strategy="lines")

        for table in table_finder.tables:
            bbox = table.bbox
            table_entity = Table(
                table_id=current_table_id,
                bbox=bbox,
                page_number=page_number,
                element_paragraph_ids=[],
                image_data=None,
            )
            tables.append(table_entity)
            current_table_id += 1

        return tables

    # テキストページから段落と図のリストを取得する
    @staticmethod
    def _get_paragraphs_figures_from_text_page(
        text_page: pymupdf.TextPage,
        width: float,
        height: float,
        page_number: int,
        current_paragraph_id: int,
        current_figure_id: int,
    ) -> Tuple[List[Paragraph], List[Figure]]:
        """ページエンティティを作成する

        Args:
            page: PyMuPDFのページオブジェクト
            page_number: ページ番号

        Returns:
            段落と図のリスト
        """

        # 取得したブロックを格納するリストを定義する
        paragraphs: List[Paragraph] = []
        figures: List[Figure] = []

        # 1. ページ内のテキストブロック・画像ブロックを取得して処理する
        blocks = text_page.extractBLOCKS()

        for block in blocks:
            x0, y0, x1, y1, block_content, block_no, block_type = block

            # 画像ブロックの場合
            if block_type == 1:
                # 図のエンティティを作成
                figure_entity = Figure(
                    figure_id=current_figure_id,
                    # ページの幅と高さを比較して、バウンディングボックスを作成
                    bbox=(
                        (x0, y0, x1, y1)
                        if width < height
                        else (width - y1, x0, width - y0, x1)
                    ),
                    page_number=page_number,
                    image_data=None,
                    element_paragraph_ids=[],
                )
                figures.append(figure_entity)
                current_figure_id += 1

            # テキストブロックの場合
            elif block_type == 0:
                # 段落のエンティティを作成
                paragraph_entity = Paragraph(
                    paragraph_id=current_paragraph_id,
                    # ページの幅と高さを比較して、バウンディングボックスを作成
                    bbox=(
                        (x0, y0, x1, y1)
                        if width < height
                        else (width - y1, x0, width - y0, x1)
                    ),
                    page_number=page_number,
                    role=None,
                    content=block_content,
                )
                paragraphs.append(paragraph_entity)
                current_paragraph_id += 1

        return paragraphs, figures
