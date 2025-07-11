# 用来计算所构建的数据集的指标import os
from tools.json_tools import load_all_traces_from_dir

# 设置目录路径
trace_dir = "h:/WORKDIR/TracePython/mbpp/trace_processed"
filename_prefix = "cleaned_trace_"
file_extension = ".json"

# 加载所有 trace 数据
samples = load_all_traces_from_dir(trace_dir=trace_dir,
                                   filename_prefix=filename_prefix,
                                   file_extension=file_extension)

# 1. 样本总数
total_samples = len(samples)
print(f"总样本数: {total_samples}")

# 2. 计算 trace 长度相关指标
trace_lengths = [len(sample.get("traces", [])) for sample in samples]
avg_trace_length = sum(trace_lengths) / total_samples if total_samples > 0 else 0
max_trace_length = max(trace_lengths) if trace_lengths else 0
min_trace_length = min(trace_lengths) if trace_lengths else 0

print(f"平均 trace 长度: {avg_trace_length:.2f}")
print(f"最长 trace 长度: {max_trace_length}")
print(f"最短 trace 长度: {min_trace_length}")

# 3. 函数名（entry_point）分布
from collections import Counter

# entry_points = [sample.get("entry_point") for sample in samples]
# ep_counter = Counter(entry_points)
# print("\n函数名分布:")
# for ep, count in ep_counter.most_common():
#     print(f" - {ep}: {count} 次")

# 4. 输入参数数量分布
input_lengths = [len(sample.get("input", [])) for sample in samples]
input_counter = Counter(input_lengths)
print("\n输入参数数量分布:")
for ilen, count in input_counter.most_common():
    print(f" - {ilen} 个参数: {count} 次")

# 5. 输出类型分布
output_types = [type(sample.get("output")).__name__ for sample in samples]
output_counter = Counter(output_types)
print("\n输出值类型分布:")
for typ, count in output_counter.most_common():
    print(f" - {typ}: {count} 次")

# 6. step 最大编号分布（每个 trace 中最大的 step 值）
def parse_step(step_val):
    if isinstance(step_val, int):
        return step_val
    elif isinstance(step_val, str):
        parts = step_val.split("->")
        if len(parts) >= 1 and parts[0].isdigit():
            return int(parts[0])
    return None  # 或者返回 0 表示无效

max_steps = []
for sample in samples:
    traces = sample.get("traces", [])
    steps_in_trace = [
        parse_step(t.get("step"))
        for t in traces
        if "step" in t
    ]
    steps_in_trace = [s for s in steps_in_trace if s is not None]

    if steps_in_trace:
        max_step = max(steps_in_trace)
        max_steps.append(max_step)
    else:
        max_steps.append(0)  # 如果没有有效 step，记为 0

avg_max_step = sum(max_steps) / total_samples if total_samples > 0 else 0
min_max_step = min(max_steps) if max_steps else 0
max_max_step = max(max_steps) if max_steps else 0

print(f"\n平均最大 step 编号: {avg_max_step:.2f}")
print(f"最小最大 step 编号: {min_max_step}")
print(f"最大最大 step 编号: {max_max_step}")
# 按区间分桶的 step 分布（例如每 10 步为一组）
BUCKET_SIZE_STEP = 20
def get_step_bucket(step_count):
    return (step_count // BUCKET_SIZE_STEP) * BUCKET_SIZE_STEP

bucketed_max_steps = [get_step_bucket(m) for m in max_steps]
step_counter = Counter(bucketed_max_steps)

print(f"\n最大 step 编号分布（每 {BUCKET_SIZE_STEP} 步一个区间）:")
for bucket, count in sorted(step_counter.items()):
    upper_bound = bucket + BUCKET_SIZE_STEP
    print(f" - {bucket} ~ {upper_bound}: {count} 个")



#---------------nl统计---------------

# 设置路径
nl_dir = "h:/WORKDIR/TracePython/mbpp/nl_result"
filename_prefix = "nl_descriptions_batch"

# 加载数据
samples = load_all_traces_from_dir(nl_dir, filename_prefix=filename_prefix)

# 提取所有 'nl' 字段长度
text_lengths = [len(sample["nl"]) for sample in samples]
avg_length = sum(text_lengths) / total_samples if total_samples > 0 else 0
max_length = max(text_lengths) if text_lengths else 0
min_length = min(text_lengths) if text_lengths else 0

print(f"\n平均文本长度: {avg_length:.2f}")
print(f"最长文本长度: {max_length}")
print(f"最短文本长度: {min_length}")

BUCKET_SIZE_TEXT = 200
# 文本长度分布（按区间）
def get_length_bucket(length):
    # 按每50字符分一个桶
    return (length // BUCKET_SIZE_TEXT) * BUCKET_SIZE_TEXT

bucketed_lengths = [get_length_bucket(l) for l in text_lengths]
length_counter = Counter(bucketed_lengths)

print(f"\n文本长度分布（每{BUCKET_SIZE_TEXT}字符区间）:")
for length_range, count in sorted(length_counter.items()):
    upper = length_range + BUCKET_SIZE_TEXT
    print(f" - {length_range} ~ {upper} 字符: {count} 个")

# # 可选：输出异常长度样本（如长度 > 5000的）
# long_texts = [(i, len(s["nl"]), s.get("id")) for i, s in enumerate(samples) if "nl" in s and len(s["nl"]) > 5000]
# if long_texts:
#     print("\n异常长文本样本（>5000 字符）:")
#     for idx, length, sid in long_texts:
#         print(f" - ID: {sid}, Index: {idx}, Length: {length}")