"""
Script de limpeza: filtra os dados de balanço patrimonial (BPA e BPP)
da CVM, mantendo apenas empresas dos setores Bancos e Intermediação
Financeira, consolida os anos de 2021 a 2025, e transforma o resultado
para o formato largo (uma linha por empresa/ano).
"""

import zipfile
import pandas as pd
from pathlib import Path
import json

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

PASTA_RAW = RAIZ_PROJETO / 'data' / 'raw'

PASTA_PROCESSED = RAIZ_PROJETO / 'data' / 'processed'

ANOS = list(range(2021, 2026))  # Anos de 2021 a 2025

def carregar_cnpjs_bancos_e_intermediacao() -> list:
    """
    Lê o cadastro de companhias abertas e retorna uma lista
    com o CNPJ de empresas dos setores Bancos e Intermediação Financeira.
    """

    caminho_cadastro = PASTA_RAW / 'cad_cia_aberta.csv'

    df_cadastro = pd.read_csv(caminho_cadastro, sep=';', encoding='latin1')

    setores = ['Bancos', 'Intermediação Financeira']

    filtro_setores = df_cadastro['SETOR_ATIV'].isin(setores)

    empresas_filtradas = df_cadastro[filtro_setores]

    return empresas_filtradas['CNPJ_CIA'].tolist()


def ler_balanco_do_zip(ano: int, tipo: str, cnpjs_filtrados: list) -> pd.DataFrame:
    """
    Lê o arquivo de balanço patrimonial (BPA ou BPP) do ano especificado
    e filtra apenas as empresas cujo CNPJ está na lista de cnpjs_filtrados.
    """

    caminho_zip = PASTA_RAW / f'dfp_cia_aberta_{ano}.zip'

    nome_csv = f'dfp_cia_aberta_{tipo}_con_{ano}.csv'

    with zipfile.ZipFile(caminho_zip) as zip_aberto:
        with zip_aberto.open(nome_csv) as arquivo_csv:
            df = pd.read_csv(arquivo_csv, sep=';', encoding='latin1')

    filtro = df['CNPJ_CIA'].isin(cnpjs_filtrados)

    df_filtrado = df[filtro]

    return df_filtrado


def criar_dicionario_contas(df: pd.DataFrame) -> dict:
    """
    Cria um dicionário mapeando CD_CONTA -> DS_CONTA (código -> nome legível),
    pra sabermos o significado de cada coluna depois do pivot.

    Ex: {"1.01": "Ativo Circulante", "2.01": "Passivo Circulante", ...}
    """

    pares_unicos = df[['CD_CONTA', 'DS_CONTA']].drop_duplicates()
    return dict(zip(pares_unicos['CD_CONTA'], pares_unicos['DS_CONTA']))


def pivotar_balanco(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma os dados do formato longo (uma linha por conta contábil)
    para o formato largo (uma linha por empresa/ano, contas viram colunas).
    """

    df_pivotado = df.pivot_table(
        index = ['CNPJ_CIA', 'DENOM_CIA', 'DT_FIM_EXERC'],
        columns = 'CD_CONTA',
        values = 'VL_CONTA'
    )

    df_pivotado.reset_index(inplace=True)

    return df_pivotado

def main() -> None:
    """
    Função principal que realiza a limpeza e consolidação dos dados.
    """

    PASTA_PROCESSED.mkdir(parents=True, exist_ok=True)

    cnpjs_bancos_intermediacao = carregar_cnpjs_bancos_e_intermediacao()

    print(f'Encontrados {len(cnpjs_bancos_intermediacao)} CNPJs de empresas dos setores Bancos e Intermediação Financeira.')

    todos_os_dfs = []

    for ano in ANOS:
        print(f'Processando ano {ano}...')

        df_bpa = ler_balanco_do_zip(ano, 'BPA', cnpjs_bancos_intermediacao)
        df_bpp = ler_balanco_do_zip(ano, 'BPP', cnpjs_bancos_intermediacao)

        todos_os_dfs.append(df_bpa)
        todos_os_dfs.append(df_bpp)


    balanco_consolidado = pd.concat(todos_os_dfs, ignore_index=True)

    dicionario_contas = criar_dicionario_contas(balanco_consolidado)
    caminho_dicionario = PASTA_PROCESSED / 'dicionario_contas.json'
    with open(caminho_dicionario, 'w', encoding='utf-8') as arquivo:
        json.dump(dicionario_contas, arquivo, ensure_ascii=False, indent=2)
    print(f'Dicionário de contas salvo em {caminho_dicionario}')


    print(f'\nTotal de linhas antes do pivot: {len(balanco_consolidado)}')
    print(f'Total de colunas antes do pivot: {len(balanco_consolidado.columns)}')
    print(f'Pivotando os dados para o formato largo (uma linha por empresa/ano)...')
    balanco_consolidado = pivotar_balanco(balanco_consolidado)

    destino = PASTA_PROCESSED / 'balanco_bancos_2021_2025.csv'

    balanco_consolidado.to_csv(destino, sep=',', index=False, encoding='utf-8')

    print(f'\nArquivo salvo em {destino}')
    print(f'Total de linhas: {len(balanco_consolidado)}')


if __name__ == "__main__":
    main()