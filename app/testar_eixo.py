import duckdb
import pandas as pd

# CAMINHO DO SEU BANCO
DB_PATH = "C:/Users/gabri/Documents/theoutliers-ufpr-hackathon/app/hackathon.duckdb"

def get_eixos_sql(tipo_pergunta, unidade):
    def construir_filtros(unidade, tabela_alias="f"):
        filtros = []
        params = []
        if unidade and unidade != "Todos":
            filtros.append(f"{tabela_alias}.SiglaLotação = ?") 
            params.append(unidade)
        return " AND ".join(filtros) if filtros else "1=1", params

    conn = duckdb.connect(DB_PATH, read_only=True)
    where_clause, params = construir_filtros(unidade)
    term_search = f"%{tipo_pergunta}%"
    final_params = params

    query = f"""
    SELECT 
        tp.GrupoDePergunta AS eixo,
        CAST(AVG(
            CASE 
                WHEN TRIM(f.Resposta) IN ('Concordo', 'Sim', 'Concordo Totalmente', 'Satisfatório', 'Ótimo', 'Bom') THEN 100
                WHEN TRIM(f.Resposta) IN ('Discordo', 'Não', 'Discordo Totalmente', 'Ruim', 'Péssimo') THEN 0
                ELSE NULL 
            END
        ) AS INTEGER) AS score
    FROM fAvaliacao f
    JOIN dPergunta p ON f.ID_Pergunta = p.ID_Pergunta
    JOIN dTipoPergunta tp ON p.TipoPergunta = tp.TipoPergunta
    WHERE {where_clause}
    GROUP BY tp.GrupoDePergunta
    HAVING score IS NOT NULL
    ORDER BY score DESC
"""

    print("🔎 QUERY USADA:")
    print(query)
    print("🔎 PARÂMETROS:")
    print(final_params)

    try:
        df = conn.execute(query, final_params).df()
        print("\n✅ RESULTADO:")
        print(df)
    except Exception as e:
        print(f"\n❌ ERRO AO EXECUTAR SQL: {e}")
    finally:
        conn.close()

# ==== TESTE ====
get_eixos_sql("Institucional", "Todos")
