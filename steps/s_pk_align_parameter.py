import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_transpose import *


def s_pk_align_parameter_prompt(md_table):
    return f"""
There is now a table related to pharmacokinetics (PK). 
{display_md_table(md_table)}
Carefully examine the pharmacokinetics (PK) table below and follow these steps to determine how the PK parameter type is represented:
(1) Identify how the PK parameter type (e.g., Cmax, tmax, t1/2, etc.) is structured in the table:
If the PK parameter type serves as the row header or is listed under a specific column, return <<the_col_name>>, replacing the_col_name with the actual column name, and enclose the name in double angle brackets.
If the PK parameter type is represented as column headers, return [[COL]].
(2) Ensure a thorough analysis of the table structure before selecting your answer.
"""


def s_pk_align_parameter_parse(content):
    content = content.replace('\n', '')
    content = content.replace(' ', '')

    match_col = re.search(r'\[\[COL\]\]', content)
    match_angle = re.search(r'<<.*?>>', content)

    if match_col:
        return None
    elif match_angle:
        match_name = match_angle.group()[2:-2]
        return match_name
    else:
        raise NotImplementedError


def s_pk_align_parameter(md_table, model_name="gemini_15_pro"):
    msg = s_pk_align_parameter_prompt(md_table)

    messages = [msg, ]
    question = ""

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
    # print(display_md_table(md_table))
    print(usage, content)

    col_name = s_pk_align_parameter_parse(content)

    if col_name:
        df_table = markdown_to_dataframe(md_table)
        df_table = df_table.rename(columns={f"{col_name}": "Parameter Type"})
        return_md_table = dataframe_to_markdown(df_table)
    else:
        df_table = f_transpose(markdown_to_dataframe(md_table))
        df_table.columns = ["Parameter Type"] + list(df_table.columns[1:])
        return_md_table = deduplicate_headers(fill_empty_headers(remove_empty_col_row(dataframe_to_markdown(df_table))))

    print(display_md_table(return_md_table))

    return return_md_table, res, content, usage, truncated
