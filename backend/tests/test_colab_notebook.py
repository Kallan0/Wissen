import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "backend" / "finetuning" / "fine_tune_colab.ipynb"
TRAINING_DATA = ROOT / "backend" / "data" / "finetuning" / "training_data.jsonl"


def test_colab_notebook_is_valid_and_precision_safe():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]

    for index, cell in enumerate(code_cells, start=1):
        source = "".join(
            line for line in cell["source"] if not line.lstrip().startswith("%")
        )
        compile(source, f"colab-cell-{index}", "exec")

    all_source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    dataset_hash = hashlib.sha256(TRAINING_DATA.read_bytes()).hexdigest()
    assert dataset_hash in all_source
    assert 'if "holdout_eval.jsonl" in uploaded' in all_source
    assert "parameter.data.to(torch.float32)" in all_source
    assert "fp16=not USE_BF16" in all_source
    assert "bf16=USE_BF16" in all_source
