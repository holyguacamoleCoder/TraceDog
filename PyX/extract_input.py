import ollama

def call_ollama_extract_code(nl_text):
    """
    调用本地 Ollama 模型 qwen2.5:7b，要求提取 input/output 示例代码。
    返回纯 Python 示例代码字符串。
    """
    prompt = f"""
请阅读以下编程问题描述，并提取出示例输入和预期输出的 Python 代码部分，
只返回代码字符串，不要任何解释、函数定义或说明内容。

问题描述:
{nl_text}

要求：
- 只返回示例输入的 Python 字面量代码。
- 注意输出是唯一的一个代码变量。
- 不要包括函数定义、注释、自然语言解释、输出等任何其他内容。
"""

    response = ollama.generate(model='qwen2.5:7b', prompt=prompt)
    code_str = response.get('response', '').strip()

    return code_str

if __name__ == '__main__':
    # 示例 nl 字段内容
    nl = """Write a solution to the following coding problem:
    You are tasked with creating a Python function that processes a list of dictionaries representing users' data.
    ...
    Expected output:
    ```python
    filtered_users = [
        {'name': 'Alice', 'age': 25, 'gender': 'female', 'location': 'Europe'},
        {'name': 'Charlie', 'age': 20, 'gender': 'male', 'location': 'Europe'}
    ]
    ```"""
    nl2 = """
        "nl": "Write a solution to the following coding problem:\nYou are given a list of integers representing the scores of students in a class. Your task is to write a Python function that returns the top three unique scores in descending order. If there are fewer than three unique scores, return all unique scores in descending order.\n\nFunction signature: `def top_three_scores(scores: List[int]) -> List[int]:`\n\n**Input:**\n- A list of integers `scores` (1 <= len(scores) <= 10^4) representing the scores of students in the class. Each score is an integer between 0 and 100.\n\n**Output:**\n- Return a list of integers representing the top three unique scores in descending order.\n\n**Example:**\n```\nInput: scores = [85, 92, 78, 85, 92, 100, 78, 90]\nOutput: [100, 92, 90]\n\nInput: scores = [75, 75, 75, 75, 75]\nOutput: [75]\n```",
"""
    nl1 = "Write a solution to the following coding problem:\nYou are tasked with creating a Python function that processes a list of dictionaries representing users' data. The function should filter out users based on specific criteria and return a list of dictionaries containing only the relevant user information. Each user dictionary contains 'name', 'age', 'gender', and 'location' keys. The function should filter users based on the following conditions:\n1. Include users who are at least 18 years old.\n2. Include users who are female.\n3. Include users who are located in 'Europe'.\n\nWrite a function `filter_users(users_data)` that takes a list of user dictionaries as input and returns a filtered list of user dictionaries based on the specified conditions.\n\nExample input:\n```python\nusers_data = [\n    {'name': 'Alice', 'age': 25, 'gender': 'female', 'location': 'Europe'},\n    {'name': 'Bob', 'age': 30, 'gender': 'male', 'location': 'Asia'},\n    {'name': 'Charlie', 'age': 20, 'gender': 'male', 'location': 'Europe'},\n    {'name': 'Diana', 'age': 22, 'gender': 'female', 'location': 'North America'}\n]\n```\n\nExpected output:\n```python\nfiltered_users = [\n    {'name': 'Alice', 'age': 25, 'gender': 'female', 'location': 'Europe'},\n    {'name': 'Charlie', 'age': 20, 'gender': 'male', 'location': 'Europe'}\n]\n```",


    # 调用模型获取代码字符串
    code_result = call_ollama_extract_code(nl2)

    # 输出结果
    print(code_result)