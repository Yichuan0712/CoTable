import re
import ast
from table_utils import *
from llm_utils import *
from operations.f_transpose import *
import pandas as pd
from difflib import get_close_matches


def s_pk_get_parameter_value_prompt(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value):
    # Extract the first line (headers) from the provided subtable
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
Please review the information in Subtable 1 row by row and complete Subtable 2.
Subtable 2 should have the following column headers only:  

**Main value, Statistics type, Variation type, Variation value, Interval type, Lower bound, Upper bound, P value** 

Main value: the value of main parameter (not a range). 
Statistics type: the statistics method to summary the Main value, like 'mean', 'median', etc.
Variation type: the variability measure (describes how spread out the data is) associated with the Main value, like 'standard deviation (SD),' 'CV%,' etc.
Variation value: the value (not a range) that corresponds to the specific variation.
Interval type: the type of interval that is being used to describe uncertainty or variability around a measure or estimate, like '95% CI,' 'range,' etc.
Lower bound: the lower bound value of the interval.
Upper bound: is the upper bound value of the interval.
P value: P-value.

Please Note:
(1) An interval consisting of two numbers must be placed separately into the Low limit and High limit fields; it is prohibited to place it in the Variation value field.
(2) For values that do not need to be filled, enter "N/A".
(3) **Important:** Please solve this problem using code and return Subtable 2 as a list of lists, excluding the headers. Ensure all values are converted to strings.
(4) **Absolutely no calculations are allowed—every value must be taken directly from Subtable 1 without any modifications.**  
(5) Format the final list within double angle brackets, like this:
<<[["0.162", "Mean", "SD", "0.090", "N/A", "N/A", "N/A", ".67"], ["0.428", "Mean", "SD", "0.162", "N/A", "N/A", "N/A", ".015"]]>>
"""


def s_pk_get_parameter_value_parse(content):
    content = content.replace('\n', '')
    # content = content.replace(' ', '')

    # match_angle = re.search(r'<<.*?>>', content)
    matches = re.findall(r'<<.*?>', content)
    match_angle = matches[-1] if matches else None

    if match_angle:
        match_list = match_angle[2:-1]
        match_list = ast.literal_eval(match_list)
        return match_list
    else:
        raise NotImplementedError


def s_pk_get_parameter_value(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value, model_name="gemini_15_pro"):
    msg = s_pk_get_parameter_value_prompt(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value)

    messages = [msg, ]
    # question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."
    question = "When writing code to solve a problem, do not give the final result immediately. First, explain your thought process in detail, including how you analyze the problem, choose an algorithm or approach, and implement key steps. Then, provide the final code solution."

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
    # print(display_md_table(md_table))
    print(usage, content)

    match_list = s_pk_get_parameter_value_parse(content)

    match_list = list(map(list, set(map(tuple, match_list))))

    if match_list:
        df_table = pd.DataFrame(match_list, columns=['Main value', 'Statistics type', 'Variation type', 'Variation value', 'Interval type', 'Lower limit', 'High limit', 'P value'])
        return_md_table = dataframe_to_markdown(df_table)
        # print(display_md_table(return_md_table))
        assert df_table.shape[0] == markdown_to_dataframe(md_table_aligned_with_1_param_type_and_value).shape[0]
        return return_md_table, res, content, usage, truncated
    else:
        NotImplementedError

# print(s_pk_get_parameter_value_prompt(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value))
# s_pk_get_parameter_value(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value, model_name="gemini_15_pro")