# Gerador de gráficos para os resultados do benchmark
#
# Lê os arquivos JSON gerados pelos scripts de benchmark e produz gráficos em PNG.
#
# Uso:
#   python gerar_graficos.py
#
# Os arquivos PNG são salvos na pasta "graficos/" criada automaticamente.

import glob
import json
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ==== CONFIGURAÇÃO ====

_BASE = os.path.dirname(os.path.abspath(__file__))
PASTA_RESULTADOS = os.path.join(_BASE, "resultados")
PASTA_SAIDA = os.path.join(_BASE, "graficos")

TEMPO_LIMITE_MS = 5000  # limite de tempo em ms (para linha de referência nos gráficos)


def _arquivo_mais_recente(prefixo):
    candidatos = sorted(glob.glob(os.path.join(PASTA_RESULTADOS, f"{prefixo}_*.json")))
    if not candidatos:
        raise FileNotFoundError(
            f"Nenhum arquivo encontrado em '{PASTA_RESULTADOS}' com prefixo '{prefixo}_'.\n"
            f"Execute o benchmark correspondente antes de gerar os gráficos."
        )
    return candidatos[-1]


CORES = {
    "GLPK":  "#1a9e58",
    "CBC":   "#d95f02",
    "HIGHS": "#1f77b4",
    "SCIP":  "#7b5ea7",
}

MARCADORES = {
    "GLPK":  "o",
    "CBC":   "s",
    "HIGHS": "^",
    "SCIP":  "D",
}

FIGSIZE = (7, 4)
DPI = 150


def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def extrair_serie(dados, filtro_func):
    """Agrupa tempos de execução por solver, filtrando os dados de entrada."""
    serie = {}
    for r in dados:
        if not filtro_func(r):
            continue
        solver = r["solver"]
        tamanho = r.get("n_alimentos") or r.get("n_itens")
        tempo = r["tempo_medio_ms"]
        desvio = r["desvio_ms"]
        if solver not in serie:
            serie[solver] = {"tamanho": [], "tempo": [], "desvio": []}
        serie[solver]["tamanho"].append(tamanho)
        serie[solver]["tempo"].append(tempo)
        serie[solver]["desvio"].append(desvio)

    for solver in serie:
        ordem = sorted(range(len(serie[solver]["tamanho"])), key=lambda i: serie[solver]["tamanho"][i])
        serie[solver]["tamanho"] = [serie[solver]["tamanho"][i] for i in ordem]
        serie[solver]["tempo"]   = [serie[solver]["tempo"][i]   for i in ordem]
        serie[solver]["desvio"]  = [serie[solver]["desvio"][i]  for i in ordem]
    return serie


def extrair_serie_otimalidade(dados, filtro_func):
    """Agrupa taxa de otimalidade (% de runs com status 'optimal') por solver."""
    serie = {}
    for r in dados:
        if not filtro_func(r):
            continue
        solver = r["solver"]
        tamanho = r.get("n_alimentos") or r.get("n_itens")
        n_rep = r.get("n_repeticoes", 10)
        n_otimas = r.get("execucoes_otimas", 0)
        taxa = round(n_otimas / n_rep * 100, 1) if n_rep > 0 else 0.0
        if solver not in serie:
            serie[solver] = {"tamanho": [], "taxa": []}
        serie[solver]["tamanho"].append(tamanho)
        serie[solver]["taxa"].append(taxa)

    for solver in serie:
        ordem = sorted(range(len(serie[solver]["tamanho"])), key=lambda i: serie[solver]["tamanho"][i])
        serie[solver]["tamanho"] = [serie[solver]["tamanho"][i] for i in ordem]
        serie[solver]["taxa"]    = [serie[solver]["taxa"][i]    for i in ordem]
    return serie


def estilo_base():
    plt.rcParams.update({
        "font.family":     "serif",
        "font.size":       10,
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.grid":         True,
        "grid.linestyle":    "--",
        "grid.alpha":        0.4,
        "figure.facecolor":  "white",
        "axes.facecolor":    "white",
    })


def salvar(fig, nome):
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    caminho = os.path.join(PASTA_SAIDA, nome)
    fig.savefig(caminho, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Salvo: {caminho}")


def legenda_fora(ax):
    ax.legend(loc="upper left", frameon=True, framealpha=0.9, fontsize=9, ncol=4)


def grafico_linha(serie, titulo_eixo_x, titulo_eixo_y, nome_arquivo, rotulos_n=None, linha_limite=False, rotacao_xticks=0):
    """Gráfico de linhas com barras de erro para escalabilidade."""
    estilo_base()
    fig, ax = plt.subplots(figsize=FIGSIZE)

    for solver, dados in serie.items():
        cor = CORES.get(solver, "gray")
        marc = MARCADORES.get(solver, "o")
        ax.errorbar(
            dados["tamanho"], dados["tempo"],
            yerr=dados["desvio"],
            label=solver,
            color=cor,
            marker=marc,
            linewidth=1.8,
            markersize=5,
            capsize=3,
            capthick=1,
        )

    if linha_limite:
        ax.axhline(y=TEMPO_LIMITE_MS, color="red", linestyle="--", linewidth=1.2,
                   alpha=0.7, label=f"limite {TEMPO_LIMITE_MS//1000}s")

    ax.set_xlabel(titulo_eixo_x, fontsize=10)
    ax.set_ylabel(titulo_eixo_y, fontsize=10)

    if rotulos_n:
        ax.set_xticks(rotulos_n)
        ax.set_xticklabels([str(n) for n in rotulos_n], rotation=45, ha="right")

    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.0f ms"))
    legenda_fora(ax)
    fig.tight_layout()
    salvar(fig, nome_arquivo)


def grafico_barras_desvio(serie, titulo_eixo_x, nome_arquivo, rotulos_n):
    """Gráfico de barras agrupadas mostrando o desvio padrão."""
    estilo_base()
    solvers = list(serie.keys())
    tamanhos = rotulos_n
    posicoes = np.arange(len(tamanhos))
    largura = 0.18
    offsets = np.linspace(-(len(solvers)-1)/2, (len(solvers)-1)/2, len(solvers)) * largura

    fig, ax = plt.subplots(figsize=FIGSIZE)

    for i, solver in enumerate(solvers):
        desvios = []
        for tam in tamanhos:
            indice = serie[solver]["tamanho"].index(tam) if tam in serie[solver]["tamanho"] else None
            desvios.append(serie[solver]["desvio"][indice] if indice is not None else 0)
        ax.bar(
            posicoes + offsets[i], desvios,
            width=largura,
            label=solver,
            color=CORES.get(solver, "gray"),
            alpha=0.85,
        )

    ax.set_xlabel(titulo_eixo_x, fontsize=10)
    ax.set_ylabel("desvio padrão (ms)", fontsize=10)
    ax.set_xticks(posicoes)
    ax.set_xticklabels([str(tam) for tam in tamanhos])
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f ms"))
    legenda_fora(ax)
    fig.tight_layout()
    salvar(fig, nome_arquivo)


def grafico_taxa_otimalidade(serie, titulo_eixo_x, nome_arquivo, rotulos_n=None):
    """Gráfico de linhas mostrando % de execuções que atingiram status 'optimal'."""
    estilo_base()
    fig, ax = plt.subplots(figsize=FIGSIZE)

    for solver, dados in serie.items():
        cor = CORES.get(solver, "gray")
        marc = MARCADORES.get(solver, "o")
        ax.plot(
            dados["tamanho"], dados["taxa"],
            label=solver,
            color=cor,
            marker=marc,
            linewidth=1.8,
            markersize=6,
        )

    ax.set_xlabel(titulo_eixo_x, fontsize=10)
    ax.set_ylabel("execuções com status ótimo (%)", fontsize=10)
    ax.set_ylim(-5, 110)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.0f%%"))

    if rotulos_n:
        ax.set_xticks(rotulos_n)
        ax.set_xticklabels([str(n) for n in rotulos_n], rotation=45, ha="right")

    legenda_fora(ax)
    fig.tight_layout()
    salvar(fig, nome_arquivo)


def grafico_barras_comparativo(dados_pl_t1, dados_pl_t2, dados_pl_t3,
                               dados_pi_t1, dados_pi_t2, dados_pi_t3,
                               nome_arquivo, tamanho_ref=1000):
    """Barras lado a lado comparando PL (3 tipos) vs PI (3 tipos) a um tamanho de referência."""
    estilo_base()
    solvers = ["GLPK", "HIGHS", "SCIP", "CBC"]
    posicoes = np.arange(len(solvers))
    largura = 0.13

    def tempo_em(serie, tam):
        tempos = {}
        for solver, dados in serie.items():
            if tam in dados["tamanho"]:
                tempos[solver] = dados["tempo"][dados["tamanho"].index(tam)]
        return tempos

    series = [
        (tempo_em(dados_pl_t1, tamanho_ref), "Dieta T1 — 10n (PL)",  "#4e79a7"),
        (tempo_em(dados_pl_t2, tamanho_ref), "Dieta T2 — 30n (PL)",  "#a0c4ff"),
        (tempo_em(dados_pl_t3, tamanho_ref), "Dieta T3 — 50n (PL)",  "#003f88"),
        (tempo_em(dados_pi_t1, tamanho_ref), "Mochila T1 (PI)",       "#f28e2b"),
        (tempo_em(dados_pi_t2, tamanho_ref), "Mochila T2 (PI)",       "#76b7b2"),
        (tempo_em(dados_pi_t3, tamanho_ref), "Mochila T3 (PI)",       "#e15759"),
    ]
    n = len(series)
    offsets = np.linspace(-(n - 1) / 2, (n - 1) / 2, n) * largura

    fig, ax = plt.subplots(figsize=(8, 4))
    for (dados, label, cor), offset in zip(series, offsets):
        valores = [dados.get(s, 0) for s in solvers]
        ax.bar(posicoes + offset, valores, largura, label=label, color=cor, alpha=0.85)

    ax.set_ylabel("tempo médio (ms)", fontsize=10)
    ax.set_xticks(posicoes)
    ax.set_xticklabels(solvers)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.0f ms"))
    ax.legend(frameon=True, framealpha=0.9, fontsize=8, ncol=2)
    fig.tight_layout()
    salvar(fig, nome_arquivo)


def main():
    print("Gerando gráficos do benchmark...\n")

    dieta   = carregar_json(_arquivo_mais_recente("dieta_grande"))
    mochila = carregar_json(_arquivo_mais_recente("mochila_grande"))

    ns_dieta    = [100, 500, 1000, 2000, 5000, 10000]
    ns_mochila  = [100, 500, 1000, 2000, 5000, 10000]

    serie_dieta_t1 = extrair_serie(dieta, lambda r: r.get("tipo") == "sparse")
    serie_dieta_t2 = extrair_serie(dieta, lambda r: r.get("tipo") == "medium")
    serie_dieta_t3 = extrair_serie(dieta, lambda r: r.get("tipo") == "dense")

    serie_mochila_t1 = extrair_serie(mochila, lambda r: r.get("tipo") == "uncorrelated")
    serie_mochila_t2 = extrair_serie(mochila, lambda r: r.get("tipo") == "weakly_correlated")
    serie_mochila_t3 = extrair_serie(mochila, lambda r: r.get("tipo") == "strongly_correlated")

    serie_otimalidade_dieta_t3   = extrair_serie_otimalidade(dieta,   lambda r: r.get("tipo") == "dense")
    serie_otimalidade_mochila_t3 = extrair_serie_otimalidade(mochila, lambda r: r.get("tipo") == "strongly_correlated")

    # Gráfico 1: escalabilidade da dieta tipo A (10 nutrientes)
    grafico_linha(
        serie_dieta_t1,
        titulo_eixo_x="número de alimentos (n)",
        titulo_eixo_y="tempo médio (ms)",
        nome_arquivo="dieta_tipo1_escalabilidade.png",
        rotulos_n=ns_dieta,
        linha_limite=True,
    )

    # Gráfico 2: desvio padrão da dieta tipo A
    grafico_barras_desvio(
        serie_dieta_t1,
        titulo_eixo_x="número de alimentos (n)",
        nome_arquivo="dieta_tipo1_desvio.png",
        rotulos_n=ns_dieta,
    )

    # Gráfico 3: escalabilidade da dieta tipo B (30 nutrientes)
    grafico_linha(
        serie_dieta_t2,
        titulo_eixo_x="número de alimentos (n)",
        titulo_eixo_y="tempo médio (ms)",
        nome_arquivo="dieta_tipo2_escalabilidade.png",
        rotulos_n=ns_dieta,
        linha_limite=True,
    )

    # Gráfico 4: desvio padrão da dieta tipo B
    grafico_barras_desvio(
        serie_dieta_t2,
        titulo_eixo_x="número de alimentos (n)",
        nome_arquivo="dieta_tipo2_desvio.png",
        rotulos_n=ns_dieta,
    )

    # Gráfico 5: escalabilidade da dieta tipo C (50 nutrientes)
    grafico_linha(
        serie_dieta_t3,
        titulo_eixo_x="número de alimentos (n)",
        titulo_eixo_y="tempo médio (ms)",
        nome_arquivo="dieta_tipo3_escalabilidade.png",
        rotulos_n=ns_dieta,
        linha_limite=True,
    )

    # Gráfico 6: desvio padrão da dieta tipo C
    grafico_barras_desvio(
        serie_dieta_t3,
        titulo_eixo_x="número de alimentos (n)",
        nome_arquivo="dieta_tipo3_desvio.png",
        rotulos_n=ns_dieta,
    )

    # Gráfico 7: taxa de otimalidade da dieta tipo C
    grafico_taxa_otimalidade(
        serie_otimalidade_dieta_t3,
        titulo_eixo_x="número de alimentos (n)",
        nome_arquivo="dieta_tipo3_otimalidade.png",
        rotulos_n=ns_dieta,
    )

    # Gráfico 8: escalabilidade da mochila tipo 1
    grafico_linha(
        serie_mochila_t1,
        titulo_eixo_x="número de itens (n)",
        titulo_eixo_y="tempo médio (ms)",
        nome_arquivo="mochila_tipo1_escalabilidade.png",
        rotulos_n=ns_mochila,
        linha_limite=True,
    )

    # Gráfico 9: desvio padrão da mochila tipo 1
    grafico_barras_desvio(
        serie_mochila_t1,
        titulo_eixo_x="número de itens (n)",
        nome_arquivo="mochila_tipo1_desvio.png",
        rotulos_n=ns_mochila,
    )

    # Gráfico 10: escalabilidade da mochila tipo 2
    grafico_linha(
        serie_mochila_t2,
        titulo_eixo_x="número de itens (n)",
        titulo_eixo_y="tempo médio (ms)",
        nome_arquivo="mochila_tipo2_escalabilidade.png",
        rotulos_n=ns_mochila,
        linha_limite=True,
    )

    # Gráfico 11: desvio padrão da mochila tipo 2
    grafico_barras_desvio(
        serie_mochila_t2,
        titulo_eixo_x="número de itens (n)",
        nome_arquivo="mochila_tipo2_desvio.png",
        rotulos_n=ns_mochila,
    )

    # Gráfico 12: escalabilidade da mochila tipo 3 (fortemente correlacionado)
    grafico_linha(
        serie_mochila_t3,
        titulo_eixo_x="número de itens (n)",
        titulo_eixo_y="tempo médio (ms)",
        nome_arquivo="mochila_tipo3_escalabilidade.png",
        rotulos_n=ns_mochila,
        linha_limite=True,
    )

    # Gráfico 13: desvio padrão da mochila tipo 3
    grafico_barras_desvio(
        serie_mochila_t3,
        titulo_eixo_x="número de itens (n)",
        nome_arquivo="mochila_tipo3_desvio.png",
        rotulos_n=ns_mochila,
    )

    # Gráfico 14: taxa de otimalidade — mochila tipo 3 (fortemente correlacionado)
    grafico_taxa_otimalidade(
        serie_otimalidade_mochila_t3,
        titulo_eixo_x="número de itens (n)",
        nome_arquivo="mochila_tipo3_otimalidade.png",
        rotulos_n=ns_mochila,
    )

    # Gráfico 15: comparativo PL (3 tipos) vs PI (3 tipos) a 10000 elementos
    grafico_barras_comparativo(
        serie_dieta_t1,
        serie_dieta_t2,
        serie_dieta_t3,
        serie_mochila_t1,
        serie_mochila_t2,
        serie_mochila_t3,
        nome_arquivo="comparativo_pl_pi_10000.png",
        tamanho_ref=10000,
    )

    print(f"\n15 gráficos gerados em: {PASTA_SAIDA}/")
    print("\nNomes dos arquivos para o LaTeX:")
    arquivos = [
        "dieta_tipo1_escalabilidade.png",
        "dieta_tipo1_desvio.png",
        "dieta_tipo2_escalabilidade.png",
        "dieta_tipo2_desvio.png",
        "dieta_tipo3_escalabilidade.png",
        "dieta_tipo3_desvio.png",
        "dieta_tipo3_otimalidade.png",
        "mochila_tipo1_escalabilidade.png",
        "mochila_tipo1_desvio.png",
        "mochila_tipo2_escalabilidade.png",
        "mochila_tipo2_desvio.png",
        "mochila_tipo3_escalabilidade.png",
        "mochila_tipo3_desvio.png",
        "mochila_tipo3_otimalidade.png",
        "comparativo_pl_pi_10000.png",
    ]
    for a in arquivos:
        print(f"  {a}")


if __name__ == "__main__":
    main()
