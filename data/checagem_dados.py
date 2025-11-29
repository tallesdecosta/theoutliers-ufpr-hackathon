import duckdb

CAMINHO_DB = "data/db/hackathon.duckdb"
con = duckdb.connect(CAMINHO_DB)

print("\n=== CHECAGEM 1: VOLUMETRIA DAS TABELAS ===")
con.sql("""
SELECT 'dCurso'        AS tabela, COUNT(*) AS linhas FROM dCurso
UNION ALL
SELECT 'dDisciplina'   AS tabela, COUNT(*) FROM dDisciplina
UNION ALL
SELECT 'dPergunta'     AS tabela, COUNT(*) FROM dPergunta
UNION ALL
SELECT 'dTipoPergunta' AS tabela, COUNT(*) FROM dTipoPergunta
UNION ALL
SELECT 'dUnidade'      AS tabela, COUNT(*) FROM dUnidade
UNION ALL
SELECT 'fAvaliacao'    AS tabela, COUNT(*) FROM fAvaliacao;
""").show()

print("\n=== CHECAGEM 2: VALORES DISTINTOS DE RESPOSTA ===")
con.sql("""
SELECT DISTINCT Resposta
FROM fAvaliacao
ORDER BY Resposta;
""").show()



print("\n=== CHECAGEM 3: INTEGRIDADE REFERENCIAL ===")

def checar_orfaos(fato, col, dim, colpk):
    print(f"\n→ Checando {col}...")
    con.sql(f"""
        SELECT COUNT(*) AS orfaos
        FROM {fato} f
        LEFT JOIN {dim} d ON f.{col} = d.{colpk}
        WHERE d.{colpk} IS NULL AND f.{col} IS NOT NULL
    """).show()

checar_orfaos("fAvaliacao", "Cod_Curso", "dCurso", "Cod_Curso")
checar_orfaos("fAvaliacao", "Cod_Disciplina", "dDisciplina", "Cod_Disciplina")
checar_orfaos("fAvaliacao", "ID_Pergunta", "dPergunta", "ID_Pergunta")

print("\n=== CHECAGEM 4: Consistência Semântica das Perguntas ===")
con.sql("""
SELECT 
    p.TipoPergunta,
    t.GrupoDePergunta,
    COUNT(*) AS total_perguntas
FROM dPergunta p
LEFT JOIN dTipoPergunta t 
       ON p.TipoPergunta = t.TipoPergunta
GROUP BY p.TipoPergunta, t.GrupoDePergunta
ORDER BY p.TipoPergunta, t.GrupoDePergunta;
""").show()



print("\n=== CHECAGEM 5: Distribuição de Respostas (para detectar inválidas) ===")
con.sql("""
SELECT 
    Resposta,
    COUNT(*) AS qtd
FROM fAvaliacao
GROUP BY Resposta
ORDER BY qtd DESC;
""").show()


con.close()
