from logging import getLogger
from typing import List

from ocr_module.domain.entities import Section
from ocr_module.domain.repositories import IOCRRepository


class GetSectionUseCase:
    def __init__(self, ocr_repository: IOCRRepository):
        self.ocr_repository = ocr_repository
        self.logger = getLogger(__name__)

    def execute(self, document_path: str) -> List[Section]:
        sections = self.ocr_repository.get_sections(document_path)
        for section in sections:
            self.logger.info(f"Section: {section}")
        return sections
