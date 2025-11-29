import duckdb
import pandas as pd


pd.set_option('display.max_columns', None)
pd.set_option('display.width', 2000)
pd.set_option('display.max_colwidth', None)


CAMINHO_DB = "data/db/hackathon.duckdb"

print(" Conectando ao banco...")
con = duckdb.connect(CAMINHO_DB)

# PASSO 1 — Garantir coluna id_avaliacao (PK artificial) E PREENCHER

print("\n=== PASSO 1: Criando/preenchendo id_avaliacao ===")

# Verifica colunas existentes
cols = [row[0] for row in con.execute("DESCRIBE fAvaliacao").fetchall()]
has_id = "id_avaliacao" in cols

if not has_id:
    print("→ Coluna id_avaliacao NÃO existe. Vou recriar a tabela com id.")
    con.execute("""
        CREATE TABLE fAvaliacao_tmp AS
        SELECT 
            row_number() OVER () AS id_avaliacao,
            *
        FROM fAvaliacao;
    """)
    con.execute("DROP TABLE fAvaliacao;")
    con.execute("ALTER TABLE fAvaliacao_tmp RENAME TO fAvaliacao;")
    print("Tabela recriada com id_avaliacao preenchido.")
else:
    # Verifica se a coluna está vazia
    total_linhas, total_ids = con.execute("""
        SELECT COUNT(*) AS total_linhas,
               COUNT(id_avaliacao) AS total_ids
        FROM fAvaliacao;
    """).fetchone()

    if total_ids == 0:
        print("→ Coluna id_avaliacao existe, mas está TODA vazia. Vou recriar a tabela.")
        con.execute("""
            CREATE TABLE fAvaliacao_tmp AS
            SELECT 
                row_number() OVER () AS id_avaliacao,
                * EXCLUDE(id_avaliacao)
            FROM fAvaliacao;
        """)
        con.execute("DROP TABLE fAvaliacao;")
        con.execute("ALTER TABLE fAvaliacao_tmp RENAME TO fAvaliacao;")
        print("Tabela recriada e id_avaliacao preenchido.")
    else:
        print(f"id_avaliacao já existe e está preenchida ({total_ids} linhas). Nada a fazer.")

# === VISUALIZAÇÃO DO PASSO 1 ===
print("\n=== VISUALIZAÇÃO PASSO 1 ===")
df = con.sql("""
    SELECT id_avaliacao, Resposta, Cod_Curso, Cod_Disciplina
    FROM fAvaliacao
    ORDER BY id_avaliacao
    LIMIT 10;
""").df()

print(df)

print("\n=== CONTAGEM PASSO 1 ===")
con.sql("""
SELECT
    COUNT(*) AS total_linhas,
    COUNT(id_avaliacao) AS total_ids
FROM fAvaliacao;
""").show()


# PASSO 2 — Criar coluna Resposta_Padronizada

print("\n=== PASSO 2: Criando coluna Resposta_Padronizada ===")

cols = [row[0] for row in con.execute("DESCRIBE fAvaliacao").fetchall()]

# Criar coluna se não existir
if "Resposta_Padronizada" not in cols:
    print("→ Coluna Resposta_Padronizada não existe. Criando...")
    con.execute("ALTER TABLE fAvaliacao ADD COLUMN Resposta_Padronizada VARCHAR")
else:
    print("→ Coluna Resposta_Padronizada já existe. Atualizando valores...")

print("→ Preenchendo Resposta_Padronizada...")

con.execute("""
UPDATE fAvaliacao
SET Resposta_Padronizada =
    CASE 
        WHEN Resposta = 'Concordo' THEN 'positivo'
        WHEN Resposta = 'Sim' THEN 'positivo'

        WHEN Resposta = 'Discordo' THEN 'negativo'
        WHEN Resposta = 'Não' THEN 'negativo'

        WHEN Resposta = 'Desconheço' THEN 'neutro'

        WHEN Resposta ~ '^[0-9]+$' THEN NULL
        ELSE NULL
    END;
""")

print(" Resposta_Padronizada preenchida.")

# === VISUALIZAÇÃO DO PASSO 2 ===
print("\n=== VISUALIZAÇÃO PASSO 2 ===")
df = con.sql("""
    SELECT id_avaliacao, Resposta, Resposta_Padronizada
    FROM fAvaliacao
    ORDER BY id_avaliacao
    LIMIT 10;
""").df()

print(df)

print("\n=== DISTRIBUIÇÃO DE Resposta_Padronizada ===")
con.sql("""
SELECT Resposta_Padronizada, COUNT(*) AS qtd
FROM fAvaliacao
GROUP BY Resposta_Padronizada
ORDER BY qtd DESC;
""").show()



# ============================================================================
# PASSO 3 — Criar Valor_Resposta (1/0/NULL)
# ============================================================================
print("\n=== PASSO 3: Criando coluna Valor_Resposta ===")

cols = [row[0] for row in con.execute("DESCRIBE fAvaliacao").fetchall()]

# Criar coluna se não existir
if "Valor_Resposta" not in cols:
    print("→ Coluna Valor_Resposta não existe. Criando...")
    con.execute("ALTER TABLE fAvaliacao ADD COLUMN Valor_Resposta INT")
else:
    print("→ Coluna Valor_Resposta já existe. Atualizando valores...")

print("→ Preenchendo Valor_Resposta...")

con.execute("""
    UPDATE fAvaliacao
    SET Valor_Resposta =
        CASE 
            WHEN Resposta_Padronizada = 'positivo' THEN 1
            WHEN Resposta_Padronizada = 'negativo' THEN 0
            ELSE NULL
        END;
""")

print(" Valor_Resposta preenchido.")

# === VISUALIZAÇÃO PASSO 3 ===
print("\n=== VISUALIZAÇÃO PASSO 3 ===")
df = con.sql("""
    SELECT id_avaliacao, Resposta, Resposta_Padronizada, Valor_Resposta
    FROM fAvaliacao
    ORDER BY id_avaliacao
    LIMIT 10;
""").df()

print(df)

print("\n=== DISTRIBUIÇÃO DE Valor_Resposta ===")
con.sql("""
SELECT Valor_Resposta, COUNT(*) AS qtd
FROM fAvaliacao
GROUP BY Valor_Resposta
ORDER BY Valor_Resposta;
""").show()

con.sql("SHOW TABLES").show()

con.sql("DESCRIBE dUnidade").show()
con.sql("DESCRIBE dCurso").show()
con.sql("DESCRIBE dDisciplina").show()


con.close()