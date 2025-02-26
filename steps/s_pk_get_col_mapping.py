import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_transpose import *
import pandas as pd
from difflib import get_close_matches


def s_pk_get_col_mapping_prompt(md_table):
    return f"""
The following table contains pharmacokinetics (PK) data:  
{display_md_table(md_table)}
Carefully analyze the table and follow these steps:  
(1) Examine all column headers and categorize each one into one of the following groups:  
   - **"Parameter value"**: Columns that contain numerical parameter values.  
   - **"P value"**: Columns that represent statistical P values.  
   - **"Parameter type"**: Columns that describe the type of pharmacokinetic parameter.  
   - **"Parameter type's unit"**: Columns that specify the unit of the parameter type.  
   - **"Uncategorized"**: Columns that do not fit into any of the above categories. 
(2) Return a dictionary where each key is a column header, and the corresponding value is its assigned category. Your dictionary should be enclosed in double angle brackets <<>>. 
"""

def s_pk_get_col_mapping_parse(content):
    content = content.replace('\n', '')
    content = content.replace(' ', '')

    match_col = re.search(r'\[\[COL\]\]', content)
    match_angle = re.search(r'<<.*?>>', content)

    if match_col:
        return None
    elif match_angle:
        match_dict = match_angle.group()[2:-2]
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
                                                                   "Parameter type's unit", "Uncategorized"], n=1) for
                  k, v in match_dict.items()}

    if match_dict:
        print(match_dict)
        return match_dict, res, content, usage, truncated
    else:
        NotImplementedError


# 三种情况 多个parameter type (似乎不太可能出现), 多个, pvalue, unit如果有应该和type一样多
# 必须解决unit问题
# count = sum(1 for v in match_dict.values() if v == "Parameter type")
#
# if count > 1:
#     raise ValueError(f'Error: "Parameter type" appears {count} times in match_dict!')