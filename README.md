# Ingestao e Busca Semantica com LangChain e Postgres

Sistema RAG (Retrieval-Augmented Generation) que ingere um PDF e responde perguntas baseadas exclusivamente no conteudo do documento.

## Pre-requisitos

- Python 3.10+
- Docker e Docker Compose

## Configuracao

1. Copie o arquivo de exemplo e preencha suas credenciais:

```bash
cp .env.example .env
```

2. Edite o `.env` conforme o provider escolhido (veja abaixo).

3. A variavel `DATABASE_URL` ja vem configurada para o Docker Compose:

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rag
```

### Usando OpenAI

1. Crie uma API Key em [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Configure o `.env`:

```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-sua-chave-aqui
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-5-nano
```

### Usando Gemini (Google)

1. Crie uma API Key em [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Configure o `.env`:

```
LLM_PROVIDER=gemini
GOOGLE_API_KEY=sua-chave-aqui
GOOGLE_EMBEDDING_MODEL=models/gemini-embedding-001
GOOGLE_LLM_MODEL=gemini-2.5-flash-lite
```

### Usando LMStudio (modelos locais)

Para rodar com um modelo local via [LMStudio](https://lmstudio.ai/):

1. Abra o LMStudio e baixe os modelos desejados (um para embeddings e um para chat/LLM)
2. Inicie o servidor local (aba "Local Server" no LMStudio)
3. Configure o `.env`:

```
LLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_EMBEDDING_MODEL=nome-do-modelo-de-embedding
LMSTUDIO_LLM_MODEL=nome-do-modelo-de-chat
```

Substitua `nome-do-modelo-de-embedding` e `nome-do-modelo-de-chat` pelos identificadores dos modelos carregados no LMStudio. Nao e necessario API key — o LMStudio roda localmente.

**Importante:** voce deve re-ingerir o PDF (`python src/ingest.py document.pdf`) ao trocar de provider, pois os embeddings sao diferentes entre modelos.

## Instalacao

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

## Execucao

### 1. Subir o banco de dados

```bash
docker compose up -d
```

### 2. Ingerir o PDF

```bash
python src/ingest.py document.pdf
```

### 3. Rodar o chat

```bash
python src/chat.py
```

Exemplo de uso:

```
Faca sua pergunta (ou digite 'sair' para encerrar):

PERGUNTA: Qual o faturamento da Empresa SuperTechIABrazil?
RESPOSTA: O faturamento foi de 10 milhoes de reais.

PERGUNTA: Qual a capital da Franca?
RESPOSTA: Nao tenho informacoes necessarias para responder sua pergunta.
```

## Estrutura do projeto

```
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── src/
│   ├── ingest.py         # Script de ingestao do PDF
│   ├── search.py         # Script de busca semantica
│   ├── chat.py           # CLI para interacao com usuario
├── document.pdf          # PDF para ingestao
└── README.md
```
