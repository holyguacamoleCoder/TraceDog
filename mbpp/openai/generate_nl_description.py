# generate_nl_description.py

import os
import json
import random
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
load_dotenv()

# 初始化 client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_API_BASE_URL"),
)


# ————————————————————————
# 工具函数
# ————————————————————————

def extract_nl_description(gen):
    return gen.strip()


def call_openai_api(system_prompt, prompt, temperature, n, model, max_tokens, stop):
    """
    调用 LLM 获取响应
    """
    print("Calling API...")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    while True:
        try:
            result = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                n=n,
                max_tokens=max_tokens,
                stop=stop
            )
            return [choice.message.content for choice in result.choices]
        except Exception as e:
            print(f"[ERROR] API call failed: {e}")
            import time; time.sleep(10)


def make_nl_description_prompt(data):
    """
    根据 trace_data 构造 prompt
    """
    code = data.get("code", "")
    entry_point = data.get("entry_point", "")
    input_args = data.get("input", [])
    output = data.get("output", None)
    traces = data.get("traces", [])

    # Step 1: 构建输入说明
    input_desc = ""
    if isinstance(input_args, list) and len(input_args) > 0:
        input_desc = "\n".join([f" - arg{i} = {repr(val)}" for i, val in enumerate(input_args)])

    # Step 2: 构建 trace 说明
    trace_desc = ""
    for step in traces:
        line = step.get("line")
        action = step.get("action")
        vars_dict = step.get("vars", {})
        step_num = step.get("step")

        var_str = "\n    ".join([f"{k} = {repr(v)}" for k, v in vars_dict.items()])
        trace_desc += f"Step {step_num} (Line {line}, {action}):\n    {var_str}\n"

    prompt = f"""
You are given a Python function named `{entry_point}` with the following code:

```python
{code}
```

The function was called with these arguments: {input_desc}

During execution, the following steps occurred: {trace_desc}

Your task is to explain what this function does and how it behaves during execution. Focus on:

The algorithm or logic implemented
How variables change over time
Why the final result is computed as it is
Provide your explanation inside [ANSWER] and [/ANSWER] tags. Do not include any extra text outside these tags.

[ANSWER] 
[/ANSWER]
"""

    return prompt.strip()


def prompt_nl_description(i, cache, gpt_query, temperature, n, model, max_tokens, stop): 
  """ 单次请求封装 """ 
  x = random.randint(1, 1000) 
  print(f"Started task {x}")
  full_prompt = make_nl_description_prompt(gpt_query)
  system_prompt = "You are an expert at Python programming."

  result = call_openai_api(
      system_prompt=system_prompt,
      prompt=full_prompt,
      temperature=temperature,
      n=n,
      model=model,
      max_tokens=max_tokens,
      stop=stop
  )

  return i, result

def batch_prompt_nl_description(queries, temperature, n, model, max_tokens, stop): 
    """ 批量调用 LLM 生成自然语言描述 """
    def fn(i, query):
      return prompt_nl_description(i, {}, query, temperature, n, model, max_tokens, stop)

    results = []

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(fn, i, query) for i, query in enumerate(queries)]
        results_with_id = [future.result() for future in futures]

    results_with_id.sort()
    raw_results = [i[1] for i in results_with_id]

    # 提取关键内容
    gens = [item for sublist in raw_results for item in sublist]  # flatten list
    extracted = [(extract_nl_description(gen), gen) for gen in gens]

    # 每个 sample 对应多个结果 (n=10)
    final_output = []
    for i in range(len(queries)):
        start = i * n
        end = start + n
        final_output.append(extracted[start:end])

    return final_output


if __name__ == "__main__":
  import sys 

  # 示例数据路径
  dataset_path = sys.argv[1] if len(sys.argv) > 1 else "../sample/trace_sample.json"
  dataset = json.load(open(dataset_path, "r"))
  print(f"dataset:{dataset}")

  results = batch_prompt_nl_description(
      queries=dataset,
      temperature=0.2,
      n=1,
      model="deepseek-chat",
      max_tokens=500,
      stop=["[/ANSWER]"]
  )

  print(f"Result:{results}")

  # 输出格式为：
  # [[(提取结果, 原始回复)], ...]
  for idx, res in enumerate(results):
      print(f"\nSample {idx}:")
      for ext, raw in res:
          print(f"Extracted:\n{ext}\n")

  output_path = "nl_descriptions.json"
  outputs_dict = {f"sample_{i}": [j[0] for j in o] for i, o in enumerate(results)}
  json.dump(outputs_dict, open(output_path, "w"), indent=2)
  print(f"Saved to {output_path}")