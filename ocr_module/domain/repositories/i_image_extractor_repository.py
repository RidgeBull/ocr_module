from abc import ABC, abstractmethod
from typing import Optional, Tuple


class IImageExtractorRepository(ABC):
    """
    OCRの結果から、FigureやTableを画像として取得するためのインターフェース
    """

    # TODO: pdf_fileをtempfileかbytesで読み取れるように変更する
    @abstractmethod
    def extract_image(
        self,
        pdf_path: str,
        page_number: int,
        inch_bbox: Tuple[float, float, float, float],
    ) -> Optional[bytes]:
        """
        PDFから指定された領域の画像を抽出する

        Args:
            pdf_path (str): PDFファイルのパス
            page_number (int): ページ番号
            inch_bbox (Tuple[float, float, float, float]): 画像の位置情報を含むFigureオブジェクト

        Returns:
            Optional[bytes]: 抽出された画像のバイナリデータ。
                           画像が見つからない場合はNone
        """
        raise NotImplementedError
