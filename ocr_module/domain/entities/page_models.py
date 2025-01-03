from dataclasses import asdict, dataclass
from typing import List, Literal, Optional, Tuple


@dataclass
class Formula:
    """
    Formula entity

    :ivar formula_id: ID of the formula.
    :vartype formula_id: int
    :ivar latex_value: LaTeX value of the formula.
    :vartype latex_value: str
    :ivar bbox: Bounding box of the formula.
    :vartype bbox: Tuple[float, float, float, float] (xmin, ymin, xmax, ymax)
    :ivar type: Type of the formula.
    :vartype type: Literal["display", "inline"]
    :ivar page_number: Page number of the formula.
    :vartype page_number: int
    """

    formula_id: int
    latex_value: str
    bbox: Tuple[float, float, float, float]
    type: Literal["display", "inline"]
    page_number: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Formula":
        return cls(**data)


@dataclass
class DisplayFormula:
    """
    Display formula entity

    :ivar formula_id: ID of the formula.
    :vartype formula_id: int
    :ivar latex_value: LaTeX value of the formula.
    :vartype latex_value: str
    :ivar bbox: Bounding box of the formula.
    :vartype bbox: Tuple[float, float, float, float]
    :ivar type: Type of the formula.
    :vartype type: Literal["display"]
    :ivar page_number: Page number of the formula.
    :vartype page_number: int
    :ivar image_data: Image data of the formula.
    :vartype image_data: Optional[bytes]
    """

    formula_id: int
    latex_value: str
    bbox: Tuple[float, float, float, float]
    type: Literal["display"]
    page_number: int
    image_data: Optional[bytes]

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("image_data")
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "DisplayFormula":
        # image_dataのkeyはdataに存在しないことに注意してクラスを生成する
        return cls(**{k: v for k, v in data.items() if k != "image_data"})


@dataclass
@dataclass
class Paragraph:
    """
    Paragraph entity

    :ivar paragraph_id: ID of the paragraph.
    :vartype paragraph_id: int
    :ivar role: Role of the paragraph.
    :vartype role: Optional[str]
    :ivar content: Content of the paragraph. contain :formula:
    :vartype content: str
    :ivar bbox: Bounding box of the paragraph.
    :vartype bbox: Tuple[float, float, float, float]
    :ivar page_number: Page number of the paragraph.
    :vartype page_number: int
    """

    paragraph_id: int
    role: Optional[str]
    content: str
    bbox: Tuple[float, float, float, float]
    page_number: int

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def to_paragraph_with_translation(self) -> "ParagraphWithTranslation":
        return ParagraphWithTranslation(
            paragraph_id=self.paragraph_id,
            role=self.role,
            content=self.content,
            bbox=self.bbox,
            page_number=self.page_number,
            translation=self.content,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Paragraph":
        return cls(**{k: v for k, v in data.items() if k != "image_data"})


@dataclass
class ParagraphWithTranslation:
    """ParagraphWithTranslation entity.

    Args:
        paragraph_id (int): paragraphsのindex番号
        role (Optional[str]): Role of the paragraph.
        content (str): Content of the paragraph.
        bbox (Tuple[float, float, float, float]): Bounding box of the paragraph.
        page_number (int): Page number of the paragraph.
        translation (Optional[str]): Translation of the paragraph.

    Attributes:
        paragraph_id (int): ID of the paragraph.
        role (Optional[str]): Role of the paragraph.
        content (str): Content of the paragraph.
        bbox (Tuple[float, float, float, float]): Bounding box of the paragraph.
        page_number (int): Page number of the paragraph.
        translation (Optional[str]): Translation of the paragraph.
    """

    paragraph_id: int
    role: Optional[str]
    content: str
    bbox: Tuple[float, float, float, float]
    page_number: int
    translation: Optional[str]

    # TODO: original content を保ち、contentに翻訳後のテキストを入れたほうがclass名通りの気がする
    # もしくは以下のようにする? 前者のほうがよさそう
    # ```
    # class ParagraphWithTranslation:
    #     paragraph: Paragraph
    #     translation_content: str
    # ```
    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "ParagraphWithTranslation":
        return cls(**data)


@dataclass
class Figure:
    """
    Figure entity

    :ivar figure_id: ID of the figure.
    :vartype figure_id: int
    :ivar bbox: Bounding box of the figure.
    :vartype bbox: Tuple[float, float, float, float]
    :ivar page_number: Page number of the figure.
    :vartype page_number: int
    :ivar image_data: Image data of the figure.
    :vartype image_data: Optional[bytes]
    """

    figure_id: int
    bbox: Tuple[float, float, float, float]
    page_number: int
    image_data: Optional[bytes]

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("image_data")
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Figure":
        return cls(**{k: v for k, v in data.items() if k != "image_data"})


@dataclass
class Table:
    """
    Table entity

    :ivar table_id: ID of the table.
    :vartype table_id: int
    :ivar bbox: Bounding box of the table.
    :vartype bbox: Tuple[float, float, float, float]
    :ivar page_number: Page number of the table.
    :vartype page_number: int
    :ivar image_data: Image data of the table.
    :vartype image_data: Optional[bytes]
    """

    table_id: int
    bbox: Tuple[float, float, float, float]
    page_number: int
    image_data: Optional[bytes]

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("image_data")
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Table":
        return cls(**{k: v for k, v in data.items() if k != "image_data"})


@dataclass
class Page:
    """
    Page entity

    :ivar page_number: Page number of the page.
    :vartype page_number: int
    :ivar width: Width of the page.
    :vartype width: float
    :ivar height: Height of the page.
    :vartype height: float
    :ivar formulas: List of formulas in the page.
    :vartype formulas: List[Formula]
    :ivar display_formulas: List of display formulas in the page.
    :vartype display_formulas: List[DisplayFormula]
    :ivar paragraphs: List of paragraphs in the page.
    :vartype paragraphs: List[Paragraph]
    :ivar figures: List of figures in the page.
    :vartype figures: List[Figure]
    :ivar tables: List of tables in the page.
    :vartype tables: List[Table]
    """

    page_number: int
    width: float
    height: float
    formulas: List[Formula]
    display_formulas: List[DisplayFormula]
    paragraphs: List[Paragraph]
    figures: List[Figure]
    tables: List[Table]

    def to_dict(self) -> dict:
        return dict(
            page_number=self.page_number,
            width=self.width,
            height=self.height,
            formulas=[formula.to_dict() for formula in self.formulas],
            display_formulas=[
                display_formula.to_dict() for display_formula in self.display_formulas
            ],
            paragraphs=[paragraph.to_dict() for paragraph in self.paragraphs],
            figures=[figure.to_dict() for figure in self.figures],
            tables=[table.to_dict() for table in self.tables],
        )

    def to_page_with_translation(self) -> "PageWithTranslation":
        return PageWithTranslation(
            page_number=self.page_number,
            width=self.width,
            height=self.height,
            paragraphs=[
                paragraph.to_paragraph_with_translation()
                for paragraph in self.paragraphs
            ],
            formulas=self.formulas,
            display_formulas=self.display_formulas,
            figures=self.figures,
            tables=self.tables,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Page":
        return cls(
            page_number=data["page_number"],
            width=data["width"],
            height=data["height"],
            formulas=[Formula.from_dict(f) for f in data["formulas"]],
            display_formulas=[
                DisplayFormula.from_dict(df) for df in data["display_formulas"]
            ],
            paragraphs=[Paragraph.from_dict(p) for p in data["paragraphs"]],
            figures=[Figure.from_dict(f) for f in data["figures"]],
            tables=[Table.from_dict(t) for t in data["tables"]],
        )


@dataclass
class PageWithTranslation:
    """
    Page with translation entity

    :ivar page_number: Page number of the page.
    :vartype page_number: int
    :ivar width: Width of the page.
    :vartype width: float
    :ivar height: Height of the page.
    :vartype height: float
    :ivar paragraphs: List of paragraphs in the page.
    :vartype paragraphs: List[ParagraphWithTranslation]
    :ivar formulas: List of formulas in the page.
    :vartype formulas: List[Formula]
    :ivar display_formulas: List of display formulas in the page.
    :vartype display_formulas: List[DisplayFormula]
    :ivar figures: List of figures in the page.
    :vartype figures: List[Figure]
    :ivar tables: List of tables in the page.
    :vartype tables: List[Table]
    """

    page_number: int
    width: float
    height: float
    paragraphs: List[ParagraphWithTranslation]
    formulas: List[Formula]
    display_formulas: List[DisplayFormula]
    figures: List[Figure]
    tables: List[Table]

    def to_dict(self) -> dict:
        return dict(
            page_number=self.page_number,
            width=self.width,
            height=self.height,
            paragraphs=[paragraph.to_dict() for paragraph in self.paragraphs],
            formulas=[formula.to_dict() for formula in self.formulas],
            display_formulas=[
                display_formula.to_dict() for display_formula in self.display_formulas
            ],
            figures=[figure.to_dict() for figure in self.figures],
            tables=[table.to_dict() for table in self.tables],
        )

    @classmethod
    def from_dict(cls, data: dict) -> "PageWithTranslation":
        return cls(
            page_number=data["page_number"],
            width=data["width"],
            height=data["height"],
            paragraphs=[
                ParagraphWithTranslation.from_dict(p) for p in data["paragraphs"]
            ],
            formulas=[Formula.from_dict(f) for f in data["formulas"]],
            display_formulas=[
                DisplayFormula.from_dict(df) for df in data["display_formulas"]
            ],
            figures=[Figure.from_dict(f) for f in data["figures"]],
            tables=[Table.from_dict(t) for t in data["tables"]],
        )
