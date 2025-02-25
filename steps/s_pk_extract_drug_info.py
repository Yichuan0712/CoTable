import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_transpose import *


def s_pk_extract_drug_info_prompt(md_table, caption):
    return f"""
The following table contains pharmacokinetics (PK) data:  
{display_md_table(md_table)}
Here is the table caption:  
{caption}
Carefully analyze the table and follow these steps:  
(1) Identify how many unique [Drug Name, Analyte, Specimen] combinations are present in the table.  
(2) List each unique combination in the format of a list of lists, using Python string syntax. Your answer should be enclosed in double angle brackets, like this:  
   <<[["Lorazepam", "Lorazepam", "Plasma"], ["Lorazepam", "Lorazepam", "Urine"]]>> (example)  
(3) Verify the source of each [Drug Name, Analyte, Specimen] combination before including it in your answer.  
(4) If any information is missing, use "N/A" as a placeholder.  
"""


def s_pk_extract_drug_info_parse(content):
    content = content.replace('\n', '')
    content = content.replace(' ', '')

    match_angle = re.search(r'<<.*?>>', content)

    if match_angle:
        match_list = match_angle.group()[2:-2]
        return match_list
    else:
        raise NotImplementedError


def s_pk_extract_drug_info(md_table, model_name="gemini_15_pro"):
    msg = s_pk_extract_drug_info_prompt(md_table)

    messages = [msg, ]
    question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
    # print(display_md_table(md_table))
    print(usage, content)

    match_list = s_pk_extract_drug_info_parse(content)

    if match_list:
        df_table = pd.DataFrame(match_list, columns=["Drug Name", "Analyte", "Specimen"])
        return_md_table = dataframe_to_markdown(df_table)
        print(display_md_table(return_md_table))
    else:
        NotImplementedError

    return return_md_table, res, content, usage, truncated
