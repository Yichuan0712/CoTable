import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_group_row import *


def s_pk_split_by_rows_prompt(md_table):
    return f"""
There is now a table related to pharmacokinetics (PK). 
{display_md_table(md_table)}
Carefully examine the table and follow these steps:
(1) 检查所有的rows, 特别是行标题, 分析是否存在子表
(2) If it has, 通过将rows进行分组的方式实现子表的划分
(3) If there is any index or descriptor row that applies to all groups when splitting by rows, ensure this descriptor is included in every subgroup created from the split.
If the table cannot be divided into subtables either by rows, return [[END]].
If it can be divided, please use the following function to create a new table:
f_group_row(row_groups)
Replace row_groups with row indices in the following format:
row_groups = [[0, 1, 2], [3, 4, 5]] (example)
When returning this, enclose the function call in double angle brackets, like this:
<<f_group_row([[0, 1, 2], [3, 4, 5]])>>
"""
