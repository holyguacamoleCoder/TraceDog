import ast
import re

def extract_function_name(code_str):
    """
    从 Python 函数定义字符串中提取函数名。
    
    参数:
        code_str (str): 包含函数定义的字符串，如：
            'def similar_elements(test_tup1, test_tup2):\n  res = tuple(...)\n  return res'
    
    返回:
        str: 提取到的函数名，如 'similar_elements'；
        None: 如果未找到匹配的函数定义。
    """
    # 正则匹配函数定义：def 后面跟着函数名和括号
    match = re.findall(r'def\s+([0-9a-zA-Z_]\w*)', code_str)
    # print(match)
    return match
def extract_function_args(assert_str, allowed_funcs=None):
    """
    从 assert 字符串中提取函数名和参数。
    
    :param assert_str: 包含 assert 表达式的字符串
    :return: (func_name, args)，其中 args 是参数列表
    """
    node = ast.parse(assert_str)

    for n in ast.walk(node):
        if isinstance(n, ast.Assert):
            test = n.test
            if isinstance(test, ast.Compare):
                left = test.left
            else:
                left = test

            def find_call(node, allowed_funcs=None):
                # 如果是函数调用，尝试提取函数名和参数
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if allowed_funcs is None or node.func.id in allowed_funcs:
                            return {'name': node.func.id, 'args': node.args}
                    elif isinstance(node.func, ast.Attribute):
                        if allowed_funcs is None or node.func.attr in allowed_funcs:
                            return {'name': node.func.attr, 'args': node.args}

                    # 继续递归查找参数中的函数调用
                    for arg in node.args:
                        result = find_call(arg, allowed_funcs)
                        if result:
                            return result
                    for keyword in node.keywords:
                        result = find_call(keyword.value, allowed_funcs)
                        if result:
                            return result

                # 处理 set / list / tuple / dict 等容器类型
                elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
                    for elt in node.elts:
                        result = find_call(elt)
                        print('elt:')
                        if result:
                            return result

                # 处理一元运算（如 not, -）
                elif isinstance(node, ast.UnaryOp):
                    return find_call(node.operand)

                # 处理二元运算（如 +, -, ==）
                elif isinstance(node, ast.BinOp):
                    left_result = find_call(node.left, allowed_funcs)
                    if left_result:
                        return left_result
                    return find_call(node.right, allowed_funcs)

                # 处理比较表达式
                elif isinstance(node, ast.Compare):
                    return find_call(node.left, allowed_funcs)

                return None

            call_info = find_call(left, allowed_funcs)
            if call_info and 'name' in call_info:
                func_name = call_info['name']
                args = call_info['args']
                evaluated_args = []
                for arg in args:
                    try:
                        evaluated_args.append(ast.literal_eval(arg))
                    except ValueError:
                        print(f"⚠️ Skipping non-literal argument: {arg}")
                        continue
                return func_name, evaluated_args
    return None, []

if __name__ == "__main__":
    # test = "def similar_elements5(test_tup1, test_tup2):\n  res = tuple(set(test_tup1) & set(test_tup2))\n  return (res) "
    # test1 = "def is_Power_Of_Two (x): \n    return x and (not(x & (x - 1))) \ndef differ_At_One_Bit_Pos(a,b): \n    return is_Power_Of_Two(a ^ b)"
    # case2 = "def similar_elements(test_tup1, test_tup2):\n  res = tuple(set(test_tup1) & set(test_tup2))\n  return (res) "
    # allow2 = extract_function_name(case2)
    # print(allow2)
    # test2 = "assert is_not_prime(2) == False"
    # test3 = "assert differ_At_One_Bit_Pos(13,9) == True"
    # test4 = "assert set(similar_elements((3, 4, 5, 6),(5, 7, 4, 10))) == set((4, 5))"
    
    func803 = "def is_perfect_square(n) :\n    i = 1\n    while (i * i<= n):\n        if ((n % i == 0) and (n / i == i)):\n            return True     \n        i = i + 1\n    return False"
    case803 = "assert not is_perfect_square(10)"
    case803_2 = "assert is_perfect_square(36)"
    allow803 = extract_function_name(func803)

    print(extract_function_args(case803_2, allow803))