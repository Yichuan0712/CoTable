import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_split_by_cols import *


def s_pk_split_by_cols_prompt(md_table, col_mapping):
    """
    Generates a structured prompt for splitting a pharmacokinetics (PK) table into sub-tables
    based on column classifications.

    Args:
        md_table (str): Markdown representation of the table.
        col_mapping (dict): Dictionary mapping column names to their respective categories.

    Returns:
        str: A formatted prompt guiding the splitting process.
    """
    mapping_str = "\n".join(f'"{k}" is categorized as "{v},"' for k, v in col_mapping.items())

    # Count occurrences of specific categories
    parameter_type_count = sum(1 for v in col_mapping.values() if v == "Parameter type")
    parameter_pvalue_count = sum(1 for v in col_mapping.values() if v == "P value")

    # Identify the situation based on category counts
    if parameter_pvalue_count > 1 and parameter_type_count <= 1:
        situation_str = "because there are multiple columns categorized as \"P value\","
    elif parameter_type_count > 1 and parameter_pvalue_count <= 1:
        situation_str = "because there are multiple columns categorized as \"Parameter type\","
    elif parameter_type_count > 1 and parameter_pvalue_count > 1:
        situation_str = "because there are multiple columns categorized as both \"Parameter type\" and \"P value\","
    else:
        situation_str = ""

    return f"""
There is a table related to pharmacokinetics (PK):
{display_md_table(md_table)}

This table contains multiple columns, categorized as follows:
{mapping_str}

This table can be split into multiple sub-tables {situation_str}.
Please follow these steps:
  (1) Carefully review all columns and analyze their relationships to determine logical groupings.
  (2) Ensure that each group contains exactly one 'Parameter type' column and at most one 'P value' column.

Return the results as a list of lists, where each inner list represents a sub-table with its included columns.
Enclose the final list within double angle brackets (<< >>) like this:
<<[["ColumnA", "ColumnB", "ColumnC", "ColumnG"], ["ColumnA", "ColumnD", "ColumnE", "ColumnF", "ColumnG"]]>>
"""


def s_pk_split_by_cols_parse(content):
    content = content.replace('\n', '')

    matches = re.findall(r'<<.*?>>', content)
    match_angle = matches[-1] if matches else None

    if match_angle:
        match_list = match_angle[2:-2]
        match_list = ast.literal_eval(match_list)
        return match_list
    else:
        raise NotImplementedError


def s_pk_split_by_cols(md_table, col_mapping, model_name="gemini_15_pro"):
    msg = s_pk_split_by_cols_prompt(md_table, col_mapping)

    messages = [msg, ]
    question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
    # print(display_md_table(md_table))
    # print(usage, content)

    col_groups = s_pk_split_by_cols_parse(content)
    if col_groups is None:
        NotImplementedError
        # return_md_tables = [md_table, ]
    else:
        col_groups = [[fix_col_name(item, md_table) for item in group] for group in col_groups]
        df_table = f_split_by_cols(col_groups, markdown_to_dataframe(md_table))
        return_md_table_list = []
        for d in df_table:
            return_md_table_list.append(dataframe_to_markdown(d))

    # for m in return_md_table_list:
        # print(display_md_table(m))

    return return_md_table_list, res, content, usage, truncated


# s_pk_split_by_cols(md_table_aligned, col_mapping, model_name="chatgpt_4o")
