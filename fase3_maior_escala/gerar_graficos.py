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


def _arquivo_mais_recente(prefixo):
    """Retorna o arquivo JSON mais recente com o prefixo dado."""
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

# Tamanho das figuras
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
        tamanho_instancia = r.get("n_alimentos") or r.get("n_itens")
        tempo = r["tempo_medio_ms"]
        desvio = r["desvio_ms"]
        if solver not in serie:
            serie[solver] = {"tamanho": [], "tempo": [], "desvio": []}
        serie[solver]["tamanho"].append(tamanho_instancia)
        serie[solver]["tempo"].append(tempo)
        serie[solver]["desvio"].append(desvio)

    for solver in serie:
        ordem = sorted(range(len(serie[solver]["tamanho"])), key=lambda i: serie[solver]["tamanho"][i])
        serie[solver]["tamanho"] = [serie[solver]["tamanho"][i] for i in ordem]
        serie[solver]["tempo"]   = [serie[solver]["tempo"][i]   for i in ordem]
        serie[solver]["desvio"]  = [serie[solver]["desvio"][i]  for i in ordem]
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
    ax.legend(
        loc="upper left",
        frameon=True,
        framealpha=0.9,
        fontsize=9,
        ncol=4,
    )


def grafico_linha(serie, titulo_eixo_x, titulo_eixo_y, nome_arquivo, rotulos_n=None):
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

    ax.set_xlabel(titulo_eixo_x, fontsize=10)
    ax.set_ylabel(titulo_eixo_y, fontsize=10)

    if rotulos_n:
        ax.set_xticks(rotulos_n)
        ax.set_xticklabels([str(n) for n in rotulos_n])

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


def grafico_barras_comparativo(dados_pl, dados_pi_t1, dados_pi_t2, nome_arquivo):
    """Barras lado a lado comparando PL vs PI tipo 1 vs PI tipo 2 a 1000 elementos."""
    estilo_base()
    solvers = ["GLPK", "HIGHS", "SCIP", "CBC"]
    posicoes = np.arange(len(solvers))
    largura = 0.25

    def tempo_a_1000(serie):
        tempos = {}
        for solver, dados in serie.items():
            if 1000 in dados["tamanho"]:
                indice = dados["tamanho"].index(1000)
                tempos[solver] = dados["tempo"][indice]
        return tempos

    t_pl    = tempo_a_1000(dados_pl)
    t_pi_t1 = tempo_a_1000(dados_pi_t1)
    t_pi_t2 = tempo_a_1000(dados_pi_t2)

    tempos_pl    = [t_pl.get(solver, 0)    for solver in solvers]
    tempos_pi_t1 = [t_pi_t1.get(solver, 0) for solver in solvers]
    tempos_pi_t2 = [t_pi_t2.get(solver, 0) for solver in solvers]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar(posicoes - largura, tempos_pl,    largura, label="Dieta (PL)",          color="#4e79a7", alpha=0.85)
    ax.bar(posicoes,           tempos_pi_t1, largura, label="Mochila tipo 1 (PI)", color="#f28e2b", alpha=0.85)
    ax.bar(posicoes + largura, tempos_pi_t2, largura, label="Mochila tipo 2 (PI)", color="#76b7b2", alpha=0.85)

    ax.set_ylabel("tempo médio (ms)", fontsize=10)
    ax.set_xticks(posicoes)
    ax.set_xticklabels(solvers)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.0f ms"))
    ax.legend(frameon=True, framealpha=0.9, fontsize=9)
    fig.tight_layout()
    salvar(fig, nome_arquivo)


def main():
    print("Gerando gráficos do benchmark...\n")

    dieta   = carregar_json(_arquivo_mais_recente("dieta_grande"))
    mochila = carregar_json(_arquivo_mais_recente("mochila_grande"))

    ns_dieta   = [100, 200, 500, 1000]
    ns_mochila = [100, 200, 500, 1000]

    serie_dieta = extrair_serie(dieta, lambda r: True)
    serie_mochila_t1 = extrair_serie(mochila, lambda r: r.get("tipo") == "uncorrelated")
    serie_mochila_t2 = extrair_serie(mochila, lambda r: r.get("tipo") == "weakly_correlated")

    # Gráfico 1: escalabilidade da dieta (PL)
    grafico_linha(
        serie_dieta,
        titulo_eixo_x="número de alimentos (n)",
        titulo_eixo_y="tempo médio (ms)",
        nome_arquivo="dieta_escalabilidade.png",
        rotulos_n=ns_dieta,
    )

    # Gráfico 2: desvio padrão da dieta (PL)
    grafico_barras_desvio(
        serie_dieta,
        titulo_eixo_x="número de alimentos (n)",
        nome_arquivo="dieta_desvio.png",
        rotulos_n=ns_dieta,
    )

    # Gráfico 3: escalabilidade da mochila tipo 1 (PI - não correlacionado)
    grafico_linha(
        serie_mochila_t1,
        titulo_eixo_x="número de itens (n)",
        titulo_eixo_y="tempo médio (ms)",
        nome_arquivo="mochila_tipo1_escalabilidade.png",
        rotulos_n=ns_mochila,
    )

    # Gráfico 4: desvio padrão da mochila tipo 1 (PI - não correlacionado)
    grafico_barras_desvio(
        serie_mochila_t1,
        titulo_eixo_x="número de itens (n)",
        nome_arquivo="mochila_tipo1_desvio.png",
        rotulos_n=ns_mochila,
    )

    # Gráfico 5: escalabilidade da mochila tipo 2 (PI - frac. correlacionado)
    grafico_linha(
        serie_mochila_t2,
        titulo_eixo_x="número de itens (n)",
        titulo_eixo_y="tempo médio (ms)",
        nome_arquivo="mochila_tipo2_escalabilidade.png",
        rotulos_n=ns_mochila,
    )

    # Gráfico 6: desvio padrão da mochila tipo 2 (PI - frac. correlacionado)
    grafico_barras_desvio(
        serie_mochila_t2,
        titulo_eixo_x="número de itens (n)",
        nome_arquivo="mochila_tipo2_desvio.png",
        rotulos_n=ns_mochila,
    )

    # Gráfico 7: comparativo PL vs PI tipo 1 vs PI tipo 2 a 1000 elementos
    grafico_barras_comparativo(
        serie_dieta,
        serie_mochila_t1,
        serie_mochila_t2,
        nome_arquivo="comparativo_pl_pi_1000.png",
    )

    print(f"\n7 gráficos gerados em: {PASTA_SAIDA}/")
    print("\nNomes dos arquivos para o LaTeX:")
    arquivos = [
        "dieta_escalabilidade.png",
        "dieta_desvio.png",
        "mochila_tipo1_escalabilidade.png",
        "mochila_tipo1_desvio.png",
        "mochila_tipo2_escalabilidade.png",
        "mochila_tipo2_desvio.png",
        "comparativo_pl_pi_1000.png",
    ]
    for a in arquivos:
        print(f"  {a}")


if __name__ == "__main__":
    main()