def is_valid_sample(sample):
    # 1. 至少有 3 个 trace 步骤
    if len(sample["traces"]) < 3:
        return False

    # 2. 代码不能是简单的返回或赋值
    code_lines = sample["code"].strip().split("\r\n")
    if len(code_lines) <= 3:  # 通常表示只有定义和返回
        return False

    # 3. 必须包含至少一个 EXECUTE 操作（非仅 INPUT + RETURN）
    execute_steps = [t for t in sample["traces"] if t["action"] == "EXECUTE"]
    if len(execute_steps) < 2:
        return False

    # 4. 至少有一个不同的变量发生变化
    # 其实这步在追踪时应该已经筛选了
    all_vars = set()
    for trace in sample["traces"]:
        if "vars" in trace:
            all_vars.update(trace["vars"].keys())
    if len([v for v in all_vars if not v.startswith("__")]) < 1:
        return False

    # 5. 输出不能是 None 或无意义的默认值
    # 不合理的！！！没有理由这么做
    # output = sample.get("output")
    # if output is None or output in (0, "", [], {}):
    #     return False

    # 6. 不是重复任务
    # 结合 task_id 去重，或结合 input/code 内容哈希去重
    # 当前数据集没有必要

    return True


def merge_trace_steps(traces):
    merged = []
    buffer = []

    for t in traces:
        if "vars" not in t or len(t["vars"]) != 1:
            # 如果不是单一变量变化，先 flush buffer
            if buffer:
                merged.extend(combine_buffer(buffer))
                buffer = []
            merged.append(t)
            continue

        var_name = list(t["vars"].keys())[0]
        var_value = t["vars"][var_name]

        if buffer:
            prev = buffer[-1]
            # 检查是否满足合并条件
            if (
                prev["line"] == t["line"]
                and var_name in prev["vars"]
                and isinstance(var_value, int)
                and prev["vars"][var_name] + 1 == var_value
            ):
                buffer.append(t)
            else:
                # 不满足合并条件，flush buffer
                merged.extend(combine_buffer(buffer))
                buffer = [t]
        else:
            buffer = [t]

    if buffer:
        merged.extend(combine_buffer(buffer))

    return merged


def combine_buffer(buffer):
    if len(buffer) <= 1:
        return buffer

    first = buffer[0]
    last = buffer[-1]
    var_name = list(first["vars"].keys())[0]
    start_val = first["vars"][var_name]
    end_val = last["vars"][var_name]

    merged_step = {
        "line": first["line"],
        "step": f"{first['step']}~{last['step']}",
        "action": "LOOP",
        "vars": {var_name: f"{start_val}→{end_val}"},
    }

    return [merged_step]



if __name__ == "__main__":
    from tools.json_tools import load_all_traces_from_dir
    from tools.json_tools import save_results_in_batches

    # 默认输入输出路径
    input_dir = "trace_result"
    output_dir = "trace_processed"
    batch_size = 50  # 每个输出文件最多包含多少个样本

    # if len(sys.argv) > 1:
    #     input_dir = sys.argv[1]
    # if len(sys.argv) > 2:
    #     output_dir = sys.argv[2]

    print(f"从 {input_dir} 加载数据...")
    raw_data = load_all_traces_from_dir(input_dir, filename_prefix="trace_batch_")

    print(f"开始筛选和合并 trace 数据...")
    valid_samples = []
    for sample in raw_data:
        if is_valid_sample(sample):
            sample["traces"] = merge_trace_steps(sample["traces"])
            valid_samples.append(sample)

    print(f"正在将 {len(valid_samples)} 个有效样本保存至 {output_dir} ...")

    save_results_in_batches(
        results=valid_samples,
        output_dir=output_dir,
        output_prefix="cleaned_trace",
        batch_size=batch_size
    )