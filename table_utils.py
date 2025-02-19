"""
todo: html -> md + csv + captions
34114632
"""

from bs4 import BeautifulSoup


def html_table_to_markdown_basic(html):
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


def html_table_to_markdown(html):
    """
    Convert an HTML table into a Markdown table.

    :param html: HTML string containing a table
    :return: Markdown-formatted table as a string
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return ""

    rows = table.find_all("tr")
    header_matrix, body_rows = [], []
    max_cols = 0

    # Parse table rows
    for row in rows:
        cols = row.find_all(["th", "td"])
        row_data = []
        col_spans = []

        for col in cols:
            # Remove superscript elements (e.g., footnotes)
            for sup in col.find_all("sup"):
                sup.decompose()

            text = " ".join(col.stripped_strings)  # Extract text content
            colspan = int(col.get("colspan", 1))  # Get colspan, default is 1
            row_data.append((text, colspan))
            col_spans.append(colspan)

        max_cols = max(max_cols, sum(col_spans))  # Track max columns for alignment

        if any(col.name == "th" for col in cols):
            header_matrix.append(row_data)  # Store header row
        else:
            body_rows.append(cols)  # Store body row

    # Format header rows
    formatted_header = []
    for row in header_matrix:
        expanded_row = []
        for text, colspan in row:
            expanded_row.extend([text] * colspan)  # Expand colspan cells
        formatted_header.append("| " + " | ".join(expanded_row) + " |")

    # Add separator line after header
    separator = "| " + " | ".join(["---"] * max_cols) + " |"
    formatted_header.append(separator)

    # Format body rows
    body_markdown = []
    for row in body_rows:
        cols = [" ".join(col.stripped_strings) for col in row]
        cols.extend([""] * (max_cols - len(cols)))  # Ensure all rows have equal columns
        body_markdown.append("| " + " | ".join(cols) + " |")

    return "\n".join(formatted_header + body_markdown)


def get_html_content_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


