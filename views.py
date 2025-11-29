import duckdb

CAMINHO_DB = "data/db/hackathon.duckdb"
con = duckdb.connect(CAMINHO_DB)

print("\n================================================")
print("=== CRIANDO VIEW: viewAvInstitucional ===")
print("================================================\n")

# 1. Criar a view
con.execute("""
CREATE OR REPLACE VIEW viewAvInstitucional AS
SELECT
    fa.id_avaliacao,
    fa.ID_Pesquisa,
    fa.ID_Pergunta,
    fa.TipoPergunta,
    fa.Ano,
    fa.SiglaLotação,
    fa.Resposta,
    fa.Resposta_Padronizada,
    fa.Valor_Resposta,

    -- Atributos da unidade
    du.UnidadeGestora,
    du.Lotação

FROM fAvaliacao fa
LEFT JOIN dUnidade du
    ON fa.SiglaLotação = du.SiglaLotação

WHERE fa.TipoPergunta = 'Institucional';
""")

print("✓ viewAvInstitucional criada com sucesso.")


# 2. Validação 1 — Contagem de linhas
print("\n--- Validação 1: Contagem de linhas ---")

total_view = con.sql("SELECT COUNT(*) AS qtd FROM viewAvInstitucional").fetchone()[0]
total_base = con.sql("SELECT COUNT(*) AS qtd FROM fAvaliacao WHERE TipoPergunta = 'Institucional'").fetchone()[0]

print(f"Linhas na view ............... {total_view}")
print(f"Linhas na fAvaliacao (base) .. {total_base}")

if total_view == total_base:
    print("✓ Contagem OK: a view contém todas as avaliações institucionais.")
else:
    print("✗ ERRO: A contagem da view NÃO bate com a base!")
    print("  Isso indica filtro errado ou join errado. Corrija antes de seguir.")


# 3. Validação 2 — Conferir se UnidadeGestora aparece
print("\n--- Validação 2: Amostra de UnidadeGestora ---")
amostra = con.sql("""
SELECT DISTINCT UnidadeGestora
FROM viewAvInstitucional
WHERE UnidadeGestora IS NOT NULL
LIMIT 10;
""").df()

print(amostra)

if amostra.empty:
    print("✗ ERRO: Nenhuma UnidadeGestora encontrada! Join pode estar incorreto.")
else:
    print("✓ Join OK: UnidadeGestora encontrada.")


# 4. Validação 3 — Verificar unidades sem correspondência na dimensão
print("\n--- Validação 3: Unidades sem correspondência no dUnidade (join falho) ---")

nao_encontradas = con.sql("""
SELECT DISTINCT SiglaLotação
FROM viewAvInstitucional
WHERE UnidadeGestora IS NULL
LIMIT 20;
""").df()

if not nao_encontradas.empty:
    print(" Aviso: Existem SiglaLotação sem match na dUnidade:")
    print(nao_encontradas)
    print("Isso não impede o uso, mas mostra que algumas unidades não existem na dimensão.")
else:
    print("✓ Todas as SiglaLotação encontradas na dUnidade.")


# 5. Visualização final — primeiras 5 linhas
print("\n--- Visualização das primeiras 5 linhas da view ---")
con.sql("SELECT * FROM viewAvInstitucional LIMIT 5").show()

print("\n=== View viewAvInstitucional finalizada com sucesso ===\n")



print("\n================================================")
print("=== CRIANDO VIEW: viewAvCurso ===")
print("================================================\n")

print("\n==============================================")
print("TESTE 1 — Verificar duplicação em fAvaliacao (TipoPergunta = 'Cursos')")
print("==============================================")

df_test1 = con.sql("""
    SELECT 
        COUNT(*) AS total, 
        COUNT(DISTINCT id_avaliacao) AS distintos
    FROM fAvaliacao
    WHERE TipoPergunta = 'Cursos'
""").df()

print(df_test1)

total = df_test1.iloc[0]["total"]
distintos = df_test1.iloc[0]["distintos"]

if total == distintos:
    print("✓ Não há duplicação na fAvaliacao para cursos.")
else:
    print(" ATENÇÃO: A fAvaliacao já tem duplicação de avaliações de curso!")
    print("  total:", total, " | distintos:", distintos)



print("\n==============================================")
print("TESTE 2 — Verificar cursos duplicados em dCurso")
print("==============================================")

df_test2 = con.sql("""
    SELECT 
        Cod_Curso, 
        COUNT(*) AS qtd
    FROM dCurso
    GROUP BY Cod_Curso
    HAVING COUNT(*) > 1
    LIMIT 20
""").df()

if df_test2.empty:
    print(" Nenhum Cod_Curso duplicado em dCurso.")
else:
    print(" Cursos duplicados encontrados na dimensão dCurso!")
    print(df_test2)





print("\n==============================================")
print("TESTE 3 — Cursos que mais aparecem na viewAvCurso (indicador de multiplicação)")
print("==============================================")

df_test3 = con.sql("""
    SELECT 
        Cod_Curso, 
        COUNT(*) AS linhas
    FROM viewAvCurso
    GROUP BY Cod_Curso
    ORDER BY linhas DESC
    LIMIT 20
""").df()

print(df_test3)

print("""
Interpretar:
- Cursos com valores MUITO altos (ex: 200, 300, 500...) indicam DUPLICAÇÃO.
- Um curso que deveria aparecer 5 vezes pode aparecer 10.
""")

con.close()
