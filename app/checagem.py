import pandas as pd
import duckdb
import glob
import os

# CONFIGURAÇÃO
CAMINHO_DADOS = "./data/dados_revisados"
CAMINHO_DB = "data/db/hackathon.duckdb"

print("🔍 INICIANDO AUDITORIA FORENSE DE DADOS\n")
con = duckdb.connect(CAMINHO_DB)

# ==============================================================================
# PROVA 1: COMPLETUDE (VOLUMETRIA)
# "O que entrou é igual ao que saiu?"
# ==============================================================================
print("--- 1. CHECAGEM DE VOLUMETRIA (EXCEL vs DUCKDB) ---")

arquivos = glob.glob(os.path.join(CAMINHO_DADOS, "*.xlsx"))
total_linhas_excel = 0

# Contagem real linha a linha nos arquivos originais
print("Contando linhas nos arquivos Excel originais (isso pode levar alguns segundos)...")
for arquivo in arquivos:
    try:
        xls = pd.ExcelFile(arquivo)
        for nome_aba in xls.sheet_names:
            # Ignora abas vazias ou de metadados se houver
            df = pd.read_excel(xls, sheet_name=nome_aba)
            # Somamos apenas abas que parecem ser de Fato (Avaliações)
            # Ajuste a lógica se necessário. Assumindo que abas com 'avalia' ou 'fato' são as respostas.
            # Se você quiser contar TUDO, remova o if.
            if 'avalia' in nome_aba.lower() or 'fato' in nome_aba.lower(): 
                 total_linhas_excel += len(df)
    except Exception as e:
        print(f"Erro ao ler {arquivo}: {e}")

total_linhas_banco = con.sql("SELECT COUNT(*) FROM fAvaliacao").fetchone()[0]

diff = total_linhas_excel - total_linhas_banco
match_symbol = "✅" if diff == 0 else "❌"

print(f"\nRESUMO VOLUMETRIA:")
print(f"Total Linhas Fato (Excel): {total_linhas_excel}")
print(f"Total Linhas Fato (Banco): {total_linhas_banco}")
print(f"Diferença: {diff} {match_symbol}")

if diff != 0:
    print("⚠️ ALERTA: Se a diferença for positiva, o ETL perdeu dados. Se for negativa, duplicou.")
    print("   (Nota: Se você filtrou duplicatas exatas no ETL, uma pequena perda é esperada e correta).")

# ==============================================================================
# PROVA 2: INTEGRIDADE REFERENCIAL (CAÇA AOS FANTASMAS)
# "Existem respostas apontando para Cursos/Disciplinas que não existem?"
# Isso é CRÍTICO. Se der erro aqui, seus dashboards vão mostrar números menores que a realidade.
# ==============================================================================
print("\n--- 2. CHECAGEM DE INTEGRIDADE (ORFÃOS) ---")

def checar_orfaos(tabela_fato, col_fk, tabela_dim, col_pk, nome_entidade):
    # Query: Seleciona linhas da fato onde o ID não é encontrado na dimensão
    query = f"""
        SELECT COUNT(*) 
        FROM {tabela_fato} f
        LEFT JOIN {tabela_dim} d ON f.{col_fk} = d.{col_pk}
        WHERE d.{col_pk} IS NULL 
          AND f.{col_fk} IS NOT NULL -- Ignora NULLs legítimos
    """
    qtd_orfaos = con.sql(query).fetchone()[0]
    
    status = "✅ Íntegro" if qtd_orfaos == 0 else f"❌ {qtd_orfaos} ORFÃOS DETECTADOS"
    print(f"Integridade {nome_entidade}: {status}")
    
    if qtd_orfaos > 0:
        print(f"   -> Ação: {qtd_orfaos} respostas apontam para um {col_fk} que NÃO EXISTE na tabela {tabela_dim}.")
        # Mostra exemplos
        exemplo = con.sql(f"""
            SELECT DISTINCT f.{col_fk} 
            FROM {tabela_fato} f
            LEFT JOIN {tabela_dim} d ON f.{col_fk} = d.{col_pk}
            WHERE d.{col_pk} IS NULL AND f.{col_fk} IS NOT NULL
            LIMIT 3
        """).df()
        print(f"   -> Exemplos de IDs fantasmas: {exemplo.values.flatten().tolist()}")

checar_orfaos('fAvaliacao', 'Cod_Curso', 'dCurso', 'Cod_Curso', 'Cursos')
checar_orfaos('fAvaliacao', 'Cod_Disciplina', 'dDisciplina', 'Cod_Disciplina', 'Disciplinas')
checar_orfaos('fAvaliacao', 'ID_Pergunta', 'dPergunta', 'ID_Pergunta', 'Perguntas')

# ==============================================================================
# PROVA 3: CONSISTÊNCIA DE DOMÍNIO (VALIDAÇÃO DE INSIGHTS)
# "As respostas de texto batem com a lógica do gráfico?"
# ==============================================================================
print("\n--- 3. CHECAGEM DE DOMÍNIO (TEXTO DAS RESPOSTAS) ---")

# Vamos ver o que NÃO está sendo capturado pelo seu CASE WHEN do gráfico anterior
query_validacao_texto = """
    SELECT 
        Resposta,
        COUNT(*) as Qtd,
        CASE 
            WHEN Resposta ILIKE '%Concordo Totalmente%' THEN 'Capturado (5)'
            WHEN Resposta ILIKE '%Concordo%' AND Resposta NOT ILIKE '%Totalmente%' THEN 'Capturado (4)'
            WHEN Resposta ILIKE '%Neutro%' THEN 'Capturado (3)'
            WHEN Resposta ILIKE '%Discordo%' AND Resposta NOT ILIKE '%Totalmente%' THEN 'Capturado (2)'
            WHEN Resposta ILIKE '%Discordo Totalmente%' THEN 'Capturado (1)'
            ELSE '⚠️ NÃO CAPTURADO (NULL)' 
        END as Status_Validacao
    FROM fAvaliacao
    WHERE Resposta IS NOT NULL
    GROUP BY Resposta, Status_Validacao
    ORDER BY Status_Validacao DESC, Qtd DESC
"""

df_validacao = con.sql(query_validacao_texto).df()
print("Auditoria das Respostas de Texto:")
print(df_validacao)

nao_capturados = df_validacao[df_validacao['Status_Validacao'].str.contains('NÃO CAPTURADO')]
if not nao_capturados.empty:
    print("\n🚨 PERIGO: Existem variações de texto que seu gráfico está ignorando!")
    print("Isso distorce a média. Adicione essas variações no CASE WHEN do seu código de gráfico.")
else:
    print("\n✅ Todas as variações de resposta conhecidas estão mapeadas.")

con.close()
print("\n🏁 AUDITORIA FINALIZADA.")