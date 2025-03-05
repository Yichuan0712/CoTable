import ast
from utils.table_utils import *
from utils.llm_utils import *
from operations.f_split_by_cols import *


def s_pk_split_by_cols_prompt(md_table):
    return f"""
There is now a table related to pharmacokinetics (PK). 
{display_md_table(md_table)}
Carefully examine the table and follow these steps:  
(1) Review all columns, especially the headers, to check if any sub-tables, nested groups, or different experimental groups are **explicitly defined** (e.g., clear sectioning, separate labels, or visible groupings).  
(2) If and only if such sub-tables, nested groups, or experimental groups are present, group the columns accordingly.  
(3) If a descriptor column applies to all groups when splitting, ensure it is included in each subgroup.   
If the table does not contain **clearly defined** groupings or experimental groups, simply return [[END]].  
If division is possible, use the function below (do not over-split based on column categories):  
f_split_by_cols(col_groups)
Replace col_groups with column names in the following format:  
col_groups = [["ColumnA", "ColumnB", "ColumnC", "ColumnG"], ["ColumnA", "ColumnD", "ColumnE", "ColumnF", "ColumnG"]] (example)
When returning this, enclose the function call in double angle brackets, like this:  
<<f_split_by_cols([["ColumnA", "ColumnB", "ColumnC", "ColumnG"], ["ColumnA", "ColumnD", "ColumnE", "ColumnF", "ColumnG"]])>>
"""


def s_pk_split_by_cols_parse(content):
    content = content.replace('\n', '')
    content = content.replace(' ', '')

    if '[[END]]' in content:
        return None

    pattern = r'\[\[.*\]\]'

    match = re.search(pattern, content.strip(), flags=re.DOTALL)

    if not match:
        raise NotImplementedError

    bracket_str = match.group(0).strip()
    data = ast.literal_eval(bracket_str)
    return data


def s_pk_split_by_cols(md_table, model_name="gemini_15_pro", previous_col_groups=None):
    if previous_col_groups:
        print(0, "Based on the cached information.")
        col_groups = [[fix_col_name(item, md_table) for item in group] for group in previous_col_groups]
        df_table = f_split_by_cols(col_groups, markdown_to_dataframe(md_table))
        return_md_tables = []
        for d in df_table:
            return_md_tables.append(dataframe_to_markdown(d))
        for m in return_md_tables:
            print(display_md_table(m))
        return return_md_tables, True, "Based on the cached information.", 0, False, col_groups

    msg = s_pk_split_by_cols_prompt(md_table)

    messages = [msg, ]
    question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
    # print(display_md_table(md_table))
    print(usage, content)

    col_groups = s_pk_split_by_cols_parse(content)
    if col_groups is None:
        return_md_tables = [md_table, ]
    else:
        col_groups = [[fix_col_name(item, md_table) for item in group] for group in col_groups]
        df_table = f_split_by_cols(col_groups, markdown_to_dataframe(md_table))
        return_md_tables = []
        for d in df_table:
            return_md_tables.append(dataframe_to_markdown(d))

    for m in return_md_tables:
        print(display_md_table(m))

    return return_md_tables, res, content, usage, truncated, col_groups


# split on the big table
# def s_pk_split_by_cols(md_table, md_tables_split_by_rows, model_name="gemini_15_pro"):
#     msg = s_pk_split_by_cols_prompt(md_table)
#
#     messages = [msg, ]
#     question = ""
#
#     res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
#     # print(display_md_table(md_table))
#     print(usage, content)
#
#     col_groups = s_pk_split_by_cols_parse(content)
#     if col_groups is None:
#         return_md_tables = md_tables_split_by_rows
#     else:
#         col_groups = [[fix_col_name(item, md_table) for item in group] for group in col_groups]
#         return_md_tables = []
#         for mt in md_tables_split_by_rows:
#             df_table = f_split_by_cols(col_groups, markdown_to_dataframe(mt))
#             for d in df_table:
#                 return_md_tables.append(dataframe_to_markdown(d))
#
#     for m in return_md_tables:
#         print(display_md_table(m))
#
#     return return_md_tables, res, content, usage, truncated