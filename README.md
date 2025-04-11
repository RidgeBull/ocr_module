# OCRモジュール

OCRと翻訳機能を提供するPythonモジュールです。PDFや画像からテキスト、テーブル、図、数式などを抽出し、構造化されたデータとして利用できます。

[![PyPI version](https://badge.fury.io/py/ocr_module.svg)](https://badge.fury.io/py/ocr_module)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 機能

- PDF文書や画像からテキスト抽出（OCR）
- テーブル検出と構造化データへの変換
- 画像やグラフの抽出
- 数式の認識と処理
- セクション分析と構造化
- 翻訳機能との連携

## インストール方法

### 安定版のインストール

```bash
pip install ocr_module
```

### 開発版のインストール

開発版は最新機能を含みますが、不安定な場合があります。

```bash
pip install ocr_module --pre
```

または直接GitHubからインストール：

```bash
pip install git+https://github.com/ridgebull/ocr_module.git@develop
```

## 必要条件

- Python 3.8以上
- 依存ライブラリ:
  - azure-ai-documentintelligence
  - openai
  - pylatex
  - pypdf2
  - pymupdf
  - pydantic-settings
  - deepl

## 基本的な使い方

### OCRモジュールの初期化

```python
from ocr_module.adapters.infra.azure.azure_ocr_repository import AzureOCRRepository
from ocr_module.adapters.infra.pymupdf.pymupdf_ocr_repository import PyMuPDFOCRRepository

# Azureを使用する場合
ocr_repo = AzureOCRRepository(
    endpoint="YOUR_AZURE_ENDPOINT",
    key="YOUR_AZURE_KEY"
)

# PyMuPDFを使用する場合
ocr_repo = PyMuPDFOCRRepository()
```

### PDFからドキュメント情報を取得

```python
# ドキュメントを取得
document, stats = ocr_repo.get_document("path/to/document.pdf")

# ページとセクションへのアクセス
for page in document.pages:
    print(f"ページ {page.page_number}:")
    print(f"  幅: {page.width}, 高さ: {page.height}")
    print(f"  段落数: {len(page.paragraphs)}")
    print(f"  テーブル数: {len(page.tables)}")
    print(f"  図の数: {len(page.figures)}")

# テーブルの処理
for table in document.pages[0].tables:
    print(f"テーブルID: {table.table_id}")
    print(f"位置: {table.bbox}")
```

### 画像からのOCR処理

```python
# 画像からテキスト抽出
document, stats = ocr_repo.get_document("path/to/image.jpg")

# テキスト内容を表示
for page in document.pages:
    for paragraph in page.paragraphs:
        print(paragraph.content)
```

## テーブル検出と処理

PyMuPDFを使用したテーブル検出の例:

```python
from ocr_module.adapters.infra.pymupdf.pymupdf_ocr_repository import PyMuPDFOCRRepository

ocr_repo = PyMuPDFOCRRepository()
document, stats = ocr_repo.get_document("path/to/document_with_tables.pdf")

# 全てのテーブルを処理
for page in document.pages:
    for table in page.tables:
        print(f"テーブルID: {table.table_id}, ページ: {table.page_number}")
        print(f"境界ボックス: {table.bbox}")
```

## エラーハンドリング

```python
try:
    document, stats = ocr_repo.get_document("path/to/document.pdf")
except Exception as e:
    print(f"OCR処理中にエラーが発生しました: {str(e)}")
```

## ロギング設定

詳細なデバッグ情報を見るためにロギングレベルを調整できます：

```python
import logging

# ロガーの設定
logging.basicConfig(level=logging.DEBUG)
```

## トラブルシューティング

### 一般的な問題と解決策

1. **テーブル検出に問題がある場合**:
   - 文書の品質を確認
   - テーブル周囲の余白を十分に確保
   - PyMuPDFの最新バージョンを使用しているか確認

2. **OCRの精度が低い場合**:
   - 高解像度の入力ファイルを使用
   - コントラストの高い画像で試行
   - カスタム言語モデルの設定を検討

3. **パフォーマンスの問題**:
   - 大きなファイルは分割して処理
   - メモリ使用量を監視
   - バッチ処理の実装を検討

## 開発者向け情報

### プロジェクト構造

```
ocr_module/
├── adapters/            # 外部サービスやライブラリとの接続
│   ├── infra/           # インフラ層の実装
│   │   ├── azure/       # Azure OCR実装
│   │   └── pymupdf/     # PyMuPDF実装
├── domain/              # ドメイン層
│   ├── entities/        # エンティティの定義
│   ├── repositories/    # リポジトリインターフェース
│   └── services/        # サービス実装
└── usecases/            # ユースケース層
```

### エンティティモデル

OCRモジュールでは以下のエンティティを使用しています：

```python
class Document:
    pages: List[Page]
    sections: List[Section]

class Page:
    page_number: int
    width: float
    height: float
    paragraphs: List[Paragraph]
    figures: List[Figure]
    tables: List[Table]
    formulas: List[Formula]
    display_formulas: List[DisplayFormula]

class Paragraph:
    paragraph_id: int
    role: Optional[str]
    content: str
    bbox: Tuple[float, float, float, float]
    page_number: int

class Table:
    table_id: int
    bbox: Tuple[float, float, float, float]
    page_number: int
    image_data: Optional[bytes]
    element_paragraph_ids: List[int]

class Figure:
    figure_id: int
    bbox: Tuple[float, float, float, float]
    page_number: int
    image_data: Optional[bytes]
    element_paragraph_ids: List[int]
```

## 貢献

貢献は歓迎します！以下の手順で貢献できます：

1. リポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## ライセンス

このプロジェクトはMITライセンスの下で公開されています - 詳細については[LICENSE](LICENSE)ファイルを参照してください。

## 連絡先

プロジェクトオーナー: [GitHub](https://github.com/ridgebull)

---

## 元の技術ドキュメント

以下は開発者向けの詳細な技術ドキュメントです。

### 翻訳手順

#### Azure OCR

##### 得られる結果

**lines = List[line]**
* page_number: int
* content: str（`:formula`を含む）
* span: dict（`offset`と`length`を含む）

**formulas**
* type: Literal[`inline`, `display`]
* value: str（latexコード）
* page_number: int

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

## バージョン管理とリリース

このプロジェクトは[セマンティックバージョニング](https://semver.org/lang/ja/)に準拠しており、GitHubのワークフローを使用して自動的なバージョン管理とリリースプロセスを実装しています。

### 最新バージョン

[![Latest Release](https://img.shields.io/github/v/release/ridgebull/ocr_module)](https://github.com/ridgebull/ocr_module/releases/latest)

### バージョン番号とタグの自動管理

バージョン番号の更新とタグの作成は自動化されています：

1. GitHubのActionsタブで「自動タグ作成」ワークフローを実行
2. パッチ（修正）、マイナー（機能追加）、メジャー（互換性の変更）から更新方法を選択
3. ワークフローが自動的に以下を実行:
   - pyproject.tomlのバージョン番号を更新
   - 変更をコミット
   - 新しいバージョンのタグを作成（v0.2.30など）
   - リポジトリにプッシュ

### リリースノートの自動生成

タグがプッシュされると、「リリース自動化」ワークフローが以下を自動的に実行します：

1. 前回のリリースからの変更履歴を取得
2. コミットメッセージからリリースノートを生成
3. GitHubリリースページに公開

詳細については[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。




