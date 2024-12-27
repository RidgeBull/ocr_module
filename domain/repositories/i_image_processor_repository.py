from abc import ABC, abstractmethod
from typing import Tuple


class IImageProcessorRepository(ABC):
    @abstractmethod
    def process_image(self, original_document_path: str, output_document_path: str):
        pass
