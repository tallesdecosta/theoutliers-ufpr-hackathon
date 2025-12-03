custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    /* O SELETOR GLOBAL ESTAVA QUEBRANDO OS ÍCONES. MANTIVE, MAS ADICIONEI A EXCEÇÃO ABAIXO */
    * { font-family: 'Roboto', sans-serif !important; }
    
    /* --- CORREÇÃO: Força a fonte de ícones a prevalecer sobre a Roboto --- */
    .fa-solid, .fas, .fa-regular, .far, .fa, .fa-brands { 
        font-family: "Font Awesome 6 Free" !important; 
    }
    
    html, body { margin: 0 !important; padding: 0 !important; width: 100%; height: 100%; overflow: hidden; background-color: #f4f6f9; }
    .container-fluid { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    .ufpr-header { 
        background-color: #004b8d; 
        color: white; 
        /* Removi height fixo para evitar quebra com a nova linha, ajustando pelo padding */
        display: flex; 
        flex-direction: column; /* Permite empilhar: Linha 1 (infos) e Linha 2 (traço) */
        justify-content: center;
        gap: 0px; 
        padding: 20px 60px; /* Ajustei levemente o padding vertical para acomodar a linha */
        width: 100%; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
        z-index: 1; 
        position: relative; 
    }
    h4 { font-weight: 700; font-size: 24px; margin: 0; }
    img { width: 100%; max-width: 120px; }
    .btn-reset { color: white !important; background: transparent !important; border: none !important; cursor: pointer !important; padding: 0 !important; margin: 0 !important; display: flex !important; align-items: center; }
    .menu-lateral { position: fixed; z-index: 99999; background-color: #fff; padding: 25px 55px; height: 100vh; width: 350px; display: none; box-shadow: 2px 0 10px rgba(0,0,0,0.2); flex-direction: column !important; }
    .btn-nav-custom { width: 100%; text-align: left; margin-bottom: 10px; background: transparent; border: none; color: #333; font-size: 18px; padding: 10px; border-bottom: 1px solid #eee; transition: 0.2s; border-radius: 5px; }
    .btn-nav-custom:hover { padding-left: 20px; background-color: #f5f5dc; color: #000; font-weight: 500; }
    .overlay-escura { background-color: black; position:fixed; top: 0; left:0; width: 100vw; height: 100vh; opacity: .5; z-index:999; display: none;}
    #btn_fechar { align-self: flex-end !important; background: transparent !important; border: none !important; font-size: 24px !important; color: #333 !important; }
    .conteudo-spa { padding: 30px 60px; height: calc(100vh - 80px); overflow-y: auto; background-color: #f8f9fa; width: 100%; }
    .page-title { 
    font-size: 24px; 
    color: #004b8d;           /* Cor do TEXTO "Visão Geral" */
    margin-bottom: 20px; 
    
    /* --- AQUI VOCÊ MUDA A LINHA --- */
    border-bottom: 1px solid rgba(0, 75, 141, 0.4);  /* Mude #ff0000 para a cor desejada */
    
    padding-bottom: 10px; 
    
    /* --- ISSO FAZ A LINHA PEGAR A LARGURA TODA --- */
    display: block;           /* Mudado de inline-block para block */
    width: 100%;              /* Garante que estique até o fim do container */
    
    font-weight: 700; 
}
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
    # ... (seu css anterior) ...
    .info-box { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); height: 100%; border-top: 4px solid #004b8d; }
    .info-title { font-size: 18px; font-weight: 700; color: #004b8d; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
    .info-text { font-size: 14px; color: #555; line-height: 1.6; }
    .eixo-item { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 14px; color: #444; }
    .eixo-icon { width: 30px; height: 30px; background: #e9ecef; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #004b8d; font-size: 12px; font-weight: bold; }
"""
