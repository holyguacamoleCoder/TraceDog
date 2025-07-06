import pandas as pd

# 读取原始数据
pyx_df = pd.read_json("hf://datasets/semcoder/PyX/pyx.jsonl", lines=True)

# 取前30条数据
pyx_sample = pyx_df.head(30)

# 保存为 JSON 文件
pyx_sample.to_json("pyx_sample.json", orient="records", indent=4)