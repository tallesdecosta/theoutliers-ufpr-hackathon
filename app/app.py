import pandas as pd
import duckdb
import glob
import os

# ==============================================================================
# 1. CONFIGURAÇÃO
# ==============================================================================
CAMINHO_DADOS = "./data/dados_revisados"
CAMINHO_DB = "data/db/hackathon.duckdb"

# Garante pastas
pasta_db = os.path.dirname(CAMINHO_DB)
if not os.path.exists(pasta_db):
    os.makedirs(pasta_db)

print(f"Conectando ao banco: {CAMINHO_DB}")
con = duckdb.connect(CAMINHO_DB)

# ==============================================================================
# 2. MAPA DE TRADUÇÃO (PADRONIZAÇÃO)
# ==============================================================================
# Garante que independente de como está no Excel, no banco fica padrão
DE_PARA_COLUNAS = {
    # Pergunta e Tipo
    'IdPergunta': 'ID_Pergunta', 'IDPergunta': 'ID_Pergunta',
    'Tipo': 'TipoPergunta', 'TipoDePergunta': 'TipoPergunta',
    'Grupo': 'GrupoDePergunta', 'GrupoPergunta': 'GrupoDePergunta',
    'Questao': 'Pergunta', 'Enunciado': 'Pergunta',
    'Ordem': 'Ordem',
    
    # Unidade
    'SiglaLotacao': 'SiglaLotação',
    'UnidadeGestora': 'UnidadeGestora', 'Unidade': 'UnidadeGestora',
    'Lotacao': 'Lotação',
    
    # Curso / Disciplina
    'CodCurso': 'Cod_Curso',
    'SetorCurso': 'Setor_Curso',
    'CodDisciplina': 'Cod_Disciplina',
    'NomeDisciplina': 'Nome_Disciplina',
    'CodProf': 'Cod_Prof',
    
    # Fato
    'IdPesquisa': 'ID_Pesquisa',
    'Ano': 'Ano'
}

# ==============================================================================
# 3. FUNÇÃO DE INGESTÃO INTELIGENTE
# ==============================================================================
def ingerir_para_tabela(df, nome_tabela_destino):
    """Joga o DataFrame para dentro de uma tabela de staging no DuckDB"""
    
    # 1. Padroniza colunas
    df.columns = df.columns.str.strip()
    df.rename(columns=DE_PARA_COLUNAS, inplace=True)
    
    # 2. Registra temporariamente
    con.register('temp_view', df)
    
    # 3. Verifica se tabela existe. Se não, cria. Se sim, insere.
    try:
        # Tenta inserir
        con.sql(f"INSERT INTO {nome_tabela_destino} BY NAME SELECT * FROM temp_view")
    except:
        # Se deu erro (provavelmente tabela não existe), cria ela
        try:
            con.sql(f"CREATE TABLE {nome_tabela_destino} AS SELECT * FROM temp_view")
        except Exception as e:
            # Se deu erro na criação (ex: coluna nova), faz o ALTER TABLE
            cols_banco = [c[0] for c in con.sql(f"DESCRIBE {nome_tabela_destino}").fetchall()]
            cols_df = df.columns.tolist()
            novas = [c for c in cols_df if c not in cols_banco]
            
            for nova in novas:
                print(f"   -> Expandindo {nome_tabela_destino} com: {nova}")
                con.sql(f'ALTER TABLE {nome_tabela_destino} ADD COLUMN "{nova}" VARCHAR')
            
            con.sql(f"INSERT INTO {nome_tabela_destino} BY NAME SELECT * FROM temp_view")

# ==============================================================================
# 4. PROCESSAMENTO DOS ARQUIVOS (ROTEADOR DE ABAS)
# ==============================================================================
print("--- Iniciando processamento por ABAS ---")

# Limpa tabelas de staging antigas para começar do zero
tabelas_stg = ['stg_dUnidade', 'stg_dPergunta', 'stg_dTipoPergunta', 'stg_dCurso', 'stg_dDisciplina', 'stg_fAvaliacao']
for t in tabelas_stg:
    con.sql(f"DROP TABLE IF EXISTS {t}")

arquivos = glob.glob(os.path.join(CAMINHO_DADOS, "*.xlsx"))

for i, arquivo in enumerate(arquivos):
    nome_arquivo = os.path.basename(arquivo)
    print(f"[{i+1}/{len(arquivos)}] Lendo: {nome_arquivo}")
    
    try:
        abas = pd.read_excel(arquivo, sheet_name=None)
    except Exception as e:
        print(f"ERRO: {e}")
        continue
        
    for nome_aba, df in abas.items():
        # Lógica de Roteamento baseada no nome da Aba
        aba_lower = nome_aba.lower()
        
        # Ignora abas vazias
        if df.empty: continue

        if 'unidade' in aba_lower:
            ingerir_para_tabela(df, 'stg_dUnidade')
            
        elif 'tipo' in aba_lower and 'pergunta' in aba_lower:
            ingerir_para_tabela(df, 'stg_dTipoPergunta')
            
        elif 'pergunta' in aba_lower: # Pega dPergunta ou dPerguntas
            ingerir_para_tabela(df, 'stg_dPergunta')
            
        elif 'curso' in aba_lower and 'av' not in aba_lower: # Evita pegar nome do arquivo se tiver na aba
            ingerir_para_tabela(df, 'stg_dCurso')
            
        elif 'disciplina' in aba_lower:
            ingerir_para_tabela(df, 'stg_dDisciplina')
            
        elif 'avalia' in aba_lower or 'fato' in aba_lower:
            ingerir_para_tabela(df, 'stg_fAvaliacao')
            
        else:
            print(f"   Aviso: Aba '{nome_aba}' não mapeada. Ignorada.")

# ==============================================================================
# 5. CRIAÇÃO FINAL (LIMPEZA DE DUPLICATAS)
# ==============================================================================
print("\n--- Consolidando tabelas finais (3NF) ---")

def criar_final(nome_stg, nome_final):
    # Verifica se a tabela de staging foi criada (se tinha dados nos excels)
    try:
        con.sql(f"SELECT 1 FROM {nome_stg} LIMIT 1")
    except:
        print(f"Pulei {nome_final} (sem dados na origem).")
        return

    print(f"Criando {nome_final}...")
    con.sql(f"CREATE OR REPLACE TABLE {nome_final} AS SELECT DISTINCT * FROM {nome_stg}")

# Cria as tabelas finais removendo duplicatas
criar_final('stg_dUnidade', 'dUnidade')
criar_final('stg_dTipoPergunta', 'dTipoPergunta')
criar_final('stg_dPergunta', 'dPergunta')
criar_final('stg_dCurso', 'dCurso')
criar_final('stg_dDisciplina', 'dDisciplina')
criar_final('stg_fAvaliacao', 'fAvaliacao')

# ==============================================================================
# 6. RESUMO
# ==============================================================================
print("\n--- RESUMO DO BANCO ---")
try:
    con.sql("SHOW TABLES").show()
    # Mostra contagem
    for t in ['dUnidade', 'dPergunta', 'dTipoPergunta', 'fAvaliacao']:
        try:
            count = con.sql(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"{t}: {count} linhas")
        except: pass
except:
    pass

con.close()