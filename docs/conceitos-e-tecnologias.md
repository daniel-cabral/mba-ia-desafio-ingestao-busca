# Conceitos e Tecnologias - Ingestao e Busca Semantica

Guia educacional sobre os conceitos, tecnologias e decisoes arquiteturais deste projeto.

---

## 1. O que e RAG (Retrieval-Augmented Generation)?

RAG e uma tecnica que **combina busca de informacao com geracao de texto por IA**. Em vez de confiar apenas no conhecimento interno de um LLM (que pode ser desatualizado ou inventar coisas), voce:

1. **Recupera** trechos relevantes de uma base de dados
2. **Injeta** esses trechos no prompt como contexto
3. **Gera** a resposta baseada apenas nesse contexto

### Por que usar RAG?

LLMs como GPT ou Gemini foram treinados com dados ate uma data de corte. Eles nao conhecem seus documentos internos. RAG resolve isso:

- **Sem RAG:** "Qual o faturamento da SuperTech?" -> LLM inventa ou diz que nao sabe
- **Com RAG:** "Qual o faturamento da SuperTech?" -> Busca no PDF -> Encontra o trecho -> LLM responde com base no trecho

### Analogia

Imagine um funcionario novo na empresa. Sem RAG, voce pergunta algo e ele **chuta**. Com RAG, ele primeiro **consulta os documentos da empresa** e depois responde com base no que encontrou.

---

## 2. Arquitetura do Projeto

O projeto tem dois fluxos principais que acontecem em momentos diferentes:

```
FLUXO 1 - INGESTAO (roda uma vez por documento)
================================================

  document.pdf
       |
       v
  [PyPDFLoader]          Leitura do PDF, pagina por pagina
       |
       v
  [RecursiveCharacterTextSplitter]   Divide em chunks de 1000 chars
       |
       v
  [Embedding Model]      Transforma cada chunk em vetor numerico
       |
       v
  [pgVector/PostgreSQL]  Armazena vetores no banco de dados


FLUXO 2 - BUSCA (roda a cada pergunta do usuario)
==================================================

  "Qual o faturamento?"
       |
       v
  [Embedding Model]      Mesma modelo! Transforma pergunta em vetor
       |
       v
  [pgVector]             similarity_search: encontra os 10 chunks
       |                 mais parecidos com a pergunta
       v
  [Prompt Template]      Monta o prompt com contexto + regras + pergunta
       |
       v
  [LLM (Gemini/GPT)]    Gera resposta baseada no contexto
       |
       v
  "O faturamento foi de 10 milhoes de reais."
```

### Ponto-chave

O modelo de embedding usado na ingestao **deve ser o mesmo** usado na busca. Se voce ingerir com `gemini-embedding-001` e buscar com `text-embedding-3-small`, os vetores estarao em "espacos" diferentes e a busca nao vai funcionar.

---

## 3. Embeddings - O Coracao da Busca Semantica

### O que sao embeddings?

Embeddings sao **representacoes numericas de texto** em forma de vetor (lista de numeros). Cada texto vira um ponto num espaco multidimensional onde **textos com significados parecidos ficam proximos**.

```
Texto: "faturamento da empresa"  ->  [0.12, -0.45, 0.78, ..., 0.33]  (768 dimensoes)
Texto: "receita corporativa"     ->  [0.11, -0.44, 0.77, ..., 0.34]  (proximo!)
Texto: "cor do ceu"              ->  [0.89, 0.23, -0.56, ..., -0.12] (distante!)
```

### Como funciona a busca?

1. A pergunta do usuario vira um vetor
2. O banco compara esse vetor com todos os vetores armazenados
3. Retorna os mais proximos (menor distancia = maior similaridade)

Isso e **busca semantica** — diferente de busca por palavras-chave, entende o *significado*:
- Busca por palavra: "faturamento" so acha textos com a palavra "faturamento"
- Busca semantica: "faturamento" tambem acha "receita", "ganhos", "rendimento"

### Modelos usados no projeto

| Provider | Modelo | Dimensoes |
|----------|--------|-----------|
| Google | `gemini-embedding-001` | 768 |
| OpenAI | `text-embedding-3-small` | 1536 |

No nosso `.env`, estamos usando Gemini: `GOOGLE_EMBEDDING_MODEL='models/gemini-embedding-001'`.

---

## 4. pgVector - Banco de Dados Vetorial

### Por que nao um banco normal?

Um banco SQL tradicional e otimizado para buscar por valores exatos (`WHERE nome = 'X'`). Mas vetores de 768 dimensoes precisam de **busca por similaridade** — encontrar os vetores mais proximos de um dado vetor de referencia.

### O que e pgVector?

pgVector e uma **extensao do PostgreSQL** que adiciona:
- Um tipo de dado `vector` para armazenar embeddings
- Operadores de distancia (cosseno, L2, produto interno)
- Indices otimizados para busca aproximada (HNSW, IVFFlat)

### Como o Docker Compose configura isso

```yaml
# Imagem oficial do pgVector (PostgreSQL 17 + extensao)
postgres:
  image: pgvector/pgvector:pg17

# Servico que ativa a extensao no banco
bootstrap_vector_ext:
  command: psql ... -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

O `bootstrap_vector_ext` roda uma unica vez apos o banco ficar saudavel (healthcheck) e cria a extensao `vector`. Sem isso, o PostgreSQL nao saberia o que fazer com dados vetoriais.

### Como o LangChain usa o pgVector

O LangChain abstrai toda a complexidade via a classe `PGVector`:

```python
# Na ingestao - cria a collection e armazena
vector_store = PGVector(
    embeddings=embeddings,
    collection_name="document_pdf",
    connection=connection_string,
    pre_delete_collection=True,  # limpa dados anteriores
)
vector_store.add_documents(chunks)

# Na busca - consulta por similaridade
results = vector_store.similarity_search_with_score(query, k=10)
```

Por baixo, o LangChain:
1. Cria tabelas `langchain_pg_collection` e `langchain_pg_embedding`
2. Na ingestao: gera o embedding de cada chunk e insere como `INSERT INTO ... vector`
3. Na busca: gera o embedding da pergunta e faz `ORDER BY embedding <=> query_vector LIMIT 10`

O operador `<=>` e a **distancia cosseno** — quanto menor, mais parecidos sao os textos.

---

## 5. Chunking - Por que Dividir o PDF?

### O problema

LLMs tem limite de contexto (tokens). Mesmo que o modelo aceite 100k tokens, enviar o PDF inteiro:
- Desperdicaria tokens com partes irrelevantes
- Diluiria a informacao relevante
- Custaria mais (APIs cobram por token)

### A solucao: chunks

Dividimos o PDF em pedacos menores (chunks) para que a busca retorne apenas os trechos relevantes.

### Parametros usados

```python
RecursiveCharacterTextSplitter(
    chunk_size=1000,     # cada pedaco tem ate 1000 caracteres
    chunk_overlap=150,   # 150 caracteres de sobreposicao entre pedacos
)
```

### Por que overlap?

Sem overlap, uma frase poderia ser cortada ao meio entre dois chunks:

```
Chunk 1: "...o faturamento da empresa foi de"
Chunk 2: "10 milhoes de reais no ano de 2023..."
```

Com overlap de 150, o final do chunk 1 se repete no inicio do chunk 2, preservando o contexto:

```
Chunk 1: "...o faturamento da empresa foi de 10 milhoes de reais no"
Chunk 2: "de 10 milhoes de reais no ano de 2023..."
```

### Por que "Recursive"?

O `RecursiveCharacterTextSplitter` tenta dividir de forma inteligente, nesta ordem de prioridade:
1. Por paragrafos (`\n\n`)
2. Por quebras de linha (`\n`)
3. Por espacos (` `)
4. Por caractere (ultimo recurso)

Isso tenta manter sentencas e paragrafos inteiros sempre que possivel.

---

## 6. LangChain - O Framework de Orquestracao

### O que e?

LangChain e um framework Python que **conecta componentes de IA** de forma padronizada. Em vez de voce chamar cada API manualmente, ele fornece abstracoes:

| Componente | O que faz | Classe no projeto |
|------------|-----------|-------------------|
| Document Loader | Carrega documentos | `PyPDFLoader` |
| Text Splitter | Divide em chunks | `RecursiveCharacterTextSplitter` |
| Embeddings | Gera vetores | `GoogleGenerativeAIEmbeddings` |
| Vector Store | Armazena/busca vetores | `PGVector` |
| Chat Model | Gera texto | `ChatGoogleGenerativeAI` |
| Prompt Template | Formata prompts | `PromptTemplate` |
| Runnable | Compoe pipelines | `RunnableLambda` |

### LCEL (LangChain Expression Language)

LangChain tem um sistema de composicao chamado LCEL. No nosso projeto, usamos `RunnableLambda` para criar uma chain customizada:

```python
chain = RunnableLambda(_run)
result = chain.invoke({"query": "Qual o faturamento?"})
```

`RunnableLambda` transforma qualquer funcao Python numa "chain" que pode ser invocada com `.invoke()`. Isso e util porque `chat.py` espera um objeto com esse metodo.

### Por que nao usamos RetrievalQA?

O LangChain tinha uma classe pronta chamada `RetrievalQA` que fazia tudo automaticamente. Mas:

1. **Foi descontinuada** (deprecated desde LangChain 0.1.17)
2. **Espera variaveis em ingles** (`{context}`, `{input}`), mas nosso template usa `{contexto}` e `{pergunta}`

A solucao foi construir a chain manualmente — o que tambem e mais educativo, pois cada passo fica explicito.

---

## 7. Prompt Engineering - O Template

O prompt e a "instrucao" que enviamos ao LLM junto com o contexto. Nosso template:

```
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informacao nao estiver explicitamente no CONTEXTO, responda:
  "Nao tenho informacoes necessarias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- ...

PERGUNTA DO USUARIO:
{pergunta}
```

### Por que tantas regras?

LLMs tem tendencia a **alucinar** — inventar informacoes que parecem plausíveis mas nao existem nos dados. As regras:

- **"Responda somente com base no CONTEXTO"** — forca o modelo a usar apenas os chunks recuperados
- **"Se nao estiver explicitamente..."** — define o comportamento para perguntas fora do escopo
- **"Nunca invente..."** — reforco contra alucinacao
- **Exemplos de perguntas fora do contexto** — few-shot learning: mostrar exemplos ajuda o modelo a entender o padrao esperado

### Engenharia de prompt na pratica

Ajustamos o prompt com regras adicionais para melhorar a qualidade das respostas:
- **Linguagem natural** — "10 milhoes de reais" em vez de "R$ 10.000.000,00"
- **Tempo verbal passado** — "O faturamento foi de..." em vez de "O faturamento e de..."

Esses ajustes mostram que prompt engineering e um processo **iterativo**: voce testa, analisa a resposta, e refina as instrucoes.

---

## 8. Provider Pattern - Suporte a Multiplos LLMs

O projeto suporta tres provedores: OpenAI, Gemini e LMStudio. Isso e feito com um padrao de **factory function**:

```python
def get_embeddings(provider: str):
    if provider == "openai":
        return OpenAIEmbeddings(model=...)
    elif provider == "gemini":
        return GoogleGenerativeAIEmbeddings(model=...)
    elif provider == "lmstudio":
        return OpenAIEmbeddings(base_url=..., api_key="lm-studio")
```

### Por que LMStudio usa OpenAIEmbeddings?

LMStudio expoe uma API **compativel com OpenAI**. Entao basta usar as classes da OpenAI apontando para `http://localhost:1234/v1`. Isso e um padrao comum — muitas ferramentas locais (Ollama, LMStudio, vLLM) implementam a API da OpenAI como padrao de interoperabilidade.

### Configuracao por variaveis de ambiente

Tudo e configuravel via `.env`:

```
LLM_PROVIDER=gemini              # Qual provedor usar
GOOGLE_EMBEDDING_MODEL=...       # Modelo de embedding
GOOGLE_LLM_MODEL=...             # Modelo de chat/geracao
```

Isso permite trocar de provedor sem alterar codigo — apenas muda a variavel.

---

## 9. Fluxo de Dados Completo (Passo a Passo)

### Ingestao (`python src/ingest.py document.pdf`)

| Passo | O que acontece | Codigo |
|-------|---------------|--------|
| 1 | Carrega `.env` | `load_dotenv()` |
| 2 | Valida provider e API keys | `validate_env(provider)` |
| 3 | Testa conexao com PostgreSQL (3 tentativas) | `test_db_connection()` |
| 4 | Le o PDF pagina por pagina | `PyPDFLoader(pdf_path).load()` |
| 5 | Divide em chunks de 1000 chars (overlap 150) | `splitter.split_documents(documents)` |
| 6 | Gera embedding de cada chunk e armazena | `vector_store.add_documents(chunks)` |

### Busca (`python src/search.py "pergunta"`)

| Passo | O que acontece | Codigo |
|-------|---------------|--------|
| 1 | Inicializa (env, provider, DB, vector store) | Mesmo fluxo da ingestao |
| 2 | Recebe pergunta do usuario | `inputs["query"]` |
| 3 | Busca os 10 chunks mais similares | `similarity_search_with_score(query, k=10)` |
| 4 | Concatena chunks com `\n\n` | `"\n\n".join(...)` |
| 5 | Monta o prompt (contexto + regras + pergunta) | `prompt.format(contexto=..., pergunta=...)` |
| 6 | Envia ao LLM | `llm.invoke(formatted)` |
| 7 | Retorna `.content` da resposta | `response.content` |

---

## 10. Conceitos-Chave para Lembrar

| Conceito | Resumo de uma frase |
|----------|---------------------|
| **RAG** | Buscar informacao relevante antes de gerar resposta |
| **Embedding** | Representacao numerica de texto que captura significado |
| **Busca semantica** | Encontrar textos pelo significado, nao por palavras exatas |
| **Chunking** | Dividir documentos grandes em pedacos gerenciaveis |
| **Overlap** | Sobreposicao entre chunks para nao perder contexto nas bordas |
| **pgVector** | Extensao do PostgreSQL para armazenar e buscar vetores |
| **Distancia cosseno** | Metrica de similaridade entre vetores (0 = identico, 1 = oposto) |
| **Prompt template** | Instrucao estruturada com variaveis para guiar o LLM |
| **Alucinacao** | Quando o LLM inventa informacao que parece verdadeira |
| **LCEL** | Sistema de composicao de pipelines do LangChain |
| **Factory pattern** | Funcao que cria objetos diferentes com base em parametros |

---

## 11. Estrutura do Projeto

```
mba-ia-desafio-ingestao-busca/
|-- docker-compose.yml     # PostgreSQL + pgVector em container
|-- requirements.txt       # Dependencias Python
|-- .env                   # Configuracao (provider, API keys, DB)
|-- document.pdf           # PDF para ingestao
|-- src/
|   |-- ingest.py          # Pipeline de ingestao (PDF -> chunks -> vetores -> DB)
|   |-- search.py          # Pipeline de busca (pergunta -> vetores -> LLM -> resposta)
|   |-- chat.py            # Interface CLI para interacao com usuario
|-- docs/
    |-- instrucoes.md      # Requisitos do desafio
    |-- conceitos-e-tecnologias.md   # Este documento
```

### Responsabilidades

- **ingest.py** — Faz o trabalho pesado uma vez: le o PDF, divide, gera embeddings, armazena. Tambem exporta funcoes utilitarias (`get_provider`, `get_embeddings`, etc.) que `search.py` reutiliza.
- **search.py** — Monta a chain de busca e resposta. Pode ser usado standalone (`python src/search.py "pergunta"`) ou como modulo (importado por `chat.py`).
- **chat.py** — Interface do usuario. Importa `search_prompt()` de `search.py` e usa a chain retornada para responder perguntas interativamente.

---

## 12. Ordem de Execucao

```bash
# 1. Subir o banco de dados
docker compose up -d

# 2. Ingerir o PDF (roda uma vez)
python src/ingest.py document.pdf

# 3. Fazer perguntas
python src/search.py "Qual o faturamento da empresa?"

# Ou usar o chat interativo
python src/chat.py
```
