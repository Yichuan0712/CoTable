"""
todo: html -> md + csv + captions
34114632
"""
from bs4 import BeautifulSoup
import re


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


def stack_md_table_headers(md_table):
    """
    Detects multi-line headers in a Markdown table and merges them by column, separating names with →,
    but keeps the original name if the stacked names are identical.

    :param md_table: Markdown table as a string
    :return: Modified Markdown table with stacked headers
    """
    lines = md_table.strip().split("\n")

    # Find the separator line (the line with ---)
    separator_idx = next((i for i, line in enumerate(lines) if re.match(r'\|\s*-+\s*\|', line)), None)
    if separator_idx is None or separator_idx == 0:
        return md_table  # No header detected or table is invalid

    # Extract header lines
    header_lines = lines[:separator_idx]

    # Split header lines into lists of columns
    header_matrix = [re.split(r'\s*\|\s*', line.strip('|')) for line in header_lines]
    max_cols = max(len(row) for row in header_matrix)

    # Stack header rows by column, keeping the original name if identical
    stacked_header = [col[0] if all(x == col[0] for x in col) else "→".join(filter(None, col)) for col in
                      zip(*header_matrix)]

    # Format stacked header back to Markdown
    stacked_header_line = "| " + " | ".join(stacked_header) + " |"

    # Reconstruct the Markdown table
    updated_md_table = "\n".join([stacked_header_line] + lines[separator_idx:])
    return updated_md_table


def remove_empty_col_row(md_table: str):
    """
    Removes empty rows and columns from a Markdown table.

    :param md_table: A string containing the Markdown table.
    :return: A cleaned Markdown table without empty rows and columns.
    """
    lines = md_table.strip().split('\n')
    if len(lines) < 2:
        return md_table  # Not enough lines to form a valid table

    # Parse table
    headers = lines[0].split('|')[1:-1]  # Remove leading and trailing empty columns
    separator = lines[1].split('|')[1:-1]
    data_rows = [line.split('|')[1:-1] for line in lines[2:]]

    # Trim whitespace
    headers = [h.strip() for h in headers]
    data_rows = [[cell.strip() for cell in row] for row in data_rows]

    # Identify valid column indices
    valid_columns = [i for i in range(len(headers)) if any(row[i] for row in data_rows)]

    # Reconstruct table
    cleaned_headers = '| ' + ' | '.join(headers[i] for i in valid_columns) + ' |'
    cleaned_separator = '| ' + ' | '.join(['---'] * len(valid_columns)) + ' |'
    cleaned_data_rows = ['| ' + ' | '.join(row[i] for i in valid_columns) + ' |' for row in data_rows if
                         any(row[i] for i in valid_columns)]

    # Combine output
    return '\n'.join([cleaned_headers, cleaned_separator] + cleaned_data_rows)


def fill_empty_headers(md_table):
    """
    Detects empty column headers in a Markdown table and assigns them unique names.

    :param md_table: Markdown table as a string
    :return: Modified Markdown table with filled headers
    """
    lines = md_table.strip().split('\n')
    if len(lines) < 2:
        return md_table  # Not enough lines to form a valid table

    # Extract header line
    headers = lines[0].split('|')[1:-1]  # Remove leading and trailing empty parts
    separator = lines[1]

    # Assign unique names to empty headers
    empty_count = 0
    for i in range(len(headers)):
        headers[i] = headers[i].strip()
        if not headers[i]:
            headers[i] = f'Unnamed_{empty_count}'
            empty_count += 1

    # Reconstruct table
    filled_header_line = '| ' + ' | '.join(headers) + ' |'

    return '\n'.join([filled_header_line, separator] + lines[2:])


def get_html_content_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


