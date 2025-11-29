import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# 1. CONEXÃO
CAMINHO_DB = "data/db/hackathon.duckdb"
con = duckdb.connect(CAMINHO_DB)

print("--- 1. CURADORIA DE DADOS (CONSIDERANDO OS ÓRFÃOS) ---")

# Vamos inserir registros 'Placeholder' para os IDs órfãos não sumirem do Join
# Para Cursos:
con.sql("""
    INSERT INTO dCurso (Cod_Curso, Curso)
    SELECT DISTINCT f.Cod_Curso, 'Curso Não Identificado (' || f.Cod_Curso || ')'
    FROM fAvaliacao f
    LEFT JOIN dCurso d ON f.Cod_Curso = d.Cod_Curso
    WHERE d.Cod_Curso IS NULL AND f.Cod_Curso IS NOT NULL
""")
print("✅ Órfãos de Curso tratados (inseridos como 'Não Identificado').")

# Para Perguntas:
try:
    con.sql("""
        INSERT INTO dPergunta (ID_Pergunta, Pergunta)
        SELECT DISTINCT f.ID_Pergunta, 'Pergunta Não Cadastrada'
        FROM fAvaliacao f
        LEFT JOIN dPergunta d ON f.ID_Pergunta = d.ID_Pergunta
        WHERE d.ID_Pergunta IS NULL AND f.ID_Pergunta IS NOT NULL
    """)
    print("✅ Órfãos de Pergunta tratados.")
except:
    print("⚠️ Não foi possível tratar órfãos de pergunta (talvez estrutura diferente).")


print("\n--- 2. ANÁLISE ROBUSTA (ÍNDICE DE APROVAÇÃO) ---")
# MUDANÇA DE ESTRATÉGIA:
# Como temos "Sim", "Concordo" e "Concordo Totalmente", não faremos média 1-5.
# Faremos "Percentual de Aprovação" (Positivos / Total Válido).

query_aprovacao = """
    WITH Classificacao AS (
        SELECT 
            c.Curso,
            Resposta,
            CASE 
                -- POSITIVOS (Numerador)
                WHEN Resposta ILIKE '%Concordo Totalmente%' THEN 1
                WHEN Resposta = 'Concordo' THEN 1 -- Exato para não pegar 'Discordo'
                WHEN Resposta = 'Sim' THEN 1
                
                -- NEGATIVOS (Denominador, mas valor 0)
                WHEN Resposta ILIKE '%Discordo%' THEN 0
                WHEN Resposta = 'Não' THEN 0
                WHEN Resposta ILIKE '%Neutro%' THEN 0 -- Neutro joga a aprovação pra baixo
                
                -- IGNORADOS (Não entram na conta)
                WHEN Resposta ILIKE '%Desconheço%' THEN NULL
                ELSE NULL -- Números estranhos (8403) viram NULL
            END as Is_Positivo
        FROM fAvaliacao f
        JOIN dCurso c ON f.Cod_Curso = c.Cod_Curso
    )
    SELECT 
        Curso,
        -- Cálculo da Taxa: Soma de 1s dividido pelo total de (0s e 1s)
        CAST(SUM(Is_Positivo) AS FLOAT) / COUNT(Is_Positivo) * 100 as Taxa_Aprovacao,
        COUNT(Is_Positivo) as Qtd_Respostas_Validas
    FROM Classificacao
    WHERE Is_Positivo IS NOT NULL
    GROUP BY Curso
    HAVING Qtd_Respostas_Validas > 20 -- Filtro estatístico
    ORDER BY Taxa_Aprovacao DESC
    LIMIT 10
"""

df = con.sql(query_aprovacao).df()

if df.empty:
    print("Nenhum dado retornado. Verifique se os textos do CASE WHEN batem com os dados.")
    con.close()
    exit()

print("Top 10 Cursos por Aprovação:")
print(df[['Curso', 'Taxa_Aprovacao']])

# --- 3. VISUALIZAÇÃO DE ALTO NÍVEL ---
# Ordena: Menor pro Maior (para o gráfico de barras ficar Maior em cima)
df = df.sort_values(by='Taxa_Aprovacao', ascending=True)

plt.style.use('seaborn-v0_8-white') 
fig, ax = plt.subplots(figsize=(12, 7), dpi=120)

# Mapa de Cores: Vermelho -> Amarelo -> Verde
norm = mcolors.Normalize(vmin=0, vmax=100) # Escala fixa 0 a 100%
cmap = plt.cm.get_cmap('RdYlGn') 
cores = [cmap(norm(valor)) for valor in df['Taxa_Aprovacao']]

bars = ax.barh(df['Curso'], df['Taxa_Aprovacao'], color=cores, height=0.65)

# Limpezas
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_color('#DDD')
ax.xaxis.set_visible(False)
ax.tick_params(axis='y', length=0, labelsize=10, labelcolor='#333')

# Data Labels (Percentual)
for bar in bars:
    width = bar.get_width()
    # Posição do texto
    x_pos = width - 8 if width > 15 else width + 1 # Se barra mt pequena, texto fora
    cor_texto = 'white' if width > 15 else '#333'
    
    ax.text(x_pos, bar.get_y() + bar.get_height()/2, 
            f'{width:.1f}%', 
            ha='right' if width > 15 else 'left', va='center', 
            color=cor_texto, fontweight='bold', fontsize=11)
    
    # N (contexto)
    qtd = int(df[df['Taxa_Aprovacao'] == width]['Qtd_Respostas_Validas'].values[0])
    ax.text(max(width, 0) + 1, bar.get_y() + bar.get_height()/2, 
            f'(n={qtd})', 
            ha='left', va='center', color='#999', fontsize=8)

plt.suptitle('Top 10 Cursos com Maior Aprovação', fontsize=16, fontweight='bold', x=0.125, ha='left')
plt.title('Considerando respostas "Concordo", "Concordo Totalmente" e "Sim" como positivas.', 
          fontsize=10, color='#666', x=0.125, ha='left', pad=20)

plt.tight_layout()
plt.show()

con.close()