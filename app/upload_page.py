# upload_page.py
from shiny import ui
from shiny.ui import tags

def criar_pagina_upload():
    """Cria a página completa de upload de dados."""
    return tags.div(
        tags.h2("Upload de Dados", class_="page-title"),
        
        ui.card(
            ui.h4("Carregar dados (Upload de Excel UFPR)", class_="mb-3"),
            ui.p("Envie um arquivo Excel no formato padrão para atualizar o banco de dados."),
            
            # Container para status/feedback
            ui.output_text("status_ingestao"),
            
            ui.input_file(
                "upload_excel",
                "Escolher arquivo Excel (.xlsx)",
                accept=[".xlsx"],
                multiple=False
            ),
            
            ui.br(),
            
            ui.input_action_button(
                "processar_excel",
                "Processar Dados",
                class_="btn btn-primary"
            ),
            
            ui.br(), ui.br(),
            
            ui.input_action_button(
                "baixar_pdf",
                "Baixar instruções (PDF)",
                class_="btn btn-secondary"
            ),
            
            ui.br(),
            
            style="padding: 30px; background: white; border-radius: 10px; max-width: 800px; margin: 0 auto;"
        ),
        
        # Seção de informações sobre o formato do arquivo
        ui.card(
            ui.h5("Formato do Arquivo Excel", class_="mb-3"),
            tags.ul(
                tags.li("O arquivo deve conter as seguintes abas:"),
                tags.ul(
                    tags.li(tags.code("dCurso"), " - Informações dos cursos"),
                    tags.li(tags.code("dDisciplina"), " - Informações das disciplinas"),
                    tags.li(tags.code("dPergunta"), " - Catálogo de perguntas"),
                    tags.li(tags.code("dTipoPergunta"), " - Tipos de perguntas"),
                    tags.li(tags.code("dUnidade"), " - Unidades administrativas"),
                    tags.li(tags.code("dProfessor"), " - Professores"),
                    tags.li(tags.code("fAvaliacao"), " - Fato das avaliações"),
                ),
                style="padding-left: 20px;"
            ),
            ui.p("Cada aba deve conter as colunas específicas conforme o modelo disponível para download."),
            style="margin-top: 20px; padding: 20px; background: #f8f9fa;"
        )
    )