# 翻訳手順

## Azure OCR

### 得られる結果

**lines = List[line]**
* page_number: int
* content: str（`:formula`を含む）
* span: dict（`offset`と`length`を含む）

**formulas**
* type: Literal[`inline`, `display`]
* value: str（latexコード）
* page_number: int
* 

**paragraphs = List[Paragraph]**
* page_number: int
* content: str
* bounding_polygon: tuple

**tables = List[Table]**
* page_number: int
* elements: List[Paragraph]

**figures = List[Figure]**
* page_number: int
* elements: List[Paragraph]

**sections = List[section]**
* elements: List["/paragraps/0", "/tables/0", "/figures/0", "/sections/0"]



## エンティティの設計案
```python
class Section:
    paragraphs: list[Paragraph]
    formula_blocks: list[Display_Formula]
    tables: list[Table]
    figures: list[Figure]

class TextParagraph:
    text: str # :formula:がプレースホルダーとなっている状態
    inline_formulas: list[str]
    lines: list[TextLine]
    bbox: tuple
    page_number: int

class TextLine:
    text: str
    inline_formulas: list[str]
    bbox: tuple
    font: str
    color_hex: str
    font_weight: Literal[bold, normal]
    background_color_hex: str


class Display_Formula:
    latex_value: str
    bbox: tuple
    page_number: int

class Table:
    row_num: int
    col_num: int
    cells: list[Cell]
    bbox: tuple
    page_number: int
    caption: Optional[Caption]

class Cell:
    row_index: int
    column_index: int
    content: str
    bbox: tuple

class Figure:
    bbox: tuple
    page_number: int
    caption: Optional[Caption]

class Caption:
    bbox: tuple
    content: str
```

## ロジックの課題

### 課題設定

Azure OCRの結果から、Section単位の情報に分割して、そのSection単位の情報のみで、翻訳とPDFの再現ができる状態にする

- まず、得られる結果の形式
```json
pages: [
    {
        "page_number": 1,
        "words": [
            ...
        ],
        "lines": [
            {
                "content": :formula:が含まれた形式の文章,
                "polygon": ポリゴン座標,
                "spans": オフセットと長さ,
            }
        ],
        "formulas": [
            {
                "kind": inline or display,
                "value": latex形式の数式,
                "polygon": ポリゴン座標,
                "spans": オフセットと長さ,
            }
        ]
    },
],
paragraphs: [
    {
        ページ番号, ポリゴン座標, 文章,
    },
],
styles: [
    {
        spans, フォント or カラー or 背景カラー
    }
],
sections: [
    {
        elements: pargraphs, figures, tables
    }
],
tables: [
    {
        ポリゴン座標,...
    }
],
figures: [
    {
        ポリゴン座標,...
    }
]
```

- ここから取得したい情報がリスト形式のSection

- さらに補題として以下のものが課題となる
1. paragraphに属するlineを特定する
2. 各lineのフォント情報やカラー情報を特定する
3. 各lineに属するinline formulaを対応させる
4. sectionに属するparagraphやfigureやtableを対応させる
5. polygonから矩形に変換する

### 考えられる解決策

> 1. paragraphに属するlineを特定する
- これについては、paragraphのspanと各lineのspanを比較することで、paragraphに含まれるlineを取得する

> 2. lineのスタイル情報を取得する
- これについては、stylesの情報から各styleのspanとlineのspanを比較することで取得する

> 3. 各lineに属するinline formulaを対応させる
- formulasをdiplayとinlineでまず分ける。そして、ページ内で、lineを最初から読んでいき、対応するinline formulaを紐づけていく

> 4. sectionに属するparagraphやfigureやtableを対応させる
- figuresとtablesはそのまま配列として保存しておく。paragraphsについても1~3の処理をした上てリストとして保存しておく。これらを元に、最後にindexを元にして、対応させていく

> 5. polygonから矩形に変換する
- 上下左右の最大値を取る

### 不透明なポイント
- span比較のロジック
例えば、paragraphに含まれるという判定はどのように行うのか。paragraphの[line_offset, line_offset + line_length] in [paragraph_offset, paragraph_offset + paragraph_length]というように完全に含まれているのか、それとも一部含まれるようなケースはあるのか？
- display_formulaがsectionと結びつかない？
sectionにelementとしては含まれないので、もし対応さえるならページ番号とspanなどから属するsectionを対応させる必要がある


## 翻訳ロジック

### 1. resultからpages,sections,tables,figures、stylesを取得する
```python
pages = result.pages
sections = result.sections
tables = result.tables
figures = result.figures
styles = result.styles
```

### 2. 各pagesを分析する
1. formulasを分ける
```python
page = pages[i]
inline_formulas = [f for f in page.formulas if f.kind == "inline"]
display_formulas = [f for f in page.formulas if f.kind == "display"]

display_formulas = [
    Display_Formula(
        latex_value=f.value
        bbox=get_bbox(f.bounding_regions) # ポリゴンから矩形に変換する
        page_number=i
    )
    for f in display_formulas
]
```

2. まず、linesに対してstyleの分析を行う
```python
page = pages[i]
lines = page.lines
current_formula_idx = 0

text_lines = []

for line in lines:
    font = get_line_font(line.spans, styles)
    color = get_line_color(line.spans. styles)
    background_color = get_line_background_color(lien.spans, styles)
    span = line.spans
    num_formula = line.content.count(":formula:")
    inline_formulas = inline_formulas[current_formula_idx:current_formula_idx + num_formula]
    current_formula_idx += num_formula

```

3. paragraphにlineを対応させる
```python
paragraphs = [paragraph for paragraph in paragraphs if paragraph.page_number == i]

paragraphのspan情報を元に、paragraphに属するlineを取得する
```

### 3. 各sectionを分析する
1. セクションに属するパラグラフのリストを取得する

2. セクションに属するテーブルのリストを取得する

3. セクションに属するfigureのリストを取得する




