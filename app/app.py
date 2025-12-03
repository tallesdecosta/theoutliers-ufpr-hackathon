import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from shiny import App, ui, reactive, render
from shiny.ui import tags

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
# Ajustado para a estrutura: app/hackathon.duckdb
base_dir = os.path.dirname(os.path.abspath(__file__))
# Tenta achar na mesma pasta, ou na pasta data/db se não estiver
if os.path.exists(os.path.join(base_dir, "hackathon.duckdb")):
    DB_PATH = os.path.join(base_dir, "hackathon.duckdb")
else:
    DB_PATH = os.path.join(base_dir, "..", "data", "db", "hackathon.duckdb")
    DB_PATH = os.path.abspath(DB_PATH)

# --- CONFIGURAÇÃO VISUAL ---
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Roboto', 'Arial', 'Helvetica', 'sans-serif']
plt.rcParams['text.color'] = '#333333'
plt.rcParams['axes.labelcolor'] = '#333333'
plt.rcParams['xtick.color'] = '#333333'
plt.rcParams['ytick.color'] = '#333333'

# --- FUNÇÕES DE BACKEND ---

def get_db_connection():
    return duckdb.connect(DB_PATH, read_only=True)

def construir_filtros(unidade, tabela_alias="f"):
    filtros = []
    params = []
    
    if unidade and unidade != "Todos":
        filtros.append(f"{tabela_alias}.SiglaLotação = ?") 
        params.append(unidade)
        
    return " AND ".join(filtros) if filtros else "1=1", params

def get_eixos_sql(tipo_pergunta, unidade):
    conn = get_db_connection()

    def construir_filtros(unidade, tabela_alias="f"):
        filtros = []
        params = []
        if unidade and unidade != "Todos":
            filtros.append(f"{tabela_alias}.SiglaLotação = ?") 
            params.append(unidade)
        return " AND ".join(filtros) if filtros else "1=1", params

    where_clause, params = construir_filtros(unidade)
    final_params = params  # ⚠️ Sem filtro por TipoPergunta!

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

    try:
        df = conn.execute(query, final_params).df()

        dados_processados = []
        for _, row in df.iterrows():
            score = row['score']
            if score < 60:
                cor, icon, peso_lbl, peso_cls = "card-red", "fa-circle-down", "Crítico", "badge-high"
            elif score <= 75:
                cor, icon, peso_lbl, peso_cls = "card-yellow", "fa-triangle-exclamation", "Importante", "badge-mid"
            else:
                cor, icon, peso_lbl, peso_cls = "card-green", "fa-circle-check", "Médio", "badge-low"

            dados_processados.append({
                "eixo": row['eixo'],
                "score": score,
                "class": cor,
                "icon": icon,
                "peso_info": {"label": peso_lbl, "class": peso_cls}
            })

        media_geral = int(df['score'].mean()) if not df.empty else 0
        return media_geral, dados_processados
    except Exception as e:
        print(f"Erro SQL Eixos: {e}")
        return 0, []
    finally:
        conn.close()

def get_donut_sql(tipo_pergunta, unidade):
    conn = get_db_connection()
    where_clause, params = construir_filtros(unidade)
    final_params = [f"%{tipo_pergunta}%"] + params
    
    query = f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN TRIM(Resposta) IN ('Concordo', 'Sim', 'Concordo Totalmente', 'Satisfatório', 'Ótimo', 'Bom') THEN 1 ELSE 0 END) as concordo,
            SUM(CASE WHEN TRIM(Resposta) IN ('Desconheço', 'Indiferente', 'Neutro') THEN 1 ELSE 0 END) as neutro,
            SUM(CASE WHEN TRIM(Resposta) IN ('Discordo', 'Não', 'Discordo Totalmente', 'Ruim', 'Péssimo') THEN 1 ELSE 0 END) as discordo
        FROM fAvaliacao f
        WHERE f.TipoPergunta LIKE ? AND {where_clause}
    """
    try:
        df = conn.execute(query, final_params).df()
        if df.empty or df.iloc[0]['total'] == 0: 
            return {"total": 0, "concordo": 0, "neutro": 0, "discordo": 0}
        return df.iloc[0].to_dict()
    except Exception as e:
        print(f"Erro SQL Donut: {e}")
        return {"total": 0, "concordo": 0, "neutro": 0, "discordo": 0}
    finally:
        conn.close()

def get_ranking_sql(tipo_pergunta, unidade):
    conn = get_db_connection()
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
    try:
        df = conn.execute(query, final_params).df()
        df = df.sort_values(by='value', ascending=True) 
        return {"titulo": titulo, "dados": df.to_dict('records')}
    except Exception as e:
        print(f"Erro SQL Ranking: {e}")
        return {"titulo": titulo, "dados": []}
    finally:
        conn.close()

def get_distribuicao_sql(tipo_pergunta, unidade):
    conn = get_db_connection()
    where_clause, params = construir_filtros(unidade)
    final_params = [f"%{tipo_pergunta}%"] + params
    
    query = f"""
        SELECT 
            CASE 
                WHEN TRIM(Resposta) IN ('Concordo', 'Sim') THEN 100.0
                WHEN TRIM(Resposta) IN ('Desconheço', 'Neutro') THEN 50.0
                WHEN TRIM(Resposta) IN ('Discordo', 'Não') THEN 0.0
                ELSE NULL
            END as nota
        FROM fAvaliacao f
        WHERE f.TipoPergunta LIKE ? AND {where_clause}
        AND nota IS NOT NULL
    """
    try:
        df = conn.execute(query, final_params).df()
        notas = df['nota'].tolist()
        media = np.mean(notas) if notas else 0
        return {"notas": notas, "media": media}
    except Exception as e:
        return {"notas": [], "media": 0}
    finally:
        conn.close()

def get_unidades_disponiveis():
    try:
        conn = get_db_connection()
        df = conn.execute("SELECT DISTINCT SiglaLotação FROM dUnidade ORDER BY 1").df()
        conn.close()
        return ["Todos"] + df['SiglaLotação'].tolist()
    except: return ["Todos"]
def get_eixos_sql_disciplina(modalidade, disciplina):
    conn = get_db_connection()

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
        JOIN dDisciplina d ON f.Cod_Disciplina = d.Cod_Disciplina
        WHERE d.Modalidade = ?
          AND (d.Nome_Disciplina = ? OR ? = 'Todas')
        GROUP BY tp.GrupoDePergunta
        HAVING score IS NOT NULL
        ORDER BY score DESC
    """

    try:
        df = conn.execute(query, [modalidade, disciplina, disciplina]).df()
        
        dados_processados = []
        for _, row in df.iterrows():
            score = row['score']
            if score < 60:
                cor, icon, peso_lbl, peso_cls = "card-red", "fa-circle-down", "Crítico", "badge-high"
            elif score <= 75:
                cor, icon, peso_lbl, peso_cls = "card-yellow", "fa-triangle-exclamation", "Importante", "badge-mid"
            else:
                cor, icon, peso_lbl, peso_cls = "card-green", "fa-circle-check", "Médio", "badge-low"

            dados_processados.append({
                "eixo": row['eixo'],
                "score": score,
                "class": cor,
                "icon": icon,
                "peso_info": {"label": peso_lbl, "class": peso_cls}
            })

        media_geral = int(df['score'].mean()) if not df.empty else 0
        return media_geral, dados_processados

    finally:
        conn.close()
def get_donut_sql_disciplina(modalidade, disciplina):
    conn = get_db_connection()

    query = f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN TRIM(Resposta) IN ('Concordo', 'Sim', 'Concordo Totalmente', 'Satisfatório', 'Ótimo', 'Bom') THEN 1 ELSE 0 END) as concordo,
            SUM(CASE WHEN TRIM(Resposta) IN ('Desconheço', 'Indiferente', 'Neutro') THEN 1 ELSE 0 END) as neutro,
            SUM(CASE WHEN TRIM(Resposta) IN ('Discordo', 'Não', 'Discordo Totalmente', 'Ruim', 'Péssimo') THEN 1 ELSE 0 END) as discordo
        FROM fAvaliacao f
        JOIN dDisciplina d ON f.Cod_Disciplina = d.Cod_Disciplina
        WHERE d.Modalidade = ?
          AND (d.Nome_Disciplina = ? OR ? = 'Todas')
    """

    try:
        df = conn.execute(query, [modalidade, disciplina, disciplina]).df()
        if df.empty or df.iloc[0]['total'] == 0:
            return {"total": 0, "concordo": 0, "neutro": 0, "discordo": 0}
        return df.iloc[0].to_dict()

    finally:
        conn.close()
def get_ranking_sql_disciplina(modalidade, disciplina):
    conn = get_db_connection()

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
        WHERE d.Modalidade = ?
          AND (d.Nome_Disciplina = ? OR ? = 'Todas')
        GROUP BY d.Nome_Disciplina
        HAVING value IS NOT NULL
        ORDER BY value DESC
        LIMIT 8
    """

    try:
        df = conn.execute(query, [modalidade, disciplina, disciplina]).df()
        df = df.sort_values(by="value", ascending=True)
        return {"titulo": "Top Disciplinas", "dados": df.to_dict("records")}
    finally:
        conn.close()
def get_distribuicao_sql_disciplina(modalidade, disciplina):
    conn = get_db_connection()

    query = f"""
        SELECT 
            CASE 
                WHEN TRIM(Resposta) IN ('Concordo', 'Sim') THEN 100.0
                WHEN TRIM(Resposta) IN ('Desconheço', 'Neutro') THEN 50.0
                WHEN TRIM(Resposta) IN ('Discordo', 'Não') THEN 0.0
                ELSE NULL
            END as nota
        FROM fAvaliacao f
        JOIN dDisciplina d ON f.Cod_Disciplina = d.Cod_Disciplina
        WHERE d.Modalidade = ?
          AND (d.Nome_Disciplina = ? OR ? = 'Todas')
          AND nota IS NOT NULL
    """

    try:
        df = conn.execute(query, [modalidade, disciplina, disciplina]).df()
        notas = df['nota'].tolist()
        media = np.mean(notas) if notas else 0
        return {"notas": notas, "media": media}
    finally:
        conn.close()

# --- CSS ---
custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    * { font-family: 'Roboto', sans-serif !important; }
    html, body { margin: 0 !important; padding: 0 !important; width: 100%; height: 100%; overflow: hidden; background-color: #f4f6f9; }
    .container-fluid { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    .ufpr-header { background-color: #004b8d; color: white; height: 80px; display: flex; gap: 35px; align-items: center; padding: 0 80px; width: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.1); z-index: 1; position: relative; }
    h4 { font-weight: 700; font-size: 28px; margin: 0; }
    img { width: 100; max-width: 120px; }
    .btn-reset { color: white !important; background: transparent !important; border: none !important; cursor: pointer !important; padding: 0 !important; margin: 0 !important; display: flex !important; align-items: center; }
    .menu-lateral { position: fixed; z-index: 99999; background-color: #fff; padding: 25px 55px; height: 100vh; width: 350px; display: none; box-shadow: 2px 0 10px rgba(0,0,0,0.2); flex-direction: column !important; }
    .btn-nav-custom { width: 100%; text-align: left; margin-bottom: 10px; background: transparent; border: none; color: #333; font-size: 18px; padding: 10px; border-bottom: 1px solid #eee; transition: 0.2s; border-radius: 5px; }
    .btn-nav-custom:hover { padding-left: 20px; background-color: #f5f5dc; color: #000; font-weight: 500; }
    .overlay-escura { background-color: black; position:fixed; top: 0; left:0; width: 100vw; height: 100vh; opacity: .5; z-index:999; display: none;}
    #btn_fechar { align-self: flex-end !important; background: transparent !important; border: none !important; font-size: 24px !important; color: #333 !important; }
    .conteudo-spa { padding: 30px 60px; height: calc(100vh - 80px); overflow-y: auto; background-color: #f8f9fa; width: 100%; }
    .page-title { color: #004b8d; margin-bottom: 20px; border-bottom: 2px solid #004b8d; padding-bottom: 10px; display: inline-block; font-weight: 700; }
    .filter-bar { background: white; padding: 15px 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; gap: 20px; margin-bottom: 25px; align-items: flex-end; }
    .excellence-card { background: white; border-radius: 12px; padding: 25px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 30px; border-left: 10px solid #ccc; }
    .exc-label { font-size: 18px; color: #555; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }
    .exc-value { font-size: 48px; font-weight: 700; color: #333; line-height: 1; }
    .exc-sub { font-size: 16px; margin-top: 5px; font-weight: 500; display:flex; align-items:center; gap: 8px; }
    .controls-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 15px;}
    .view-toggles { display: flex; gap: 15px; align-items: center; }
    .scroll-container { display: flex; flex-wrap: nowrap; overflow-x: auto; gap: 20px; padding-bottom: 15px; margin-bottom: 30px; -webkit-overflow-scrolling: touch; }
    .scroll-container::-webkit-scrollbar { height: 8px; }
    .scroll-container::-webkit-scrollbar-track { background: #e0e0e0; border-radius: 4px; }
    .scroll-container::-webkit-scrollbar-thumb { background: #bbb; border-radius: 4px; }
    .kpi-card { flex: 0 0 auto; width: 280px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); padding: 20px; border-left: 6px solid #ccc; display: flex; flex-direction: column; justify-content: space-between; height: 200px; transition: transform 0.2s; }
    .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 4px 10px rgba(0,0,0,0.15); }
    .kpi-title { font-size: 14px; font-weight: 500; color: #555; margin-top: 5px; margin-bottom: 5px; height: 50px; overflow: hidden; line-height: 1.3;}
    .kpi-score { font-size: 36px; font-weight: 700; color: #333; }
    .kpi-footer { font-size: 12px; color: #888; display: flex; align-items: center; gap: 5px; }
    .badge-weight { font-size: 10px; padding: 4px 8px; border-radius: 4px; text-transform: uppercase; font-weight: 700; display: inline-block; width: fit-content; margin-bottom: 8px; }
    .badge-low { background-color: #e9ecef; color: #495057; }
    .badge-mid { background-color: #cff4fc; color: #055160; }
    .badge-high { background-color: #f8d7da; color: #842029; }
    .card-red { border-left-color: #dc3545 !important; } .text-red { color: #dc3545 !important; }
    .card-yellow { border-left-color: #ffc107 !important; } .text-yellow { color: #d39e00 !important; }
    .card-green { border-left-color: #198754 !important; } .text-green { color: #198754 !important; }
    .radar-container { background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 30px; height: 600px; display: flex; justify-content: center; align-items: center; padding: 20px; position: relative; }
    .radar-container img { object-fit: contain; max-height: 100%; max-width: 100%; margin: auto; }
    .chart-box { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); height: 350px; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; }
    .chart-box img { object-fit: contain !important; max-height: 100% !important; max-width: 100% !important; width: auto !important; height: auto !important; }
    .chart-title { font-size: 16px; font-weight: 600; color: #444; margin-bottom: 15px; width: 100%; text-align: center; border-bottom: 1px solid #eee; padding-bottom: 10px; }
"""

# --- PLOTS ---

def criar_plot_radar(lista_dados):
    if not lista_dados: return None
    labels = [d['eixo'] for d in lista_dados]
    valores = [d['score'] for d in lista_dados]
    valores += valores[:1] 
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    ax.plot(angles, valores, color='#004b8d', linewidth=2, linestyle='solid')
    ax.fill(angles, valores, color='#004b8d', alpha=0.25)
    ax.set_xticks(angles[:-1])
    labels_wrapped = [l.replace(' ', '\n', 1) if len(l) > 12 else l for l in labels]
    ax.set_xticklabels(labels_wrapped, size=10, color='#333')
    ax.tick_params(axis='x', pad=20) 
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], color="#999", size=9)
    ax.spines['polar'].set_visible(False)
    fig.patch.set_alpha(0.0)
    plt.tight_layout(pad=3.0)
    return fig

def criar_plot_donut(dados):
    total = dados['total']
    if total == 0: return None
    vals = [dados['concordo'], dados['neutro'], dados['discordo']]
    colors = ['#198754', '#adb5bd', '#dc3545'] 
    labels_legenda = []
    labels_base = ["Concordo", "Neutro", "Discordo"]
    for val, lbl in zip(vals, labels_base):
        pct = (val / total * 100)
        labels_legenda.append(f"{lbl}: {val} ({pct:.1f}%)")

    fig, ax = plt.subplots(figsize=(6, 4))
    wedges, texts = ax.pie(vals, colors=colors, startangle=90, wedgeprops=dict(width=0.4))
    ax.text(0, 0, f"{total}", ha='center', va='center', fontsize=22, fontweight='bold', color='#333')
    ax.legend(wedges, labels_legenda, title="Respostas", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=False)
    fig.patch.set_alpha(0.0)
    return fig

def criar_plot_barras(dados_dict):
    dados = dados_dict["dados"]
    if not dados: return None
    labels = [d['label'] for d in dados]
    values = [d['value'] for d in dados]
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.barh(labels, values, color='#004b8d', height=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#cccccc')
    ax.spines['left'].set_visible(False)
    ax.grid(axis='x', linestyle='--', alpha=0.3)
    ax.set_xlim(0, 115)
    ax.tick_params(axis='y', length=0)
    for bar in bars: 
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, f'{int(bar.get_width())}', ha='left', va='center', fontsize=10, fontweight='bold', color='#004b8d')
    plt.tight_layout()
    fig.patch.set_alpha(0.0)
    return fig

def criar_plot_distribuicao(dados):
    notas = dados['notas']
    media = dados['media']
    if not notas: return None
    
    fig, ax = plt.subplots(figsize=(6, 4))
    n, bins, patches = ax.hist(notas, bins=5, range=(0, 100), edgecolor='white', linewidth=0.5) 
    for i, patch in enumerate(patches):
        x_val = patch.get_x() + patch.get_width() / 2
        if x_val < 40: 
            patch.set_facecolor('#dc3545')
            patch.set_alpha(0.7)
        elif x_val < 60: 
            patch.set_facecolor('#adb5bd')
            patch.set_alpha(0.7) 
        else: 
            patch.set_facecolor('#198754')
            patch.set_alpha(0.7)
            
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#cccccc')
    ax.set_yticks([])
    ax.plot(media, -max(n)*0.05, marker='^', color='#333', markersize=10, clip_on=False)
    ax.text(media, -max(n)*0.15, f"{media:.1f}", ha='center', va='top', fontweight='bold', color='#333')
    plt.tight_layout()
    fig.patch.set_alpha(0.0)
    return fig

# --- UI HELPER ---
def render_page_structure(prefixo, titulo):

   
    if prefixo == "disc":
        # Filtros ESPECÍFICOS para aba Disciplinas
        filtro_html = tags.div(
            # Modalidade
            tags.div(
                tags.label("Modalidade", style="font-weight: 500; font-size: 12px;"),
                ui.input_select("disc_modalidade", label=None, choices=[], width="200px"),
                style="display:flex; flex-direction:column;"
            ),

            # Nome da Disciplina
            tags.div(
                tags.label("Disciplina", style="font-weight: 500; font-size: 12px;"),
                ui.input_select("disc_nome", label=None, choices=[], width="300px"),
                style="display:flex; flex-direction:column;"
            ),

            # Botão
            tags.div(
                ui.input_action_button("disc_btn_filtrar", "Atualizar Dados", class_="btn-primary"),
                style="padding-bottom: 5px;"
            ),

            class_="filter-bar"
        )

    else:
        # Filtros originais para Institucional e Cursos
        filtro_html = tags.div(
            tags.div(
                tags.label("Unidade", style="font-weight: 500; font-size: 12px;"),
                ui.input_select(f"{prefixo}_campus", label=None, choices=[], width="200px"),
                style="display:flex; flex-direction:column;"
            ),
            tags.div(
                ui.input_action_button(f"{prefixo}_btn_filtrar", "Atualizar Dados", class_="btn-primary"),
                style="padding-bottom: 5px;"
            ),
            class_="filter-bar"
        )


    return tags.div(
        tags.h2(titulo, class_="page-title"),

        # BLOCO DE FILTRO (dinâmico conforme prefixo)
        filtro_html,

        # Card Excelência
        ui.output_ui(f"{prefixo}_card_excelencia"),

        # Título + Seleção cards/radar
        tags.div(
            tags.div(
                tags.h5("Detalhamento por Eixos", style="margin:0; margin-right: 20px; color: #666;"),
                ui.input_radio_buttons(
                    f"{prefixo}_view_mode",
                    label=None,
                    choices={"cards": "Cards", "radar": "Gráfico Radar"},
                    selected="cards",
                    inline=True
                ),
                class_="view-toggles"
            ),

            # Ordenação quando em modo cards
            ui.panel_conditional(
                f"input.{prefixo}_view_mode === 'cards'",
                ui.input_radio_buttons(
                    f"{prefixo}_sort_order",
                    label=None,
                    choices={"asc": "Menor Nota (Crítico)", "desc": "Maior Nota"},
                    selected="asc",
                    inline=True
                )
            ),

            class_="controls-row"
        ),

        # Lista de cards
        ui.panel_conditional(
            f"input.{prefixo}_view_mode === 'cards'",
            ui.output_ui(f"{prefixo}_lista_cards")
        ),

        # Gráfico radar
        ui.panel_conditional(
            f"input.{prefixo}_view_mode === 'radar'",
            tags.div(
                ui.output_plot(f"{prefixo}_grafico_radar", width="100%", height="100%"),
                class_="radar-container"
            )
        ),

        tags.hr(),

        # Título
        tags.h5("Visão Geral das Respostas", style="margin-bottom: 20px; color: #666;"),

        # GRADE DE GRÁFICOS
        ui.layout_column_wrap(
            tags.div(
                tags.div("Status Geral das Respostas", class_="chart-title"),
                ui.output_plot(f"{prefixo}_grafico_donut", width="100%", height="100%"),
                class_="chart-box"
            ),
            tags.div(
                tags.div("Ranking de Destaques", class_="chart-title"),
                ui.output_plot(f"{prefixo}_grafico_barras", width="100%", height="100%"),
                class_="chart-box"
            ),
            tags.div(
                tags.div("Consistência das Avaliações", class_="chart-title"),
                ui.output_plot(f"{prefixo}_grafico_dist", width="100%", height="100%"),
                class_="chart-box"
            ),
            width=1/3,
        ),

        tags.br(),
        tags.br()
    )

app_ui = ui.page_fluid(
    tags.head(tags.style(custom_css)),
    tags.head(tags.title("UFPR Analytics"), tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css", crossorigin="anonymous"),),
    ui.output_ui("css_controlador"), 
    tags.div(class_="overlay-escura"),
    tags.section(
        ui.input_action_button("btn_fechar", "✕"), 
        tags.nav(tags.ul(
            tags.li(ui.input_action_button("nav_home", "Painel Principal", class_="btn-nav-custom")), 
            tags.li(ui.input_action_button("nav_inst", "Institucional", class_="btn-nav-custom")), 
            tags.li(ui.input_action_button("nav_cursos", "Cursos", class_="btn-nav-custom")), 
            tags.li(ui.input_action_button("nav_disc", "Disciplinas", class_="btn-nav-custom"))
        ), style="list-style: none; padding: 0;"), class_="menu-lateral"
    ),
    tags.header(
        ui.input_action_link("btn_sidebar_toggle", label=None, icon=tags.i(class_="fa-solid fa-bars", style="font-size:24px;"), class_="btn-reset"),
        tags.img(src="https://ufpr.br/wp-content/themes/wpufpr_bootstrap5_portal/images/ufpr.png"),
        tags.h4("UNIVERSIDADE FEDERAL DO PARANÁ"),
        class_="ufpr-header"
    ),
    tags.div(
        ui.navset_hidden(
            ui.nav_panel("home", tags.h2("Visão Geral", class_="page-title"), tags.div(tags.h3("Bem-vindo"), tags.p("Selecione uma categoria no menu para iniciar a análise."), style="padding: 40px; background: white; border-radius: 8px; text-align: center; color: #555;")),
            ui.nav_panel("institucional", render_page_structure("inst", "Institucional")),
            ui.nav_panel("cursos", render_page_structure("curso", "Cursos")),
            ui.nav_panel("disciplinas", render_page_structure("disc", "Disciplinas")),
            id="router_principal"
        ), class_="conteudo-spa"
    ), padding=0
)

def server(input, output, session):
    estado_menu = reactive.Value(False)
    
    @reactive.effect
    @reactive.event(input.btn_sidebar_toggle)
    def _(): 
        estado_menu.set(not estado_menu.get())
        
    @reactive.effect
    @reactive.event(input.btn_fechar)
    def _(): 
        estado_menu.set(False)
    
    def navegar_para(page_id): 
        ui.update_navset("router_principal", selected=page_id)
        estado_menu.set(False)
    
    @reactive.effect
    @reactive.event(input.nav_home)
    def _(): 
        navegar_para("home")
    
    @reactive.effect
    @reactive.event(input.nav_inst)
    def _(): 
        navegar_para("institucional")
    
    @reactive.effect
    @reactive.event(input.nav_cursos)
    def _(): 
        navegar_para("cursos")
    
    @reactive.effect
    @reactive.event(input.nav_disc)
    def _(): 
        navegar_para("disciplinas")
        
    @render.ui
    def css_controlador(): 
        return tags.style(".menu-lateral { display: flex !important;} .overlay-escura { display: block !important; }") if estado_menu.get() else None

    # Load Selects
    unidades = get_unidades_disponiveis()
    ui.update_select("inst_campus", choices=unidades)
    ui.update_select("curso_campus", choices=unidades)
    conn = get_db_connection()
    modalidades = conn.execute("SELECT DISTINCT Modalidade FROM dDisciplina ORDER BY 1").df()["Modalidade"].tolist()
    conn.close()
    ui.update_select("disc_modalidade", choices=modalidades)
    ui.update_select("disc_nome", choices=["Selecione uma modalidade"])
    @reactive.effect
    @reactive.event(input.disc_modalidade)
    def _():
        mod = input.disc_modalidade()

        conn = get_db_connection()
        df = conn.execute("""
            SELECT DISTINCT Nome_Disciplina
            FROM dDisciplina
            WHERE Modalidade = ?
            ORDER BY Nome_Disciplina
        """, [mod]).df()
        conn.close()

        disciplinas = ["Todas"] + df["Nome_Disciplina"].tolist()
        ui.update_select("disc_nome", choices=disciplinas)
    # Initial Data (AGGREGATED - No Year)
    
    dados_inst = reactive.Value(get_eixos_sql("Institucional", "Todos"))
    donut_inst = reactive.Value(get_donut_sql("Institucional", "Todos"))
    barras_inst = reactive.Value(get_ranking_sql("Institucional", "Todos"))
    dist_inst = reactive.Value(get_distribuicao_sql("Institucional", "Todos"))

    dados_curso = reactive.Value(get_eixos_sql("Cursos", "Todos"))
    donut_curso = reactive.Value(get_donut_sql("Cursos", "Todos"))
    barras_curso = reactive.Value(get_ranking_sql("Cursos", "Todos"))
    dist_curso = reactive.Value(get_distribuicao_sql("Cursos", "Todos"))

    # ---- DISCIPLINAS: valores iniciais "vazios" ----
    dados_disc = reactive.Value((0, []))  # media=0, lista vazia de eixos
    donut_disc = reactive.Value({"total": 0, "concordo": 0, "neutro": 0, "discordo": 0})
    barras_disc = reactive.Value({"titulo": "Top Disciplinas", "dados": []})
    dist_disc = reactive.Value({"notas": [], "media": 0})

    # ---- FILTRO DAS ABAS INSTITUCIONAL / CURSOS (mantém como estava) ----
    @reactive.effect
    @reactive.event(input.inst_btn_filtrar)
    def _():
        u = input.inst_campus()
        dados_inst.set(get_eixos_sql("Institucional", u))
        donut_inst.set(get_donut_sql("Institucional", u))
        barras_inst.set(get_ranking_sql("Institucional", u))
        dist_inst.set(get_distribuicao_sql("Institucional", u))

    @reactive.effect
    @reactive.event(input.curso_btn_filtrar)
    def _():
        u = input.curso_campus()
        dados_curso.set(get_eixos_sql("Cursos", u))
        donut_curso.set(get_donut_sql("Cursos", u))
        barras_curso.set(get_ranking_sql("Cursos", u))
        dist_curso.set(get_distribuicao_sql("Cursos", u))

    # ---- FILTRO DA ABA DISCIPLINAS (modalidade + disciplina) ----
    @reactive.effect
    @reactive.event(input.disc_btn_filtrar)
    def _():
        modalidade = input.disc_modalidade()
        disciplina = input.disc_nome()

        dados_disc.set(get_eixos_sql_disciplina(modalidade, disciplina))
        donut_disc.set(get_donut_sql_disciplina(modalidade, disciplina))
        barras_disc.set(get_ranking_sql_disciplina(modalidade, disciplina))
        dist_disc.set(get_distribuicao_sql_disciplina(modalidade, disciplina))


    def render_excellence_card(media):
        if media < 60: 
            cor, txt, icon = "card-red", "text-red", "fa-circle-xmark"
        elif 60 <= media <= 75: 
            cor, txt, icon = "card-yellow", "text-yellow", "fa-triangle-exclamation"
        else: 
            cor, txt, icon = "card-green", "text-green", "fa-circle-check"
        return tags.div(tags.div(tags.div("Nível de Excelência", class_="exc-label"), tags.div(tags.i(class_=f"fa-solid {icon}"), "Status Geral", class_=f"exc-sub {txt}")), tags.div(tags.span(str(media), class_=f"exc-value {txt}"), tags.span("%", style="font-size: 24px; color: #999;")), class_=f"excellence-card {cor}")

    def render_cards_lista(lista_dados, ordem):
        if not lista_dados: return tags.div("Sem dados para exibir.", style="padding: 20px; color: #666;")
        lista_final = sorted(lista_dados, key=lambda x: x['score'], reverse=(ordem == "desc"))
        html = []
        for item in lista_final:
            html.append(tags.div(tags.span(item['peso_info']['label'], class_=f"badge-weight {item['peso_info']['class']}"), tags.div(item['eixo'], class_="kpi-title"), tags.div(str(item['score']), class_="kpi-score"), tags.div(tags.i(class_=f"fa-solid {item['icon']}"), "Pontuação", class_="kpi-footer"), class_=f"kpi-card {item['class']}"))
        return tags.div(html, class_="scroll-container")

    @render.ui
    def inst_card_excelencia(): 
        media, _ = dados_inst.get()
        return render_excellence_card(media)
    
    @render.ui
    def inst_lista_cards(): 
        _, lista = dados_inst.get()
        return render_cards_lista(lista, input.inst_sort_order())
    
    @render.plot
    def inst_grafico_radar(): 
        _, lista = dados_inst.get()
        return criar_plot_radar(lista)
    
    @render.plot
    def inst_grafico_donut(): 
        return criar_plot_donut(donut_inst.get())
    
    @render.plot
    def inst_grafico_barras(): 
        return criar_plot_barras(barras_inst.get())
    
    @render.plot
    def inst_grafico_dist(): 
        return criar_plot_distribuicao(dist_inst.get())

    @render.ui
    def curso_card_excelencia(): 
        media, _ = dados_curso.get()
        return render_excellence_card(media)
    
    @render.ui
    def curso_lista_cards(): 
        _, lista = dados_curso.get()
        return render_cards_lista(lista, input.curso_sort_order())
    
    @render.plot
    def curso_grafico_radar(): 
        _, lista = dados_curso.get()
        return criar_plot_radar(lista)
    
    @render.plot
    def curso_grafico_donut(): 
        return criar_plot_donut(donut_curso.get())
    
    @render.plot
    def curso_grafico_barras(): 
        return criar_plot_barras(barras_curso.get())
    
    @render.plot
    def curso_grafico_dist(): 
        return criar_plot_distribuicao(dist_curso.get())

    @render.ui
    def disc_card_excelencia(): 
        media, _ = dados_disc.get()
        return render_excellence_card(media)
    
    @render.ui
    def disc_lista_cards(): 
        _, lista = dados_disc.get()
        return render_cards_lista(lista, input.disc_sort_order())
    
    @render.plot
    def disc_grafico_radar(): 
        _, lista = dados_disc.get()
        return criar_plot_radar(lista)
    
    @render.plot
    def disc_grafico_donut(): 
        return criar_plot_donut(donut_disc.get())
    
    @render.plot
    def disc_grafico_barras(): 
        return criar_plot_barras(barras_disc.get())
    
    @render.plot
    def disc_grafico_dist(): 
        return criar_plot_distribuicao(dist_disc.get())

app = App(app_ui, server)