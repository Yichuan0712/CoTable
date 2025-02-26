import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_transpose import *
import pandas as pd
from difflib import get_close_matches


def s_pk_get_parameter_type_and_unit_prompt(match_dict, md_table, caption):
    # md_table = re.sub(r'[^\x00-\x7F]+', '', md_table)
    parameter_type_count = list(match_dict.values()).count("Parameter type")
    parameter_unit_count = list(match_dict.values()).count("Parameter unit")
    if parameter_type_count == 1 and parameter_unit_count == 0:
        key_with_parameter_type = [key for key, value in match_dict.items() if value == "Parameter type"][0]
        return f"""
The following table contains pharmacokinetic (PK) data:  
{display_md_table(md_table)}
Please note that the column "{key_with_parameter_type}" represents the parameter type.
Carefully analyze the table and follow these steps:  
(1) Split the column "{key_with_parameter_type}" into two separate lists: one for "Parameter type" and another for "Parameter unit".  
(2) Return a tuple containing two lists:  
    - The first list should contain the extracted "Parameter type" values.  
    - The second list should contain the corresponding "Parameter unit" values.  
(3) If a value is not a valid pharmacokinetic parameter type (e.g., it is a drug name or another non-parameter entry), assign "ERROR" to the corresponding "Parameter unit".  
(4) The returned list should be enclosed within double angle brackets, like this:  
    <<(["Parameter type 1", "Parameter type 2", ...], ["Unit 1", "Unit 2", ...])>>  
"""


def s_pk_get_parameter_type_and_unit_parse(content):
    content = content.replace('\n', '')
    # content = content.replace(' ', '')
    # match_angle = re.search(r'<<.*?>>', content)
    matches = re.findall(r'<<.*?>>', content)
    match_angle = matches[-1] if matches else None

    if match_angle:
        match_tuple = match_angle[2:-2]
        match_tuple = ast.literal_eval(match_tuple)
        return match_tuple
    else:
        return None


def s_pk_get_parameter_type_and_unit(col_dict, md_table, caption, model_name="gemini_15_pro"):
    parameter_type_count = list(col_dict.values()).count("Parameter type")
    parameter_unit_count = list(col_dict.values()).count("Parameter unit")
    if parameter_type_count == 1 and parameter_unit_count == 1:
        return None, True, "Skipped", 0, False
    elif parameter_type_count == 1 and parameter_unit_count == 0:
        msg = s_pk_get_parameter_type_and_unit_prompt(col_dict, md_table, caption)

        messages = [msg, ]
        question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."

        res, content, usage, truncated = get_llm_response(messages, question, model=model_name)

        print(usage, content)

        match_tuple = s_pk_get_parameter_type_and_unit_parse(content)
        if match_tuple is None:
            raise NotImplementedError
        else:
          return match_tuple, res, content, usage, truncated
    else:
        raise NotImplementedError

