import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_split_table import *


def s_pk_split_table_prompt(md_table):
    strengthen_reasoning = "Please provide your reasoning process step by step before giving the final answer."
    return f"""
There is now a table related to pharmacokinetics (PK). 
{display_md_table(md_table)}
Carefully examine the table and follow these steps:
(1) Determine if this table can be further divided into subtables.
This is the ONLY criterion: Check columns and rows separately to identify if there are highly similar or repeating patterns. If such patterns exist, the table can be split into subtables accordingly. If not, do not split the table.
(2) If it can be divided, specify whether the division should be by rows, columns, or both.
Important: If there is any index or descriptor column or row (e.g., "PK parameter") that applies to all groups when splitting by columns or rows, ensure this descriptor is included in every subgroup created from the split.
If the table cannot be divided into subtables either by rows or columns, return [[END]].
If it can be divided, please use the following function to create a new table:
f_split_table(row_groups, col_groups)
Replace row_groups with row indices in the following format:
row_groups = [[0, 1, 2], [3, 4, 5]] (example)
Replace col_groups with column names in the following format:
col_groups = [["ColumnA", "ColumnB", "ColumnC"], ["ColumnA", "ColumnD", "ColumnE", "ColumnF"]] (example)
When returning this, enclose the function call in double angle brackets, like this:
<<f_split_table([[0, 1, 2], [3, 4, 5]], [["ColumnA", "ColumnB", "ColumnC"], ["ColumnA", "ColumnD", "ColumnE", "ColumnF"]])>>
"""


def s_pk_split_table_parse(content):
    match_end = re.search(r'\[\[END\]\]', content)
    match_angle = re.search(r'<<.*?>>', content)

    if match_end:
        return None, None

    elif match_angle:
        inner_content = match_angle.group()[2:-2]
        match_func = re.match(r'\w+\s*\(\s*(?:\w+\s*=\s*)?(\[\s*\[[^\]]*\](?:\s*,\s*\[[^\]]*\])*\s*\])\s*,\s*(?:\w+\s*=\s*)?(\[\s*\[[^\]]*\](?:\s*,\s*\[[^\]]*\])*\s*\])\s*\)', inner_content)

        if match_func:
            arg1_str = match_func.group(1)
            arg2_str = match_func.group(2)
            arg1 = ast.literal_eval(arg1_str)
            arg2 = ast.literal_eval(arg2_str)
            return arg1, arg2
        else:
            return None, None

    else:
        raise NotImplementedError


def s_pk_split_table(md_table, model_name="gemini_15_pro"):
    msg = s_pk_split_table_prompt(md_table)

    messages = [msg, ]
    question = ""

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)

    row_groups, col_groups = s_pk_split_table_parse(content)

    col_groups = [[fix_col_name(item, md_table) for item in group] for group in col_groups]

    df_subtables = f_split_table(row_groups, col_groups, markdown_to_dataframe(md_table))

    md_subtables = {}
    for key, value in df_subtables.items():
        md_subtables[key] = dataframe_to_markdown(value)

    return md_subtables, res, content, usage, truncated

