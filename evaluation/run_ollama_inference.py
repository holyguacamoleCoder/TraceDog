import json
import subprocess
import time
import os
from tqdm import tqdm

# 设置路径
DATASET_PATH = "./data/cruxeval_sample.jsonl"
GENERATIONS_DIR = "./model_generations/your_model_name/generations/output"

PROMPT_TEMPLATE = """Below is an instruction that describes a task, paired with an input and output. Write a Python function to solve the task.

### Instruction:
{instruction}

### Input:
{input}

### Response:"""

def load_cruxeval_dataset(path):
    """加载 cruxeval.jsonl 数据集"""
    dataset = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            dataset.append(json.loads(line.strip()))
    return dataset


def generate_with_ollama(prompt, model_name="llama3", max_tokens=200, temperature=0.2):
    """
    调用 ollama 生成响应
    :param prompt: 提示词
    :param model_name: 模型名
    :param max_tokens: 最大输出 token 数
    :param temperature: 温度参数
    :return: 模型输出文本
    """
    cmd = [
        "ollama",
        "run",
        model_name,
        prompt
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=60,
            check=True,
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"⚠️ Ollama 生成失败: {e}")
        return ""


def build_prompt(sample):
    """根据 sample 构建 Alpaca 格式 prompt"""
    return PROMPT_TEMPLATE.format(
        instruction=sample["nl"],
        input=str(sample["input"]),
    )


def main(model_name="codellama", temperature=0.2):
    # 创建输出目录
    os.makedirs(GENERATIONS_DIR, exist_ok=True)

    # 加载数据集
    dataset = load_cruxeval_dataset(DATASET_PATH)
    print(f"✅ 加载了 {len(dataset)} 条测试样本")

    generations = {}
    for idx, sample in enumerate(tqdm(dataset, desc="🧠 Generating")):
        prompt = build_prompt(sample)

        # 调用 ollama 生成
        response = generate_with_ollama(prompt, model_name=model_name)

        generations[f"sample_{idx}"] = [response]  # 支持多 generation，这里只保留一个

        # 可选：控制速率
        time.sleep(0.1)

    # 保存生成结果
    output_path = os.path.join(GENERATIONS_DIR, f"{model_name}_temp{temperature}_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(generations, f, indent=2, ensure_ascii=False)

    print(f"\n💾 生成完成！结果已保存至: {output_path}")


if __name__ == "__main__":
    main(model_name="deepseek-coder:6.7b", temperature=0.2)