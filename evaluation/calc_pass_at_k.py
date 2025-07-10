import re
import json

# 由输入的generations文件计算pass@k

# 正则表达式 pattern
pattern = re.compile(r" Above all ,The output is: (.*?)(\n|$)", re.DOTALL)

def extract_output(text):
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return None



def item_matches_label(item, label):
    predict = item.get('predict', [])
    output = extract_output(predict)

    # 去除两边引号并 strip 空格后再比较
    if output is not None:
        # 去掉首尾的引号和空格
        output_clean = output.strip().strip("'").strip('"')
        label_clean = label.strip().strip("'").strip('"')

        # print(f"Output: '{output_clean}', Label: '{label_clean}'")
        return output_clean == label_clean

    return False

def get_correct_matrix(file_paths):
    """
    输入多个文件路径，返回 N x M 的布尔矩阵：
    matrix[i][j] 表示第 i 个样本在第 j 次预测中是否通过
    """
    matrices = []

    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            matrices.append([False] * len(lines))

            for idx, line in enumerate(lines):
                try:
                    item = json.loads(line)
                    label = item.get('label', '').strip()
                    matrices[-1][idx] = item_matches_label(item, label)
                except Exception as e:
                    print(f"Error parsing line {idx} in {file_path}: {e}")
                    matrices[-1][idx] = False

    # 转置成 N x M 矩阵（N 个样本，M 次尝试）
    correct_matrix = list(zip(*matrices))
    return correct_matrix


def pass_at_k(file_paths, k):
    """
    接收文件路径列表和 k 值，返回 pass@k 分数。
    内部逻辑：
    1. 构建正确性矩阵
    2. 使用标准 pass@k 公式计算得分
    """
    correct_matrix = get_correct_matrix(file_paths)
    # print(correct_matrix)
    total = len(correct_matrix)
    passed = 0

    for sample_result in correct_matrix:
        n = len(sample_result)  # 总共尝试了多少次（如 3）
        c = sum(sample_result)  # 成功了几次

        if n < k:
            raise ValueError(f"Sample has only {n} attempts, less than required k={k}")

        # 如果没有成功，直接跳过
        if c == 0:
            continue

        # 否则计算 pass@k 概率（只要有一次对就算通过）
        # 这里是简化版，可以替换为更复杂的概率模型
        if any(sample_result[:k]):
            passed += 1

    return passed / total


# 示例调用
if __name__ == "__main__":
    # base_dir = './generations/sample'
    base_dir = './generations/deepseek-coder-6.7b-instruct'
    file_paths1 = [
        # f"{base_dir}/generated_third.jsonl"
        # f"{base_dir}/generated_second.jsonl"
        f"{base_dir}/generated_third.jsonl"
    ]
    file_paths3 = [
        f"{base_dir}/generated_first.jsonl",
        f"{base_dir}/generated_second.jsonl",
        f"{base_dir}/generated_third.jsonl"
    ]

    # 只需调用一次 pass_at_k 函数即可
    pass1_score = pass_at_k(file_paths1, k=1)
    pass3_score = pass_at_k(file_paths3, k=3)

    print(f"Pass@1: {pass1_score:.4f}")
    print(f"Pass@3: {pass3_score:.4f}")