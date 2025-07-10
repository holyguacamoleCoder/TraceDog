import os
import json

# 文件已经弃用！硬件条件原因，笔者使用LLaMAfactory进行生成


CACHE_DIR_PREFIX = "./cache"
cache_path = os.path.join(CACHE_DIR_PREFIX, "cache.json")

def load_cache():
    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_cache(cache):
    # prompt + model + temperature
    os.makedirs(CACHE_DIR_PREFIX, exist_ok=True)
    tmp_path = cache_path + ".tmp"
    bak_path = cache_path + ".bak"
    with open(tmp_path, "w") as f:
        json.dump(cache, f, indent=2)
    if os.path.exists(cache_path):
        os.rename(cache_path, bak_path)
    os.rename(tmp_path, cache_path)
    if os.path.exists(bak_path):
        os.remove(bak_path)