import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_select_row_col import *


def s_keep_pk_summary_prompt(md_table_for_display):
    instructions = f"""
    There is now a table related to pharmacokinetics (PK). 
    {md_table_for_display}
    Carefully examine the table and follow these two steps:
    (1) Remove any columns or rows that are NOT about PK study.
    (2) Remove any information that is specific to an individual.
    If the table already meets these two criteria (no unrelated parts and no individual-specific information), return [[END]].
    If the table does NOT meet these criteria, use the following function to create a new table:
    f_select_row_col(row_list, col_list)
    Replace row_list with row indices that meet the above two criteria.
    Replace col_list with column names that meet the above two criteria.
    Return how you would use this function.
    Enclose the function call within double angle brackets.
    """
    return instructions


def s_keep_pk_summary_parse(response):
    match_end = re.search(r'\[\[END\]\]', response)
    match_angle = re.search(r'<<.*?>>', response)

    if match_end:
        match_start = match_end.start()
        period_pos = response.rfind('.', 0, match_start)
        if period_pos != -1:
            return response[:period_pos + 1], None, None
        else:
            return response[:match_start], None, None

    elif match_angle:
        match_start = match_angle.start()
        period_pos = response.rfind('.', 0, match_start)
        if period_pos != -1:
            thought = response[:period_pos + 1]
        else:
            thought = response[:match_start]

        inner_content = match_angle.group()[2:-2]
        match_func = re.match(r'\w+\s*\(\s*(\[[^\]]*\])\s*,\s*(\[[^\]]*\])\s*\)', inner_content)

        if match_func:
            arg1_str = match_func.group(1)
            arg2_str = match_func.group(2)
            arg1 = ast.literal_eval(arg1_str)
            arg2 = ast.literal_eval(arg2_str)
            return thought, arg1, arg2
        else:
            return thought, None, None

    else:
        raise NotImplementedError


def s_keep_pk_summary(md_table, model_name="gemini_15_pro"):
    msg = s_keep_pk_summary_prompt(display_md_table(md_table))
    print(display_md_table(md_table))
    messages = [msg, ]
    question = ""
    _, response, _, _ = get_llm_response(messages, question, model=model_name)
    thought, row_list, col_list = s_keep_pk_summary_parse(response)
    print("->")
    print(thought)
    print("->")
    df_table = f_select_row_col(row_list, col_list, markdown_to_dataframe(md_table))
    return_md_table = dataframe_to_markdown(df_table)
    print(display_md_table(return_md_table))
    return return_md_table
