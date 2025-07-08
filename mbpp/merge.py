import os
import json
from tools.json_tools import load_all_traces_from_dir

# 设置路径
curdir = os.path.dirname(os.path.abspath(__file__))
nl_dir = os.path.join(curdir, "nl_result")
trace_dir = os.path.join(curdir, "trace_processed")
output_dir = os.path.join(curdir, "data")

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

print("正在加载所有 trace 数据...")
# 加载所有 trace 数据并构建成 id -> item 的字典
all_trace_samples = load_all_traces_from_dir(trace_dir, filename_prefix="cleaned_trace_", file_extension=".json")
trace_dict = {item["id"]: item for item in all_trace_samples}
print(f"共加载 {len(trace_dict)} 条 trace 数据")

print("\n🔄 正在加载所有 nl 数据...")
# 加载所有 nl 数据
all_nl_samples = load_all_traces_from_dir(nl_dir, filename_prefix="nl_descriptions_batch", file_extension=".json")
print(f"共加载 {len(all_nl_samples)} 条 nl 描述数据")

# 合并数据
print("\n开始按 id 合并数据...")
final_data = []

for nl_item in all_nl_samples:
    item_id = nl_item.get("id")
    if item_id in trace_dict:
        trace_item = trace_dict[item_id]
        code = trace_item.get("code", "")
        nl = nl_item.get("nl", "")
        merged_item = {
            "id": item_id,
            # "code": trace_item.get("code", ""),
            "instruction": f"please reasoning about the following code according to input: {code}",
            "input": str(str(trace_item.get("input", [])).replace("\"", "\'")),
            "output": str(str(trace_item.get("output", "")).replace("\"", "\'")) + "Here is analyze the code and output:\n" + nl,
            # "nl": nl_item.get("nl", "")
        }
        final_data.append(merged_item)

print(f"合并完成，共 {len(final_data)} 条有效数据")

# 保存为 .jsonl 格式
output_path = os.path.join(output_dir, "alpaca_finetune_dataset.jsonl")
with open(output_path, "w", encoding="utf-8") as f:
    for item in final_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"\n数据已保存为 .jsonl 格式: {output_path}")