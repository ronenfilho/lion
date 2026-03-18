"""
Dicionário de Metadados de Documentos
Mapeia arquivos markdown processados para seus metadados legislativos
"""

DOCUMENT_METADATA = {
    # Exposições de Motivos (pl-1087-25_Exm-0019-25-MF_doc.md)
    "pl-1087-25_Exm-0019-25-MF_doc": {
        "type": "Exposição de Motivos",
        "project_number": "PROJETO DE LEI Nº 1.087, DE 2025",
        "converted_to_law": "Lei nº 15.270, de 2025",
        "full_title": "PROJETO DE LEI Nº 1.087, DE 2025 - Convertido na Lei nº 15.270, de 2025 - Exposição de Motivos",
        "description": "Altera a legislação do Imposto sobre a Renda para instituir a redução do imposto devido nas bases de cálculo mensal e anual e instituir a tributação mínima para as pessoas físicas que auferem altas rendas",
        "ministry": "Ministério da Fazenda",
    },
    
    # Lei nº 15.270 (pl-1087-25_processed.md)
    "pl-1087-25_processed": {
        "type": "Lei",
        "law_number": "Lei nº 15.270",
        "law_date": "de 26 de novembro de 2025",
        "project_number": "PROJETO DE LEI Nº 1.087, DE 2025",
        "full_title": "Lei nº 15.270, de 26 de novembro de 2025 - Altera a legislação do Imposto sobre a Renda",
        "description": "Altera a legislação do Imposto sobre a Renda para instituir a redução do imposto devido nas bases de cálculo mensal e anual e instituir a tributação mínima para as pessoas físicas que auferem altas rendas",
    },
    
    # Lei nº 9.250 (L9250compilado_processed.md)
    "L9250compilado_processed": {
        "type": "Lei",
        "law_number": "Lei nº 9.250",
        "law_date": "de 26 de dezembro de 1995",
        "full_title": "Lei nº 9.250 - Regula o imposto sobre a renda das pessoas físicas",
        "description": "Regula o imposto sobre a renda das pessoas físicas e dá outras providências",
    },
    
    # Lei nº 7.713 (L7713compilada_processed.md)
    "L7713compilada_processed": {
        "type": "Lei",
        "law_number": "Lei nº 7.713",
        "law_date": "de 22 de dezembro de 1988",
        "full_title": "Lei nº 7.713 - Altera a legislação do imposto sobre a renda",
        "description": "Altera a legislação do imposto sobre a renda e dá outras providências",
    },
    
    # Decreto nº 9.580 (D9580_processed.md)
    "D9580_processed": {
        "type": "Decreto",
        "decree_number": "Decreto nº 9.580",
        "decree_date": "de 22 de novembro de 2018",
        "full_title": "Decreto nº 9.580 - Regulamenta a tributação da renda",
        "description": "Regulamenta a tributação da renda das pessoas físicas, a tributação do lucro da pessoa jurídica",
    },
    
    # IN RFB nº 2178-2024 (IN RFB nº 2178-2024_processed.md)
    "IN RFB nº 2178-2024_processed": {
        "type": "Instrução Normativa",
        "instruction_number": "Instrução Normativa RFB nº 2.178",
        "instruction_date": "de 5 de março de 2024",
        "full_title": "Instrução Normativa RFB nº 2.178/2024",
        "description": "Instrução Normativa da Receita Federal do Brasil",
    },
    
    # IN RFB nº 1500-2014 (IN RFB nº 1500_2014_processed.md)
    "IN RFB nº 1500_2014_processed": {
        "type": "Instrução Normativa",
        "instruction_number": "Instrução Normativa RFB nº 1.500",
        "instruction_date": "de 29 de outubro de 2014",
        "full_title": "Instrução Normativa RFB nº 1.500/2014",
        "description": "Instrução Normativa da Receita Federal do Brasil",
    },
}


def get_document_metadata(doc_stem: str) -> dict:
    """
    Retorna metadados de um documento baseado em seu stem (nome sem extensão).
    
    Args:
        doc_stem: Nome do arquivo sem extensão (ex: "pl-1087-25_Exm-0019-25-MF_doc")
    
    Returns:
        Dict com metadados do documento, ou dict vazio se não encontrado
    """
    return DOCUMENT_METADATA.get(doc_stem, {})


def get_document_full_title(doc_stem: str) -> str:
    """Retorna o título completo do documento"""
    metadata = get_document_metadata(doc_stem)
    return metadata.get("full_title", doc_stem)


def is_exposicao_de_motivos(doc_stem: str) -> bool:
    """Verifica se documento é uma Exposição de Motivos"""
    metadata = get_document_metadata(doc_stem)
    return metadata.get("type") == "Exposição de Motivos"


if __name__ == "__main__":
    # Teste
    print("Testando document_metadata.py:\n")
    for doc_stem, metadata in DOCUMENT_METADATA.items():
        print(f"{doc_stem}:")
        print(f"  Tipo: {metadata.get('type', 'N/A')}")
        print(f"  Título: {metadata.get('full_title', 'N/A')}\n")
