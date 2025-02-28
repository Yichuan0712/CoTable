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
from steps.s_pk_split_by_cols import *


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
    # print("\n"*1)
    """
    Step 2-1: Extract Population Information (Round 1)
    """
    print("=" * 64)
    step_name = "Extract Population Information (Round 1)"
    print(COLOR_START+step_name+COLOR_END)
    patient_info_1 = run_with_retry(
        s_pk_extract_patient_info,
        md_table,
        description,
        llm,
        max_retries=max_retries,
        base_delay=base_delay,
    )
    if patient_info_1 is None:
        return None
    md_table_patient_1, res_patient_1, content_patient_1, usage_patient_1, truncated_patient_1 = patient_info_1
    step_list.append(step_name)
    res_list.append(res_patient_1)
    content_list.append(content_patient_1)
    usage_list.append(usage_patient_1)
    truncated_list.append(truncated_patient_1)
    print(COLOR_START+"Usage:"+COLOR_END, usage_patient_1)
    print(COLOR_START+"Result:\n"+COLOR_END, display_md_table(md_table_patient_1))
    print(COLOR_START+"Reasoning:\n"+COLOR_END, content_patient_1)
    # print("\n"*1)
    """
    Step 2-2: Extract Population Information (Round 2)
    """
    time.sleep(6)
    print("=" * 64)
    step_name = "Extract Population Information (Round 2)"
    print(COLOR_START+step_name+COLOR_END)
    patient_info_2 = run_with_retry(
        s_pk_extract_patient_info,
        md_table,
        description,
        llm,
        max_retries=max_retries,
        base_delay=base_delay,
    )
    if patient_info_2 is None:
        return None
    md_table_patient_2, res_patient_2, content_patient_2, usage_patient_2, truncated_patient_2 = patient_info_2
    step_list.append(step_name)
    res_list.append(res_patient_2)
    content_list.append(content_patient_2)
    usage_list.append(usage_patient_2)
    truncated_list.append(truncated_patient_2)
    print(COLOR_START+"Usage:"+COLOR_END, usage_patient_2)
    print(COLOR_START+"Result:\n"+COLOR_END, display_md_table(md_table_patient_2))
    print(COLOR_START+"Reasoning:\n"+COLOR_END, content_patient_2)
    # print("\n"*1)
    """
    Step 2-3: Extract Population Information (Keep The Longest Table)
    """
    if len(md_table_patient_1) >= len(md_table_patient_2):
        patient_info = patient_info_1
    else:
        patient_info = patient_info_2
    md_table_patient, res_patient, content_patient, usage_patient, truncated_patient = patient_info
    """
    Step 3: Delete Individual Data
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
    if summary_only_info is None:
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
    # print("\n"*1)
    """
    Step 4: Align Parameter Type
    """
    print("=" * 64)
    step_name = "Align Parameter Type"
    print(COLOR_START+step_name+COLOR_END)
    aligned_info = run_with_retry(
        s_pk_align_parameter,
        md_table_summary,
        llm,
        max_retries=max_retries,
        base_delay=base_delay,
    )
    if aligned_info is None:
        return None
    md_table_aligned, res_aligned, content_aligned, usage_aligned, truncated_aligned = aligned_info
    step_list.append(step_name)
    res_list.append(res_aligned)
    content_list.append(content_aligned)
    usage_list.append(usage_aligned)
    truncated_list.append(truncated_aligned)
    print(COLOR_START+"Usage:"+COLOR_END, usage_aligned)
    print(COLOR_START+"Result:\n"+COLOR_END, display_md_table(md_table_aligned))
    print(COLOR_START+"Reasoning:\n"+COLOR_END, content_aligned)
    # print("\n"*1)
    """
    Step 5: Categorize Column Headers
    """
    print("=" * 64)
    step_name = "Categorize Column Headers"
    print(COLOR_START+step_name+COLOR_END)
    mapping_info = run_with_retry(
        s_pk_get_col_mapping,
        md_table_aligned,
        llm,
        max_retries=max_retries,
        base_delay=base_delay,
    )
    if mapping_info is None:
        return None
    col_mapping, res_mapping, content_mapping, usage_mapping, truncated_mapping = mapping_info
    step_list.append(step_name)
    res_list.append(res_mapping)
    content_list.append(content_mapping)
    usage_list.append(usage_mapping)
    truncated_list.append(truncated_mapping)
    print(COLOR_START+"Usage:"+COLOR_END, usage_mapping)
    print(COLOR_START+"Result:\n"+COLOR_END, col_mapping)
    print(COLOR_START+"Reasoning:\n"+COLOR_END, content_mapping)
    # print("\n"*1)
    """
    Step 6: Diagnose & Decide (Unseen to Users)
    """
    parameter_type_count = list(col_mapping.values()).count("Parameter type")
    parameter_unit_count = list(col_mapping.values()).count("Parameter unit")
    parameter_value_count = list(col_mapping.values()).count("Parameter value")
    parameter_pvalue_count = list(col_mapping.values()).count("P value")
    need_get_unit = True
    need_split_col = False
    need_match_drug = True
    need_match_patient = True
    if parameter_value_count == 0:
        return
    if parameter_type_count == 0:
        return
    if parameter_type_count > 1 or parameter_pvalue_count > 1:
        need_split_col = True
    if parameter_unit_count == 1:
        need_get_unit = False
    if markdown_to_dataframe(md_table_drug).shape[0] == 1:
        need_match_drug = False
    if markdown_to_dataframe(md_table_patient).shape[0] == 1:
        need_match_patient = False
    """
    Step 7: Split into Sub-tables
    """
    print("=" * 64)
    step_name = "Split into Sub-tables"
    print(COLOR_START + step_name + COLOR_END)
    if need_split_col:
        split_returns = run_with_retry(
            s_pk_split_by_cols,
            md_table_aligned,
            col_mapping,
            llm,
            max_retries=max_retries,
            base_delay=base_delay,
        )
        if split_returns is None:
            return None
        md_table_list, res_split, content_split, usage_split, truncated_split = split_returns
        step_list.append(step_name)
        res_list.append(res_split)
        content_list.append(content_split)
        usage_list.append(usage_split)
        truncated_list.append(truncated_split)
        # print("\n"*1)
    else:
        usage_split = 0
        content_split = "There is no need to divide the table.\n"
        md_table_list = [md_table_aligned, ]
    print(COLOR_START + "Usage:" + COLOR_END, usage_split)
    print(COLOR_START + "Result:" + COLOR_END)
    for i in range(len(md_table_list)):
        print("Index -", i)
        print(display_md_table(md_table_list[i]))
    print(COLOR_START + "Reasoning:\n" + COLOR_END, content_split)
    return


