import duckdb
from shiny import App, ui, reactive, render
from shiny.ui import tags
from pathlib import Path

# Importações dos novos arquivos
from style import custom_css
from data import * 
from components import *
from ui_content import get_home_content
from logic_filter import setup_cascading_filters
from modules import dashboard_ui, dashboard_server

www_dir = Path(__file__).parent / "www"

app_ui = ui.page_fluid(
    tags.head(
        tags.style(custom_css),
        tags.title("Fechamento CPA - Universidade Federal do Paraná"), 
        tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css", crossorigin="anonymous"),
        tags.link(rel="icon", type="image/png", href="/static/icon.png?v=2"),
        tags.link(rel="shortcut icon", href="/static/icon.png?v=2")
    ),
    
    ui.output_ui("css_controlador"), 
    tags.div(class_="overlay-escura"),
    
    render_sidebar_nav(), # Componente Sidebar
    render_header_ufpr("btn_sidebar_toggle"), # Componente Header
    
    tags.div(
        ui.navset_hidden(
            ui.nav_panel("home", get_home_content()),
            
            # Aba Institucional usando Módulo
            ui.nav_panel("institucional", 
                dashboard_ui("inst", "Institucional", criar_filtro_simples("inst"))
            ),
            
            # Aba Cursos usando Módulo
            ui.nav_panel("cursos", 
                dashboard_ui("cursos", "Cursos", criar_filtro_simples("curso"))
            ),
            
            # Aba Disciplinas usando Módulo
            ui.nav_panel("disciplinas", 
                dashboard_ui("disc", "Disciplinas", criar_filtro_disciplinas())
            ),
            
            id="router_principal"
        ), class_="conteudo-spa"
    ), padding=0
)

def server(input, output, session):
    
    # --- LÓGICA DE UI E NAVEGAÇÃO ---
    estado_menu = reactive.Value(False)
    
    @reactive.effect
    @reactive.event(input.btn_sidebar_toggle)
    def _(): estado_menu.set(not estado_menu.get())
        
    @reactive.effect
    @reactive.event(input.btn_fechar)
    def _(): estado_menu.set(False)
    
    def navegar_para(page_id): 
        ui.update_navset("router_principal", selected=page_id)
        estado_menu.set(False)
    
    @reactive.effect
    @reactive.event(input.nav_home)
    def _(): navegar_para("home")
    
    @reactive.effect
    @reactive.event(input.nav_inst)
    def _(): navegar_para("institucional")
    
    @reactive.effect
    @reactive.event(input.nav_cursos)
    def _(): navegar_para("cursos")
    
    @reactive.effect
    @reactive.event(input.nav_disc)
    def _(): navegar_para("disciplinas")
        
    @render.ui
    def css_controlador(): 
        return tags.style(".menu-lateral { display: flex !important;} .overlay-escura { display: block !important; }") if estado_menu.get() else None

    # --- INICIALIZAÇÃO DE FILTROS ---
    unidades = get_unidades_disponiveis()
    ui.update_select("inst_campus", choices=unidades)
    ui.update_select("curso_campus", choices=unidades)
    
    # Chama a lógica complexa de filtros de disciplina (logic_filters.py)
    setup_cascading_filters(input, ui)

    # --- ESTADO DOS DADOS (REACTIVE VALUES) ---
    # Institucional
    dados_inst = reactive.Value(get_eixos_sql("Institucional", "Todos"))
    donut_inst = reactive.Value(get_donut_sql("Institucional", "Todos"))
    barras_inst = reactive.Value(get_ranking_sql("Institucional", "Todos"))
    dist_inst = reactive.Value(get_distribuicao_sql("Institucional", "Todos"))

    # Cursos
    dados_curso = reactive.Value(get_eixos_sql("Cursos", "Todos"))
    donut_curso = reactive.Value(get_donut_sql("Cursos", "Todos"))
    barras_curso = reactive.Value(get_ranking_sql("Cursos", "Todos"))
    dist_curso = reactive.Value(get_distribuicao_sql("Cursos", "Todos"))

    # Disciplinas
    dados_disc = reactive.Value((0, []))
    donut_disc = reactive.Value({"total": 0, "concordo": 0, "neutro": 0, "discordo": 0})
    barras_disc = reactive.Value({"titulo": "Top Disciplinas", "dados": []})
    dist_disc = reactive.Value({"notas": [], "media": 0})

    # --- EVENTOS DE ATUALIZAÇÃO DE DADOS ---
    # Apenas a atualização dos valores reativos fica aqui. O render é delegado aos módulos.

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

    @reactive.effect
    @reactive.event(input.disc_btn_filtrar)
    def _():
        setor = input.disc_setor()
        depto = input.disc_depto()
        curso = input.disc_curso()
        disciplina = input.disc_disciplina()

        dados_disc.set(get_eixos_sql_disciplina(setor, depto, curso, disciplina))
        donut_disc.set(get_donut_sql_disciplina(setor, depto, curso, disciplina))
        barras_disc.set(get_ranking_sql_disciplina(setor, depto, curso, disciplina))
        dist_disc.set(get_distribuicao_sql_disciplina(setor, depto, curso, disciplina))

    # --- CHAMADA DOS MÓDULOS (Dashboard Server) ---
    # Note que passamos os objetos reactive.Value, não o valor deles (sem parênteses)
    dashboard_server("inst", dados_inst, donut_inst, barras_inst, dist_inst)
    dashboard_server("cursos", dados_curso, donut_curso, barras_curso, dist_curso)
    dashboard_server("disc", dados_disc, donut_disc, barras_disc, dist_disc)

app = App(app_ui, server, static_assets={"/static": www_dir})