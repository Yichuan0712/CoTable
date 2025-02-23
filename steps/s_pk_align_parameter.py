import re
import ast
from table_utils import *
from llm_utils import *


def s_pk_align_parameter_prompt(md_table):
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