# Problema da Mochila — Fase 3: Instâncias de Maior Porte com Limite de Tempo
#
# Lê instâncias no formato de Pisinger disponíveis em: https://github.com/dnlfm/knapsack-01-instances
#
# Formato dos arquivos:
#   Linha 1:        n  capacidade
#   Linhas 2..n+1:  valor  peso
#   Última linha:   solução ótima (vetor binário separado por espaços)
#
# Tipos de instância avaliados:
#   Tipo 1 — não correlacionado (uncorrelated)
#   Tipo 2 — fracamente correlacionado (weakly correlated)
#   Tipo 3 — fortemente correlacionado (strongly correlated)
#
# Referência: Pisinger, D. (2005). Where are the hard knapsack problems?
# Computers & Operations Research, 32(9), 2271–2284.

import json
import os
import statistics
import time
from datetime import datetime

import pyomo.environ as pyo

# ==== CONFIGURAÇÃO ====
PASTA_INSTANCIAS = os.path.join(
    os.path.dirname(__file__),
    "instancias",
    "knapsack-01-instances",
    "pisinger_instances_01_KP",
    "large_scale",
)

PASTA_RESULTADOS = os.path.join(os.path.dirname(__file__), "resultados")

N_REPETICOES = 10
SOLVERS = ["glpk", "cbc", "highs", "scip"]
TEMPO_LIMITE = 5  # segundos

INSTANCIAS_SELECIONADAS = [
    # Tipo 1 — não correlacionado
    "knapPI_1_100_1000_1",
    "knapPI_1_500_1000_1",
    "knapPI_1_1000_1000_1",
    "knapPI_1_2000_1000_1",
    "knapPI_1_5000_1000_1",
    "knapPI_1_10000_1000_1",
    # Tipo 2 — fracamente correlacionado
    "knapPI_2_100_1000_1",
    "knapPI_2_500_1000_1",
    "knapPI_2_1000_1000_1",
    "knapPI_2_2000_1000_1",
    "knapPI_2_5000_1000_1",
    "knapPI_2_10000_1000_1",
    # Tipo 3 — fortemente correlacionado
    "knapPI_3_100_1000_1",
    "knapPI_3_500_1000_1",
    "knapPI_3_1000_1000_1",
    "knapPI_3_2000_1000_1",
    "knapPI_3_5000_1000_1",
    "knapPI_3_10000_1000_1",
]


def ler_instancia(caminho):
    with open(caminho, "r") as f:
        linhas = f.read().split()

    n_itens = int(linhas[0])
    capacidade = int(linhas[1])

    valores = []
    pesos = []
    pos = 2
    for _ in range(n_itens):
        valores.append(int(linhas[pos]))
        pesos.append(int(linhas[pos + 1]))
        pos += 2

    otimo = []
    if pos < len(linhas):
        otimo = [int(x) for x in linhas[pos:pos + n_itens]]

    return n_itens, capacidade, valores, pesos, otimo


def calcular_valor_otimo(valores, otimo):
    if not otimo:
        return None
    return sum(v for v, x in zip(valores, otimo) if x == 1)


def criar_modelo(n_itens, capacidade, valores, pesos):
    itens = list(range(n_itens))
    modelo = pyo.ConcreteModel()
    modelo.x = pyo.Var(itens, domain=pyo.Binary)

    modelo.objetivo = pyo.Objective(
        expr=sum(valores[j] * modelo.x[j] for j in itens),
        sense=pyo.maximize,
    )

    modelo.capacidade = pyo.Constraint(
        expr=sum(pesos[j] * modelo.x[j] for j in itens) <= capacidade
    )
    return modelo


def criar_solver(nome_solver):
    solver = pyo.SolverFactory(nome_solver)
    if solver is None or not solver.available(False):
        return None
    return solver


def resolver_instancia(nome_solver, n_itens, capacidade, valores, pesos):
    modelo = criar_modelo(n_itens, capacidade, valores, pesos)
    solver = criar_solver(nome_solver)

    if solver is None:
        return "solver_indisponivel", None, None

    opcoes = {}
    if nome_solver == "glpk":
        opcoes["tmlim"] = TEMPO_LIMITE
    elif nome_solver == "cbc":
        opcoes["sec"] = TEMPO_LIMITE
    elif nome_solver == "highs":
        opcoes["time_limit"] = TEMPO_LIMITE
    elif nome_solver == "scip":
        opcoes["limits/time"] = TEMPO_LIMITE

    try:
        inicio = time.perf_counter()
        resultado = solver.solve(modelo, options=opcoes)
        fim = time.perf_counter()
    except Exception as e:
        return "erro_execucao", None, None

    status = str(resultado.solver.termination_condition)
    tempo_ms = round((fim - inicio) * 1000, 3)

    try:
        raw = pyo.value(modelo.objetivo)
        valor_total = round(raw) if raw is not None else None
    except Exception:
        valor_total = None

    return status, valor_total, tempo_ms


def executar_n_vezes(nome_solver, n_itens, capacidade, valores, pesos):
    resolver_instancia(nome_solver, n_itens, capacidade, valores, pesos)  # warm-up

    tempos = []
    valor_total = None
    execucoes_otimas = 0
    status = None

    for _ in range(N_REPETICOES):
        status_exec, valor, tempo = resolver_instancia(
            nome_solver, n_itens, capacidade, valores, pesos
        )
        if tempo is not None:
            tempos.append(tempo)
        if status_exec == "optimal":
            execucoes_otimas += 1
            if valor_total is None:
                valor_total = valor
        elif valor is not None:
            # Guarda a melhor solução parcial encontrada antes do timeout
            if valor_total is None or valor > valor_total:
                valor_total = valor
        if status is None:
            status = status_exec

    if status is None and tempos:
        status = status_exec

    media = round(statistics.mean(tempos), 3) if tempos else None
    desvio = round(statistics.stdev(tempos), 3) if len(tempos) > 1 else 0.0

    return status, valor_total, execucoes_otimas, tempos, media, desvio


def exibir_resultado(solver, status, valor_total, valor_otimo, execucoes_otimas, media, desvio, n_itens):
    if valor_total is not None and valor_otimo is not None:
        if valor_total == valor_otimo:
            qualidade = "gap 0.00%"
        else:
            gap = round((valor_otimo - valor_total) / valor_otimo * 100, 2)
            qualidade = f"gap {gap:.2f}%"
    elif valor_total is None:
        qualidade = "sem solução"
    else:
        qualidade = "—"

    estab_str = f"{execucoes_otimas}/{N_REPETICOES} ótimas"
    print(f"  {solver:<8} | status: {status:<20} | valor: {str(valor_total):<8} "
          f"| {qualidade:<16} | tempo: {str(media)+'ms':<10} ± {desvio}ms | {estab_str}")


def salvar_resultados(todos_resultados):
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    caminho_json = os.path.join(PASTA_RESULTADOS, f"mochila_grande_{timestamp}.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(todos_resultados, f, ensure_ascii=False, indent=2)

    print(f"\nResultados salvos em: {PASTA_RESULTADOS}")


def classificar_tipo(nome_arquivo):
    tipos = {"1": "uncorrelated", "2": "weakly_correlated", "3": "strongly_correlated"}
    partes = nome_arquivo.split("_")
    if len(partes) >= 2:
        return tipos.get(partes[1], "desconhecido")
    return "desconhecido"


def executar():
    print("=" * 70)
    print("PROBLEMA DA MOCHILA — Fase 3: Instâncias de Maior Porte")
    print("=" * 70)
    print(f"Repetições por solver por instância: {N_REPETICOES} (+ 1 warm-up)")
    print(f"Limite de tempo por execução: {TEMPO_LIMITE}s")
    print(f"Tipos: não correlacionado (T1), fracamente correlacionado (T2), "
          f"fortemente correlacionado (T3)")
    print(f"Instâncias: {len(INSTANCIAS_SELECIONADAS)}")
    print()

    todos_resultados = []

    for nome in INSTANCIAS_SELECIONADAS:
        caminho = os.path.join(PASTA_INSTANCIAS, nome)

        if not os.path.exists(caminho):
            print(f"[AVISO] Arquivo não encontrado: {nome}")
            continue

        n_itens, capacidade, valores, pesos, otimo_vetor = ler_instancia(caminho)
        valor_otimo = calcular_valor_otimo(valores, otimo_vetor)
        tipo = classificar_tipo(nome)

        print(f"\nInstância: {nome}")
        print(f"  Tipo: {tipo} | Itens: {n_itens} | Capacidade: {capacidade} | Ótimo: {valor_otimo}")
        print(f"  {'-'*65}")

        for nome_solver in SOLVERS:
            status, valor_total, execucoes_otimas, tempos, media, desvio = executar_n_vezes(
                nome_solver, n_itens, capacidade, valores, pesos
            )
            exibir_resultado(
                nome_solver.upper(), status, valor_total,
                valor_otimo, execucoes_otimas, media, desvio, n_itens
            )

            gap_pct = None
            if valor_total is not None and valor_otimo is not None and valor_otimo > 0:
                gap_pct = round((valor_otimo - valor_total) / valor_otimo * 100, 2)

            todos_resultados.append({
                "instancia": nome,
                "tipo": tipo,
                "n_itens": n_itens,
                "solver": nome_solver.upper(),
                "status": status,
                "valor_encontrado": valor_total,
                "valor_otimo": valor_otimo,
                "gap_pct": gap_pct,
                "tempo_medio_ms": media,
                "desvio_ms": desvio,
                "execucoes_otimas": execucoes_otimas,
                "n_repeticoes": N_REPETICOES,
                "tempos_individuais": tempos,
            })

    salvar_resultados(todos_resultados)


if __name__ == "__main__":
    executar()
