from abc import ABC, abstractmethod
from typing import List

from domain.entities import Document, Page, Section


class IOCRRepository(ABC):
    @abstractmethod
    def get_document(self, document_path: str) -> Document:
        """
        ドキュメントを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            Document: ドキュメントの解析結果
        """
        raise NotImplementedError

    @abstractmethod
    def get_pages(self, document_path: str) -> List[Page]:
        """
        ページを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            List[Page]: ページのリスト
        """
        raise NotImplementedError

    @abstractmethod
    def get_sections(self, document_path: str) -> List[Section]:
        """
        セクションを取得する

        Args:
            document_path (str): ドキュメントのパス

        Returns:
            List[Section]: セクションのリスト
        """
        raise NotImplementedError
