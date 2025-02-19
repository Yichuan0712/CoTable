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


def get_html_content_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


