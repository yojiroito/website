#!/usr/bin/env python3
"""
build_lists.py — data/research.yml から Markdown / LaTeX 断片を生成する。

Quarto の pre-render フックから自動実行されるため、通常は手で叩く必要はない。
出力先は _generated/（アンダースコア始まりなので Quarto はページとして扱わない）。

  _generated/publications-web.md       index.qmd 用（Markdown 箇条書き）
  _generated/working-papers-web.md
  _generated/works-in-progress-web.md
  _generated/publications-cv.md        cv.qmd 用（生 LaTeX の段落形式）
  _generated/working-papers-cv.md
  _generated/works-in-progress-cv.md
"""

from pathlib import Path
import sys

try:
    import yaml
except ImportError:
    sys.exit("pyyaml が必要です:  pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "research.yml"
OUT = ROOT / "_generated"


# ---------------------------------------------------------------- 共通ヘルパー

def join_names(names):
    """['A'] -> 'A' / ['A','B'] -> 'A and B' / 3人以上は 'A, B, and C'"""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def latex_escape(text):
    """LaTeX の特殊文字をエスケープする（タイトルに & や % が含まれる場合の保険）。"""
    for char in ("&", "%", "$", "#", "_"):
        text = text.replace(char, "\\" + char)
    return text


def citation_parts(item):
    """掲載誌・シリーズ名・巻号・年を順に返す。italic 化は呼び出し側で行う。"""
    return [
        ("italic", item.get("outlet")),
        ("plain", item.get("series")),
        ("plain", item.get("details")),
        ("plain", str(item["year"]) if item.get("year") else None),
    ]


# ------------------------------------------------------------------ Web 用

def build_web_entry(item):
    """Markdown の箇条書き1行を作る。"""
    title = item["title"]
    url = item.get("url")
    line = f"[{title}]({url})" if url else title

    co = item.get("coauthors")
    if co:
        line += f" (with {join_names(co)})"

    tail = []
    for kind, value in citation_parts(item):
        if value:
            tail.append(f"*{value}*" if kind == "italic" else value)
    if tail:
        line += ", " + ", ".join(tail)

    if item.get("note"):
        line += f". {item['note']}"

    line = line.rstrip(".") + "."

    pres = item.get("presentations")
    if pres:
        # styles.css の .gs-venues で小さく灰色に整形される
        line += " [Presented at: " + ", ".join(pres) + ".]{.gs-venues}"

    return "* " + line


# ------------------------------------------------------------------- CV 用

def build_cv_entry(item):
    """main.tex に倣った「箇条書きなしの段落」を生 LaTeX で作る。"""
    title = latex_escape(item["title"])
    url = item.get("url")
    line = f"\\href{{{url}}}{{{title}}}" if url else title

    co = item.get("coauthors")
    if co:
        line += ", with " + latex_escape(join_names(co))

    tail = []
    for kind, value in citation_parts(item):
        if value:
            value = latex_escape(value)
            tail.append(f"\\textit{{{value}}}" if kind == "italic" else value)
    if tail:
        line += ", " + ", ".join(tail)

    if item.get("note"):
        line += f". {latex_escape(item['note'])}"

    line = line.rstrip(".") + "."

    pres = item.get("presentations")
    if pres:
        joined = latex_escape(", ".join(pres))
        # 改行して一段小さい斜体で報告歴を添える
        line += f"\\\\\n{{\\small\\itshape Presented at: {joined}.}}"

    return line


# ------------------------------------------------------------------ 書き出し

HEADER = (
    "<!-- このファイルは scripts/build_lists.py が自動生成しています。 -->\n"
    "<!-- 直接編集せず data/research.yml を編集してください。       -->\n\n"
)


def write_section(items, mode, filename):
    if mode == "cv":
        # 生 LaTeX ブロックとして渡す（波括弧をそのまま LaTeX に届けるため）
        body = "\n\n\\vspace{0.4em}\n\n".join(build_cv_entry(i) for i in items)
        body = "```{=latex}\n" + body + "\n```"
    else:
        body = "\n".join(build_web_entry(i) for i in items)

    (OUT / filename).write_text(HEADER + body + "\n", encoding="utf-8")


def main():
    if not DATA.exists():
        sys.exit(f"データファイルが見つかりません: {DATA}")

    data = yaml.safe_load(DATA.read_text(encoding="utf-8")) or {}
    OUT.mkdir(exist_ok=True)

    sections = {
        "publications": "publications",
        "working_papers": "working-papers",
        "works_in_progress": "works-in-progress",
    }

    for key, slug in sections.items():
        items = data.get(key) or []
        for mode in ("web", "cv"):
            write_section(items, mode, f"{slug}-{mode}.md")
        print(f"  {slug}: {len(items)} 件")

    print("断片を _generated/ に生成しました。")


if __name__ == "__main__":
    main()
