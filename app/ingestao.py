# ingestao.py
import pandas as pd
import duckdb
import os

# ============================================================
# CONFIGURAÇÕES DO EXCEL
# ============================================================

ABAS_OBRIGATORIAS = [
    "dCurso",
    "dDisciplina",
    "dPergunta",
    "dTipoPergunta",
    "dUnidade",
    "fAvaliacao",
]

COLUNAS = {
    "dCurso": ["Cod_Curso", "Curso", "Setor_Curso"],
    "dDisciplina": ["Cod_Disciplina", "Nome_Disciplina", "Cod_Curso", "Departamento", "Cod_Prof", "Modalidade"],
    "dPergunta": ["ID_Pergunta", "Ordem", "TipoPergunta", "Pergunta"],
    "dTipoPergunta": ["TipoPergunta", "GrupoDePergunta"],
    "dUnidade": ["SiglaLotação", "UnidadeGestora", "Lotação"],
    "fAvaliacao": [
        "ID_Pesquisa",
        "ID_Pergunta",
        "Resposta",
        "Cod_Disciplina",
        "Cod_Curso",
        "TipoPergunta",
        "Pergunta",
        "SiglaLotação",
        "Ano",
    ],
}

def carregar_excel(path_excel: str) -> dict:
    """Lê o Excel em memória."""
    try:
        excel = pd.ExcelFile(path_excel)
        dfs = {sheet: pd.read_excel(excel, sheet) for sheet in excel.sheet_names}
        print(f"[INFO] Excel carregado. Abas: {list(dfs.keys())}")
        return dfs
    except Exception as e:
        raise Exception(f"Erro ao ler Excel: {e}")

def validar_abas(dfs):
    """Valida se todas as abas obrigatórias estão presentes."""
    faltando = [a for a in ABAS_OBRIGATORIAS if a not in dfs]
    if faltando:
        raise Exception(f"Abas faltando no Excel: {faltando}")
    print("[INFO] Todas as abas obrigatórias presentes.")

def validar_colunas(dfs):
    """Valida se todas as colunas necessárias estão presentes."""
    for aba, cols in COLUNAS.items():
        if aba not in dfs:
            continue
        colunas_faltando = set(cols) - set(dfs[aba].columns)
        if colunas_faltando:
            raise Exception(f"Colunas faltantes em {aba}: {colunas_faltando}")
    print("[INFO] Todas as colunas necessárias presentes.")


def inserir_dados_diretamente(con, dfs, evitar_duplicatas=False):
    """Insere dados diretamente no banco principal."""
    total_registros = 0
    
    for tabela, df in dfs.items():
        if tabela not in COLUNAS:
            continue
            
        print(f"[INFO] Processando tabela: {tabela}")
        
        # Seleciona apenas as colunas definidas
        colunas_validas = [col for col in COLUNAS[tabela] if col in df.columns]
        df = df[colunas_validas]
        
        # Remove linhas completamente vazias
        df = df.dropna(how='all')
        
        if df.empty:
            print(f"[INFO] Tabela {tabela} vazia após limpeza. Pulando.")
            continue
        
        # Se evitar_duplicatas estiver ativado, remove duplicatas baseadas em todas as colunas
        if evitar_duplicatas:
            df = df.drop_duplicates()
            print(f"[INFO] Removidas duplicatas da tabela {tabela}")
        
        # Insere os dados
        con.register("df_temp", df)
        con.execute(f"INSERT INTO {tabela} SELECT * FROM df_temp")
        
        registros_inseridos = len(df)
        total_registros += registros_inseridos
        print(f"[INFO] {registros_inseridos} registros inseridos na tabela {tabela}")
    
    return total_registros

def processar_excel(path_excel: str, path_banco_principal: str, evitar_duplicatas=True):
    """Processa arquivo Excel e insere diretamente no banco principal."""
    try:
        print(f"[INFO] Iniciando processamento do Excel: {path_excel}")
        print(f"[INFO] Banco principal: {path_banco_principal}")
        
        # 1. Carregar Excel
        dfs = carregar_excel(path_excel)
        
        # 2. Validar estrutura
        validar_abas(dfs)
        validar_colunas(dfs)
        
        # 3. Conectar ao banco principal
        con = duckdb.connect(path_banco_principal)
        

        
        # 5. Inserir dados diretamente
        total_registros = inserir_dados_diretamente(con, dfs, evitar_duplicatas)
        
        con.close()
        
        print(f"[SUCESSO] {total_registros} registros inseridos no banco principal.")
        return total_registros
        
    except Exception as e:
        print(f"[ERRO] Falha ao processar Excel: {e}")
        raise Exception(f"Erro ao processar Excel: {e}")