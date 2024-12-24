from abc import ABC, abstractmethod
from typing import List
from ocr.domain.entities import Section


class IPDFGeneratorRepository(ABC):
    @abstractmethod
    def generate_pdf(
        self, sections: List[Section], page_num: int, output_path: str
    ):
        pass
