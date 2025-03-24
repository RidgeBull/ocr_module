from typing import Tuple, List, Dict, Any, Optional
from ocr_module.domain.repositories import IOCRRepository
from ocr_module.domain.entities import (
    DisplayFormula,
    Document,
    Figure,
    Formula,
    Page,
    Paragraph,
    Section,
    Table,
    OCRUsageStatsConfig,
)
import pymupdf
from logging import DEBUG, INFO, getLogger


class PyMuPDFOCRRepository(IOCRRepository):
    """PyMuPDFを使用したOCRリポジトリクラス
    
    PyMuPDFライブラリを使用してPDFや画像からテキストやテーブルなどの要素を抽出し、
    ドメインエンティティに変換するリポジトリ実装。
    """
    
    def __init__(self):
        """初期化メソッド - ロガーのセットアップ"""
        self._logger = getLogger(__name__)
        self._logger.setLevel(INFO)

    def get_document(self, document_path: str) -> Tuple[Document, OCRUsageStatsConfig]:
        """ドキュメントを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            Tuple[Document, OCRUsageStatsConfig]: ドキュメントと使用統計情報
        """
        self._logger.info(f"ドキュメントを取得: {document_path}")
        document = pymupdf.open(document_path)

        # ファイルタイプに基づいた処理を選択
        if document_path.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff")):
            self._logger.info("画像ファイルを検出、OCRを使用")
            return self._get_document_from_image(document)
        else:
            self._logger.info("PDFファイルを検出、PyMuPDFを使用")
            return self._get_document_from_pdf(document)
        
    def get_pages(self, document_path: str) -> Tuple[List[Page], OCRUsageStatsConfig]:
        """ページを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            Tuple[List[Page], OCRUsageStatsConfig]: ページのリストと使用統計情報
        """
        self._logger.info(f"ページを取得: {document_path}")
        document = pymupdf.open(document_path)
        document_entity, ocr_usage_stats_config = self._get_document_from_pdf(document)
        return document_entity.pages, ocr_usage_stats_config
    
    def get_sections(self, document_path: str) -> Tuple[List[Section], OCRUsageStatsConfig]:
        """セクションを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            Tuple[List[Section], OCRUsageStatsConfig]: セクションのリストと使用統計情報
        """
        self._logger.info(f"セクションを取得: {document_path}")
        document = pymupdf.open(document_path)
        document_entity, ocr_usage_stats_config = self._get_document_from_pdf(document)
        return document_entity.sections, ocr_usage_stats_config

    def _get_document_from_image(
        self, document: pymupdf.Document
    ) -> Tuple[Document, OCRUsageStatsConfig]:
        """画像ファイルからドキュメントを取得する

        Args:
            document (pymupdf.Document): PyMuPDFドキュメントオブジェクト

        Returns:
            Tuple[Document, OCRUsageStatsConfig]: ドキュメントと使用統計情報
        """
        self._logger.info("画像ファイルからドキュメントを取得")
        
        # 各種IDの初期化
        paragraph_id = 0
        figure_id = 0
        table_id = 0
        
        # 結果格納用のリスト
        pages: List[Page] = []
        page_number = 1
        
        # ドキュメント内の各ページを処理
        for page in document:
            try:
                # OCRを使用してテキスト情報を取得
                text_page = page.get_textpage_ocr()
                
                # ページの要素を抽出
                paragraphs, figures, tables, paragraph_id, figure_id, table_id = self._extract_elements_from_ocr(
                    text_page, page_number, paragraph_id, figure_id, table_id
                )
                
                # ページエンティティを作成
                page_entity = self._create_page_entity(
                    page, page_number, paragraphs, figures, tables
                )
                pages.append(page_entity)
                page_number += 1
                
            except Exception as e:
                self._logger.error(f"ページ {page_number} の処理中にエラー: {str(e)}")
        
        # ドキュメントエンティティを作成
        document_entity = Document(
            pages=pages,
            sections=[],  # OCRでは現在セクション情報は取得しない
        )
        
        # 使用統計情報を作成
        ocr_usage_stats_config = OCRUsageStatsConfig(
            page_count=len(pages),
        )
        
        return document_entity, ocr_usage_stats_config
    
    def _extract_elements_from_ocr(
        self, 
        text_page: Any, 
        page_number: int, 
        paragraph_id: int, 
        figure_id: int, 
        table_id: int
    ) -> Tuple[List[Paragraph], List[Figure], List[Table], int, int, int]:
        """OCRテキストページから要素を抽出する

        Args:
            text_page: OCRで生成されたテキストページ
            page_number: 現在のページ番号
            paragraph_id: 段落ID開始値
            figure_id: 図ID開始値
            table_id: テーブルID開始値

        Returns:
            抽出した段落、図、テーブルのリストと更新されたID
        """
        paragraphs: List[Paragraph] = []
        figures: List[Figure] = []
        tables: List[Table] = []
        
        # テキストブロックを処理
        for block in text_page.extractBLOCKS():
            x0, y0, x1, y1, text, block_no, block_type = block
            
            if block_type == 0:  # テキストブロック
                paragraph = Paragraph(
                    paragraph_id=paragraph_id,
                    role="text",
                    content=text,
                    bbox=(x0, y0, x1, y1),
                    page_number=page_number,
                )
                paragraphs.append(paragraph)
                paragraph_id += 1
                
            elif block_type == 1:  # 画像ブロック
                figure = Figure(
                    figure_id=figure_id,
                    bbox=(x0, y0, x1, y1),
                    page_number=page_number,
                    image_data=None,
                    element_paragraph_ids=[],
                )
                figures.append(figure)
                figure_id += 1
        
        return paragraphs, figures, tables, paragraph_id, figure_id, table_id
    
    def _get_document_from_pdf(
        self,
        document: pymupdf.Document
    ) -> Tuple[Document, OCRUsageStatsConfig]:
        """PDFファイルからドキュメントを取得する

        Args:
            document (pymupdf.Document): PyMuPDFドキュメントオブジェクト

        Returns:
            Tuple[Document, OCRUsageStatsConfig]: ドキュメントと使用統計情報
        """
        self._logger.info("PDFファイルからドキュメントを取得")
        
        # テキスト抽出の設定
        text_flags = pymupdf.TEXT_DEHYPHENATE
        
        # 結果格納用のリスト
        pages: List[Page] = []
        all_paragraphs: List[Paragraph] = []
        all_figures: List[Figure] = []
        all_tables: List[Table] = []
        
        # 各種IDの初期化
        paragraph_id = 0
        figure_id = 0
        table_id = 0
        page_number = 1
        
        # ドキュメント内の各ページを処理
        for page in document:
            try:
                # ページからテキスト情報とテーブル情報を取得
                page_dict = page.get_text("dict", text_flags)
                table_finder = page.find_tables()
                
                # ブロック処理
                page_paragraphs, page_figures, paragraph_id, figure_id = self._process_blocks(
                    page_dict.get("blocks", []), page_number, paragraph_id, figure_id
                )
                
                # テーブル処理
                page_tables, table_id = self._process_tables(
                    table_finder, page, page_number, table_id
                )
                
                # 全体リストに追加
                all_paragraphs.extend(page_paragraphs)
                all_figures.extend(page_figures)
                all_tables.extend(page_tables)
                
                # ページエンティティを作成
                page_entity = self._create_page_entity(
                    page, 
                    page_number, 
                    page_paragraphs, 
                    page_figures, 
                    page_tables
                )
                pages.append(page_entity)
                page_number += 1
                
            except Exception as e:
                self._logger.error(f"ページ {page_number} の処理中にエラー: {str(e)}")
        
        # ドキュメントエンティティを作成
        document_entity = Document(
            pages=pages,
            sections=[],  # 現在はセクション情報を取得しない
        )
        
        # 使用統計情報を作成
        ocr_usage_stats_config = OCRUsageStatsConfig(
            page_count=len(pages),
        )
        
        return document_entity, ocr_usage_stats_config
    
    def _process_blocks(
        self, 
        blocks: List[Any], 
        page_number: int, 
        paragraph_id: int, 
        figure_id: int
    ) -> Tuple[List[Paragraph], List[Figure], int, int]:
        """テキストブロックを処理する

        Args:
            blocks: ブロックのリスト
            page_number: 現在のページ番号
            paragraph_id: 段落ID開始値
            figure_id: 図ID開始値

        Returns:
            処理した段落と図のリスト、更新されたID
        """
        paragraphs: List[Paragraph] = []
        figures: List[Figure] = []
        
        for block in blocks:
            if len(block) < 7:  # 必要な要素数を確認
                self._logger.warning(f"不正なブロック形式: {block}")
                continue
                
            x0, y0, x1, y1, text, block_no, block_type = block[:7]
            
            if block_type == 0:  # テキストブロック
                paragraph = Paragraph(
                    paragraph_id=paragraph_id,
                    role="text",
                    content=text,
                    bbox=(x0, y0, x1, y1),
                    page_number=page_number,
                )
                paragraphs.append(paragraph)
                paragraph_id += 1
                
            elif block_type == 1:  # 画像ブロック
                figure = Figure(
                    figure_id=figure_id,
                    bbox=(x0, y0, x1, y1),
                    page_number=page_number,
                    image_data=None,
                    element_paragraph_ids=[],
                )
                figures.append(figure)
                figure_id += 1
        
        return paragraphs, figures, paragraph_id, figure_id
    
    def _process_tables(
        self, 
        table_finder: Any, 
        page: pymupdf.Page, 
        page_number: int, 
        table_id: int
    ) -> Tuple[List[Table], int]:
        """テーブル情報を処理する

        Args:
            table_finder: テーブル検索結果オブジェクト
            page: ページオブジェクト
            page_number: 現在のページ番号
            table_id: テーブルID開始値

        Returns:
            処理したテーブルのリストと更新されたテーブルID
        """
        tables: List[Table] = []
        for table in table_finder.tables:
            try:
                # テーブルの境界ボックスを取得
                bbox = table.bbox
                
                # テーブルエンティティを作成
                table_entity = Table(
                    table_id=table_id,
                    bbox=bbox,
                    page_number=page_number,
                    image_data=None,
                    element_paragraph_ids=[],
                )
                
                tables.append(table_entity)
                table_id += 1
                
            except Exception as e:
                self._logger.error(f"テーブル処理中にエラー: {str(e)}")
        
        return tables, table_id
    
    def _create_page_entity(
        self, 
        page: pymupdf.Page,
        page_number: int, 
        paragraphs: List[Paragraph], 
        figures: List[Figure], 
        tables: List[Table]
    ) -> Page:
        """ページエンティティを作成する

        Args:
            page: PyMuPDFのページオブジェクト
            page_number: ページ番号
            paragraphs: 段落のリスト
            figures: 図のリスト
            tables: テーブルのリスト

        Returns:
            作成されたPageエンティティ
        """
        # ページの寸法情報を取得
        width = page.rect.width
        height = page.rect.height
        
        # ページエンティティを作成して返す
        return Page(
            page_number=page_number,
            width=width,
            height=height,
            paragraphs=paragraphs,
            figures=figures,
            tables=tables,
            formulas=[],  # 現在数式情報は取得しない
            display_formulas=[],  # 現在ディスプレイ数式情報は取得しない
        )