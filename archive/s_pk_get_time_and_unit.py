import ast
from TabFuncFlow.utils.llm_utils import *
from TabFuncFlow.operations.f_transpose import *
import pandas as pd


def s_pk_get_time_and_unit_prompt(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value):
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

**Time, Time unit** 

Time: The specific moment, expressed as numerical value, when data is measured, a drug dose is administered, or any other relevant event occurs. Only entries with concrete numerical value should be recorded.
Time unit: The unit of measurement corresponding to the recorded time point, ensuring clarity and precision in data representation.

Please Note:
(1) For values that do not need to be filled, enter "N/A".
(2) Strictly ensure that you process only rows 0 to {markdown_to_dataframe(md_table_aligned_with_1_param_type_and_value).shape[0] - 1} from the Subtable 1 (which has {markdown_to_dataframe(md_table_aligned_with_1_param_type_and_value).shape[0]} rows in total).  
    - The number of processed rows must **exactly match** the number of rows in the Subtable 1—no more, no less.  
(3) For rows that can not be extracted, enter "N/A" for the entire row.
(4) **Important:** Please return Subtable 2 as a list of lists, excluding the headers. Ensure all values are converted to strings.
(5) **Absolutely no calculations are allowed—every value must be taken directly from main table and its caption without any modifications.**  
(6) Format the final list within double angle brackets, like this:
<<[["0-24", "h"], ["10", "min"]]>>
"""


def s_pk_get_time_and_unit_parse(content, usage):
    content = content.replace('\n', '')
    matches = re.findall(r'<<.*?>>', content)
    match_angle = matches[-1] if matches else None

    if match_angle:
        try:
            match_list = ast.literal_eval(match_angle[2:-2])  # Extract list from `<<(...)>>`
            if not isinstance(match_list, list):
                raise ValueError(f"Parsed content is not a valid list: {match_list}", f"\n{content}", f"\n<<{usage}>>")
            return match_list
        except (SyntaxError, ValueError) as e:
            raise ValueError(f"Failed to parse parameter values: {e}", f"\n{content}", f"\n<<{usage}>>") from e
    else:
        raise ValueError("No valid parameter values found in content.", f"\n{content}", f"\n<<{usage}>>")  # Clearer error message


def s_pk_get_time_and_unit(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value, model_name="gemini_15_pro"):
    msg = s_pk_get_time_and_unit_prompt(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value)
    msg = fix_angle_brackets(msg)

    messages = [msg, ]
    question = "Do not give the final result immediately. First, explain your thought process, then provide the answer."
    # question = "When writing code to solve a problem, do not give the final result immediately. First, explain your thought process in detail, including how you analyze the problem, choose an algorithm or approach, and implement key steps. Then, provide the final code solution."

    res, content, usage, truncated = get_llm_response(messages, question, model=model_name)
    # print(display_md_table(md_table))
    # print(usage, content)

    try:
        match_list = s_pk_get_time_and_unit_parse(content, usage)  # Parse extracted values
    except Exception as e:
        raise RuntimeError(f"Error in s_pk_get_time_and_unit_parse: {e}", f"\n{content}", f"\n<<{usage}>>") from e

    if not match_list:
        raise ValueError(
            "Time extraction failed: No valid values found.", f"\n{content}", f"\n<<{usage}>>")  # Ensures the function does not return None

    df_table = pd.DataFrame(match_list, columns=[
        'Time', 'Time unit'
    ])

    expected_rows = markdown_to_dataframe(md_table_aligned_with_1_param_type_and_value).shape[0]
    if df_table.shape[0] != expected_rows:
        raise ValueError(
            f"Mismatch: Expected {expected_rows} rows, but got {df_table.shape[0]} extracted values.", f"\n{content}", f"\n<<{usage}>>"
        )

    return_md_table = dataframe_to_markdown(df_table)

    return return_md_table, res, content, usage, truncated

# print(s_pk_get_time_and_unit_prompt(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value))
# s_pk_get_time_and_unit(md_table_aligned, caption, md_table_aligned_with_1_param_type_and_value, model_name="gemini_15_pro")