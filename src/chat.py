"""Interactive CLI chat over ingested PDF documents.

Usage:
    python src/chat.py
"""

from search import search_prompt


def main():
    chain = search_prompt()

    if not chain:
        print("Nao foi possivel iniciar o chat. Verifique os erros de inicializacao.")
        return

    print("Faca sua pergunta (ou digite 'sair' para encerrar):\n")

    while True:
        try:
            pergunta = input("PERGUNTA: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not pergunta:
            continue

        if pergunta.lower() in ("sair", "exit", "quit"):
            break

        resposta = chain.invoke({"query": pergunta})
        print(f"RESPOSTA: {resposta}\n")


if __name__ == "__main__":
    main()
