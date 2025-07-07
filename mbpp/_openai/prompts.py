def make_sys_prompt():
    return """
You are an expert code interpreter that generates precise and consistent natural language explanations 
from Python function traces. Your goal is to clearly describe the algorithmic logic, variable changes, 
and execution flow based on the provided trace data.
"""


shot1 = """
[ANSWER]
The function `min_cost` calculates the minimum cost to reach the bottom-right corner of a 3x3 matrix using dynamic programming.

Execution steps:
1. The function starts with input parameters: a 3x3 cost matrix and target coordinates `(m=2, n=2)`.
2. A 3x3 table `tc` is initialized with zeros to store intermediate results.
3. The starting cell `tc[0][0]` is set to the value of `cost[0][0] = 1`.
4. The first column is filled by accumulating values from top to bottom:
   - `tc[1][0] = tc[0][0] + cost[1][0] = 1 + 4 = 5`
   - `tc[2][0] = tc[1][0] + cost[2][0] = 5 + 1 = 6`
5. The first row is filled similarly from left to right:
   - `tc[0][1] = tc[0][0] + cost[0][1] = 1 + 2 = 3`
   - `tc[0][2] = tc[0][1] + cost[0][2] = 3 + 3 = 6`
6. For each inner cell `(i,j)`, the cost is calculated as the minimum of the three possible incoming paths (top, left, diagonal) plus the current cost:
   - `tc[1][1] = min(tc[0][0], tc[0][1], tc[1][0]) + cost[1][1] = min(1, 3, 5) + 8 = 9`
   - `tc[1][2] = min(tc[0][1], tc[0][2], tc[1][1]) + cost[1][2] = min(3, 6, 9) + 2 = 5`
   - `tc[2][1] = min(tc[1][0], tc[1][1], tc[2][0]) + cost[2][1] = min(5, 9, 6) + 5 = 10`
   - `tc[2][2] = min(tc[1][1], tc[1][2], tc[2][1]) + cost[2][2] = min(9, 5, 10) + 3 = 8`
7. Finally, the function returns `tc[2][2] = 8`.

This approach ensures that the path with the lowest cumulative cost is selected through a structured dynamic programming process.
[/ANSWER]
"""

shot2 = """
[ANSWER]
The function `counting_sort` implements the counting sort algorithm to sort a list of non-negative integers.

In this execution:
1. The input list `[1, 23, 4, 5, 6, 7, 8]` is provided.
2. First, the maximum value in the list is determined by iterating through all elements. It is found to be `23`.
3. A `buckets` array of size `24` (max_value + 1) is initialized with zeros.
4. The function then iterates over the input list and increments the count for each number in the buckets:
   - `buckets[1] = 1`
   - `buckets[4] = 1`
   - `buckets[5] = 1`
   - `buckets[6] = 1`
   - `buckets[7] = 1`
   - `buckets[8] = 1`
   - `buckets[23] = 1`
5. Finally, the function reconstructs the sorted list by iterating through the buckets and placing each index value into the output list the number of times it occurred.

The final output list becomes: `[1, 4, 5, 6, 7, 8, 23]`.

This sorting process leverages the direct mapping between values and indices, making it efficient for small integer ranges.
[/ANSWER]
"""

def make_reason_output_prompt(data):
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
  
  return f"""
You are given a Python python code with entry function named `{entry_point}` :

```python
{code}
```

The function was called with these arguments: {input_desc}

During execution, the following steps occurred: {trace_desc}

Your task is to explain what this function does and how it behaves during execution. Focus on:

1. The algorithm or logic implemented
2. How variables change over time
3. Why The final result is computed as it is
Please provide your explanation inside [ANSWER]...[/ANSWER] tags.

Here are some examples for reference:

{shot1}

{shot2}

Provide your explanation inside [ANSWER] and [/ANSWER] tags. Do not include any extra text outside these tags.

[ANSWER] 
[/ANSWER]
"""