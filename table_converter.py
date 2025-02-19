"""
todo: html -> md + csv + captions
34114632
"""

from bs4 import BeautifulSoup


def parse_html_table(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')

    if not table:
        return "No table found"

    rows = table.find_all('tr')
    data = []
    colspans = {}

    for row in rows:
        cells = row.find_all(['th', 'td'])
        row_data = []
        col_index = 0

        for cell in cells:
            while col_index in colspans and colspans[col_index] > 0:
                row_data.append('')
                colspans[col_index] -= 1
                col_index += 1

            colspan = int(cell.get('colspan', 1))
            cell_text = cell.get_text(strip=True)
            row_data.append(cell_text)

            if colspan > 1:
                for i in range(1, colspan):
                    colspans[col_index + i] = colspan - 1

            col_index += 1

        data.append(row_data)

    return data


def get_html_content_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


