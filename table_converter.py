"""
todo: html -> md + csv + captions
34114632
"""

from bs4 import BeautifulSoup


def html_table_to_markdown(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return ""

    rows = table.find_all("tr")
    markdown = []

    for i, row in enumerate(rows):
        cols = [" ".join(col.stripped_strings) for col in row.find_all(["th", "td"])]
        markdown.append(" | ".join(cols))
        if i == 0:
            markdown.append(" | ".join(["---"] * len(cols)))

    return "\n".join(markdown)


def html_table_to_markdown_2(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return ""

    rows = table.find_all("tr")
    header_rows = []
    body_rows = []

    # 解析表头（支持多层级表头和 colspan）
    header_matrix = []
    max_cols = 0

    for row in rows:
        cols = row.find_all(["th", "td"])
        row_data = []
        col_spans = []

        for col in cols:
            for sup in col.find_all("sup"):
                sup.decompose()  # 彻底移除 <sup> 标签及其内容
            text = " ".join(col.stripped_strings)
            colspan = int(col.get("colspan", 1))  # 获取 colspan
            row_data.append((text, colspan))
            col_spans.append(colspan)

        max_cols = max(max_cols, sum(col_spans))
        if any(col.name == "th" for col in cols):
            header_matrix.append(row_data)
        else:
            body_rows.append(cols)

    # 构建完整的表头结构
    formatted_header = [""] * len(header_matrix)
    for i, row in enumerate(header_matrix):
        expanded_row = []
        for text, colspan in row:
            expanded_row.extend([text] * colspan)  # 按 colspan 扩展列
        formatted_header[i] = "| " + " | ".join(expanded_row) + " |"

    # 生成分隔行
    separator = "| " + " | ".join(["---"] * max_cols) + " |"
    formatted_header.append(separator)

    # 处理数据行
    body_markdown = []
    for row in body_rows:
        cols = []
        for col in row:
            for sup in col.find_all("sup"):
                sup.decompose()  # 彻底移除 <sup> 标签及其内容
            cols.append(" ".join(col.stripped_strings))
        while len(cols) < max_cols:
            cols.append("")  # 补齐缺少的列
        body_markdown.append("| " + " | ".join(cols) + " |")

    return "\n".join(formatted_header + body_markdown)


def get_html_content_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


