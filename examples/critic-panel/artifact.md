# critic-panel example

This example demonstrates a three-critic quorum gate for evaluating artifact quality.

## What it does

The maker improves a draft document. After each iteration, three independent critics
score it against a rubric. The loop continues until at least two of the three critics
score the artifact at or above 80 out of 100.

## Usage

```
bash run_demo.sh
```

The demo runs entirely in a temporary directory and does not require a live LLM.

## Output

`critics.jsonl` — one JSON line per critic per iteration, recording the score,
provider, rubric hash, artifact hash, and quorum configuration.
