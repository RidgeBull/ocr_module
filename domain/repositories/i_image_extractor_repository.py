from abc import ABC, abstractmethod
from typing import Optional
from ocr.domain.entities import Figure


class IImageExtractorRepository(ABC):
    """
    画像抽出のためのリポジトリインターフェース
    """

    @abstractmethod
    def extract_image(self, pdf_path: str, figure: Figure) -> Optional[bytes]:
        """
        PDFから指定された領域の画像を抽出する

        Args:
            pdf_path (str): PDFファイルのパス
            figure (Figure): 画像の位置情報を含むFigureオブジェクト

        Returns:
            Optional[bytes]: 抽出された画像のバイナリデータ。
                           画像が見つからない場合はNone
        """
        raise NotImplementedError
