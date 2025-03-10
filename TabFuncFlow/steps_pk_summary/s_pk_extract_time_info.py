import ast
from TabFuncFlow.utils.llm_utils import *
from TabFuncFlow.operations.f_transpose import *
import pandas as pd
import time
import re


def s_pk_extract_time_info_prompt(md_table, caption):
    return f"""
The following table contains pharmacokinetics (PK) data:  
{display_md_table(md_table)}
Here is the table caption:  
{caption}
Carefully analyze the table and follow these steps:  
(1) Identify how many unique [Time value, Time unit] combinations are present in the table.  
- **Time Value:** A specific moment (numerical or time range) when data is recorded, a drug dose is administered, or any other relevant event occurs.  
  - Examples: Sampling times, dosing times, or reported observation times.  
  - **DO NOT include half-lives (T½ Beta), elimination rate constants (Beta), or other PK parameters unless they explicitly represent a measurement time.**  
- **Time Unit:** The unit corresponding to the recorded time point (e.g., "Hour", "Min", "Day").  
(2) List each unique combination in the format of a list of lists, using Python string syntax. Your answer should be enclosed in double angle brackets, like this:  
   <<[["0-1", "Hour"], ["10", "Min"]]>> (example)  
(3) Verify the source of each [Time value, Time unit] combination before including it in your answer.  
(4) **Absolutely no calculations are allowed—every value must be taken directly from the table without any modifications.** 
(5) **If no valid [Time value, Time unit] combinations are found, return the default output:**  
    **<<[["N/A", "N/A"]]>>**  

**Examples:**
Include:  
   - "0-12" (indicating a dosing period)  
   - "24" (indicating a time of sample collection)  
   - "5 min" (indicating a measured event)  

Do NOT include:  
   - "T½Beta(hr)" values (half-life, not a recorded time)  
   - "Beta(hr)" values (elimination rate constant)  
   
"""


def s_pk_extract_time_info(md_table, caption, model_name="gemini_15_pro", max_retries=5, initial_wait=1):
    msg = s_pk_extract_time_info_prompt(md_table, caption)
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
                    raise ValueError(f"Failed to parse extracted time information. {e}") from e
            else:
                raise ValueError("No time information found in the extracted content.")

            if not match_list:
                raise ValueError("Time information extraction failed: No valid entries found!")

            df_table = pd.DataFrame(match_list, columns=["Time value", "Time unit"])
            return_md_table = dataframe_to_markdown(df_table)

            return return_md_table, res, "\n\n".join(all_content), total_usage, truncated

        except Exception as e:
            retries += 1
            print(f"Attempt {retries}/{max_retries} failed: {e}")
            if retries < max_retries:
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                wait_time *= 2

    raise RuntimeError(f"All {max_retries} attempts failed. Unable to extract time information.")
