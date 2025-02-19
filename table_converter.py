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

    for row in rows:
        cols = row.find_all(["th", "td"])
        if any(col.name == "th" for col in cols):
            header_rows.append(cols)
        else:
            body_rows.append(cols)

    max_cols = max(len(row) for row in header_rows) if header_rows else 0
    header_markdown = []

    for row in header_rows:
        cols = [" ".join(col.stripped_strings) for col in row]
        while len(cols) < max_cols:
            cols.append("")
        header_markdown.append("| " + " | ".join(cols) + " |")

    separator = "| " + " | ".join(["---"] * max_cols) + " |"
    header_markdown.append(separator)

    body_markdown = []
    for row in body_rows:
        cols = [" ".join(col.stripped_strings) for col in row]
        while len(cols) < max_cols:
            cols.append("")
        body_markdown.append("| " + " | ".join(cols) + " |")

    return "\n".join(header_markdown + body_markdown)


def get_html_content_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


