from abc import ABC, abstractmethod
from typing import List, Tuple
from ocr.domain.entities import Section, DisplayFormula, SectionWithTranslation


class IPDFGeneratorRepository(ABC):
    @abstractmethod
    def generate_pdf(
        self,
        sections: List[Section],
        page_num: int,
        output_path: str,
        display_formulas: List[DisplayFormula],
        page_size: Tuple[float, float],
    ):
        pass
