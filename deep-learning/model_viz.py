from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("facebook/opt-125m")
tok = AutoTokenizer.from_pretrained("facebook/opt-125m")
inputs = tok("hello", return_tensors="pt")
torch.onnx.export(
    model,
    (inputs.input_ids,),
    "opt125m.onnx",
    input_names=["input_ids"],
    opset_version=14,
)
