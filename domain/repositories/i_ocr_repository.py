from abc import ABC, abstractmethod
from typing import List
from ocr.domain.entities import Section

class IOcrRepository(ABC):
    @abstractmethod
    def get_sections(self, document_path: str) -> List[Section]:
        pass

    @abstractmethod
    def get_page_number(self) -> int:
        pass