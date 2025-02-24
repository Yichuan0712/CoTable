import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_select_row_col import *


def s_pk_delete_individual_prompt(md_table):
    return f"""
There is now a table related to pharmacokinetics (PK). 
{display_md_table(md_table)}
Carefully examine the table and follow these steps:
(1) Remove any information that is specific to an individual.
If the table already meets this requirement, return [[END]].
If not, please use the following function to create a new table: f_select_row_col(row_list, col_list)
Replace row_list with the row indices that satisfy the requirement, and col_list with the column names that satisfy the requirement. 
When returning this, enclose the function call in double angle brackets.
"""


def s_pk_delete_individual_parse(content):
    content = content.replace('\n', '')
    content = content.replace(' ', '')

    match_end = re.search(r'\[\[END\]\]', content)
    match_angle = re.search(r'<<.*?>>', content)

    if match_end:
        return None, None

    elif match_angle:
        inner_content = match_angle.group()[2:-2]
        match_func = re.match(r'\w+\s*\(\s*(?:\w+\s*=\s*)?(\[[^\]]*\])\s*,\s*(?:\w+\s*=\s*)?(\[[^\]]*\])\s*\)', inner_content)

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


def s_pk_delete_individual(md_table, model_name="gemini_15_pro"):
    msg = s_pk_delete_individual_prompt(md_table)

    messages = [msg, ]
    question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
    # print(display_md_table(md_table))
    print(usage, content)

    row_list, col_list = s_pk_delete_individual_parse(content)
    if col_list:
        col_list = [fix_col_name(item, md_table) for item in col_list]
    df_table = f_select_row_col(row_list, col_list, markdown_to_dataframe(md_table))
    return_md_table = dataframe_to_markdown(df_table)
    print(display_md_table(return_md_table))

    return return_md_table, res, content, usage, truncated
