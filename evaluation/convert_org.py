import json
# 将原始数据转换为更适合让ML生成的格式

# 输入输出文件路径
input_file_path = "./data/cruxeval_org.jsonl"
output_file_path = "./data/cruxeval.json"

# 存储转换后的数据
converted_data = []

# 读取 .jsonl 文件并进行转换
with open(input_file_path, "r", encoding="utf-8") as infile:
    for line in infile:
        item = json.loads(line.strip())
        
        # 构建新的条目
        new_item = {
            "id": item.get("id"),
            "instruction": "Please reasoning about the following code according to input:",
            "input": f"Here is code:\n{item.get('code')}\nAnd input is:\n{item.get('input')}",
            "output": item.get('output')
        }
        
        converted_data.append(new_item)

# 写入到新的 JSON 文件
with open(output_file_path, "w", encoding="utf-8") as outfile:
    json.dump(converted_data, outfile, indent=4)