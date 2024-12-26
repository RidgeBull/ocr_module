from ocr.domain.repositories import IOcrRepository, IPDFGeneratorRepository
from dataclasses import dataclass
from typing import List
from logging import getLogger


class OCRPDFUseCase:
    def __init__(
        self, ocr_repository: IOcrRepository, pdf_repository: IPDFGeneratorRepository
    ):
        self.ocr_repository = ocr_repository
        self.pdf_repository = pdf_repository
        self.logger = getLogger(__name__)

    def execute(self, document_path: str, output_path: str):
        sections = self.ocr_repository.get_sections(document_path)
        self.logger.info(f"Sections are extracted from {document_path} successfully {sections}")
        page_num = self.ocr_repository.get_page_number()
        display_formulas = self.ocr_repository.get_display_formulas()
        self.logger.info(f"Display formulas are extracted from {document_path} successfully {display_formulas}")
        self.pdf_repository.generate_pdf(sections, page_num, output_path, display_formulas)
        self.logger.info(f"PDF file is generated at {output_path}")
        return output_path
