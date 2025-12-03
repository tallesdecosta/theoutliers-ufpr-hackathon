from shiny import ui
from shiny.ui import tags

def get_home_content():
    return tags.div(
        tags.h2("Apresentação dos Resultados", class_="page-title"),
        
        # Introdução Geral
        tags.div(
            tags.p(
                "Bem-vindo à ferramenta de visualização de dados da Avaliação Institucional da UFPR. ",
                "Este painel foi desenvolvido para democratizar o acesso aos resultados das pesquisas conduzidas pela ",
                tags.strong("Comissão Própria de Avaliação (CPA)"),
                ", permitindo que a comunidade acadêmica compreenda o desempenho da instituição em suas diversas dimensões.",
                style="font-size: 16px; color: #444; margin-bottom: 30px;"
            )
        ),

        # Grid de Informações
        ui.layout_column_wrap(
            # Card 1: O que é o SINAES
            tags.div(
                tags.div(tags.i(class_="fa-solid fa-scale-balanced"), "Contexto Legal (SINAES)", class_="info-title"),
                tags.div(
                    "A avaliação segue as diretrizes do Sistema Nacional de Avaliação da Educação Superior (Lei nº 10.861/2004). ",
                    "O objetivo é promover a melhoria da qualidade do ensino, da pesquisa e da extensão, além da responsabilidade social da instituição.",
                    class_="info-text"
                ),
                class_="info-box"
            ),

            # Card 2: Metodologia de Pontuação
            tags.div(
                tags.div(tags.i(class_="fa-solid fa-chart-pie"), "Como ler os Dados", class_="info-title"),
                tags.div(
                    "Os índices de satisfação variam de ", tags.strong("0 a 100"), " e representam a taxa de concordância.",
                    tags.br(), tags.br(),
                    tags.ul(
                        tags.li(tags.strong("Concordo/Sim:"), " Contribui para aumentar a nota (100%)."),
                        tags.li(tags.strong("Neutro/Desconheço:"), " Contribui parcialmente (50%)."),
                        tags.li(tags.strong("Discordo/Não:"), " Reduz a nota (0%)."),
                        style="padding-left: 20px; margin: 0;"
                    ),
                    class_="info-text"
                ),
                class_="info-box"
            ),

            # Card 3: Navegação
            tags.div(
                tags.div(tags.i(class_="fa-solid fa-location-arrow"), "Navegação", class_="info-title"),
                tags.div(
                    "Utilize o menu lateral para filtrar os resultados:",
                    tags.br(), tags.br(),
                    tags.strong("Institucional:"), " Visão macro por Campus e Unidades Administrativas.", tags.br(),
                    tags.strong("Cursos:"), " Avaliação específica por cursos de graduação.", tags.br(),
                    tags.strong("Disciplinas:"), " Detalhamento por departamento e oferta acadêmica.",
                    class_="info-text"
                ),
                class_="info-box"
            ),
            width=1/3
        ),

        tags.br(),

        # Seção dos 5 Eixos (Pode ser componentizada se desejar, mas deixei aqui por ser estático)
        tags.div(
            tags.h4("Eixos Avaliativos do SINAES", style="color: #004b8d; margin-bottom: 20px; font-weight: 700;"),
            tags.div(
                *[tags.div(tags.div(str(i), class_="eixo-icon"), tags.span(nome), class_="eixo-item") 
                  for i, nome in enumerate(["Planejamento e Avaliação Institucional", "Desenvolvimento Institucional", "Políticas Acadêmicas", "Políticas de Gestão", "Infraestrutura Física"], start=1)],
                style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: space-between; background: #fff; padding: 20px; border-radius: 8px; border-left: 5px solid #004b8d;"
            )
        )
    )