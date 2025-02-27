import time
from table_utils import *
from llm_utils import *
from steps.s_pk_delete_individual import *
from steps.s_pk_align_parameter import *
from steps.s_pk_extract_drug_info import *
from steps.s_pk_extract_patient_info import *
from steps.s_pk_get_col_mapping import *
from steps.s_pk_get_parameter_type_and_unit import *
from steps.s_pk_match_drug_info import *
from steps.s_pk_match_patient_info import *


def run_with_retry(func, *args, max_retries=5, base_delay=10, **kwargs):
    delay = base_delay
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
            else:
                print("Max retries reached. Returning None.")
                return None

    # it will not get here
    return None


def p_pk_summary(md_table, description, llm="gemini_15_pro", max_retries=5, base_delay=10, use_color=True):
    """
    PK Summary Pipeline 250227
    Summarizes pharmacokinetic (PK) data from a given markdown table.

    :param md_table: The markdown representation of a SINGLE HTML table containing PK data.
    :param description: Additional contextual information, including captions, footnotes, etc.
    :param llm: The language model to use for processing ("gemini_15_pro" or "chatgpt_4o").
    :param max_retries: Maximum number of retries before failing.
    :param base_delay: Initial delay before retrying (in seconds), which doubles on each failure.
    :return:
    """
    if use_color:
        # COLOR_START = "\033[31m"  # red
        COLOR_START = "\033[32m"  # green
        # COLOR_START = "\033[33m"  # yellow
        COLOR_END = "\033[0m"

    step_list = []
    res_list = []
    content_list = []
    usage_list = []
    truncated_list = []

    """
    Step 1: Extract Drug Information
    """
    print("=" * 64)
    step_name = "Extract Drug Information"
    print(COLOR_START+step_name+COLOR_END)
    drug_info = run_with_retry(
        s_pk_extract_drug_info,
        md_table,
        description,
        llm,
        max_retries=max_retries,
        base_delay=base_delay,
    )
    if drug_info is None:
        return None
    md_table_drug, res_drug, content_drug, usage_drug, truncated_drug = drug_info
    step_list.append(step_name)
    res_list.append(res_drug)
    content_list.append(content_drug)
    usage_list.append(usage_drug)
    truncated_list.append(truncated_drug)
    print(COLOR_START+"Usage:"+COLOR_END, usage_drug)
    print(COLOR_START+"Result:\n"+COLOR_END, display_md_table(md_table_drug))
    print(COLOR_START+"Reasoning:\n"+COLOR_END, content_drug)
    print("\n"*1)
    """
    Step 2: Extract Population Information
    """
    print("=" * 64)
    step_name = "Extract Population Information"
    print(COLOR_START+step_name+COLOR_END)
    patient_info = run_with_retry(
        s_pk_extract_patient_info,
        md_table,
        description,
        llm,
        max_retries=max_retries,
        base_delay=base_delay,
    )
    if patient_info is None:
        return None
    md_table_patient, res_patient, content_patient, usage_patient, truncated_patient = patient_info
    step_list.append(step_name)
    res_list.append(res_patient)
    content_list.append(content_patient)
    usage_list.append(usage_patient)
    truncated_list.append(truncated_patient)
    print(COLOR_START+"Usage:"+COLOR_END, usage_patient)
    print(COLOR_START+"Result:\n"+COLOR_END, display_md_table(md_table_patient))
    print(COLOR_START+"Reasoning:\n"+COLOR_END, content_patient)
    print("\n"*1)
    """
    Step 3: Extract Population Information
    """
    print("=" * 64)
    step_name = "Delete Individual Data"
    print(COLOR_START+step_name+COLOR_END)
    summary_only_info = run_with_retry(
        s_pk_delete_individual,
        md_table,
        llm,
        max_retries=max_retries,
        base_delay=base_delay,
    )
    if patient_info is None:
        return None
    md_table_summary, res_summary, content_summary, usage_summary, truncated_summary = summary_only_info
    step_list.append(step_name)
    res_list.append(res_summary)
    content_list.append(content_summary)
    usage_list.append(usage_summary)
    truncated_list.append(truncated_summary)
    print(COLOR_START+"Usage:"+COLOR_END, usage_summary)
    print(COLOR_START+"Result:\n"+COLOR_END, display_md_table(md_table_summary))
    print(COLOR_START+"Reasoning:\n"+COLOR_END, content_summary)
    print("\n"*1)
    return


