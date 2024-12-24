from dataclasses import dataclass
from typing import List, Optional, Literal

@dataclass
class Section:
    """
    Section entity

    :ivar paragraphs: List of paragraphs in the section.
    :vartype paragraphs: List[TextParagraph]
    :ivar formula_blocks: List of display formulas in the section.
    :vartype formula_blocks: List[DisplayFormula]
    :ivar tables: List of tables in the section.
    :vartype tables: List[Table]
    :ivar figures: List of figures in the section.
    :vartype figures: List[Figure]
    """
    paragraphs: List['TextParagraph']
    formula_blocks: List['DisplayFormula']
    tables: List['Table']
    figures: List['Figure']

@dataclass
class TextParagraph:
    """
    TextParagraph entity

    :ivar text: The text content of the paragraph.
    :vartype text: str
    :ivar inline_formulas: List of inline formulas in the text.
    :vartype inline_formulas: List[str]
    :ivar lines: List of text lines in the paragraph.
    :vartype lines: List[TextLine]
    :ivar bbox: Bounding box of the paragraph.
    :vartype bbox: tuple
    :ivar page_number: Page number where the paragraph is located.
    :vartype page_number: int
    """
    text: str  # :formula:がプレースホルダーとなっている状態
    inline_formulas: List[str]
    lines: List['TextLine']
    bbox: tuple
    page_number: int

@dataclass
class TextLine:
    """
    TextLine entity

    :ivar text: The text content of the line.
    :vartype text: str
    :ivar inline_formulas: List of inline formulas in the text.
    :vartype inline_formulas: List[str]
    :ivar bbox: Bounding box of the line.
    :vartype bbox: tuple
    :ivar font: Font used in the text line.
    :vartype font: str
    :ivar color_hex: Color of the text in hexadecimal format.
    :vartype color_hex: str
    :ivar font_weight: Weight of the font (bold or normal).
    :vartype font_weight: Literal['bold', 'normal']
    :ivar background_color_hex: Background color of the text in hexadecimal format.
    :vartype background_color_hex: str
    """
    text: str
    inline_formulas: List[str]
    bbox: tuple
    font: str
    color_hex: str
    font_weight: Literal['bold', 'normal']
    background_color_hex: str

@dataclass
class DisplayFormula:
    """
    DisplayFormula entity

    :ivar latex_value: LaTeX representation of the formula.
    :vartype latex_value: str
    :ivar bbox: Bounding box of the formula.
    :vartype bbox: tuple
    :ivar page_number: Page number where the formula is located.
    :vartype page_number: int
    """
    latex_value: str
    bbox: tuple
    page_number: int

@dataclass
class Table:
    """
    Table entity

    :ivar row_num: Number of rows in the table.
    :vartype row_num: int
    :ivar col_num: Number of columns in the table.
    :vartype col_num: int
    :ivar cells: List of cells in the table.
    :vartype cells: List[Cell]
    :ivar bbox: Bounding box of the table.
    :vartype bbox: tuple
    :ivar page_number: Page number where the table is located.
    :vartype page_number: int
    :ivar caption: Caption of the table.
    :vartype caption: Optional[Caption]
    """
    row_num: int
    col_num: int
    cells: List['Cell']
    bbox: tuple
    page_number: int
    caption: Optional['Caption']

@dataclass
class Cell:
    """
    Cell entity

    :ivar row_index: Row index of the cell.
    :vartype row_index: int
    :ivar column_index: Column index of the cell.
    :vartype column_index: int
    :ivar content: Content of the cell.
    :vartype content: str
    :ivar bbox: Bounding box of the cell.
    :vartype bbox: tuple
    """
    row_index: int
    column_index: int
    content: str
    bbox: tuple

@dataclass
class Figure:
    """
    Figure entity

    :ivar bbox: Bounding box of the figure.
    :vartype bbox: tuple
    :ivar page_number: Page number where the figure is located.
    :vartype page_number: int
    :ivar caption: Caption of the figure.
    :vartype caption: Optional[Caption]
    """
    bbox: tuple
    page_number: int
    caption: Optional['Caption']

@dataclass
class Caption:
    """
    Caption entity

    :ivar bbox: Bounding box of the caption.
    :vartype bbox: tuple
    :ivar content: Content of the caption.
    :vartype content: str
    """
    bbox: tuple
    content: str
