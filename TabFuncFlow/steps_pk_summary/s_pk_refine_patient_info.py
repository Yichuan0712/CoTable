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

(1) Identify all unique combinations of **[Population, Pregnancy stage, Gestational age, Pediatric age, Subject N]** from the table.
    - **Population**: The age group of the subjects.  
      **Common categories include:**  
        - "Maternal"  
        - "Preterm" or "Premature" (≤ 37 weeks of gestation)  
        - "Neonates" or "Newborns" (birth to 1 month)  
        - "Infants" (1 month to 1 year)  
        - "Children" (1 year to 12 years)  
        - "Adolescents" or "Teenagers" (13 years to 17 years)  
        - "Adults" (18 years or older)  
      
    - **Pregnancy stage**: The stage of pregnancy for the patients in the study.  
      **Common categories include:**  
        - "Trimester 1" (≤ 14 weeks of pregnancy)  
        - "Trimester 2" (15–28 weeks of pregnancy)  
        - "Trimester 3" (≥ 28 weeks of pregnancy)  
        - "Fetus" or "Fetal Stage" (developing baby during pregnancy)  
        - "Parturition," "Labor," or "Delivery" (process of childbirth)  
        - "Postpartum" (6–8 weeks after birth)  
        - "Nursing," "Breastfeeding," or "Lactation"  

    - **Gestational age**: The fetal or neonatal age (or age range) at a specific point in the study. Retain the original wording whenever possible.  
    - **Pediatric age**: The child's age (or age range) at a specific point in the study. Retain the original wording whenever possible.  
    - **Subject N**: The number of subjects corresponding to the specific population.

(2) Compile each unique combination in the format of a **list of lists**, using **Python string syntax**.  
   - Your response should be enclosed in **double angle brackets** `<< >>` and formatted as a **single line**.

(3) For each Population, determine whether it can be classified under one of the common categories listed above. If it does, replace it with the corresponding standard category. If it does not fit any common category, retain the original wording.

(4) For each Pregnancy Stage, check whether it aligns with any of the common categories. If it does, replace it with the corresponding standard category. If it does not fit any common category, keep the original wording unchanged.

(5) If any information is missing, attempt to infer it based on available data (e.g., context, related entries, or common pharmacokinetic knowledge).  
   - Only use **"N/A"** if the information **cannot** be reasonably inferred.
   
(6) Strictly ensure that you process only rows 0 to {markdown_to_dataframe(patient_md_table).shape[0] - 1} from the Subtable 1 (which has {markdown_to_dataframe(patient_md_table).shape[0]} rows in total).   
    - The number of processed rows must **exactly match** the number of rows in the Subtable 1—no more, no less.  

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
            print(content)

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
                    raise ValueError(f"Failed to parse refined population information. {e}") from e
            else:
                raise ValueError(f"No refined population information found in the content.")

            if not match_list:
                raise ValueError(f"Population information refinement failed: No valid entries found!")

            expected_rows = markdown_to_dataframe(patient_md_table).shape[0]
            if len(match_list) != expected_rows:
                messages = [msg, "Wrong answer example:\n" + content + f"\nWhy it's wrong:\nMismatch: Expected {expected_rows} rows, but got {len(match_list)} extracted matches."]
                raise ValueError(
                    f"Mismatch: Expected {expected_rows} rows, but got {len(match_list)} extracted matches."
                )

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

    raise RuntimeError(f"All {max_retries} attempts failed. Unable to refine population information.")
