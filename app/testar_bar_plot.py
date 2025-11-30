import duckdb

# CAMINHO DO SEU BANCO
DB_PATH = "C:/Users/gabri/Documents/theoutliers-ufpr-hackathon/app/hackathon.duckdb"

def construir_filtros(unidade, alias="f"):
    if unidade and unidade != "Todos":
        return f"{alias}.SiglaLotação = ?", [unidade]
    else:
        return "1=1", []

def testar_ranking(tipo_pergunta, unidade="Todos"):
    where_clause, params = construir_filtros(unidade)
    final_params = [f"%{tipo_pergunta}%"] + params

    if 'Institucional' in tipo_pergunta:
        join_clause = "JOIN dUnidade d ON f.SiglaLotação = d.SiglaLotação"
        label_col = "d.UnidadeGestora"
        titulo = "Satisfação por Unidade"
    elif 'Curso' in tipo_pergunta: 
        join_clause = "JOIN dCurso d ON f.Cod_Curso = d.Cod_Curso"
        label_col = "d.Curso"
        titulo = "Top Cursos"
    else: 
        join_clause = "JOIN dDisciplina d ON f.Cod_Disciplina = d.Cod_Disciplina"
        label_col = "d.Nome_Disciplina"
        titulo = "Top Disciplinas"

    query = f"""
        SELECT 
            {label_col} as label,
            CAST(AVG(
                CASE 
                    WHEN TRIM(f.Resposta) IN ('Concordo', 'Sim') THEN 100
                    WHEN TRIM(f.Resposta) IN ('Discordo', 'Não') THEN 0
                    ELSE NULL 
                END
            ) AS INTEGER) as value
        FROM fAvaliacao f
        {join_clause}
        WHERE f.TipoPergunta LIKE ? AND {where_clause}
        GROUP BY {label_col}
        HAVING value IS NOT NULL
        ORDER BY value DESC
        LIMIT 8
    """

    print("🔍 QUERY USADA:\n", query)
    print("📦 PARÂMETROS:", final_params)

    try:
        conn = duckdb.connect(DB_PATH, read_only=True)
        df = conn.execute(query, final_params).df()
        df = df.sort_values(by="value", ascending=True)
        print("\n✅ RESULTADO FINAL:")
        print(df)
    except Exception as e:
        print(f"\n❌ ERRO AO EXECUTAR SQL: {e}")
    finally:
        conn.close()

# ==== TESTE REAL ====
testar_ranking("Institucional")
