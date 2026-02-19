"""
Prompts - LION
Templates de prompts especializados para assistente IRPF
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Template de prompt"""
    name: str
    system_instruction: str
    user_template: str
    description: str


class PromptManager:
    """
    Gerenciador de prompts para o sistema LION.
    
    Fornece templates especializados para diferentes tipos de queries
    sobre Imposto de Renda.
    """
    
    # Sistema base para todas as queries
    BASE_SYSTEM = """Você é um assistente especializado em Imposto de Renda Pessoa Física (IRPF) brasileiro.

REGRAS IMPORTANTES:
1. Base suas respostas EXCLUSIVAMENTE nas informações do contexto fornecido
2. Se a informação não estiver no contexto, diga claramente "Não encontrei essa informação nos documentos consultados"
3. Cite os artigos, parágrafos ou seções relevantes quando aplicável
4. Use linguagem clara e acessível, evitando jargão desnecessário
5. Se a pergunta for ambígua, peça esclarecimentos
6. Para cálculos, mostre o passo a passo
7. Indique sempre o ano-calendário quando relevante

FORMATO DA RESPOSTA:
- Seja direto e objetivo
- Use bullets ou numeração quando listar múltiplos itens
- Destaque valores monetários e percentuais claramente
- Finalize com uma frase resumindo a resposta principal"""

    def __init__(self):
        """Inicializa gerenciador de prompts."""
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, PromptTemplate]:
        """
        Carrega templates de prompts.
        
        Returns:
            Dict de templates por nome
        """
        templates = {}
        
        # Template padrão RAG
        templates['rag_default'] = PromptTemplate(
            name='rag_default',
            system_instruction=self.BASE_SYSTEM,
            user_template="""Contexto recuperado dos documentos:
{context}

Pergunta do usuário: {query}

Forneça uma resposta baseada apenas no contexto acima.""",
            description='Template RAG padrão com contexto'
        )
        
        # Template para deduções
        templates['deductions'] = PromptTemplate(
            name='deductions',
            system_instruction=self.BASE_SYSTEM + """

FOCO: Deduções permitidas no IRPF
- Tipos de deduções (dependentes, educação, saúde, previdência)
- Limites de valores
- Documentação necessária
- Condições e restrições""",
            user_template="""Documentos sobre deduções:
{context}

Pergunta sobre deduções: {query}

Explique quais deduções se aplicam, seus limites e requisitos.""",
            description='Especializado em deduções fiscais'
        )
        
        # Template para cálculos
        templates['calculation'] = PromptTemplate(
            name='calculation',
            system_instruction=self.BASE_SYSTEM + """

FOCO: Cálculos e alíquotas do IRPF
- Tabela progressiva
- Cálculo do imposto devido
- Deduções aplicáveis
- Imposto a pagar ou restituir

IMPORTANTE: Mostre SEMPRE o passo a passo dos cálculos.""",
            user_template="""Informações sobre cálculo:
{context}

Situação para calcular: {query}

Forneça o cálculo detalhado com todos os passos.""",
            description='Especializado em cálculos de imposto'
        )
        
        # Template para prazos
        templates['deadlines'] = PromptTemplate(
            name='deadlines',
            system_instruction=self.BASE_SYSTEM + """

FOCO: Prazos e obrigatoriedades
- Prazo de entrega da declaração
- Datas de pagamento
- Multas por atraso
- Retificação de declarações""",
            user_template="""Informações sobre prazos:
{context}

Pergunta sobre prazos: {query}

Informe as datas relevantes e consequências de atraso.""",
            description='Especializado em prazos e datas'
        )
        
        # Template para rendimentos
        templates['income'] = PromptTemplate(
            name='income',
            system_instruction=self.BASE_SYSTEM + """

FOCO: Tipos de rendimentos
- Rendimentos tributáveis
- Rendimentos isentos
- Rendimentos sujeitos à tributação exclusiva
- Carnê-leão e outras antecipações""",
            user_template="""Informações sobre rendimentos:
{context}

Pergunta sobre rendimentos: {query}

Explique como declarar e tributar o tipo de rendimento mencionado.""",
            description='Especializado em tipos de rendimentos'
        )
        
        # Template para dependentes
        templates['dependents'] = PromptTemplate(
            name='dependents',
            system_instruction=self.BASE_SYSTEM + """

FOCO: Dependentes na declaração
- Quem pode ser declarado como dependente
- Valores de dedução por dependente
- Inclusão de despesas médicas e educacionais de dependentes
- Alimentandos""",
            user_template="""Informações sobre dependentes:
{context}

Pergunta sobre dependentes: {query}

Explique as regras para dependentes e deduções aplicáveis.""",
            description='Especializado em dependentes'
        )
        
        # Template para consulta geral (sem contexto)
        templates['general'] = PromptTemplate(
            name='general',
            system_instruction=self.BASE_SYSTEM,
            user_template="""{query}

Responda de forma clara e estruturada.""",
            description='Template genérico sem contexto RAG'
        )
        
        return templates
    
    def get_template(self, name: str = 'rag_default') -> PromptTemplate:
        """
        Obtém template por nome.
        
        Args:
            name: Nome do template
            
        Returns:
            PromptTemplate
        """
        return self.templates.get(name, self.templates['rag_default'])
    
    def format_prompt(
        self,
        template_name: str,
        query: str,
        context: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Formata prompt usando template.
        
        Args:
            template_name: Nome do template
            query: Pergunta do usuário
            context: Contexto opcional (chunks recuperados)
            
        Returns:
            Tupla (system_instruction, user_prompt)
        """
        template = self.get_template(template_name)
        
        # Formatar prompt do usuário
        if context:
            user_prompt = template.user_template.format(
                query=query,
                context=context
            )
        else:
            # Template sem contexto (general)
            user_prompt = template.user_template.format(query=query)
        
        return template.system_instruction, user_prompt
    
    def detect_query_type(self, query: str) -> str:
        """
        Detecta tipo de query para selecionar template adequado.
        
        Args:
            query: Pergunta do usuário
            
        Returns:
            Nome do template sugerido
        """
        query_lower = query.lower()
        
        # Palavras-chave para cada tipo
        keywords = {
            'deductions': ['dedução', 'deduzir', 'abater', 'desconto', 'despesa'],
            'calculation': ['calcular', 'cálculo', 'quanto', 'valor', 'alíquota', 'imposto devido'],
            'deadlines': ['prazo', 'data', 'quando', 'entregar', 'multa', 'atraso'],
            'income': ['rendimento', 'salário', 'renda', 'tributável', 'isento', 'carnê-leão'],
            'dependents': ['dependente', 'filho', 'alimentando', 'cônjuge', 'incluir dependente']
        }
        
        # Contar matches
        scores = {}
        for template_name, words in keywords.items():
            score = sum(1 for word in words if word in query_lower)
            if score > 0:
                scores[template_name] = score
        
        # Retornar template com maior score
        if scores:
            best_template = max(scores.items(), key=lambda x: x[1])[0]
            return best_template
        
        return 'rag_default'
    
    def generate_rag_prompt(
        self,
        question: str,
        context_chunks: List[str]
    ) -> str:
        """
        Gera prompt RAG com contexto.
        
        Args:
            question: Pergunta do usuário
            context_chunks: Lista de chunks de contexto
        
        Returns:
            Prompt formatado completo
        """
        # Detectar melhor template
        template_name = self.detect_query_type(question)
        template = self.get_template(template_name)
        
        # Formatar contexto
        context = "\n\n".join([
            f"[Trecho {i+1}]\n{chunk}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        # Formatar prompt
        user_prompt = template.user_template.format(
            query=question,
            context=context
        )
        
        # Retornar prompt completo (system + user)
        return f"{template.system_instruction}\n\n{user_prompt}"
    
    def generate_no_rag_prompt(self, question: str) -> str:
        """
        Gera prompt sem RAG (baseline).
        
        Args:
            question: Pergunta do usuário
        
        Returns:
            Prompt formatado sem contexto
        """
        system = """Você é um assistente especializado em Imposto de Renda Pessoa Física (IRPF) brasileiro.

Responda à pergunta do usuário com base no seu conhecimento sobre legislação tributária brasileira.

Use linguagem clara e acessível. Cite artigos de lei quando apropriado."""
        
        return f"{system}\n\nPergunta: {question}\n\nResposta:"
    
    def generate_few_shot_prompt(
        self,
        question: str,
        context_chunks: List[str],
        examples: List[Dict[str, str]]
    ) -> str:
        """
        Gera prompt com few-shot learning.
        
        Args:
            question: Pergunta do usuário
            context_chunks: Lista de chunks de contexto
            examples: Lista de dicts com 'question' e 'answer'
        
        Returns:
            Prompt formatado com exemplos
        """
        # System instruction
        system = """Você é um assistente especializado em Imposto de Renda Pessoa Física (IRPF) brasileiro.

REGRAS IMPORTANTES:
1. Base suas respostas EXCLUSIVAMENTE nas informações do contexto fornecido
2. Se a informação não estiver no contexto, diga claramente "Não encontrei essa informação nos documentos consultados"
3. Cite os artigos, parágrafos ou seções relevantes quando aplicável
4. Use linguagem clara e acessível
5. Seja direto e objetivo

Veja os exemplos abaixo de como responder:"""
        
        # Construir exemplos
        examples_text = "\n\n---\n\n".join([
            f"Exemplo {i+1}:\nPergunta: {ex['question']}\nResposta: {ex['answer']}"
            for i, ex in enumerate(examples)
        ])
        
        # Construir contexto
        context = "\n\n".join([
            f"[Trecho {i+1}]\n{chunk}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        # Montar prompt final
        user_prompt = f"""{examples_text}

---

Agora responda à seguinte pergunta usando o contexto fornecido:

Contexto:
{context}

Pergunta: {question}

Resposta:"""
        
        return f"{system}\n\n{user_prompt}"
    
    def list_templates(self) -> List[Dict[str, str]]:
        """
        Lista todos os templates disponíveis.
        
        Returns:
            Lista de dicts com info dos templates
        """
        return [
            {
                'name': name,
                'description': template.description
            }
            for name, template in self.templates.items()
        ]


def create_prompt_manager() -> PromptManager:
    """
    Factory function para criar gerenciador de prompts.
    
    Returns:
        PromptManager configurado
    """
    return PromptManager()


# Exemplo de uso
if __name__ == "__main__":
    manager = create_prompt_manager()
    
    print("📋 Templates disponíveis:")
    for template_info in manager.list_templates():
        print(f"   • {template_info['name']}: {template_info['description']}")
    
    # Teste de detecção
    test_queries = [
        "Quais deduções posso fazer no IRPF?",
        "Como calcular o imposto devido?",
        "Qual o prazo para entregar a declaração?",
        "Como declarar rendimentos de aluguel?",
        "Posso incluir meu filho como dependente?"
    ]
    
    print("\n🔍 Detecção automática de template:")
    for query in test_queries:
        detected = manager.detect_query_type(query)
        print(f"\n   Query: {query}")
        print(f"   Template: {detected}")
    
    # Exemplo de formatação
    print("\n📝 Exemplo de prompt formatado:")
    query = "Quais deduções posso fazer?"
    context = "[Trecho 1]\nArt. 68. São permitidas deduções de despesas com educação e saúde."
    
    system, user_prompt = manager.format_prompt('deductions', query, context)
    print(f"\n   System instruction: {system[:100]}...")
    print(f"\n   User prompt: {user_prompt[:200]}...")
