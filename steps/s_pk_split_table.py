from table_utils import *
from llm_utils import *


def s_pk_split_table_prompt(md_table):
    return f"""
    There is now a table related to pharmacokinetics (PK). 
    {display_md_table(md_table)}
    Carefully examine the table and follow these steps:
    (1) 检查所有行, 是否能根据实验内容进行进一步分组
    (2) 检查所有列, 是否能根据实验内容进一步分组
    If the table already meets this requirement, return [[END]].
    If not, please use the following function to create a new table: f_select_row_col(row_list, col_list)
    Replace row_list with the row indices that satisfy the requirement, and col_list with the column names that satisfy the requirement. 
    When returning this, enclose the function call in double angle brackets.
    """

