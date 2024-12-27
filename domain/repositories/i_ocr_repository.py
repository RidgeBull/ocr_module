from abc import ABC, abstractmethod
from typing import List, Tuple
from ocr.domain.entities import Section, DisplayFormula

class IOcrRepository(ABC):
    @abstractmethod
    def get_sections(self, document_path: str) -> List[Section]:
        pass

    @abstractmethod
    def get_page_number(self) -> int:
        pass

    @abstractmethod
    def get_page_size(self) -> Tuple[float, float]:
        pass

    @abstractmethod
    def get_display_formulas(self) -> List[DisplayFormula]:
        pass
