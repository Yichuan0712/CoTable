import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_transpose import *
import pandas as pd
from difflib import get_close_matches


def s_pk_get_col_mapping_prompt(md_table):
    df = markdown_to_dataframe(md_table)  # Assuming this is your DataFrame
    column_headers_str = 'These are all its column headers: ' + ", ".join(f'"{col}"' for col in df.columns)
    return f"""
The following table contains pharmacokinetics (PK) data:  
{display_md_table(md_table)}
{column_headers_str}
Carefully analyze the table and follow these steps:  
(1) Examine all column headers and categorize each one into one of the following groups:  
   - **"Parameter type"**: Columns that describe the type of pharmacokinetic parameter.  
   - **"Parameter unit"**: Columns that specify the unit of the parameter type.  
   - **"Parameter value"**: Columns that contain numerical parameter values.  
   - **"P value"**: Columns that represent statistical P values.  
   - **"Uncategorized"**: Columns that do not fit into any of the above categories. 
(2) Return a dictionary where each key is a column header, and the corresponding value is its assigned category. Your dictionary should be enclosed in double angle brackets <<>>. 
"""


def s_pk_get_col_mapping_parse(content):
    content = content.replace('\n', '')
    # content = content.replace(' ', '')

    # match_col = re.search(r'\[\[COL\]\]', content)
    # match_angle = re.search(r'<<.*?>>', content)
    matches = re.findall(r'<<.*?>>', content)
    match_angle = matches[-1] if matches else None

    if match_angle:
        match_dict = match_angle[2:-2]
        match_dict = ast.literal_eval(match_dict)
        return match_dict
    else:
        raise NotImplementedError


def s_pk_get_col_mapping(md_table, model_name="gemini_15_pro"):
    msg = s_pk_get_col_mapping_prompt(md_table)

    messages = [msg, ]
    question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
    # print(display_md_table(md_table))
    print(usage, content)

    match_dict = s_pk_get_col_mapping_parse(content)

    match_dict = {fix_col_name(k, md_table): get_close_matches(v, ["Parameter value", "P value", "Parameter type",
                                                                   "Parameter unit", "Uncategorized"], n=1)[0] for
                  k, v in match_dict.items()}

    assert len(match_dict.keys()) == markdown_to_dataframe(md_table).shape[1]

    if match_dict:
        parameter_type_count = list(match_dict.values()).count("Parameter type")
        if parameter_type_count != 1:
            raise ValueError
        # print(match_dict)
        return match_dict, res, content, usage, truncated
    else:
        NotImplementedError

# 检查是否包含所有列标题

# 三种情况 多个parameter type (似乎不太可能出现), 多个, pvalue, unit如果有应该和type一样多
# 必须解决unit问题
# count = sum(1 for v in match_dict.values() if v == "Parameter type")
#
# if count > 1:
#     raise ValueError(f'Error: "Parameter type" appears {count} times in match_dict!')