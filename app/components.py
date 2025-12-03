from shiny import ui
from shiny.ui import tags

def render_header_ufpr(toggle_id):
    return tags.header(
        tags.div(
            ui.input_action_link(toggle_id, label=None, icon=tags.i(class_="fa-solid fa-bars", style="font-size:24px;"), class_="btn-reset"),
            tags.img(src="https://ufpr.br/wp-content/themes/wpufpr_bootstrap5_portal/images/ufpr.png"),
            tags.h4("UNIVERSIDADE FEDERAL DO PARANÁ"),
            style="display: flex; gap: 25px; align-items: center; width: 100%;"
        ),
        tags.div(
            style="height: 0.1px; background-color: white; width: 100%; margin-top: 15px; border-radius: 2px; opacity: 0.4;"
        ),
        class_="ufpr-header"
    )

def render_sidebar_nav():
    return tags.section(
        ui.input_action_button("btn_fechar", "✕"), 
        tags.nav(tags.ul(
            tags.li(ui.input_action_button("nav_home", "Painel Principal", class_="btn-nav-custom")), 
            tags.li(ui.input_action_button("nav_inst", "Institucional", class_="btn-nav-custom")), 
            tags.li(ui.input_action_button("nav_cursos", "Cursos", class_="btn-nav-custom")), 
            tags.li(ui.input_action_button("nav_disc", "Disciplinas", class_="btn-nav-custom"))
        ), style="list-style: none; padding: 0;"), class_="menu-lateral"
    )

def card_excelencia_ui(media):
    """Gera o HTML do card de excelência baseado na média."""
    if media < 60: 
        cor, txt, icon = "card-red", "text-red", "fa-circle-xmark"
    elif 60 <= media <= 75: 
        cor, txt, icon = "card-yellow", "text-yellow", "fa-triangle-exclamation"
    else: 
        cor, txt, icon = "card-green", "text-green", "fa-circle-check"
    
    return tags.div(
        tags.div(tags.div("Nível de Excelência", class_="exc-label"), tags.div(tags.i(class_=f"fa-solid {icon}"), "Status Geral", class_=f"exc-sub {txt}")), 
        tags.div(tags.span(str(media), class_=f"exc-value {txt}"), tags.span("%", style="font-size: 24px; color: #999;")), 
        class_=f"excellence-card {cor}"
    )

def lista_kpis_ui(lista_dados, ordem):
    """Gera a lista de cards/KPIs ordenada."""
    if not lista_dados: return tags.div("Sem dados para exibir.", style="padding: 20px; color: #666;")
    
    lista_final = sorted(lista_dados, key=lambda x: x['score'], reverse=(ordem == "desc"))
    html = []
    for item in lista_final:
        html.append(tags.div(
            tags.span(item['peso_info']['label'], class_=f"badge-weight {item['peso_info']['class']}"), 
            tags.div(item['eixo'], class_="kpi-title"), 
            tags.div(str(item['score']), class_="kpi-score"), 
            tags.div(tags.i(class_=f"fa-solid {item['icon']}"), "Pontuação", class_="kpi-footer"), 
            class_=f"kpi-card {item['class']}"
        ))
    return tags.div(html, class_="scroll-container")

def criar_filtro_simples(prefixo):
    """Cria o filtro padrão (Unidade) para Inst e Cursos."""
    return tags.div(
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

def criar_filtro_disciplinas():
    """Cria o filtro complexo em cascata para Disciplinas."""
    return tags.div(
        tags.div(
            tags.div(
                tags.label("Setor", style="font-weight: 500; font-size: 12px;"),
                ui.input_select("disc_setor", label=None, choices=[], width="100%"),
                style="flex: 1;"
            ),
            tags.div(
                tags.label("Departamento", style="font-weight: 500; font-size: 12px;"),
                ui.input_select("disc_depto", label=None, choices=[], width="100%"),
                style="flex: 1;"
            ),
            style="display:flex; gap: 15px; width: 100%;"
        ),
        tags.div(
            tags.div(
                tags.label("Curso", style="font-weight: 500; font-size: 12px;"),
                ui.input_select("disc_curso", label=None, choices=[], width="100%"),
                style="flex: 1;"
            ),
            tags.div(
                tags.label("Disciplina", style="font-weight: 500; font-size: 12px;"),
                ui.input_select("disc_disciplina", label=None, choices=[], width="100%"),
                style="flex: 1;"
            ),
            style="display:flex; gap: 15px; width: 100%; margin-top: 10px;"
        ),
        tags.div(
            ui.input_action_button("disc_btn_filtrar", "Atualizar Dados", class_="btn-primary"),
            style="padding-top: 15px;"
        ),
        class_="filter-bar",
        style="flex-direction: column; align-items: stretch;"
    )