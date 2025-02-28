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
import re


def clean_llm_reasoning(text: str) -> str:
    """
    Cleans the LLM inference string by removing content after the last occurrence
    of '<<' or '[[END]]', keeping only the portion up to the last preceding period.
    If the last period is too close to the previous newline, truncate at the newline instead.
    Ensures the output ends with a newline.

    :param text: The input inference string.
    :return: The cleaned inference string, ensuring it ends with a newline.
    """
    # Try finding '<<' first
    last_double_angle = text.rfind("<<")

    if last_double_angle != -1:
        cutoff_index = last_double_angle
    else:
        # If '<<' is not found, look for '[[END]]'
        last_end_marker = text.rfind("[[END]]")
        if last_end_marker != -1:
            cutoff_index = last_end_marker
        else:
            # If neither is found, return original text (ensuring newline)
            return text if text.endswith("\n") else text + "\n"

    # Find the last period before the cutoff index
    last_period = text.rfind(".", 0, cutoff_index)

    if last_period != -1:
        # Find the last newline before the period
        last_newline = text.rfind("\n", 0, last_period)

        # If newline is found and period is too close to it, truncate at newline
        if last_newline != -1 and (last_period - last_newline) < 5:
            result = text[:last_newline + 1]
        else:
            result = text[:last_period + 1]
    else:
        result = text  # No period found, return full text

    # Ensure the output ends with a newline
    return result if result.endswith("\n") else result + "\n"


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


def p_pk_summary(md_table, description, llm="gemini_15_pro", max_retries=5, base_delay=10, use_color=True, clean_reasonig=True):
    """
    PK Summary Pipeline 250227
    Summarizes pharmacokinetic (PK) data from a given markdown table.

    :param md_table: The markdown representation of a SINGLE HTML table containing PK data.
    :param description: Additional contextual information, including captions, footnotes, etc.
    :param llm: The language model to use for processing ("gemini_15_pro" or "chatgpt_4o").
    :param max_retries: Maximum number of retries before failing.
    :param base_delay: Initial delay before retrying (in seconds), which doubles on each failure.
    :param use_color: Better-looking print output.
    :param clean_reasonig: When printing output, hide the parsing-related parts in the reasoning.
    :return:
    """
    if use_color:
        # COLOR_START = "\033[31m"  # red
        COLOR_START = "\033[32m"  # green
        # COLOR_START = "\033[33m"  # yellow
        COLOR_END = "\033[0m"
    else:
        COLOR_START = ""
        COLOR_END = ""

    step_list = []
    res_list = []
    content_list = []
    content_list_clean = []
    usage_list = []
    truncated_list = []

    """
    Step 0: Pre-launch Inspection
    """
    print("=" * 64)
    step_name = "Pre-launch Inspection"
    print(COLOR_START+step_name+COLOR_END)
    print(COLOR_START+"Usage:"+COLOR_END, 0)
    print(COLOR_START+"Result:"+COLOR_END)
    print("Markdown Table:")
    print(display_md_table(md_table))
    print("Description:")
    print(description)
    print(COLOR_START + "Reasoning:" + COLOR_END)
    print("Auto-processed.\n")

    """
    Step 1: Drug Information Extraction
    """
    print("=" * 64)
    step_name = "Drug Information Extraction"
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
    content_list_clean.append(clean_llm_reasoning(content_drug))
    usage_list.append(usage_drug)
    truncated_list.append(truncated_drug)
    print(COLOR_START+"Usage:"+COLOR_END, usage_list[-1])
    print(COLOR_START+"Result:"+COLOR_END)
    print(display_md_table(md_table_drug))
    content_to_print = content_list_clean[-1] if clean_reasonig else content_list[-1]
    print(COLOR_START + "Reasoning:" + COLOR_END)
    print(content_to_print)
    # print("\n"*1)
    """
    Step 2-1: Population Information Extraction (Trial 1)
    """
    print("=" * 64)
    step_name = "Population Information Extraction (Trial 1)"
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
    content_list_clean.append(clean_llm_reasoning(content_patient_1))
    usage_list.append(usage_patient_1)
    truncated_list.append(truncated_patient_1)
    print(COLOR_START+"Usage:"+COLOR_END, usage_list[-1])
    print(COLOR_START+"Result:"+COLOR_END)
    print(display_md_table(md_table_patient_1))
    content_to_print = content_list_clean[-1] if clean_reasonig else content_list[-1]
    print(COLOR_START + "Reasoning:" + COLOR_END)
    print(content_to_print)
    # print("\n"*1)
    """
    Step 2-2: Population Information Extraction (Trial 2)
    """
    time.sleep(6)
    print("=" * 64)
    step_name = "Population Information Extraction (Trial 2)"
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
    content_list_clean.append(clean_llm_reasoning(content_patient_2))
    usage_list.append(usage_patient_2)
    truncated_list.append(truncated_patient_2)
    print(COLOR_START+"Usage:"+COLOR_END, usage_list[-1])
    print(COLOR_START+"Result:"+COLOR_END)
    print(display_md_table(md_table_patient_2))
    content_to_print = content_list_clean[-1] if clean_reasonig else content_list[-1]
    print(COLOR_START + "Reasoning:\n" + COLOR_END)
    print(content_to_print)
    # print("\n"*1)
    """
    Step 2-3: Population Information Extraction (Keep The Longest Table)
    """
    if len(md_table_patient_1) >= len(md_table_patient_2):
        patient_info = patient_info_1
    else:
        patient_info = patient_info_2
    print("=" * 64)
    step_name = "Population Information Extraction (Final Decision)"
    print(COLOR_START+step_name+COLOR_END)
    print(COLOR_START+"Usage:"+COLOR_END, 0)
    print(COLOR_START+"Result:"+COLOR_END)
    print(display_md_table(patient_info[0]))
    print(COLOR_START + "Reasoning:" + COLOR_END)
    print("Auto-processed.\n")
    md_table_patient, res_patient, content_patient, usage_patient, truncated_patient = patient_info
    """
    Step 3: Individual Data Deletion
    """
    print("=" * 64)
    step_name = "Individual Data Deletion"
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
    content_list_clean.append(clean_llm_reasoning(content_summary))
    usage_list.append(usage_summary)
    truncated_list.append(truncated_summary)
    print(COLOR_START+"Usage:"+COLOR_END, usage_list[-1])
    print(COLOR_START+"Result:"+COLOR_END)
    print(display_md_table(md_table_summary))
    content_to_print = content_list_clean[-1] if clean_reasonig else content_list[-1]
    print(COLOR_START + "Reasoning:" + COLOR_END)
    print(content_to_print)
    # print("\n"*1)
    """
    Step 4: Parameter Type Alignment
    """
    print("=" * 64)
    step_name = "Parameter Type Alignment"
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
    content_list_clean.append(clean_llm_reasoning(content_aligned))
    usage_list.append(usage_aligned)
    truncated_list.append(truncated_aligned)
    print(COLOR_START+"Usage:"+COLOR_END, usage_list[-1])
    print(COLOR_START+"Result:"+COLOR_END)
    print(display_md_table(md_table_aligned))
    content_to_print = content_list_clean[-1] if clean_reasonig else content_list[-1]
    print(COLOR_START + "Reasoning:" + COLOR_END)
    print(content_to_print)
    # print("\n"*1)
    """
    Step 5: Column Header Categorization
    """
    print("=" * 64)
    step_name = "Column Header Categorization"
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
    content_list_clean.append(clean_llm_reasoning(content_mapping))
    usage_list.append(usage_mapping)
    truncated_list.append(truncated_mapping)
    print(COLOR_START+"Usage:"+COLOR_END, usage_list[-1])
    print(COLOR_START+"Result:"+COLOR_END)
    print(col_mapping)
    content_to_print = content_list_clean[-1] if clean_reasonig else content_list[-1]
    print(COLOR_START + "Reasoning:" + COLOR_END)
    print(content_to_print)
    # print("\n"*1)
    """
    Step 6: Task Allocation (Preferably hidden from Users)
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
    if parameter_unit_count == 1 and parameter_type_count == 1:
        need_get_unit = False
    if markdown_to_dataframe(md_table_drug).shape[0] == 1:
        need_match_drug = False
    if markdown_to_dataframe(md_table_patient).shape[0] == 1:
        need_match_patient = False
    print("=" * 64)
    step_name = "Task Allocation"
    print(COLOR_START+step_name+COLOR_END)
    print(COLOR_START+"Usage:"+COLOR_END, 0)
    print(COLOR_START+"Result:"+COLOR_END)
    tasks = ["Unit Extraction", "Sub-table Creation", "Drug Matching", "Population Matching"]
    statuses = [need_get_unit, need_split_col, need_match_drug, need_match_patient]
    active_tasks = [task for task, status in zip(tasks, statuses) if status]
    canceled_tasks = [task for task, status in zip(tasks, statuses) if not status]
    print(f"LLM Execution: {', '.join(active_tasks) if active_tasks else 'None'}")
    print(f"Auto Execution: {', '.join(canceled_tasks) if canceled_tasks else 'None'}")
    print(COLOR_START + "Reasoning:" + COLOR_END)
    print("Auto-processed.\n")
    """
    Step 7: Sub-table Creation
    """
    print("=" * 64)
    step_name = "Sub-table Creation"
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
        content_list_clean.append(clean_llm_reasoning(content_split))
        usage_list.append(usage_split)
        truncated_list.append(truncated_split)
        # print("\n"*1)
    else:
        usage_split = 0
        content_split = "Auto-processed.\n"
        md_table_list = [md_table_aligned, ]
    print(COLOR_START + "Usage:" + COLOR_END)
    print(usage_split)
    print(COLOR_START + "Result:" + COLOR_END)
    for i in range(len(md_table_list)):
        print(f"Index [{i}]:")
        print(display_md_table(md_table_list[i]))
    print(COLOR_START + "Reasoning:" + COLOR_END)
    print(content_split)
    return


