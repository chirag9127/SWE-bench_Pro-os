# Run Loss Analysis

The data in `data/` has been prepared from `../runs/swepro-15task-mini-20260608`.

Important: the source run did not include verifier rewards. The prepared
`results.csv` uses a provisional process-analysis proxy documented in
`data/README.md`.

## 1. Install Python Dependencies

```bash
cd auto-loss-analysis-main
python3 -m pip install pandas matplotlib toml python-docx
```

## 2. Verify The Prepared Data

```bash
cd auto-loss-analysis-main
python3 scripts/compute_stats.py --data ./data --output ./output/analysis/statistics.json
```

Expected prepared dataset:

- 15 tasks
- 3 models: `claude-haiku-4-5`, `claude-opus-4-8`, `kimi-k2.5`
- 45 trajectory files under `data/evals`

## 3. Run The Claude Code Loss Analysis Controller

From inside `auto-loss-analysis-main`, run:

```bash
/loss-analysis
```

The controller skill reads `data/`, runs the staged analysis waves, and writes:

- `output/analysis/*.json`
- `output/figures/*.png`
- `output/sections/*.md`
- `output/report.md`
- `output/report.docx`

## 4. Manual Fallback

If the slash command is not available, use
`.claude/skills/loss-analysis/SKILL.md` as the controller procedure. Run the
Python steps directly, then use the prompts in `skills/*.md` for the LLM
classification, investigation, critique, and writing waves.

Useful direct commands:

```bash
cd auto-loss-analysis-main
python3 scripts/compute_stats.py --data ./data --output ./output/analysis/statistics.json
python3 scripts/generate_charts.py --analysis ./output/analysis --figures ./output/figures
python3 scripts/md_to_docx.py --input output/report.md --output output/report.docx
```
