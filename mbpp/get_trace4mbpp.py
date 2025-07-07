from extract_info import extract_function_name, extract_function_args
from trace_tools import execute_function
from json_tools import load_jsonl, save_results_in_batches
from tqdm import tqdm
import json
import os

if __name__ == "__main__":
    curdir = os.path.dirname(os.path.abspath(__file__))

    # with open(curdir + "/sample/mbpp_sample.json", "r", encoding="utf-8") as f:
    # with open("sanitized-mbpp.json", "r", encoding="utf-8") as f:
        # samples = json.load(f)
    samples = load_jsonl(curdir + "/data/mbpp.jsonl")

    results = []
    i = 0

    for sample in tqdm(samples, desc="Processing Samples", total=len(samples)):
        sample_id = sample.get("task_id")
        code_str = sample["code"]

        defined_funcs = extract_function_name(code_str)
        if not defined_funcs:
            print(f"⚠️ No function defined in code string for sample {sample_id}")
            continue

        for test_case in sample["test_list"]:
            func_name, input_args = extract_function_args(test_case, defined_funcs)

            if not func_name:
                print(f"⚠️ Could not extract function name from test case: {test_case}")
                continue

            if func_name not in defined_funcs:
                print(f"⚠️ Test case uses undefined function '{func_name}', skipping...")
                continue

            try:
                result = execute_function(code_str, input_args=input_args, target_func_name=func_name)
                result["id"] = i
                i += 1
                result["task_id"] = sample_id
                result["exist_function"] = defined_funcs
                results.append(result)
            except Exception as e:
                print(f"Error executing {sample_id}: {e}")

    # 使用封装好的工具进行分批存储
    save_results_in_batches(
        results,
        output_dir= curdir + "/trace_result",
        # output_dir= curdir + "/sample",
        output_prefix="trace_batch",
        batch_size=50
    )