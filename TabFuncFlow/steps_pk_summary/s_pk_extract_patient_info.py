import ast
from TabFuncFlow.utils.llm_utils import *
from TabFuncFlow.operations.f_transpose import *
import pandas as pd
import time
import re


def extract_integers(text):
    """
    Extract only "pure integers":
    - Skip numbers with decimal points (including forms like 3.14, 1.0, .99, etc.)
    - Skip numbers immediately followed (possibly with spaces) by '%' or '％' (e.g., 8%, 8 %)
    - Keep only integers like 42, 100, etc.
    - Remove duplicates and exclude 0
    """
    # 1) (?<![\d.]) ensures that the left side is not a digit or a dot.
    # 2) (\d+) matches a sequence of digits.
    # 3) (?![\d.]| *[%％]) ensures that the right side is not a digit, a dot,
    #    or zero or more spaces followed by '%' or '％'.
    pattern = r'(?<![\d.])(\d+)(?![\d.]| *[%％])'

    # Convert matched digit-strings to integers, use a set to remove duplicates,
    # then remove 0 if present
    return list(
        set(
            int(num_str)
            for num_str in re.findall(pattern, text)
        ) - {0}
    )

#         **If the study provides a more specific description, please retain the original terminology whenever possible.**
def s_pk_extract_patient_info_prompt(md_table, caption):
    int_list = extract_integers(md_table+caption)
    # print("*"*32)
    # print(int_list)
    # print("*"*32)
    return f"""
The following table contains pharmacokinetics (PK) data:  
{display_md_table(md_table)}
Here is the table caption:  
{caption}
Carefully analyze the table, **row by row and column by column**, and follow these steps:  
(1) Identify how many unique [Population, Pregnancy stage, Gestational age, Pediatric age, Subject N] combinations are present in the table.  
    - Population is the patient age group. 
        **Common categories include:**
        "Maternal"
        "Preterm" or "premature": ≤ 37 weeks of gestation
        "Neonates" or "Newborns": from birth to 1 month
        "Infants": 1 month to 1 year 
        "Children": 1 year through 12 years
        "Adolescents" or "Teenagers": 13 years through 17 years
        "Adults": 18 years or older

    - Pregnancy stage is the pregnancy stages of patients mentioned in the study.
        **Common categories include:**
        "Trimester 1": ≤ 14 weeks of pregnancy
        "Trimester 2": 15-28 weeks of pregnancy
        "Trimester 3": ≥ 28 weeks of pregnancy
        "Fetus" or "Fetal stage": baby during the pregnancy stage
        "Parturition," "Labor," or "Delivery": process of giving birth
        "Postpartum": 6-8 weeks (about 2 months) after birth of baby
        "Nursing," "Breast feeding," or "Lactation"

    - Gestational age refers to the fetal or neonatal age (or age range) at a specific point in the study. Please retain the original wording whenever possible.
    - Pediatric age refers to the child’s age (or age range) at a specific point in the study. Please retain the original wording whenever possible.
    - Subject N is the number of subjects that correspond to the specific population.
(2) List each unique combination in the format of a list of lists in one line, using Python string syntax. Your answer should be enclosed in double angle brackets <<>>. 
(3) Verify the source of each [Population, Pregnancy stage, Gestational age, Pediatric age, Subject N] combination before including it in your answer.  
(4) The "Subject N" values within each population group sometimes differ slightly across parameters. This reflects data availability for each specific parameter within that age group. You must include all the Ns for each age group. 
Specifically, make sure to check every number in this list: {int_list} to determine if it should be listed in Subject N. Fill in "N/A" when you don't know the exact N.
(5) If any information is missing, first try to infer it from the available data (e.g., using context, related entries, or common pharmacokinetic knowledge). Only use "N/A" as a last resort if the information cannot be reasonably inferred. 
"""


def s_pk_extract_patient_info(md_table, caption, model_name="gemini_15_pro", max_retries=5, initial_wait=1):
    msg = s_pk_extract_patient_info_prompt(md_table, caption)
    msg = fix_angle_brackets(msg)
    messages = [msg]
    question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."

    retries = 0
    wait_time = initial_wait
    total_usage = 0
    all_content = []

    while retries < max_retries:
        try:
            res, content, usage, truncated = get_llm_response(messages, question, model=model_name)

            total_usage += usage
            all_content.append(f"Attempt {retries + 1}:\n{content}")

            content = content.replace('\n', '')
            matches = re.findall(r'<<.*?>>', content)
            match_angle = matches[-1] if matches else None

            if match_angle:
                try:
                    match_list = ast.literal_eval(match_angle[2:-2])
                    match_list = list(map(list, set(map(tuple, match_list))))
                except Exception as e:
                    raise ValueError(f"Failed to parse extracted population information. {e}") from e
            else:
                raise ValueError(f"No population information found in the extracted content.")

            if not match_list:
                raise ValueError(f"Population information extraction failed: No valid entries found!")

            df_table = pd.DataFrame(match_list, columns=["Population", "Pregnancy stage", "Gestational age", "Pediatric age", "Subject N"])
            return_md_table = dataframe_to_markdown(df_table)

            return return_md_table, res, "\n\n".join(all_content), total_usage, truncated

        except Exception as e:
            retries += 1
            print(f"Attempt {retries}/{max_retries} failed: {e}")
            if retries < max_retries:
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                wait_time *= 2

    raise RuntimeError(f"All {max_retries} attempts failed. Unable to extract population information.")

# def s_pk_extract_patient_info_prompt(md_table, caption):
#     int_list = extract_integers(md_table+caption)
#     # print("*"*32)
#     # print(int_list)
#     # print("*"*32)
#     return f"""
# The following table contains pharmacokinetics (PK) data:
# {display_md_table(md_table)}
# Here is the table caption:
# {caption}
# Carefully analyze the table, **row by row and column by column**, and follow these steps:
# (1) Identify how many unique [Population, Pregnancy stage, Subject N] combinations are present in the table.
# Population is the patient age group.
# Pregnancy stage is the pregnancy stages of patients mentioned in the study.
# Subject N is the number of subjects that correspond to the specific parameter.
# (2) List each unique combination in the format of a list of lists in one line, using Python string syntax. Your answer should be enclosed in double angle brackets <<>>.
# (3) Verify the source of each [Population, Pregnancy stage, Subject N] combination before including it in your answer.
# (4) The "Subject N" values within each population group sometimes differ slightly across parameters. This reflects data availability for each specific parameter within that age group. You must include all the Ns for each age group.
# Specifically, make sure to check every number in this list: {int_list} to determine if it should be listed in Subject N. Fill in "N/A" when you don't know the exact N.
# (5) If any information is missing, first try to infer it from the available data (e.g., using context, related entries, or common pharmacokinetic knowledge). Only use "N/A" as a last resort if the information cannot be reasonably inferred.
# """
#
#
# def s_pk_extract_patient_info(md_table, caption, model_name="gemini_15_pro", max_retries=5, initial_wait=1):
#     msg = s_pk_extract_patient_info_prompt(md_table, caption)
#     msg = fix_angle_brackets(msg)
#     messages = [msg]
#     question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."
#
#     retries = 0
#     wait_time = initial_wait
#     total_usage = 0
#     all_content = []
#
#     while retries < max_retries:
#         try:
#             res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
#
#             total_usage += usage
#             all_content.append(f"Attempt {retries + 1}:\n{content}")
#
#             content = content.replace('\n', '')
#             matches = re.findall(r'<<.*?>>', content)
#             match_angle = matches[-1] if matches else None
#
#             if match_angle:
#                 try:
#                     match_list = ast.literal_eval(match_angle[2:-2])
#                     match_list = list(map(list, set(map(tuple, match_list))))
#                 except Exception as e:
#                     raise ValueError(f"Failed to parse extracted population information. {e}") from e
#             else:
#                 raise ValueError(f"No population information found in the extracted content.")
#
#             if not match_list:
#                 raise ValueError(f"Population information extraction failed: No valid entries found!")
#
#             df_table = pd.DataFrame(match_list, columns=["Population", "Pregnancy stage", "Subject N"])
#             return_md_table = dataframe_to_markdown(df_table)
#
#             return return_md_table, res, "\n\n".join(all_content), total_usage, truncated
#
#         except Exception as e:
#             retries += 1
#             print(f"Attempt {retries}/{max_retries} failed: {e}")
#             if retries < max_retries:
#                 print(f"Retrying in {wait_time} seconds...")
#                 time.sleep(wait_time)
#                 wait_time *= 2
#
#     raise RuntimeError(f"All {max_retries} attempts failed. Unable to extract population information.")
