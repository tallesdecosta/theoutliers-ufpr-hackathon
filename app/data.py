import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from shiny import App, ui, reactive, render
from shiny.ui import tags
from pathlib import Path


# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
base_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(base_dir, "hackathon.duckdb")):
    DB_PATH = os.path.join(base_dir, "hackathon.duckdb")
else:
    # Caminho alternativo caso esteja rodando em estrutura de pastas diferente
    DB_PATH = os.path.join(base_dir, "..", "data", "db", "hackathon.duckdb")
    DB_PATH = os.path.abspath(DB_PATH)

def get_db_connection():
    return duckdb.connect(DB_PATH, read_only=True)

def get_estrutura_academica():
    """
    Carrega a hierarquia completa para os filtros:
    Setor (via dCurso) -> Departamento (via dDisciplina) -> Curso -> Disciplina
    """
    conn = get_db_connection()
    # Fazemos o JOIN entre Disciplina e Curso para garantir que a hierarquia bata com o Star Schema
    query = """
        SELECT DISTINCT
            c.Setor_Curso as Setor,
            d.Departamento,
            c.Curso,
            d.Nome_Disciplina
        FROM dDisciplina d
        JOIN dCurso c ON d.Cod_Curso = c.Cod_Curso
        ORDER BY 1, 2, 3, 4
    """
    try:
        df = conn.execute(query).df()
        return df
    except Exception as e:
        print(f"Erro ao carregar estrutura acadêmica: {e}")
        # Retorna DataFrame vazio com colunas para evitar crash
        return pd.DataFrame(columns=['Setor', 'Departamento', 'Curso', 'Nome_Disciplina'])
    finally:
        conn.close()

# Carrega a estrutura na memória ao iniciar a aplicação
df_estrutura = get_estrutura_academica()

# --- FUNÇÕES SQL: INSTITUCIONAL E CURSOS (MANTIDAS) ---

def construir_filtros_simples(unidade, tabela_alias="f"):
    filtros = []
    params = []
    if unidade and unidade != "Todos":
        filtros.append(f"{tabela_alias}.SiglaLotação = ?") 
        params.append(unidade)
    return " AND ".join(filtros) if filtros else "1=1", params

def get_eixos_sql(tipo_pergunta, unidade):
    conn = get_db_connection()
    where_clause, params = construir_filtros_simples(unidade)
    
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
        df = conn.execute(query, params).df()
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
    where_clause, params = construir_filtros_simples(unidade)
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
    finally:
        conn.close()

def get_ranking_sql(tipo_pergunta, unidade):
    conn = get_db_connection()
    where_clause, params = construir_filtros_simples(unidade)
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
    except Exception:
        return {"titulo": titulo, "dados": []}
    finally:
        conn.close()

def get_distribuicao_sql(tipo_pergunta, unidade):
    conn = get_db_connection()
    where_clause, params = construir_filtros_simples(unidade)
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
    finally:
        conn.close()

# --- FUNÇÕES SQL: DISCIPLINAS (NOVAS COM HIERARQUIA) ---

def construir_where_disciplina(setor, depto, curso, disciplina):
    filtros = []
    params = []
    
    # JOIN necessário: fAvaliacao -> dDisciplina -> dCurso (para pegar Setor)
    
    if setor != "Todos":
        filtros.append("c.Setor_Curso = ?")
        params.append(setor)
    if depto != "Todos":
        filtros.append("d.Departamento = ?")
        params.append(depto)
    if curso != "Todos":
        filtros.append("c.Curso = ?")
        params.append(curso)
    if disciplina != "Todas":
        filtros.append("d.Nome_Disciplina = ?")
        params.append(disciplina)
        
    return (" AND ".join(filtros) if filtros else "1=1"), params

def get_eixos_sql_disciplina(setor, depto, curso, disciplina):
    conn = get_db_connection()
    where_clause, params = construir_where_disciplina(setor, depto, curso, disciplina)

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
        JOIN dDisciplina d ON f.Cod_Disciplina = d.Cod_Disciplina
        JOIN dCurso c ON d.Cod_Curso = c.Cod_Curso
        JOIN dPergunta p ON f.ID_Pergunta = p.ID_Pergunta
        JOIN dTipoPergunta tp ON p.TipoPergunta = tp.TipoPergunta
        WHERE {where_clause}
        GROUP BY tp.GrupoDePergunta
        HAVING score IS NOT NULL
        ORDER BY score DESC
    """
    try:
        df = conn.execute(query, params).df()
        
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
        print(f"Erro SQL Disciplina Eixos: {e}")
        return 0, []
    finally:
        conn.close()

def get_donut_sql_disciplina(setor, depto, curso, disciplina):
    conn = get_db_connection()
    where_clause, params = construir_where_disciplina(setor, depto, curso, disciplina)

    query = f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN TRIM(Resposta) IN ('Concordo', 'Sim', 'Concordo Totalmente', 'Satisfatório', 'Ótimo', 'Bom') THEN 1 ELSE 0 END) as concordo,
            SUM(CASE WHEN TRIM(Resposta) IN ('Desconheço', 'Indiferente', 'Neutro') THEN 1 ELSE 0 END) as neutro,
            SUM(CASE WHEN TRIM(Resposta) IN ('Discordo', 'Não', 'Discordo Totalmente', 'Ruim', 'Péssimo') THEN 1 ELSE 0 END) as discordo
        FROM fAvaliacao f
        JOIN dDisciplina d ON f.Cod_Disciplina = d.Cod_Disciplina
        JOIN dCurso c ON d.Cod_Curso = c.Cod_Curso
        WHERE {where_clause}
    """
    try:
        df = conn.execute(query, params).df()
        if df.empty or df.iloc[0]['total'] == 0:
            return {"total": 0, "concordo": 0, "neutro": 0, "discordo": 0}
        return df.iloc[0].to_dict()
    finally:
        conn.close()

def get_ranking_sql_disciplina(setor, depto, curso, disciplina):
    conn = get_db_connection()
    where_clause, params = construir_where_disciplina(setor, depto, curso, disciplina)

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
        JOIN dCurso c ON d.Cod_Curso = c.Cod_Curso
        WHERE {where_clause}
        GROUP BY d.Nome_Disciplina
        HAVING value IS NOT NULL
        ORDER BY value DESC
        LIMIT 8
    """
    try:
        df = conn.execute(query, params).df()
        df = df.sort_values(by="value", ascending=True)
        return {"titulo": "Melhores Disciplinas (Seleção)", "dados": df.to_dict("records")}
    finally:
        conn.close()

def get_distribuicao_sql_disciplina(setor, depto, curso, disciplina):
    conn = get_db_connection()
    where_clause, params = construir_where_disciplina(setor, depto, curso, disciplina)

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
        JOIN dCurso c ON d.Cod_Curso = c.Cod_Curso
        WHERE {where_clause}
        AND nota IS NOT NULL
    """
    try:
        df = conn.execute(query, params).df()
        notas = df['nota'].tolist()
        media = np.mean(notas) if notas else 0
        return {"notas": notas, "media": media}
    finally:
        conn.close()

def get_unidades_disponiveis():
    try:
        conn = get_db_connection()
        df = conn.execute("SELECT DISTINCT SiglaLotação FROM dUnidade ORDER BY 1").df()
        conn.close()
        return ["Todos"] + df['SiglaLotação'].tolist()
    except: return ["Todos"]