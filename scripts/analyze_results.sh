#!/bin/bash
# Script auxiliar para análise de resultados de experimentos

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔍 Análise de Resultados - LION"
echo "================================"
echo ""

# Ativar ambiente virtual se existir
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Configurar PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Verificar argumentos
if [ $# -eq 0 ]; then
    echo "Uso: $0 <experiment_type> [options]"
    echo ""
    echo "Exemplos:"
    echo "  $0 rag_vs_no_rag                           # Análise básica"
    echo "  $0 rag_vs_no_rag --compare                 # Com comparação detalhada"
    echo "  $0 rag_vs_no_rag --statistical-test        # Com testes estatísticos"
    echo "  $0 rag_vs_no_rag --output report.md        # Gerar relatório completo"
    echo ""
    echo "Experimentos disponíveis:"
    echo "  - rag_vs_no_rag"
    echo "  - retrieval_strategy"
    echo "  - chunk_count"
    echo "  - llm_size"
    echo ""
    exit 1
fi

# Executar análise
python "$SCRIPT_DIR/analyze_results.py" "$@"
