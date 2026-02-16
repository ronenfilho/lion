#!/bin/bash
# Wrapper para executar experimentos do LION

# Ativar ambiente virtual
source /home/decode/workspace/lion/venv/bin/activate

# Adicionar diretório raiz ao PYTHONPATH
export PYTHONPATH="/home/decode/workspace/lion:$PYTHONPATH"

# Executar script Python
python scripts/4_run_experiments.py "$@"
