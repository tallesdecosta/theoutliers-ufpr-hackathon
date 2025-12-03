import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from shiny import App, ui, reactive, render
from shiny.ui import tags
from pathlib import Path



# --- CONFIGURAÇÃO VISUAL (MATPLOTLIB) ---
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Roboto', 'Arial', 'Helvetica', 'sans-serif']
plt.rcParams['text.color'] = '#333333'
plt.rcParams['axes.labelcolor'] = '#333333'
plt.rcParams['xtick.color'] = '#333333'
plt.rcParams['ytick.color'] = '#333333'



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
