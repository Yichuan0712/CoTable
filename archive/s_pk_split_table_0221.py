import ast
from utils.table_utils import *
from utils.llm_utils import *
from archive.f_split_table import *


def s_pk_split_table_prompt(md_table):
    return f"""
There is now a table related to pharmacokinetics (PK). 
{display_md_table(md_table)}
Carefully examine the table and follow these steps:
(1) Determine if this table has subtables.
(2) If it has, specify whether the division should be by rows, columns, or both.
(3) If there is any index or descriptor column or row (e.g., "PK parameter") that applies to all groups when splitting by columns or rows, ensure this descriptor is included in every subgroup created from the split.
(4) Important note: Pay attention to repeating column names, such as "N," "N_1," and "N_2," which indicates that the columns can certainly be divided into at least three groups.
If the table cannot be divided into subtables either by rows or columns, return [[END]].
If it can be divided, please use the following function to create a new table:
f_split_table(row_groups, col_groups)
Replace row_groups with row indices in the following format:
row_groups = [[0, 1, 2], [3, 4, 5]] (example)
Replace col_groups with column names in the following format:
col_groups = [["ColumnA", "ColumnB", "ColumnC", "ColumnG"], ["ColumnA", "ColumnD", "ColumnE", "ColumnF", "ColumnG"]] (example)
When returning this, enclose the function call in double angle brackets, like this:
<<f_split_table([[0, 1, 2], [3, 4, 5]], [["ColumnA", "ColumnB", "ColumnC", "ColumnG"], ["ColumnA", "ColumnD", "ColumnE", "ColumnF", "ColumnG"]])>>
"""


def s_pk_split_table_parse(content):
    content = content.replace('\n', '')
    content = content.replace(' ', '')

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


def adjust_splits(row_groups, col_groups, df_table):
    """
    Shit happens.
    I wipe.
    """
    _row_groups = row_groups.copy()
    _col_groups = col_groups.copy()

    # remove wrong names
    for col_list in _col_groups:
        if False in col_list:
            col_list.remove(False)

    # remove duplicate
    def remove_duplicates_keep_order(groups):
        seen = set()
        new_groups = []
        for group in groups:
            t_group = tuple(group)
            if t_group not in seen:
                seen.add(t_group)
                new_groups.append(group)
        return new_groups

    _col_groups = remove_duplicates_keep_order(_col_groups)
    _row_groups = remove_duplicates_keep_order(_row_groups)


    # remove sublists
    def remove_sublists(list_of_lists):
      sets = [set(sublist) for sublist in list_of_lists]
      keep_indices = set(range(len(list_of_lists)))
      for i in range(len(sets)):
          for j in range(len(sets)):
              if i != j and sets[i].issubset(sets[j]):
                  keep_indices.discard(i)
                  break
      return [list_of_lists[i] for i in keep_indices]
    _row_groups = remove_sublists(_row_groups)
    _col_groups = remove_sublists(_col_groups)

    return _row_groups, _col_groups


def s_pk_split_table(md_table, model_name="gemini_15_pro"):
    msg = s_pk_split_table_prompt(md_table)

    messages = [msg, ]
    question = ""

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)

    print(content)

    row_groups, col_groups = s_pk_split_table_parse(content)

    if row_groups is None and col_groups is None:
        col_groups = [markdown_to_dataframe(md_table).columns.tolist()]
        row_groups = [markdown_to_dataframe(md_table).index.tolist()]

    col_groups = [[fix_col_name(item, md_table) for item in group] for group in col_groups]

    _row_groups, _col_groups = adjust_splits(row_groups, col_groups, markdown_to_dataframe(md_table))

    if _row_groups != row_groups or _col_groups != col_groups:
        content += "\n\nYICHUAN: ERROR DETECTED\n\n"

    print(_row_groups)
    print(_col_groups)

    df_subtables = f_split_table(_row_groups, _col_groups, markdown_to_dataframe(md_table))

    md_subtables = {}
    for key, value in df_subtables.items():
        md_subtables[key] = dataframe_to_markdown(value)

    return md_subtables, res, content, usage, truncated
