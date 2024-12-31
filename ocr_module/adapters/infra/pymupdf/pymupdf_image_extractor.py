from logging import DEBUG, ERROR, INFO, getLogger
from typing import Optional, Tuple

import pymupdf

from domain.entities import Figure
from domain.repositories import IImageExtractorRepository


class PyMuPDFImageExtractor(IImageExtractorRepository):
    def __init__(self):
        self.logger = getLogger(__name__)
        self.logger.setLevel(DEBUG)

    def extract_image(
        self,
        pdf_path: str,
        page_number: int,
        inch_bbox: Tuple[float, float, float, float],
    ) -> Optional[bytes]:
        """
        指定された矩形領域から画像を抽出

        Args:
            pdf_path: PDFファイルのパス
            figure: 画像の位置情報

        Returns:
            bytes: 抽出された画像のバイナリデータ
            None: 画像が見つからない場合
        """
        try:
            doc = pymupdf.open(pdf_path)
            page = doc.load_page(page_number - 1)

            # インチからポイントに変換
            bbox_pt = [x * 72 for x in inch_bbox]

            # 高解像度で抽出
            matrix = pymupdf.Matrix(2.0, 2.0)  # 2倍に拡大
            pix = page.get_pixmap(clip=bbox_pt, matrix=matrix, dpi=300)  # DPIを指定

            return pix.tobytes("png")  # PNG形式で出力

        except Exception as e:
            self.logger.error(f"Failed to extract image: {e}")
            return None

        finally:
            doc.close()
