from datasets import load_dataset

print("Testing SQID dataset connection...")
try:
    ds = load_dataset("Crossing-Minds/shopping-queries-image-dataset", split="train[:5]")
    print(ds)
    print(ds[0].keys())
except Exception as e:
    print("Error:", e)
