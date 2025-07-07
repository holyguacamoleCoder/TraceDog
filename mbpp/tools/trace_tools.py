import sys
import json
import types
import copy
from functools import wraps, reduce
from mbpp.tools.json_tools import convert_dict_keys
# -----------------------------
# Trace 工具部分
# -----------------------------
trace_records = []
trace_target_func_name = None
last_line = None         # 上一行号
last_vars = {}           # 上一行执行后的变量状态
pending_vars = {}        # 当前帧的变量状态（用于 RETURN）
trace_step = 1

def is_serializable(val):
    if isinstance(val, (types.ModuleType, types.GeneratorType)):  # 直接排除模块对象
        return False
    try:
        json.dumps(val)
        return True
    except (TypeError, OverflowError):
        return False
def filter_vars(d):
    return {k: v for k, v in d.items() if is_serializable(v)}

def deep_diff(old, new, path=""):
    changes = []

    if isinstance(old, dict) and isinstance(new, dict):
        all_keys = set(old.keys()).union(set(new.keys()))
        for key in all_keys:
            new_path = f"{path}.{key}" if path else key
            if key not in old:
                changes.append(new_path)
            elif key not in new:
                changes.append(new_path)
            else:
                changes.extend(deep_diff(old[key], new[key], new_path))

    elif isinstance(old, (list, tuple)) and isinstance(new, (list, tuple)):
        for i in range(max(len(old), len(new))):
            new_path = f"{path}[{i}]"
            if i >= len(old):
                changes.append(new_path)
            elif i >= len(new):
                changes.append(new_path)
            else:
                changes.extend(deep_diff(old[i], new[i], new_path))

    else:
        if old != new:
            changes.append(path)

    return changes

def get_nested_value(data, path):
    """
    从 data 中提取嵌套路径 path 的值。
    支持格式：
        - my_list[i][j]
        - my_dict.key.subkey
        - buckets[14]
    """
    try:
        # 处理类似 buckets[14] 的路径
        if '[' in path:
            parts = []
            current = ''
            i = 0
            while i < len(path):
                if path[i] == '[':
                    if current:
                        parts.append(current)
                        current = ''
                    i += 1
                    bracket_content = ''
                    while i < len(path) and path[i] != ']':
                        bracket_content += path[i]
                        i += 1
                    parts.append(bracket_content)
                    i += 1
                else:
                    current += path[i]
                    i += 1
            if current:
                parts.append(current)

            result = data.get(parts[0]) if isinstance(data, dict) else None
            for p in parts[1:]:
                if isinstance(result, (list, tuple)) and p.isdigit():
                    if int(p) < len(result):
                        result = result[int(p)]
                    else:
                        return None  # 索引超出范围 → 返回 None
                elif isinstance(result, dict) and p in result:
                    result = result[p]
                else:
                    return None
            return result

        # 处理类似 a.b.c 的路径
        elif '.' in path:
            parts = path.split('.')
            result = data.get(parts[0]) if isinstance(data, dict) else None
            for p in parts[1:]:
                if isinstance(result, (list, tuple)) and p.isdigit():
                    if int(p) < len(result):
                        result = result[int(p)]
                    else:
                        return None
                elif isinstance(result, dict) and p in result:
                    result = result[p]
                else:
                    return None
            return result

        # 简单变量名
        else:
            return data[path] if isinstance(data, dict) and path in data else None

    except Exception as e:
        print(f"[ERROR] get_nested_value({data}, {path}) -> {e}")
        return None

def trace_calls(frame, event, arg):
    global last_line, last_vars, pending_vars, trace_step

    func_name = frame.f_code.co_name

    if func_name != trace_target_func_name:
        return trace_calls

    current_line = frame.f_lineno
    # 排除模块对象和系统内置变量
    filtered_vars = {}
    for k, v in dict(frame.f_locals).items():
        if isinstance(v, types.ModuleType):
            continue
        if k in ('__builtins__', '__loader__', '__name__', '__package__'):
            continue
        filtered_vars[k] = v
    current_vars = copy.deepcopy(filtered_vars)

    if event == 'call':
        trace_records.clear()
        trace_step = 1
        trace_records.append({
            "line": current_line,
            "step": trace_step,
            "action": "INPUT",
            "vars": current_vars.copy()
        })
        trace_step += 1
        last_line = current_line
        last_vars = copy.deepcopy(current_vars)
        return trace_calls

    elif event == 'return':
        if last_line and last_vars:
            changed = {
                k: v for k, v in last_vars.items()
                if k not in current_vars or current_vars[k] != v
            }
            changed = {k: v for k, v in changed.items() if is_serializable(v)}
            if changed:
                trace_records.append({
                    "line": last_line,
                    "step": trace_step,
                    "action": "EXECUTE",
                    "vars": changed
                })
                trace_step += 1

        trace_records.append({
            "line": current_line,
            "step": trace_step,
            "action": "RETURN",
            "vars": {"__return__": arg}
        })

    elif event == 'line':
        if last_line is not None:
            # 获取当前变量的完整路径变化
            changed_paths = deep_diff(last_vars, current_vars)

            # 强制加入所有局部变量名用于检查（防止漏掉基本变量如 i, j）
            for var_name in current_vars:
                if var_name in ('__builtins__', '__loader__', '__name__', '__package__'):
                    continue  # 忽略系统内置变量
                if var_name not in last_vars or current_vars[var_name] != last_vars[var_name]:
                    if is_serializable(current_vars[var_name]):
                        changed_paths.append(var_name)



            # 构建发生变化的变量及其完整结构
            changed_vars = {}
            changed_paths = sorted(set(changed_paths), key=lambda x: x.count('.') + x.count('['), reverse=True)
            for path in changed_paths:  # 去重
                # print(f"Path: {path}")
                value = get_nested_value(current_vars, path)
                # print(f"Value: {value}")
                if value is not None and is_serializable(value):
                    is_subpath = any(k.startswith(path + '[') or k.startswith(path + '.') for k in changed_vars)
                    if not is_subpath:
                        changed_vars[path] = value
                    # print(f"Changed_vars: {changed_vars}")

            if changed_vars:
                trace_records.append({
                    "line": last_line,
                    "step": trace_step,
                    "action": "EXECUTE",
                    "vars": changed_vars
                })
                trace_step += 1

        # 更新为当前帧的状态
        last_line = current_line
        last_vars = copy.deepcopy(current_vars)
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
def execute_function(code_str, input_args=None, target_func_name=None):
    global trace_target_func_name

    if input_args is None:
        input_args = []

    namespace = {}
    exec(code_str, namespace)

    functions = {k: v for k, v in namespace.items() if isinstance(v, types.FunctionType)}
    if not functions:
        raise ValueError("No function defined in the code string.")

    # 设置要追踪的目标函数名
    trace_target_func_name = target_func_name
    target_func = functions.get(target_func_name)
    # print("Target function:", target_func_name)
    if not target_func:
        raise ValueError(f"Function '{target_func_name}' not found in code string.")

    @enable_tracing
    def wrapped():
        return target_func(*input_args)

    output = wrapped()
    cleaned_input = convert_dict_keys(input_args)
    cleaned_output = convert_dict_keys(output)
    cleaned_traces = convert_dict_keys(trace_records.copy())
    return {
        "code": code_str.strip(),
        "entry_point": trace_target_func_name,
        "input": cleaned_input,
        "output": cleaned_output,
        "traces": cleaned_traces
    }