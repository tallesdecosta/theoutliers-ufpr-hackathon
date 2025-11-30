import duckdb
import os
import pandas as pd

# Caminho para o banco de dados
base_dir = os.path.dirname(os.path.abspath(__file__))

if os.path.exists(os.path.join(base_dir, "hackathon.duckdb")):
    DB_PATH = os.path.join(base_dir, "hackathon.duckdb")
else:
    DB_PATH = os.path.join(base_dir, "..", "data", "db", "hackathon.duckdb")
    DB_PATH = os.path.abspath(DB_PATH)

# Conecta ao banco
conn = duckdb.connect(DB_PATH, read_only=True)

# TipoPergunta que vamos testar
tipo_pergunta = "Disciplina"
unidade = "Todos"

# Simulando os filtros do app
where_clause = "1=1"
params = [f"%{tipo_pergunta}%"]

# Query baseada na função get_ranking_sql() para Disciplinas
query = f"""
    SELECT 
        d.Nome_Disciplina as label,
        CAST(AVG(
            CASE 
                WHEN TRIM(f.Resposta) IN ('Concordo', 'Sim') THEN 100
                WHEN TRIM(f.Resposta) IN ('Discordo', 'Não') THEN 0
                ELSE NULL 
            END
        ) AS INTEGER) as value
    FROM fAvaliacao f
    JOIN dDisciplina d ON f.Cod_Disciplina = d.Cod_Disciplina
    WHERE f.TipoPergunta LIKE ? AND {where_clause}
    GROUP BY d.Nome_Disciplina
    HAVING value IS NOT NULL
    ORDER BY value DESC
    LIMIT 8
"""

try:
    df = conn.execute(query, params).df()
    print("\nRESULTADO DA QUERY DE DISCIPLINAS:\n")
    print(df)
except Exception as e:
    print(f"Erro ao executar query: {e}")
finally:
    conn.close()
