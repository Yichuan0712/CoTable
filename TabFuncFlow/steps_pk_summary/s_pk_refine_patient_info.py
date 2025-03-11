import ast
from TabFuncFlow.utils.llm_utils import *
from TabFuncFlow.operations.f_transpose import *
import re
import time


def s_pk_refine_patient_info_prompt(md_table_aligned, caption, patient_md_table):
    return f"""
The following main table contains pharmacokinetics (PK) data:  
{display_md_table(md_table_aligned)}
Here is the table caption:  
{caption}
From the main table above, I have extracted the following information to create Subtable 1, where each row represents a unique combination of "Population" - "Pregnancy stage" - "Subject N," as follows:
{display_md_table(patient_md_table)}
Carefully analyze the tables and follow these steps to refine Subtable 1 into a more detailed Subtable 2:  

(1) Identify all unique combinations of **[Population, Pregnancy Stage, Gestational Age, Pediatric Age, Subject N]** from the table.
    - **Population**: The age group of the subjects.  
      **Common categories include:**  
        - "Maternal"  
        - "Preterm" or "Premature" (≤ 37 weeks of gestation)  
        - "Neonates" or "Newborns" (birth to 1 month)  
        - "Infants" (1 month to 1 year)  
        - "Children" (1 year to 12 years)  
        - "Adolescents" or "Teenagers" (13 years to 17 years)  
        - "Adults" (18 years or older)  
      
    - **Pregnancy Stage**: The stage of pregnancy for the patients in the study.  
      **Common categories include:**  
        - "Trimester 1" (≤ 14 weeks of pregnancy)  
        - "Trimester 2" (15–28 weeks of pregnancy)  
        - "Trimester 3" (≥ 28 weeks of pregnancy)  
        - "Fetus" or "Fetal Stage" (developing baby during pregnancy)  
        - "Parturition," "Labor," or "Delivery" (process of childbirth)  
        - "Postpartum" (6–8 weeks after birth)  
        - "Nursing," "Breastfeeding," or "Lactation"  

    - **Gestational Age**: The fetal or neonatal age (or age range) at a specific point in the study. Retain the original wording whenever possible.  
    - **Pediatric Age**: The child's age (or age range) at a specific point in the study. Retain the original wording whenever possible.  
    - **Subject N**: The number of subjects corresponding to the specific population.

(2) Compile each unique combination in the format of a **list of lists**, using **Python string syntax**.  
   - Your response should be enclosed in **double angle brackets** `<< >>` and formatted as a **single line**.

(3) Verify the source of each **[Population, Pregnancy Stage, Gestational Age, Pediatric Age, Subject N]** combination before including it in your response.

(4) If any information is missing, attempt to infer it based on available data (e.g., context, related entries, or common pharmacokinetic knowledge).  
   - Only use **"N/A"** if the information **cannot** be reasonably inferred.

"""
# (3) If a row in Subtable 1 cannot be matched, return -1 for that row.


def s_pk_refine_patient_info(md_table_aligned, caption, patient_md_table, model_name="gemini_15_pro", max_retries=5, initial_wait=1):
    msg = s_pk_refine_patient_info_prompt(md_table_aligned, caption, patient_md_table)
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

            if not matches:
                raise ValueError(f"No valid matched patient information found.")

            extracted_data = matches[-1][2:-2]

            try:
                match_list = ast.literal_eval(extracted_data)
            except (SyntaxError, ValueError) as e:
                raise ValueError(f"Failed to parse matched patient info: {e}") from e

            if not isinstance(match_list, list):
                raise ValueError(
                    f"Parsed content is not a valid list: {match_list}"
                )

            if not match_list:
                raise ValueError(
                    f"Patient information matching failed: No valid matches found."
                )

            expected_rows = markdown_to_dataframe(patient_md_table).shape[0]
            if len(match_list) != expected_rows:
                messages = [msg, "Wrong answer example:\n" + content + f"\nWhy it's wrong:\nMismatch: Expected {expected_rows} rows, but got {len(match_list)} extracted matches."]
                raise ValueError(
                    f"Mismatch: Expected {expected_rows} rows, but got {len(match_list)} extracted matches."
                )

            return match_list, res, "\n\n".join(all_content), total_usage, truncated

        except (RuntimeError, ValueError) as e:
            retries += 1
            print(f"Attempt {retries}/{max_retries} failed: {e}")
            if retries < max_retries:
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                wait_time *= 2

    raise RuntimeError(f"All {max_retries} attempts failed. Unable to match patient information.")

