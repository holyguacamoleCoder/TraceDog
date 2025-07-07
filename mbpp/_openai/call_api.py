from openai import OpenAI
import os
import time
from dotenv import load_dotenv
load_dotenv()

# 初始化 client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_API_BASE_URL"),
)

def call_openai_api(system_prompt, prompt, temperature, n, model, max_tokens, stop):
    """
    调用 LLM 获取响应
    """
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
            # 特定错误处理：token 超限
            if "maximum context length" in str(e):
                print(f"[ERROR] 请求内容过长，无法处理。提示：请缩短 prompt 内容或降低 max_tokens。")
                return [""] * n  # 返回空结果，避免程序崩溃

            else:
                print(f"[ERROR] API call failed: {e}")
                print("[INFO] 等待 10 秒后重试...")
                time.sleep(10)