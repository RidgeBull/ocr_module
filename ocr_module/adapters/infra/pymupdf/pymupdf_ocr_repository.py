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
import traceback  # スタックトレース用
from logging import DEBUG, INFO, getLogger


class PyMuPDFOCRRepository(IOCRRepository):
    """PyMuPDFを使用したOCRリポジトリクラス
    
    PyMuPDFライブラリを使用してPDFや画像からテキストやテーブルなどの要素を抽出し、
    ドメインエンティティに変換するリポジトリ実装。
    """

    def __init__(self):
        """初期化メソッド - ロガーのセットアップ"""
        self._logger = getLogger(__name__)
        self._logger.setLevel(DEBUG)  # DEBUGレベルに設定して詳細なログを出力

    def get_document(self, document_path: str) -> Tuple[Document, OCRUsageStatsConfig]:
        """ドキュメントを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            Tuple[Document, OCRUsageStatsConfig]: ドキュメントと使用統計情報
        """
        self._logger.info(f"ドキュメントを取得: {document_path}")
        try:
            document = pymupdf.open(document_path)
            self._logger.debug(
                f"ドキュメントを開きました: {document_path}, ページ数: {len(document)}"
            )

            # ファイルタイプに基づいた処理を選択
            if document_path.endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff")
            ):
                self._logger.info("画像ファイルを検出、OCRを使用")
                return self._get_document_from_image(document)
            else:
                self._logger.info("PDFファイルを検出、PyMuPDFを使用")
                return self._get_document_from_pdf(document)
        except Exception as e:
            self._logger.error(f"ドキュメント取得中にエラーが発生: {str(e)}")
            self._logger.debug(traceback.format_exc())
            raise

    def get_pages(self, document_path: str) -> Tuple[List[Page], OCRUsageStatsConfig]:
        """ページを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            Tuple[List[Page], OCRUsageStatsConfig]: ページのリストと使用統計情報
        """
        self._logger.info(f"ページを取得: {document_path}")
        try:
            document = pymupdf.open(document_path)
            document_entity, ocr_usage_stats_config = self._get_document_from_pdf(
                document
            )
            return document_entity.pages, ocr_usage_stats_config
        except Exception as e:
            self._logger.error(f"ページ取得中にエラーが発生: {str(e)}")
            self._logger.debug(traceback.format_exc())
            raise

    def get_sections(self, document_path: str) -> Tuple[List[Section], OCRUsageStatsConfig]:
        """セクションを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            Tuple[List[Section], OCRUsageStatsConfig]: セクションのリストと使用統計情報
        """
        self._logger.info(f"セクションを取得: {document_path}")
        try:
            document = pymupdf.open(document_path)
            document_entity, ocr_usage_stats_config = self._get_document_from_pdf(
                document
            )
            return document_entity.sections, ocr_usage_stats_config
        except Exception as e:
            self._logger.error(f"セクション取得中にエラーが発生: {str(e)}")
            self._logger.debug(traceback.format_exc())
            raise

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
                self._logger.debug(f"ページ {page_number} の処理を開始")
                # OCRを使用してテキスト情報を取得
                try:
                    text_page = page.get_textpage_ocr()
                    self._logger.debug(
                        f"ページ {page_number} のOCRテキストページを取得"
                    )
                except Exception as e:
                    self._logger.error(f"OCRテキストページ取得中にエラー: {str(e)}")
                    self._logger.debug(traceback.format_exc())
                    continue

                # ページの要素を抽出
                try:
                    self._logger.debug(f"ページ {page_number} の要素抽出を開始")
                    result = self._extract_elements_from_ocr(
                        text_page, page_number, paragraph_id, figure_id, table_id
                    )
                    self._logger.debug(
                        f"要素抽出結果: {type(result)}, 要素数: {len(result) if isinstance(result, tuple) else 'not tuple'}"
                    )
                    paragraphs, figures, tables, paragraph_id, figure_id, table_id = (
                        result
                    )
                except Exception as e:
                    self._logger.error(f"要素抽出中にエラー: {str(e)}")
                    self._logger.debug(traceback.format_exc())
                    continue

                # ページエンティティを作成
                try:
                    page_entity = self._create_page_entity(
                        page, page_number, paragraphs, figures, tables
                    )
                    pages.append(page_entity)
                    self._logger.debug(f"ページ {page_number} のエンティティを作成")
                except Exception as e:
                    self._logger.error(f"ページエンティティ作成中にエラー: {str(e)}")
                    self._logger.debug(traceback.format_exc())
                    continue

                page_number += 1

            except Exception as e:
                self._logger.error(f"ページ {page_number} の処理中にエラー: {str(e)}")
                self._logger.debug(traceback.format_exc())
                page_number += 1

        # ドキュメントエンティティを作成
        document_entity = Document(
            pages=pages,
            sections=[],  # OCRでは現在セクション情報は取得しない
        )

        # 使用統計情報を作成
        ocr_usage_stats_config = OCRUsageStatsConfig(
            page_count=len(pages),
        )

        self._logger.info(
            f"画像ファイルからドキュメントを取得完了、ページ数: {len(pages)}"
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
        try:
            self._logger.debug("OCRテキストブロックの抽出を開始")
            blocks = text_page.extractBLOCKS()
            self._logger.debug(
                f"抽出されたブロック数: {len(blocks) if blocks else 'None'}"
            )

            for i, block in enumerate(blocks):
                try:
                    if len(block) < 7:
                        self._logger.warning(f"不正なブロック形式 (要素不足): {block}")
                        continue

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
                except Exception as e:
                    self._logger.error(f"ブロック {i} の処理中にエラー: {str(e)}")
        except Exception as e:
            self._logger.error(f"ブロック抽出処理中にエラー: {str(e)}")
            self._logger.debug(traceback.format_exc())

        self._logger.debug(
            f"OCR要素抽出完了 - 段落: {len(paragraphs)}, 図: {len(figures)}, テーブル: {len(tables)}"
        )
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
                self._logger.debug(f"ページ {page_number} の処理を開始")
                # ページからテキスト情報とテーブル情報を取得
                try:
                    self._logger.debug(f"ページ {page_number} のテキスト情報を取得")
                    page_dict = page.get_text("dict", flags=text_flags)
                    self._logger.debug(f"ページ {page_number} のテキスト取得完了")

                    # ページ辞書の内容を検証
                    if not isinstance(page_dict, dict):
                        self._logger.warning(
                            f"ページ辞書が辞書型ではありません: {type(page_dict)}"
                        )
                        continue

                    if "blocks" not in page_dict:
                        self._logger.warning(
                            f"ページ辞書に 'blocks' キーがありません: {page_dict.keys()}"
                        )
                        continue
                except Exception as e:
                    self._logger.error(f"テキスト情報取得中にエラー: {str(e)}")
                    self._logger.debug(traceback.format_exc())
                    continue

                try:
                    self._logger.debug(f"ページ {page_number} のテーブル情報を取得")
                    table_finder = page.find_tables()
                    self._logger.debug(f"テーブルファインダー: {type(table_finder)}")
                    if hasattr(table_finder, "tables"):
                        self._logger.debug(f"テーブル数: {len(table_finder.tables)}")
                except Exception as e:
                    self._logger.error(f"テーブル情報取得中にエラー: {str(e)}")
                    self._logger.debug(traceback.format_exc())
                    table_finder = None

                # ブロック処理
                try:
                    # 構文エラーを修正: page_dict.get["blocks"] -> page_dict.get("blocks", [])
                    blocks = page_dict.get("blocks", [])
                    self._logger.debug(f"ブロック数: {len(blocks)}")

                    # 型情報をログに出力
                    if blocks and len(blocks) > 0:
                        self._logger.debug(f"最初のブロックの型: {type(blocks[0])}")
                        self._logger.debug(
                            f"最初のブロックの要素数: {len(blocks[0]) if isinstance(blocks[0], (list, tuple)) else 'not sequence'}"
                        )

                    # ブロック処理を実行し、戻り値の型を検証
                    result = self._process_blocks(
                        blocks, page_number, paragraph_id, figure_id
                    )
                    self._logger.debug(f"ブロック処理結果の型: {type(result)}")
                    self._logger.debug(
                        f"ブロック処理結果の要素数: {len(result) if isinstance(result, tuple) else 'not tuple'}"
                    )

                    page_paragraphs, page_figures, paragraph_id, figure_id = result
                    self._logger.debug(
                        f"ブロック処理完了 - 段落: {len(page_paragraphs)}, 図: {len(page_figures)}"
                    )
                except Exception as e:
                    self._logger.error(f"ブロック処理中にエラー: {str(e)}")
                    self._logger.debug(traceback.format_exc())
                    page_paragraphs = []
                    page_figures = []

                # テーブル処理
                try:
                    if table_finder:
                        page_tables, table_id = self._process_tables(
                            table_finder, page, page_number, table_id
                        )
                        self._logger.debug(
                            f"テーブル処理完了 - テーブル: {len(page_tables)}"
                        )
                    else:
                        page_tables = []
                except Exception as e:
                    self._logger.error(f"テーブル処理中にエラー: {str(e)}")
                    self._logger.debug(traceback.format_exc())
                    page_tables = []

                # 全体リストに追加
                all_paragraphs.extend(page_paragraphs)
                all_figures.extend(page_figures)
                all_tables.extend(page_tables)

                # ページエンティティを作成
                try:
                    page_entity = self._create_page_entity(
                        page, page_number, page_paragraphs, page_figures, page_tables
                    )
                    pages.append(page_entity)
                    self._logger.debug(f"ページ {page_number} のエンティティを作成")
                except Exception as e:
                    self._logger.error(f"ページエンティティ作成中にエラー: {str(e)}")
                    self._logger.debug(traceback.format_exc())

                page_number += 1

            except Exception as e:
                self._logger.error(f"ページ {page_number} の処理中にエラー: {str(e)}")
                self._logger.debug(traceback.format_exc())
                page_number += 1

        # ドキュメントエンティティを作成
        document_entity = Document(
            pages=pages,
            sections=[],  # 現在はセクション情報を取得しない
        )

        # 使用統計情報を作成
        ocr_usage_stats_config = OCRUsageStatsConfig(
            page_count=len(pages),
        )

        self._logger.info(
            f"PDFファイルからドキュメントを取得完了、ページ数: {len(pages)}"
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
            blocks: ブロックのリスト（辞書型またはタプル型）
            page_number: 現在のページ番号
            paragraph_id: 段落ID開始値
            figure_id: 図ID開始値

        Returns:
            処理した段落と図のリスト、更新されたID
        """
        self._logger.debug(f"テキストブロック処理を開始 - ブロック数: {len(blocks)}")
        paragraphs: List[Paragraph] = []
        figures: List[Figure] = []

        for i, block in enumerate(blocks):
            try:
                # ブロックの形式を判断して処理
                if isinstance(block, dict):
                    # get_text("dict")から返された辞書形式のブロックの処理
                    try:
                        # 必要なキーが存在するか確認
                        if "type" in block:
                            block_type = block.get("type", -1)

                            # ブロックタイプに応じた処理
                            if block_type == 0:  # テキストブロック
                                # テキストブロックの場合、さらに階層があるケースがある
                                if "lines" in block:
                                    text_content = ""
                                    for line in block["lines"]:
                                        if "spans" in line:
                                            for span in line["spans"]:
                                                if "text" in span:
                                                    text_content += span.get("text", "")

                                    # ブロックの境界ボックスを取得
                                    if "bbox" in block:
                                        bbox = block["bbox"]
                                        x0, y0, x1, y1 = bbox

                                        paragraph = Paragraph(
                                            paragraph_id=paragraph_id,
                                            role="text",
                                            content=text_content,
                                            bbox=(x0, y0, x1, y1),
                                            page_number=page_number,
                                        )
                                        paragraphs.append(paragraph)
                                        paragraph_id += 1

                            elif block_type == 1:  # 画像ブロック
                                if "bbox" in block:
                                    bbox = block["bbox"]
                                    x0, y0, x1, y1 = bbox

                                    figure = Figure(
                                        figure_id=figure_id,
                                        bbox=(x0, y0, x1, y1),
                                        page_number=page_number,
                                        image_data=None,
                                        element_paragraph_ids=[],
                                    )
                                    figures.append(figure)
                                    figure_id += 1
                    except Exception as e:
                        self._logger.error(
                            f"辞書型ブロック {i} の処理中にエラー: {str(e)}"
                        )
                        self._logger.debug(f"問題のブロック: {block}")

                elif isinstance(block, (list, tuple)):
                    # 従来のリスト/タプル形式のブロック処理
                    if len(block) < 7:  # 必要な要素数を確認
                        self._logger.warning(
                            f"ブロック {i} の要素数が不足: {len(block)}"
                        )
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
                else:
                    self._logger.warning(
                        f"ブロック {i} は未対応の型です: {type(block)}"
                    )
            except Exception as e:
                self._logger.error(f"ブロック {i} の処理中にエラー: {str(e)}")
                self._logger.debug(traceback.format_exc())

        self._logger.debug(
            f"テキストブロック処理完了 - 段落: {len(paragraphs)}, 図: {len(figures)}"
        )
        # 明示的にタプルとして返す
        return (paragraphs, figures, paragraph_id, figure_id)

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
        self._logger.debug("テーブル処理を開始")
        tables: List[Table] = []

        # テーブルが見つからない場合は空のリストを返す
        if not hasattr(table_finder, "tables") or not table_finder.tables:
            self._logger.debug("テーブルが見つかりませんでした")
            return tables, table_id

        self._logger.debug(f"テーブル数: {len(table_finder.tables)}")
        for i, table in enumerate(table_finder.tables):
            try:
                self._logger.debug(f"テーブル {i} の処理を開始")
                # テーブルの境界ボックスを取得
                if not hasattr(table, "bbox"):
                    self._logger.warning(f"テーブル {i} に bbox 属性がありません")
                    continue

                bbox = table.bbox
                self._logger.debug(f"テーブル {i} の境界ボックス: {bbox}")

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
                self._logger.debug(f"テーブル {i} のエンティティを作成")

            except Exception as e:
                self._logger.error(f"テーブル {i} の処理中にエラー: {str(e)}")
                self._logger.debug(traceback.format_exc())

        self._logger.debug(f"テーブル処理完了 - テーブル数: {len(tables)}")
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
        try:
            width = page.rect.width
            height = page.rect.height
            self._logger.debug(f"ページ寸法: 幅 {width}, 高さ {height}")
        except Exception as e:
            self._logger.error(f"ページ寸法取得中にエラー: {str(e)}")
            self._logger.debug(traceback.format_exc())
            width = 0
            height = 0

        # ページエンティティを作成して返す
        try:
            # 同じページのエンティティのみフィルタリング
            page_paragraphs = [p for p in paragraphs if p.page_number == page_number]
            page_figures = [f for f in figures if f.page_number == page_number]
            page_tables = [t for t in tables if t.page_number == page_number]

            self._logger.debug(
                f"ページエンティティ作成 - 段落: {len(page_paragraphs)}, 図: {len(page_figures)}, テーブル: {len(page_tables)}"
            )

            page_entity = Page(
                page_number=page_number,
                width=width,
                height=height,
                paragraphs=page_paragraphs,
                figures=page_figures,
                tables=page_tables,
                formulas=[],  # 現在数式情報は取得しない
                display_formulas=[],  # 現在ディスプレイ数式情報は取得しない
            )
            return page_entity
        except Exception as e:
            self._logger.error(f"ページエンティティ作成中にエラー: {str(e)}")
            self._logger.debug(traceback.format_exc())
            # エラー時は最小限のページエンティティを返す
            return Page(
                page_number=page_number,
                width=width,
                height=height,
                paragraphs=[],
                figures=[],
                tables=[],
                formulas=[],
                display_formulas=[],
            )
