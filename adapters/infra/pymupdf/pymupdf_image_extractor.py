from typing import Optional, Tuple
import pymupdf
from logging import getLogger, DEBUG, INFO, ERROR
from ocr.domain.entities import Figure
from ocr.domain.repositories import IImageExtractorRepository


class PyMuPDFImageExtractor(IImageExtractorRepository):
    def __init__(self):
        self.logger = getLogger(__name__)
        self.logger.setLevel(DEBUG)

    def extract_image(self, pdf_path: str, page_number: int, inch_bbox: Tuple[float, float, float, float]) -> Optional[bytes]:
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
            bbox_pt = (
                inch_bbox[0] * 72,
                inch_bbox[1] * 72,
                inch_bbox[2] * 72,
                inch_bbox[3] * 72,
            )
            matrix = pymupdf.Matrix(2.0, 2.0)
            dpi = 300
            image = page.get_pixmap(clip=bbox_pt, matrix=matrix, dpi=dpi)
            self.logger.debug(f"Image extracted: {image}")
            return image.tobytes()
        except Exception as e:
            self.logger.error(f"Failed to extract image: {e}")
            return None

        finally:
            doc.close()
