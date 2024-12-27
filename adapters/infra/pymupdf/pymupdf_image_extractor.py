from typing import Optional, Tuple
import pymupdf
from logging import getLogger, DEBUG, INFO, ERROR
from ocr.domain.entities import Figure
from ocr.domain.repositories import IImageExtractorRepository


class PyMuPDFImageExtractor(IImageExtractorRepository):
    def __init__(self):
        self.logger = getLogger(__name__)
        self.logger.setLevel(DEBUG)

    def extract_image(self, pdf_path: str, figure: Figure) -> Optional[bytes]:
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
            page = doc.load_page(figure.page_number - 1)
            bbox_pt = (
                figure.bbox[0] * 72,
                figure.bbox[1] * 72,
                figure.bbox[2] * 72,
                figure.bbox[3] * 72,
            )
            image = page.get_pixmap(clip=bbox_pt)
            self.logger.debug(f"Image extracted: {image}")
            print(image)
            print(image.tobytes())
            return image.tobytes()
        except Exception as e:
            self.logger.error(f"Failed to extract image: {e}")
            return None

        finally:
            doc.close()
