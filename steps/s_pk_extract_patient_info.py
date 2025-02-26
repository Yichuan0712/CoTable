import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_transpose import *
import pandas as pd


def s_pk_extract_patient_info_prompt(md_table, caption):
    return f"""
The following table contains pharmacokinetics (PK) data:  
{display_md_table(md_table)}
Here is the table caption:  
{caption}
Carefully analyze the table and follow these steps:  
(1) Identify how many unique [Population, Pregnancy Stage, Subject N] combinations are present in the table.  
Population is the patient age group.
Pregnancy stage is the pregnancy stages of patients mentioned in the study.
Subject N is the number of subjects that correspond to the specific parameter.
(2) List each unique combination in the format of a list of lists, using Python string syntax. Your answer should be enclosed in double angle brackets <<>>. 
(3) Verify the source of each [Population, Pregnancy Stage, Subject N] combination before including it in your answer.  
(4) If any information is missing, first try to infer it from the available data (e.g., using context, related entries, or common pharmacokinetic knowledge). Only use "N/A" as a last resort if the information cannot be reasonably inferred. 
"""


def s_pk_extract_patient_info_parse(content):
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
        raise NotImplementedError


def s_pk_extract_patient_info(md_table, caption, model_name="gemini_15_pro"):
    msg = s_pk_extract_patient_info_prompt(md_table, caption)

    messages = [msg, ]
    question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
    # print(display_md_table(md_table))
    print(usage, content)

    match_list = s_pk_extract_patient_info_parse(content)

    match_list = list(map(list, set(map(tuple, match_list))))

    if match_list:
        df_table = pd.DataFrame(match_list, columns=["Population", "Pregnancy stage", "Subject N"])
        return_md_table = dataframe_to_markdown(df_table)
        print(display_md_table(return_md_table))
        return return_md_table, res, content, usage, truncated
    else:
        NotImplementedError
