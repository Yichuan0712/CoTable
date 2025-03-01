import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_transpose import *
import pandas as pd
from operations.f_select_row_col import *


def s_pk_match_patient_info_prompt(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value, patient_md_table):
    first_line = md_table_aligned_with_1_param_type_and_value.strip().split("\n")[0]
    headers = [col.strip() for col in first_line.split("|") if col.strip()]
    extracted_param_types = f""" "{'", "'.join(headers)}" """
    return f"""
The following main table contains pharmacokinetics (PK) data:  
{display_md_table(md_table_aligned)}
Here is the table caption:  
{caption}
From the main table above, I have extracted the following columns to create Subtable 1:  
{extracted_param_types}  
Below is Subtable 1:
{display_md_table(md_table_aligned_with_1_param_type_and_value)}
Additionally, I have compiled Subtable 2, where each row represents a unique combination of "Population" - "Pregnancy stage" - "Subject N," as follows:
{display_md_table(patient_md_table)}
Carefully analyze the tables and follow these steps:  
(1) For each row in Subtable 1, find a matching row in Subtable 2. Return a list of unique row indices (as integers) from Subtable 2 that correspond to each row in Subtable 1.  
(2) If a row in Subtable 1 is not correctly filled out (usually does not meet the requirements of the column headers), return -1 for that row.
(3) Format the final list within double angle brackets without removing duplicates or sorting, like this:
    <<[1,1,2,2,3,3]>>
"""


def s_pk_match_patient_info_parse(content):
    content = content.replace('\n', '')
    # content = content.replace(' ', '')
    # match_angle = re.search(r'<<.*?>>', content)
    matches = re.findall(r'<<.*?>>', content)
    match_angle = matches[-1] if matches else None

    if match_angle:
        match_list = match_angle[2:-2]
        match_list = ast.literal_eval(match_list)
        return match_list
    else:
        return None


def s_pk_match_patient_info(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value, patient_md_table, model_name="gemini_15_pro"):

    msg = s_pk_match_patient_info_prompt(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value, patient_md_table)

    messages = [msg, ]
    question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)

    print(usage, content)

    match_list = s_pk_match_patient_info_parse(content)
    if match_list is None:
        raise NotImplementedError
    else:
        assert len(match_list) == markdown_to_dataframe(md_table_aligned_with_1_param_type_and_value).shape[0]
        return match_list, res, content, usage, truncated

# md_table_aligned_with_1_param_type_and_value_list = get_1_param_type_and_value_sub_md_table_list(col_mapping, md_table_aligned)
# print(s_pk_match_patient_info(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value_list[1], md_table_patient))

