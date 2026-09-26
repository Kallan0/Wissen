import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = ROOT / "backend" / "finetuning" / "evaluate_adapter_colab.ipynb"


def test_adapter_evaluation_notebook_is_valid_and_pinned():
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    code_cells = ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]
    source = "\n".join(code_cells)

    for index, cell_source in enumerate(code_cells):
        if not cell_source.lstrip().startswith("%"):
            compile(cell_source, f"adapter-eval-cell-{index}", "exec")

    assert "eaf9efd5c0f29421d17e9a4a87a546f671f4913b2551addeb1e15c18790982c1" in source
    assert "8d25b49f6d706254b61f9361e56592185b674a79af504175bcf65888484e1d72" in source
    assert "8afb486c1db24fe5011ec46dfbe5b5dccdb575c2" in source
    assert "record['messages'][:2]" in source
    assert "PROGRESS_PATH" in source
    assert "adapter_holdout_outputs.json" in source
    assert "merge_and_unload" not in source
    assert "training_data.jsonl" not in source


def test_adapter_evaluation_notebook_keeps_holdout_labels_out_of_prompts():
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    source = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )

    prompt_line = next(line for line in source.splitlines() if "apply_chat_template" in line)
    assert "[:2]" in prompt_line
    assert "messages'][2]" not in prompt_line
