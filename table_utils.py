from bs4 import BeautifulSoup
import pandas as pd
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


def markdown_to_dataframe(md_table):
    """
    Convert a Markdown table to a Pandas DataFrame, treating all values as strings.

    :param md_table: A string containing the Markdown table.
    :return: Pandas DataFrame representing the table with all values as strings.
    """
    lines = md_table.strip().split('\n')
    if len(lines) < 3:
        return pd.DataFrame()  # Return empty DataFrame if table is invalid

    # Extract header and data rows, skipping the separator line
    headers = lines[0].split('|')[1:-1]  # Remove leading and trailing empty parts
    data_rows = [line.split('|')[1:-1] for line in lines[2:]]

    # Trim whitespace from headers and data cells
    headers = [h.strip() for h in headers]
    data_rows = [[cell.strip() for cell in row] for row in data_rows]

    # Create DataFrame treating all values as strings
    df = pd.DataFrame(data_rows, columns=headers, dtype=str)
    return df


def dataframe_to_markdown(df_table):
    """
    Convert a Pandas DataFrame to a Markdown-formatted table.

    :param df_table: Pandas DataFrame to convert
    :return: Markdown-formatted table as a string
    """
    if df_table.empty:
        return ""  # Return empty string if DataFrame is empty

    # Prepare header
    headers = df_table.columns.tolist()
    header_line = '| ' + ' | '.join(headers) + ' |'
    separator_line = '| ' + ' | '.join(['---'] * len(headers)) + ' |'

    # Prepare data rows
    data_lines = []
    for _, row in df_table.iterrows():
        row_str = '| ' + ' | '.join(str(cell) for cell in row) + ' |'
        data_lines.append(row_str)

    # Combine into final Markdown table
    md_table = '\n'.join([header_line, separator_line] + data_lines)

    return md_table


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


def remove_empty_col_row(md_table):
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
            headers[i] = f'Unnamed' if empty_count == 0 else f'Unnamed_{empty_count}'
            empty_count += 1

    # Reconstruct table
    filled_header_line = '| ' + ' | '.join(headers) + ' |'

    return '\n'.join([filled_header_line, separator] + lines[2:])


def deduplicate_headers(md_table):
    """
    Detects duplicate column headers in a Markdown table and renames them with _0, _1, ... suffixes.

    :param md_table: Markdown table as a string
    :return: Modified Markdown table with unique headers
    """
    lines = md_table.strip().split('\n')
    if len(lines) < 2:
        return md_table  # Not enough lines to form a valid table

    # Extract header line
    headers = lines[0].split('|')[1:-1]  # Remove leading and trailing empty parts
    separator = lines[1]

    # Deduplicate headers
    seen = {}
    for i in range(len(headers)):
        headers[i] = headers[i].strip()
        if headers[i] in seen:
            seen[headers[i]] += 1
            headers[i] = f"{headers[i]}_{seen[headers[i]]}"
        else:
            seen[headers[i]] = 0  # First occurrence remains unchanged

    # Reconstruct table
    deduplicated_header_line = '| ' + ' | '.join(headers) + ' |'

    return '\n'.join([deduplicated_header_line, separator] + lines[2:])


def display_md_table(md_table):
    """
    Adds labels to each row in a Markdown table.

    The first row is prefixed with "col:", and subsequent rows are prefixed with "row 1:", "row 2:", etc.

    :param md_table: Markdown table as a string
    :return: Modified Markdown table with labeled rows
    """
    lines = md_table.strip().split('\n')
    if len(lines) < 2:
        return md_table  # Not enough lines to form a valid table

    labeled_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            headers = line.split('|')
            headers = [f'"{header.strip()}"' for header in headers if header.strip()]
            labeled_lines.append(f"col: | {' | '.join(headers)} |")
        elif i == 1 and re.match(r'\|\s*-+\s*\|', line):
            labeled_lines.append(line)  # Keep separator unchanged
        else:
            labeled_lines.append(f"row {i - 2}: {line}")

    return '\n'.join(labeled_lines)


def get_html_content_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


