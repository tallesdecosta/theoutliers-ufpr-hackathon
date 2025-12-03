from shiny import module, ui, render, reactive
from shiny.ui import tags
from graphs import *
from components import card_excelencia_ui, lista_kpis_ui

# --- UI GENÉRICA DO MÓDULO ---
@module.ui
def dashboard_ui(titulo, filtro_customizado_ui):
    return tags.div(
        tags.h2(titulo, class_="page-title"),

        # BLOCO DE FILTRO (Injetado)
        filtro_customizado_ui,

        # Card Excelência
        ui.output_ui("card_excelencia"),

        # Título + Seleção cards/radar
        tags.div(
            tags.div(
                tags.h5("Detalhamento por Eixos", style="margin:0; margin-right: 20px; color: #666;"),
                ui.input_radio_buttons(
                    "view_mode",
                    label=None,
                    choices={"cards": "Cards", "radar": "Gráfico Radar"},
                    selected="cards",
                    inline=True
                ),
                class_="view-toggles"
            ),

            # Ordenação
            ui.panel_conditional(
                "input.view_mode === 'cards'",
                ui.input_radio_buttons(
                    "sort_order",
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
            "input.view_mode === 'cards'",
            ui.output_ui("lista_cards")
        ),

        # Gráfico radar
        ui.panel_conditional(
            "input.view_mode === 'radar'",
            tags.div(
                ui.output_plot("grafico_radar", width="100%", height="100%"),
                class_="radar-container"
            )
        ),

        tags.hr(),
        tags.h5("Visão Geral das Respostas", style="margin-bottom: 20px; color: #666;"),

        # GRADE DE GRÁFICOS
        ui.layout_column_wrap(
            tags.div(
                tags.div("Status Geral das Respostas", class_="chart-title"),
                ui.output_plot("grafico_donut", width="100%", height="100%"),
                class_="chart-box"
            ),
            tags.div(
                tags.div("Destaques (Top/Bottom)", class_="chart-title"),
                ui.output_plot("grafico_barras", width="100%", height="100%"),
                class_="chart-box"
            ),
            tags.div(
                tags.div("Consistência das Avaliações", class_="chart-title"),
                ui.output_plot("grafico_dist", width="100%", height="100%"),
                class_="chart-box"
            ),
            width=1/3,
        ),
        tags.br(), tags.br()
    )

# --- SERVER GENÉRICO DO MÓDULO ---
@module.server
def dashboard_server(input, output, session, dados_getter, donut_getter, barras_getter, dist_getter):
    
    @render.ui
    def card_excelencia(): 
        media, _ = dados_getter()
        return card_excelencia_ui(media)
    
    @render.ui
    def lista_cards(): 
        _, lista = dados_getter()
        return lista_kpis_ui(lista, input.sort_order())
    
    @render.plot
    def grafico_radar(): 
        _, lista = dados_getter()
        return criar_plot_radar(lista)
    
    @render.plot
    def grafico_donut(): return criar_plot_donut(donut_getter())
    
    @render.plot
    def grafico_barras(): return criar_plot_barras(barras_getter())
    
    @render.plot
    def grafico_dist(): return criar_plot_distribuicao(dist_getter())