"""
Script para calcular índices financeiros a partir do balanço patrimonial
já limpo e no formato largo (data/processed/balanco_bancos_2021_2025.csv).
 
NOTA SOBRE ESCOPO: outros índices típicos do setor bancário (Índice de
Basileia, Índice de Eficiência, Depósitos/Empréstimos) foram avaliados e
descartados nesta versão:
  - Basileia: depende de dado regulatório (Patrimônio de Referência, RWA)
    não disponível no balanço patrimonial público.
  - Eficiência: depende de dados da DRE, fora do escopo atual do projeto
    (que usa apenas BPA/BPP).
  - Depósitos/Empréstimos: os códigos de subconta (CD_CONTA) abaixo do
    nível 2 (ex: 2.02.01.xx) não são padronizados entre os bancos -- cada
    instituição estrutura suas subcontas de forma diferente. Um índice
    calculado a partir desses códigos seria impreciso, por isso foi
    descartado em favor de manter apenas índices baseados em códigos
    verdadeiramente padronizados (nível 1 e 2).
 
Códigos de conta usados (padronizados, válidos para todas as empresas
do dataset):
  1        -> Ativo Total
  1.01     -> Ativo Circulante
  1.02     -> Ativo Não Circulante
  2        -> Passivo Total
  2.01     -> Passivo Circulante
  2.02     -> Passivo Não Circulante
  2.03     -> Patrimônio Líquido
 
(consulte data/processed/dicionario_contas.json para conferir
os códigos exatos presentes nos seus dados)
"""


import pandas as pd
from pathlib import Path
import numpy as np

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_PROCESSED = RAIZ_PROJETO / 'data' / 'processed'


def pl(df: pd.DataFrame) -> pd.Series:
    """
    Retorna o Patrimônio Líquido (PL) a partir do balanço patrimonial
    no formato largo (uma linha por empresa/ano).
    """
    return df['1'] - df['2.01'] - df['2.02']  # Ativo Total - Passivo Circulante - Passivo Não Circulante = Patrimônio Líquido

def liquidez_corrente(df: pd.DataFrame) -> pd.Series:
    """
        Liquidez Corrente = Ativo Circulante / Passivo Circulante
 
    ATENÇÃO CONTÁBIL: esse índice foi desenhado para empresas não
    financeiras (indústria, comércio). Para bancos, a classificação
    circulante/não circulante não reflete bem a liquidez real, já que
    a maior parte do balanço é composta por instrumentos financeiros.
    Mantido aqui por completude, mas deve ser interpretado com cautela
    para o setor bancário -- analistas do setor costumam preferir
    índices regulatórios específicos (ex: Índice de Basileia), que não
    são calculáveis a partir dos dados públicos do balanço.

    """
    liquidez = df['1.01'] / df['2.01']
    return liquidez.replace([np.inf, -np.inf], np.nan)

def endividamento(df: pd.DataFrame) -> pd.Series:
    """
    Endividamento Geral = Passivo Total / Ativo Total
 
    Mede que proporção dos ativos é financiada por capital de terceiros
    (dívida), em vez de capital próprio. Aplicável a qualquer setor,
    incluindo bancos.
    """
    return 1 - (df['patrimonio_liquido'] / df['1'])  # 1 - (PL / Ativo Total) = Passivo Total / Ativo Total


def participacao_capital_terceiros(df: pd.DataFrame) -> pd.Series:
    """
        Participação de Capital de Terceiros = Passivo Total / Patrimônio Líquido
 
    Compara quanto a empresa deve em relação ao que é capital próprio
    dos acionistas. Quanto maior, mais alavancada a empresa está.
    Para bancos, alavancagem alta é normal e esperada (é o próprio
    modelo de negócio: captar recursos de terceiros para emprestar),
    então esse índice deve ser comparado entre bancos, não contra o
    padrão de empresas não financeiras.

    """
    capital_terceiros = df['1'] - df['patrimonio_liquido']  # Passivo Total = Ativo Total - Patrimônio Líquido
    return capital_terceiros / df['patrimonio_liquido']


def composicao_endividamento(df: pd.DataFrame) -> pd.Series:
    """
        Composição do Endividamento = Passivo Circulante / Passivo Total
 
    Mede a proporção da dívida que é de curto prazo (circulante) em
    relação à dívida total. Quanto maior, mais a empresa depende de
    capital de terceiros de curto prazo, o que pode indicar maior risco
    de liquidez.
    """
    capital_terceiros = df['1'] - df['patrimonio_liquido']  # Passivo Total = Ativo Total - Patrimônio Líquido
    return df['2.01'] / capital_terceiros  # Passivo Circulante / Passivo Total (capital de terceiros)


def indice_imobilizacao_pl(df: pd.DataFrame) -> pd.Series:
    """
        Índice de Imobilização do Patrimônio Líquido = Ativo Não Circulante / Patrimônio Líquido
 
    Mede quanto do patrimônio líquido está investido em ativos de longo prazo
    (não circulantes). Quanto maior, mais a empresa depende de capital próprio
    para financiar ativos que não geram retorno imediato. Para bancos, esse índice
    deve ser interpretado com cautela, pois a maior parte do ativo é composta por
    instrumentos financeiros, e não por ativos fixos.
    """
    return df['1.02'] / df['patrimonio_liquido']  # Ativo Não Circulante / Patrimônio Líquido


def calcular_indices_financeiros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula os índices financeiros a partir do balanço patrimonial
    no formato largo (uma linha por empresa/ano).
    """
    df_com_indices = df.copy()
    
    df_com_indices['liquidez_corrente'] = liquidez_corrente(df)
    df_com_indices['endividamento_geral'] = endividamento(df)
    df_com_indices['participacao_capital_terceiros'] = participacao_capital_terceiros(df)
    df_com_indices['composicao_endividamento'] = composicao_endividamento(df)
    df_com_indices['indice_imobilizacao_pl'] = indice_imobilizacao_pl(df)

    return df_com_indices


def main():
    """
    Função principal: lê o balanço patrimonial já limpo e no formato largo,
    calcula os índices financeiros e salva o resultado em um novo arquivo CSV.
    """

    caminho_entrada = PASTA_PROCESSED / 'balanco_bancos_2021_2025.csv'
    df = pd.read_csv(caminho_entrada)

    print(f"Calculando índices financeiros para {len(df)} registros...")

    df_com_indices = calcular_indices_financeiros(df)

    destino = PASTA_PROCESSED / 'balanco_bancos_2021_2025_com_indices.csv'
    df_com_indices.to_csv(destino, index=False)

    print(f"Índices financeiros calculados e salvos em {destino}")
    print(f"Total de linhas com índices calculados: {len(df_com_indices)}")
    print(
        "Indicadores calculados: liquidez_corrente, endividamento_geral, " \
        "participacao_capital_terceiros, composicao_endividamento, indice_imobilizacao_pl"
    )


if __name__ == "__main__":
    main()
