import sys
import json
import types
from functools import wraps
from extract_input import call_ollama_extract_code

# -----------------------------
# Trace 工具部分
# -----------------------------
trace_records = []
trace_target_func_name = None
last_line = None         # 上一行号
last_vars = {}           # 上一行执行后的变量状态
pending_vars = {}        # 当前帧的变量状态（用于 RETURN）

def trace_calls(frame, event, arg):
    global last_line, last_vars, pending_vars

    func_name = frame.f_code.co_name

    # 只追踪目标函数
    if func_name != trace_target_func_name:
        return trace_calls

    current_line = frame.f_lineno
    current_vars = dict(frame.f_locals)

    if event == 'call':
        # 函数调用：记录输入参数
        trace_records.append({
            "line": current_line,
            "action": "INPUT",
            "vars": current_vars.copy()
        })
        last_line = current_line
        last_vars = current_vars.copy()

    elif event == 'return':
        # 返回：提交最后未提交的 EXECUTE（如果有）
        if last_line and last_vars:
            changed = {
                k: v for k, v in last_vars.items()
                if k not in frame.f_locals or frame.f_locals[k] != v
            }
            if changed:
                trace_records.append({
                    "line": last_line,
                    "action": "EXECUTE",
                    "vars": changed
                })

        # 记录返回值
        trace_records.append({
            "line": current_line,
            "action": "RETURN",
            "vars": {"__return__": arg}
        })

    elif event == 'line':
        if last_line is not None:
            changed = {}
    
            # 检查旧变量是否有变化
            for var, val in last_vars.items():
                if var not in current_vars or current_vars[var] != val:
                    changed[var] = val
    
            # 检查新变量（新增变量）
            for var, val in current_vars.items():
                if var not in last_vars:
                    changed[var] = val
    
            if changed:
                trace_records.append({
                    "line": last_line,
                    "action": "EXECUTE",
                    "vars": changed
                })
    
        # 更新为当前帧的状态
        last_line = current_line
        last_vars = current_vars.copy()
    return trace_calls
def enable_tracing(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        global trace_records
        trace_records.clear()
        sys.settrace(trace_calls)
        result = fn(*args, **kwargs)
        sys.settrace(None)
        return result
    return wrapper


# -----------------------------
# 主处理函数
# -----------------------------
def execute_function(code_str, input_dict=None):
    global trace_target_func_name

    if input_dict is None:
        input_dict = {}

    namespace = {}
    exec(code_str, namespace)

    functions = {k: v for k, v in namespace.items() if isinstance(v, types.FunctionType)}
    if not functions:
        raise ValueError("No function defined in the code string.")

    func_name, func = next(iter(functions.items()))

    trace_target_func_name = func_name  # 设置为目标函数名

    @enable_tracing
    def wrapped():
        return func(**input_dict)

    output = wrapped()
    return {
        "code": code_str.strip(),
        "input": input_dict,
        "output": output,
        "traces": trace_records.copy()
    }

import re
import ast

def code_str_to_vars(code_str: str) -> dict:
    """
    提取第一个合法的 Python 字面量并返回：
        {"scores": [...]} 或 {"users_data": [...]}
    """

    if not code_str or not code_str.strip():
        return {}

    # 匹配最可能的 Python 字面量结构（list/dict/tuple/set）
    pattern = r'$$.*?$$|{.*?}|$.*?$'
    matches = re.findall(pattern, code_str, re.DOTALL)

    for match in matches:
        try:
            value = ast.literal_eval(match)
            # 强制指定参数名（根据当前样本决定）
            return {"scores": value}
        except Exception as e:
            continue

    print("❌ 无法识别有效的 Python 字面量")
    return {}
# -----------------------------
# 示例读取与处理
# -----------------------------
if __name__ == "__main__":
    with open("pyx_sample0.json", "r", encoding="utf-8") as f:
        samples = json.load(f)

    results = []


    for sample in samples:
        sample_id = sample.get("id")
        response = sample["response"]
        code_str = response.strip().replace("```python\n", "").rstrip("```")
        code_input_str = call_ollama_extract_code(sample["nl"]).strip().replace("```python\n", "").rstrip("```")
        # 从 nl 中提取信息
        try:
            input_data = code_str_to_vars(code_input_str)
        except Exception as e:
            print(f"Error parsing nl for {sample['id']}: {e}")
            continue

        try:
            print(f"input_data:{input_data}")
            result = execute_function(code_str, input_data)
            result["id"] = sample_id
            results.append(result)
        except Exception as e:
            print(f"Error executing {sample['id']}: {e}")

    output_file = "execution_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


    import pprint
    pprint.pprint(results)