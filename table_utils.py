"""
todo: html -> md + csv + captions
34114632
"""

from bs4 import BeautifulSoup


def html_table_to_markdown(html):
    """
    Convert an HTML table into a Markdown table, handling both colspan and rowspan.

    :param html: HTML string containing a table
    :return: Markdown-formatted table as a string
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return ""

    rows = table.find_all("tr")

    # Matrix to store the table structure, considering rowspan and colspan
    table_matrix = []
    max_cols = 0

    rowspan_tracker = {}  # Dictionary to track rowspan placements

    for row_idx, row in enumerate(rows):
        cols = row.find_all(["th", "td"])
        row_data = []
        col_idx = 0

        # Fill in existing rowspan values
        while col_idx in rowspan_tracker and rowspan_tracker[col_idx][1] > 0:
            row_data.append(rowspan_tracker[col_idx][0])  # Use stored text
            rowspan_tracker[col_idx] = (rowspan_tracker[col_idx][0], rowspan_tracker[col_idx][1] - 1)
            if rowspan_tracker[col_idx][1] == 0:
                del rowspan_tracker[col_idx]
            col_idx += 1

        is_header = all(col.name == "th" for col in cols)

        for col in cols:
            for sup in col.find_all("sup"):  # Remove superscript elements
                sup.decompose()

            text = "".join(col.stripped_strings)
            colspan = int(col.get("colspan", 1))
            rowspan = int(col.get("rowspan", 1))

            row_data.extend([text] * colspan)  # Expand colspan cells

            if rowspan > 1:
                for i in range(colspan):
                    rowspan_tracker[col_idx + i] = (text, rowspan - 1)  # Store rowspan values

            col_idx += colspan

        max_cols = max(max_cols, len(row_data))
        table_matrix.append((row_data, is_header))

    # Normalize all rows to the maximum column count, keeping rowspan values
    for row, _ in table_matrix:
        while len(row) < max_cols:
            missing_col_idx = len(row)
            if missing_col_idx in rowspan_tracker:
                row.append(rowspan_tracker[missing_col_idx][0])  # Fill with rowspan text
            else:
                row.append("")  # Fallback to empty string

    # Identify header rows (continuous header rows at the beginning)
    header_end_idx = 0
    for i, (_, is_header) in enumerate(table_matrix):
        if is_header:
            header_end_idx = i
        else:
            break

    # Convert to Markdown
    markdown_rows = ["| " + " | ".join(row) + " |" for row, _ in table_matrix]
    separator = "| " + " | ".join(["---"] * max_cols) + " |"

    return "\n".join(markdown_rows[:header_end_idx + 1] + [separator] + markdown_rows[header_end_idx + 1:])


def get_html_content_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


