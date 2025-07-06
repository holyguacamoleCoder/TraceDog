from datasets import load_dataset

ds = load_dataset("Muennighoff/mbpp", "sanitized")
ds.save_to_disk("mbpp")

from datasets import load_dataset

ds = load_dataset("Muennighoff/mbpp", "full")
ds.save_to_disk("mbpp")
