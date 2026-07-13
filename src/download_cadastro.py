"""
Script para baixar o cadastro de companhias abertas da CVM.

Esse arquivo contém dados cadastrais de cada empresa, incluindo
o setor de atividade (SETOR_ATIV) -- é o que vamos usar pra filtrar
só as empresas do setor bancário.

Fonte: https://dados.cvm.gov.br/dataset/cia_aberta-cad
"""

import requests
from pathlib import Path

URL_CADASTRO = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

DESTINO = RAIZ_PROJETO / "data" / "raw" / "cad_cia_aberta.csv"

def baixar_cadastro() -> None:
    """
    Baixa o arquivo de cadastro de companhias abertas e salva na pasta de destino.
    """
    DESTINO.parent.mkdir(parents=True, exist_ok=True)

    print(f"Baixando cadastro de companhias abertas...")

    resposta = requests.get(URL_CADASTRO, timeout=30)

    if resposta.status_code == 200:
        with open(DESTINO, 'wb') as arquivo:
            arquivo.write(resposta.content)

        print(f'  -> Salvo em {DESTINO}')

    else:
        print(f'  -> Falha ao baixar cadastro. Status code: {resposta.status_code}')

if __name__ == "__main__":
    baixar_cadastro()
    print("\nDownload concluído.")
    