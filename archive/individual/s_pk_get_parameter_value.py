import ast
from TabFuncFlow.utils.llm_utils import *
from TabFuncFlow.operations.f_transpose import *
import pandas as pd
import re
import time


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

**Parameter type, Parameter unit, Parameter value, Time value, Time unit** 

- **Parameter type:** The type of pharmacokinetic parameter (e.g., "Concentration", "Cmax", "Tmax" etc.), keep it simple
- **Parameter unit:** The unit corresponding to the parameter (e.g., "ng/mL", "mg·h/L", "hour").  
- **Parameter value:** The numerical value of the parameter extracted from Subtable 1.  
- **Time value:** A specific moment (numerical or time range) when the row of data is recorded, or a drug dose is administered.  
- **Time unit:** The unit corresponding to the recorded time point (e.g., "Hour", "Min", "Day").  

Please Note:
(1) For values that do not need to be filled, enter "N/A".
(3) Strictly ensure that you process only rows 0 to {markdown_to_dataframe(md_table_aligned_with_1_param_type_and_value).shape[0] - 1} from the Subtable 1 (which has {markdown_to_dataframe(md_table_aligned_with_1_param_type_and_value).shape[0]} rows in total). 
    - The number of processed rows must **exactly match** the number of rows in the Subtable 1—no more, no less.  
(4) For rows in Subtable 1 that can not be extracted, enter "N/A" for the entire row.
(5) **Important:** Please return Subtable 2 as a list of lists, excluding the headers. Ensure all values are converted to strings.
(6) **Absolutely no calculations are allowed—every value must be taken directly from Subtable 1 without any modifications.**  
(7) Format the final list within double angle brackets, like this:
<<[["IFX Dose", "mg/kg", "1", "N/A", "N/A"], ["IFX at Birth", "μg/ml", "4.4", "N/A", "N/A"]]>>
"""


def s_pk_get_parameter_value(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value, model_name="gemini_15_pro", max_retries=5, initial_wait=1):
    msg = s_pk_get_parameter_value_prompt(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value)
    messages = [msg]
    question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."

    retries = 0
    wait_time = initial_wait
    total_usage = 0
    all_content = []

    while retries < max_retries:
        try:
            res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
            content = fix_angle_brackets(content)

            total_usage += usage
            all_content.append(f"Attempt {retries + 1}:\n{content}")

            content = content.replace('\n', '')
            matches = re.findall(r'<<.*?>>', content)

            if not matches:
                raise ValueError(f"No valid parameter values found.")

            extracted_data = matches[-1][2:-2]

            try:
                match_list = ast.literal_eval(fix_trailing_brackets(extracted_data))
            except (SyntaxError, ValueError) as e:
                raise ValueError(f"Failed to parse parameter values: {e}") from e

            if not isinstance(match_list, list):
                raise ValueError(
                    f"Parsed content is not a valid list: {match_list}"
                )

            if not match_list:
                raise ValueError(
                    f"Parameter value extraction failed: No valid values found."
                )

            expected_columns = [
                'Parameter type', 'Parameter unit', 'Parameter value', 'Time value', 'Time unit'
            ]

            for row in match_list:
                if len(row) != len(expected_columns):
                    messages = [msg,
                                "Wrong answer example:\n" + content + f"\nWhy it's wrong:\nInvalid data format: Expected {len(expected_columns)} columns per row, but got {len(row)}.\nRow: {row}"]
                    raise ValueError(
                        f"Invalid data format: Expected {len(expected_columns)} columns per row, but got {len(row)}.\nRow: {row}"
                    )

            df_table = pd.DataFrame(match_list, columns=expected_columns)

            expected_rows = markdown_to_dataframe(md_table_aligned_with_1_param_type_and_value).shape[0]
            if df_table.shape[0] != expected_rows:
                messages = [msg,
                            "Wrong answer example:\n" + content + f"\nWhy it's wrong:\nMismatch: Expected {expected_rows} rows, but got {df_table.shape[0]} extracted values."]
                raise ValueError(
                    f"Mismatch: Expected {expected_rows} rows, but got {df_table.shape[0]} extracted values."
                )

            return_md_table = dataframe_to_markdown(df_table)

            return return_md_table, res, "\n\n".join(all_content), total_usage, truncated

        except (RuntimeError, ValueError) as e:
            retries += 1
            print(f"Attempt {retries}/{max_retries} failed: {e}")

            if retries < max_retries:
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                wait_time *= 2

    raise RuntimeError(f"All {max_retries} attempts failed. Unable to extract parameter values.")
