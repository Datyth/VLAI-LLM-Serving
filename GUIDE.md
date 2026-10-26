Environment:

```
conda env create -f environment.yml
conda activate vlai-llm

python --version
python -m pip install -e ".[dev]"
```

Testing:
```
python -m pytest -q
python -m ruff check .
```