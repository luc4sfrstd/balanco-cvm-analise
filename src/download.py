"""
Script para baixar os dados de DFP (Demonstrações Financeiras Padronizadas)
diretamente do Portal de Dados Abertos da CVM.

Rodar o script dessa forma:
    python src/download.py

Fonte: https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp
"""

import requests
from pathlib import Path

URL_BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/"

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

PASTA_DESTINO = RAIZ_PROJETO / 'data' / 'raw'

ANOS = list(range(2021,2026)) # Anos de 2021 a 2025

def baixar_arquivo(ano: int) -> None:
    """
    Baixa o arquivo do ano especificado e salva na pasta de destino.
    """
    
    nome_arquivo = f"dfp_cia_aberta_{ano}.zip"

    url = URL_BASE + nome_arquivo

    destino = PASTA_DESTINO / nome_arquivo

    print(f"Baixando {nome_arquivo}...")

    resposta = requests.get(url, timeout=30)

    if resposta.status_code == 200:
        with open(destino, 'wb') as arquivo:
            arquivo.write(resposta.content)

        print(f'  -> Salvo em {destino}')
    
    else:
        print(f'  -> Falha ao baixar {nome_arquivo}. Status code: {resposta.status_code}')



def main() -> None:
    """
    Função principal para baixar os arquivos de DFP para os anos especificados.
    """
    PASTA_DESTINO.mkdir(parents=True, exist_ok=True)

    for ano in ANOS:
        baixar_arquivo(ano)

    print("\nDownload concluído.")


if __name__ == "__main__":
    main()