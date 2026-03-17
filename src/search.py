"""RAG search chain for question answering over ingested PDF documents.

Retrieves relevant chunks from pgVector, injects them into the prompt
template, and sends to the configured LLM for a context-grounded answer.

Usage:
    python src/search.py "question" [pdf_path]

If no pdf_path is provided, defaults to 'document.pdf'.
"""

import os
import sys

# Ensure UTF-8 output on Windows for Rich unicode characters
if sys.platform == "win32":
    os.environ.setdefault("PYTHONUTF8", "1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_postgres import PGVector
from rich.panel import Panel

from ingest import (
    console,
    get_collection_name,
    get_embeddings,
    get_provider,
    test_db_connection,
    validate_env,
)

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.
- Responda em linguagem natural, de forma clara e amigável. Use números por extenso quando apropriado (ex: "10 milhões de reais" em vez de "R$ 10.000.000,00"). Note que o primeiro valor é dito em número em caso de valores "redondos", e os demais em texto: "O faturamento foi de 10 milhões de reais", com o "10" como número, e não como "dez".
- Use o tempo verbal passado ao relatar fatos do documento (ex: "O faturamento foi de..." em vez de "O faturamento é de...").

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

_ERROR_TITLE = "[red]Error[/red]"


def get_llm(provider: str):
    """Create the LLM chat model for the configured provider.

    Returns a LangChain chat model instance for the given provider.
    """
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        model = os.getenv("OPENAI_LLM_MODEL", "gpt-5-nano")
        return ChatOpenAI(model=model)
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = os.getenv("GOOGLE_LLM_MODEL", "gemini-2.5-flash-lite")
        return ChatGoogleGenerativeAI(model=model)
    elif provider == "lmstudio":
        from langchain_openai import ChatOpenAI

        base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        model = os.getenv("LMSTUDIO_LLM_MODEL", "llm-model")
        return ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key="lm-studio",
        )


def search_prompt(question=None, pdf_name=None):
    """Initialize the RAG search chain and optionally run a query.

    When called with a question, executes the search and prints the result.
    When called without a question, returns a RunnableLambda chain that
    chat.py can invoke via chain.invoke({"query": "..."}).

    Returns None on any initialization failure (never crashes).
    """
    try:
        load_dotenv()
        provider = get_provider()
        validate_env(provider)

        connection_string = os.environ["DATABASE_URL"]
        test_db_connection(connection_string)

        # Determine PDF path for collection name
        if pdf_name is not None:
            pdf_path = pdf_name
        elif len(sys.argv) > 2:
            pdf_path = sys.argv[2]
        else:
            pdf_path = "document.pdf"

        collection_name = get_collection_name(pdf_path)
        embeddings = get_embeddings(provider)
        llm = get_llm(provider)

        # Read-only vector store (no pre_delete_collection)
        vector_store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=connection_string,
            use_jsonb=True,
        )

        prompt = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=["contexto", "pergunta"],
        )

        def _run(inputs: dict) -> str:
            query = inputs["query"]
            results = vector_store.similarity_search_with_score(query, k=10)
            contexto = "\n\n".join(doc.page_content for doc, _score in results)
            formatted = prompt.format(contexto=contexto, pergunta=query)
            response = llm.invoke(formatted)
            return response.content

        chain = RunnableLambda(_run)

        if question is not None:
            result = chain.invoke({"query": question})
            console.print(result)
            return None

        return chain

    except (Exception, SystemExit) as exc:
        console.print(
            Panel(
                f"Failed to initialize search chain: {exc}",
                title=_ERROR_TITLE,
                border_style="red",
            )
        )
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print(
            Panel(
                "Usage: python src/search.py \"question\" [pdf_path]",
                title="Search",
                border_style="blue",
            )
        )
        sys.exit(1)

    question = sys.argv[1]
    search_prompt(question=question)
