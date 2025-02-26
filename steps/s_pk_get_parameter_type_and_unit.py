import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_transpose import *
import pandas as pd
from difflib import get_close_matches


def s_pk_get_parameter_type_and_unit_prompt(match_dict, md_table, caption):
    parameter_type_count = list(match_dict.values()).count("Parameter type")
    parameter_unit_count = list(match_dict.values()).count("Parameter unit")
    if parameter_type_count == 1 and parameter_unit_count == 0:
        key_with_parameter_type = [key for key, value in match_dict.items() if value == "Parameter type"][0]
        return f"""
    The following table contains pharmacokinetics (PK) data:  
    {display_md_table(md_table)}
    Here is the table caption:  
    {caption}
    请注意{key_with_parameter_type}这一列是parameter type
    Carefully analyze the table and follow these steps:  
    (1) 将{key_with_parameter_type}这一列变成两列, 分别是"Parameter type"和"Parameter unit"
    (2) 返回一个字典, 字典的两个key 分别是"Parameter type", "Parameter unit", 他们的值都是字符串列表
    (3) 返回的字典应该be enclosed in double angle brackets <<>>
    """


def s_pk_get_parameter_type_and_unit_parse(content):
    content = content.replace('\n', '')
    # content = content.replace(' ', '')

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


def s_pk_get_parameter_type_and_unit(match_dict, md_table, caption, model_name="gemini_15_pro"):
    parameter_type_count = list(match_dict.values()).count("Parameter type")
    parameter_unit_count = list(match_dict.values()).count("Parameter unit")
    if parameter_type_count == 1 and parameter_unit_count == 1:
        return None, True, "Skipped", 0, False
    elif parameter_type_count == 1 and parameter_unit_count == 0:
        msg = s_pk_get_parameter_type_and_unit_prompt(match_dict, md_table, caption)

        messages = [msg, ]
        question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."

        res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
        # print(display_md_table(md_table))
        print(usage, content)


