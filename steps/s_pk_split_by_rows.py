import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_split_by_rows import *


def s_pk_split_by_rows_prompt(md_table):
    return f"""
There is now a table related to pharmacokinetics (PK). 
{display_md_table(md_table)}
Carefully examine the table and follow these steps:  
(1) Review all rows, especially the headers, to check if any sub-tables or nested groups are **explicitly defined by the author** (e.g., clear sectioning, separate labels, or visible groupings).  
(2) If and only if sub-tables are **explicitly present**, group the rows accordingly.  
(3) If a descriptor row or index applies to all groups when splitting, ensure it is included in each subgroup.  
If the table does not contain **clearly defined** sub-tables, simply return [[END]].  
If division is possible, use the function below (do not over-split based on row categories):  
f_split_by_rows(row_groups)
Replace row_groups with row indices in the following format:  
row_groups = [[0, 1, 2], [3, 4, 5]] (example).  
When returning this, enclose the function call in double angle brackets, like this:  
<<f_split_by_rows([[0, 1, 2], [3, 4, 5]])>>
"""


def s_pk_split_by_rows_parse(content):
    content.replace('\n', '')

    if '[[END]]' in content:
        return None

    pattern = r'\[\[.*\]\]'

    match = re.search(pattern, content.strip(), flags=re.DOTALL)

    if not match:
        raise NotImplementedError

    bracket_str = match.group(0).strip()
    data = ast.literal_eval(bracket_str)
    return data


def s_pk_split_by_rows(md_table, model_name="gemini_15_pro"):
    msg = s_pk_split_by_rows_prompt(md_table)

    messages = [msg, ]
    question = ""

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
    # print(display_md_table(md_table))
    print(usage)
    print(content)

    row_groups = s_pk_split_by_rows_parse(content)
    if row_groups is None:
        return_md_tables = [md_table, ]
    else:
        df_table = f_split_by_rows(row_groups, markdown_to_dataframe(md_table))
        return_md_tables = []
        for d in df_table:
            return_md_tables.append(dataframe_to_markdown(d))

    for m in return_md_tables:
        print(display_md_table(m))

    return return_md_tables, res, content, usage, truncated
