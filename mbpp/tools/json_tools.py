import json
import types
import os

def load_jsonl(file_path):
    """
    从 .jsonl 文件中加载样本数据。
    
    参数:
        file_path (str): .jsonl 文件路径
        
    返回:
        list: 解析后的样本列表
    """
    samples = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                sample = json.loads(line)
                samples.append(sample)
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to parse line {line_num + 1}: {e}")
                continue
                
    return samples


def load_all_traces_from_dir(trace_dir, filename_prefix="trace_batch_", file_extension=".json", start_idx=None, end_idx=None):
    """
    从指定目录中加载所有符合命名格式的 trace 文件，并支持按文件编号区间筛选。

    参数:
        trace_dir (str): 包含 trace 文件的目录路径
        filename_prefix (str): 文件名前缀，如 "trace_batch_"
        file_extension (str): 文件扩展名，默认 ".json"
        start_idx (int): 起始文件编号（包含）
        end_idx (int): 结束文件编号（不包含）

    返回:
        list: 合并后的所有 trace 样本列表
    """
    all_samples = []

    for filename in os.listdir(trace_dir):
        if filename.startswith(filename_prefix) and filename.endswith(file_extension):
            # 提取文件编号
            suffix = filename[len(filename_prefix):].removesuffix(file_extension)
            try:
                idx = int(suffix)
            except ValueError:
                continue  # 忽略无法解析为数字的文件

            # 判断是否在指定区间内
            if start_idx is not None and idx < start_idx:
                continue
            if end_idx is not None and idx >= end_idx:
                continue

            file_path = os.path.join(trace_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_samples.extend(data)
                    else:
                        print(f"文件 {filename} 内容不是数组类型，跳过")
            except Exception as e:
                print(f"无法加载文件 {filename}: {e}")

    print(f"共加载 {len(all_samples)} 个样本。")
    return all_samples

def save_results_in_batches(results, output_dir=".", output_prefix="execution_results_batch", batch_size=100):
    """
    将结果按批次保存为多个 JSON 文件，并支持自定义输出目录
    
    参数:
        results (list): 要保存的结果列表
        output_dir (str): 输出目录路径（会自动创建）
        output_prefix (str): 输出文件名前缀
        batch_size (int): 每个文件的最大结果数
    """
    from itertools import islice

    def batched(iterable, size):
        """将迭代器分批"""
        it = iter(iterable)
        while True:
            batch = list(islice(it, size))
            if not batch:
                break
            yield batch

    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {os.path.abspath(output_dir)}")

    for idx, batch in enumerate(batched(results, batch_size)):
        filename = os.path.join(output_dir, f"{output_prefix}_{idx}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False, indent=2, cls=SetEncoder)
        print(f"Saved {len(batch)} records to {filename}")

class SetEncoder(json.JSONEncoder):
    def default(self, o):
        # 处理 set 和 frozenset
        if isinstance(o, (set, frozenset)):
            return list(o)
        
        # 处理生成器（如 heapq.merge 返回的 generator）
        elif isinstance(o, types.GeneratorType):
            try:
                return list(o)
            except Exception:
                return str(o)  # 如果无法展开，就返回字符串
        
        # 处理模块对象（如 import re）
        elif isinstance(o, types.ModuleType):
            return f"<module '{o.__name__}'>"
        
        # 处理自定义对象
        elif hasattr(o, "__dict__"):
            return str(o)
        
        # 处理 bytes / bytearray
        elif isinstance(o, (bytes, bytearray)):
            return str(o)
        
        elif isinstance(o, tuple):
            return list(o)
        
        # 其他无法序列化的类型
        try:
            return super().default(o)
        except TypeError:
            return str(o)
        
def convert_dict_keys(d):
    """
    递归地将 dict 中的所有非标量 key（如 tuple）转为字符串。
    同时处理嵌套结构。
    """
    if isinstance(d, dict):
        new_d = {}
        for k, v in d.items():
            # 处理 key
            new_k = str(k) if not isinstance(k, (str, int, float, bool,type(None))) else k
            # 递归处理 value
            new_d[new_k] = convert_dict_keys(v)
        return new_d
    elif isinstance(d, list):
        return [convert_dict_keys(item) for item in d]
    elif isinstance(d, tuple):
        return str(d)
    elif isinstance(d, set):
        return [convert_dict_keys(x) for x in d]
    else:
        return d
    
def convert_data_to_json_safe(data):
    if isinstance(data, dict):
        return {
            convert_data_to_json_safe(k): convert_data_to_json_safe(v) for k, v in data.items()
        }
    elif isinstance(data, (list, tuple, set, frozenset)):
        return [convert_data_to_json_safe(item) for item in data]
    elif isinstance(data, types.GeneratorType):
        return [convert_data_to_json_safe(x) for x in data]
    elif isinstance(data, types.ModuleType):
        return f"<module '{data.__name__}'>"
    elif hasattr(data, "__dict__"):
        return convert_data_to_json_safe(vars(data))
    elif isinstance(data, (bytes, bytearray)):
        return str(data)
    elif not isinstance(data, (str, int, float, bool, type(None))):
        try:
            # 尝试转换为 hashable 类型（如 tuple）
            hash(data)
            return data
        except TypeError:
            # 如果不可 hash，则转为字符串
            return str(data)
    else:
        return data