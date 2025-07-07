from _openai.prompts import make_reason_output_prompt
from _openai.prompts import make_sys_prompt
from _openai.cache import load_cache, save_cache
from _openai.call_api import call_openai_api
# from _openai.checkpoint import load_checkpoint, save_checkpoint

import os
import json
import random
from concurrent.futures import ThreadPoolExecutor


max_workers = 30

def extract_nl_description(gen):
    if gen is None: 
        return ""
    return gen.replace("[ANSWER]", "").strip()

def prompt_nl_description(i, cache, gpt_query, temperature, n, model, max_tokens, stop): 
    """ 单次请求封装 """ 
    data_id = gpt_query["id"]
    print(f"Started id {data_id}")
    full_prompt = make_reason_output_prompt(gpt_query).strip()

    if temperature == 0:
        cache_key = f"{data_id}_{model}"
    else:
        cache_key = f"{data_id}_{model}_{str(temperature)}"

    if cache_key in cache and len(cache[cache_key]) >= n:
        print(f"Using cached result for {cache_key}")
        return i, cache[cache_key][:n]

    system_prompt = make_sys_prompt()

    result = call_openai_api(
        system_prompt=system_prompt,
        prompt=full_prompt,
        temperature=temperature,
        n=n,
        model=model,
        max_tokens=max_tokens,
        stop=stop
    )

    cache[cache_key] = result
    save_cache(cache)
    return i, result

def batch_prompt_nl_description(queries, temperature, n, model, max_tokens, stop): 
    """ 批量调用 LLM 生成自然语言描述 """
    cache = load_cache()
    def fn(i, query, cache):
      return prompt_nl_description(i, cache, query, temperature, n, model, max_tokens, stop)

    # results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fn, i, query, cache) for i, query in enumerate(queries)]
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
    from tools.json_tools import load_all_traces_from_dir
    from tools.json_tools import save_results_in_batches

    # 批量输出sample
    # dataset_path = "./sample/processed_trace_sample.json"
    # output_path = "./sample/nl_descriptions_batch_sample.json"

    # 单条输出sample
    # dataset_path = "./sample/trace_sample.json"
    # output_path = "./sample/nl_description_sample.json"
    
    # dataset = json.load(open(dataset_path, "r"))
    # print(f"dataset:{dataset}")
    
    # import sys
    # if len(sys.argv) > 1:
    #     input_dir = sys.argv[1]
    # if len(sys.argv) > 2:
    #     output_dir = sys.argv[2]
    # if len(sys.argv) > 3:
    #     output_prefix = sys.argv[3]
    # if len(sys.argv) > 4:
    #     batch_size = int(sys.argv[4])

    # 生产使用
    input_dir = "./trace_processed"
    output_dir = "./nl_result"
    output_prefix = "nl_descriptions_batch"
    batch_size = 100

    # dataset = load_all_traces_from_dir(input_dir, "cleaned_trace_", ".json")
    # 加载 0~9 批次的文件
    dataset = load_all_traces_from_dir("./trace_processed", filename_prefix="cleaned_trace_", start_idx=20, end_idx=26)
    # load_all_traces_from_dir("./trace_processed", filename_prefix="trace_batch_", start_idx=10, end_idx=20)
    
    results = batch_prompt_nl_description(
        queries=dataset,
        temperature=0.2,
        n=1,
        model="deepseek-chat",
        max_tokens=1024,
        stop=["[/ANSWER]"]
    )

    # print(f"Result:{results}")

    # 输出格式为：
    # [[(提取结果, 原始回复)], ...]
    output_data = []
    for idx, res in enumerate(results):
        data_id = dataset[idx].get("id")  # 获取原始数据中的 id 字段
        for ext, raw in res:
            output_data.append({
                "id": data_id,
                "nl": ext.strip()
            })


    # 写入 JSON 文件
    curdir = os.path.dirname(os.path.abspath(__file__))
    save_results_in_batches(
        output_data,
        output_dir=curdir + "/nl_result",
        # !!!!!!!!!!!!注意改!!!!!!!!!!!!!!
        # TODO
        output_prefix="nl_descriptions_batch2",
        batch_size=100
    )

    # json.dump(output_data, open(output_path, "w"), indent=2, ensure_ascii=False)
    # print(f"Saved {len(output_data)} descriptions to {output_path}")