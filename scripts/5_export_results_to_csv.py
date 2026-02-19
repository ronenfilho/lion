"""
Export Results to CSV - LION
Script para consolidar metadados e métricas agregadas de todos os arquivos JSON
Uma linha por experimento (sem expandir resultados individuais)
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse
import logging


def setup_logging():
    """Configura logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"{timestamp}_csv_export.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logging.info(f"Log iniciado: {log_file}")


def extract_all_results_to_csv(
    results_dir: str = "experiments/results/raw",
    output_file: str = None
) -> str:
    """
    Extrai todos os resultados JSON para um único CSV tabular.
    
    Args:
        results_dir: Diretório com arquivos JSON
        output_file: Nome do arquivo CSV de saída (None = auto-gerado)
    
    Returns:
        Caminho do arquivo CSV gerado
    """
    results_path = Path(results_dir)
    
    if not results_path.exists():
        raise ValueError(f"Diretório não encontrado: {results_dir}")
    
    print("\n" + "="*70)
    print("📊 EXPORT DE RESULTADOS JSON PARA CSV")
    print("="*70 + "\n")
    
    # Descobrir todos os arquivos JSON (ignorar summary)
    json_files = [
        f for f in results_path.glob("*.json")
        if '_summary' not in f.name
    ]
    
    print(f"🔍 Arquivos JSON encontrados: {len(json_files)}\n")
    
    all_rows = []
    
    for json_file in sorted(json_files):
        logging.info(f"Processando: {json_file.name}")
        print(f"📄 {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Informações básicas do experimento
            base_row = {
                'arquivo_json': json_file.name,
                'experiment_name': data.get('experiment_name', 'N/A'),
                'timestamp': data.get('timestamp', 'N/A'),
                'total_questions': data.get('total_questions', 0),
                'successful_queries': data.get('successful_queries', 0),
                'failed_queries': data.get('failed_queries', 0),
            }
            
            # Extrair configuração
            config = data.get('config', {})
            for key, value in config.items():
                base_row[f'config_{key}'] = value
            
            # Extrair métricas agregadas
            metrics = data.get('aggregated_metrics', {})
            for metric_key, metric_value in metrics.items():
                base_row[metric_key] = metric_value
            
            # Adicionar apenas a linha consolidada (uma linha por arquivo JSON)
            all_rows.append(base_row)
        
        except Exception as e:
            logging.error(f"Erro ao processar {json_file.name}: {e}")
            print(f"   ⚠️  Erro: {e}")
            continue
    
    # Criar DataFrame
    df = pd.DataFrame(all_rows)
    
    print(f"\n✅ Total de linhas processadas: {len(df)}")
    print(f"   Total de colunas: {len(df.columns)}")
    
    # Gerar nome do arquivo se não fornecido
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"EXPORT_COMPLETO_RESULTADOS_{timestamp}.csv"
    
    # Garantir extensão .csv
    if not output_file.endswith('.csv'):
        output_file += '.csv'
    
    # Salvar no diretório de análises
    analysis_dir = Path("experiments/results/analysis")
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = analysis_dir / output_file
    
    # Exportar CSV com separador ; e decimal ,
    df.to_csv(
        csv_path,
        index=False,
        sep=';',
        decimal=',',
        encoding='utf-8-sig'  # BOM para Excel
    )
    
    print(f"\n💾 CSV salvo: {csv_path}")
    print(f"   Formato: separador ';' | decimal ',' | encoding UTF-8 BOM")
    
    # Estatísticas
    print(f"\n📊 Estatísticas:")
    print(f"   Experimentos processados: {len(df)}")
    print(f"   Experimentos únicos: {df['experiment_name'].nunique()}")
    print(f"   Total de questões: {df['total_questions'].sum()}")
    
    # Mostrar preview das colunas
    print(f"\n📋 Colunas exportadas ({len(df.columns)}):")
    cols_by_category = {
        'Básicas': [c for c in df.columns if c.startswith(('arquivo', 'experiment', 'timestamp', 'total', 'successful', 'failed'))],
        'Configuração': [c for c in df.columns if c.startswith('config_')],
        'Métricas Agregadas': [c for c in df.columns if any(x in c for x in ['_mean', '_std', '_min', '_max', '_median'])]
    }
    
    for category, cols in cols_by_category.items():
        if cols:
            print(f"\n   {category} ({len(cols)}):")
            for col in sorted(cols)[:10]:  # Mostrar primeiras 10
                print(f"      - {col}")
            if len(cols) > 10:
                print(f"      ... e mais {len(cols) - 10}")
    
    logging.info(f"CSV exportado: {csv_path}")
    
    return str(csv_path)


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Exporta todos os resultados JSON para CSV tabular'
    )
    parser.add_argument(
        '--results-dir',
        default='experiments/results/raw',
        help='Diretório com arquivos JSON'
    )
    parser.add_argument(
        '--output',
        help='Nome do arquivo CSV de saída (padrão: auto-gerado com timestamp)'
    )
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        csv_path = extract_all_results_to_csv(
            results_dir=args.results_dir,
            output_file=args.output
        )
        
        print("\n" + "="*70)
        print("✅ EXPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*70 + "\n")
        
        print(f"📁 Arquivo gerado: {csv_path}")
        print(f"\n💡 Dica: Abra no Excel/LibreOffice com:")
        print(f"   - Separador: ponto-e-vírgula (;)")
        print(f"   - Encoding: UTF-8")
        print(f"   - Decimal: vírgula (,)")
        
    except Exception as e:
        logging.error(f"Erro durante exportação: {e}")
        print(f"\n❌ Erro: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
