import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime
from cache import load_cache, save_cache

# 文件已经弃用！硬件条件原因，笔者使用LLaMAfactory进行生成


# 配置
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "trace-dogv1:latest"
model_prefix = "trace-dogv1"
# MODEL_NAME = "deepseek-coder"  # 替换为你的模型名
MAX_WORKERS = 2                # 并发数（根据GPU显存调整）
K = 1                          # Pass@k 的 k值
TEMPERATURE = 0.3              # 温度（0.1~1.0）
TOP_P = 0.9                    # 核采样
TIMEOUT = 120                  # 请求超时（秒）
ERROR_LOG = "./error/error_log.jsonl"   # 错误记录文件
CACHE_FILE = "./cache/cache.json"

# 加载数据
def load_data(file_path):
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]


# 生成请求
def generate(item, prompt, temperature=TEMPERATURE):
    # 加载缓存
    cache = load_cache()

    # 构造缓存 key（可以加上 temperature）
    cache_key = item["id"]

    if cache_key in cache:
        print(f"Using cached result for {cache_key}")
        return cache[cache_key]
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "options": {
                    "temperature": temperature,
                    "top_p": TOP_P,
                    "num_predict": 1024
                },
                "stream": False
            },
            timeout=TIMEOUT
        )
        # print(response.json())
        print(f"Generated result for {cache_key}")
        response.raise_for_status()
        cache[cache_key] = response.json()["response"]
        save_cache(cache)
        return response.json()["response"].strip()
    except Exception as e:
        log_error({
            "error": str(e),
            "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "timestamp": datetime.now().isoformat()
        })
        return None

# 记录错误案例
def log_error(error_data):
    with open(ERROR_LOG, "a") as f:
        f.write(json.dumps(error_data) + "\n")

# 构造提示模板
def build_prompt(item):
    return f"""Please reasoning about the following code according to input:
Here is code: {item['code']}
And input is: {item['input']}
"""

# 修改后的 evaluate 函数
def exec_batch_generation(dataset, sample_count=100):
    samples = dataset[:min(sample_count, len(dataset))]

    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for item in samples:
            prompt = build_prompt(item)
            for _ in range(K):  # K次生成任务
                futures.append(executor.submit(generate, item, prompt, TEMPERATURE))

        progress = tqdm(total=len(futures), desc="Generating")

        for future in as_completed(futures):
            generated_content = future.result()
            results.append({
                "id": future["id"],
                "generated": generated_content,
                "input": future["input"],
                "expected_output": future["output"],
                # "output": generated_content,
            })
            progress.update(1)
        progress.close()

    # 仅保存生成内容
    with open(f"./generations/{model_prefix}_t{TEMPERATURE}.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n模型生成内容已保存至 ./generations/{model_prefix}_t{TEMPERATURE}.json")

if __name__ == "__main__":
    dataset = load_data("./data/cruxeval.jsonl")
    exec_batch_generation(dataset, sample_count=1000)