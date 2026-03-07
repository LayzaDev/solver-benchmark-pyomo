# Problema da Dieta — Programação Linear (PL)
#
# Objetivo: encontrar a combinação de alimentos de menor custo que
# satisfaça os requisitos nutricionais mínimos diários.

import csv
import json
import os
import statistics
import time
from datetime import datetime

import pyomo.environ as pyo

PASTA_RESULTADOS = os.path.join(os.path.dirname(__file__), "resultados")
N_REPETICOES = 10
SOLVERS = ["glpk", "cbc", "highs", "scip"]
TOLERANCIA_CUSTO = 1e-4

# ==== DADOS DO PROBLEMA ====
alimentos = [
    "Arroz", "Feijão", "Frango", "Brócolis", "Leite",
    "Ovo", "Batata", "Atum", "Cenoura", "Banana",
    "Pão Integral", "Queijo"
]

custo = {
    "Arroz": 1.50,
    "Feijão": 1.20,
    "Frango": 4.00,
    "Brócolis": 2.00,
    "Leite": 1.80,
    "Ovo": 0.80,
    "Batata": 1.00,
    "Atum": 3.50,
    "Cenoura": 1.10,
    "Banana": 0.90,
    "Pão Integral": 1.40,
    "Queijo": 2.50,
}

nutrientes = ["Calorias", "Proteína", "Carboidratos", "Gordura", "Fibra", "Cálcio"]

tabela_nutricional = {
    "Arroz": {"Calorias": 200, "Proteína": 4, "Carboidratos": 45, "Gordura": 1, "Fibra": 1, "Cálcio": 10},
    "Feijão": {"Calorias": 150, "Proteína": 10, "Carboidratos": 28, "Gordura": 1, "Fibra": 7, "Cálcio": 50},
    "Frango": {"Calorias": 250, "Proteína": 30, "Carboidratos": 0, "Gordura": 8, "Fibra": 0, "Cálcio": 15},
    "Brócolis": {"Calorias": 55, "Proteína": 4, "Carboidratos": 11, "Gordura": 1, "Fibra": 3, "Cálcio": 100},
    "Leite": {"Calorias": 120, "Proteína": 8, "Carboidratos": 12, "Gordura": 5, "Fibra": 0, "Cálcio": 300},
    "Ovo": {"Calorias": 80, "Proteína": 6, "Carboidratos": 1, "Gordura": 5, "Fibra": 0, "Cálcio": 28},
    "Batata": {"Calorias": 160, "Proteína": 3, "Carboidratos": 37, "Gordura": 0, "Fibra": 3, "Cálcio": 12},
    "Atum": {"Calorias": 130, "Proteína": 28, "Carboidratos": 0, "Gordura": 1, "Fibra": 0, "Cálcio": 20},
    "Cenoura": {"Calorias": 40, "Proteína": 1, "Carboidratos": 9, "Gordura": 0, "Fibra": 2, "Cálcio": 33},
    "Banana": {"Calorias": 90, "Proteína": 1, "Carboidratos": 23, "Gordura": 0, "Fibra": 3, "Cálcio": 5},
    "Pão Integral": {"Calorias": 130, "Proteína": 5, "Carboidratos": 24, "Gordura": 2, "Fibra": 4, "Cálcio": 40},
    "Queijo": {"Calorias": 110, "Proteína": 7, "Carboidratos": 1, "Gordura": 9, "Fibra": 0, "Cálcio": 200},
}

requisito_minimo = {
    "Calorias": 2000,
    "Proteína": 50,
    "Carboidratos": 250,
    "Gordura": 55,
    "Fibra": 25,
    "Cálcio": 800,
}


# ==== CONSTRUÇÃO DO MODELO ====
def criar_modelo():
    modelo = pyo.ConcreteModel()
    modelo.x = pyo.Var(alimentos, domain=pyo.NonNegativeReals)

    modelo.objetivo = pyo.Objective(
        expr=sum(custo[j] * modelo.x[j] for j in alimentos),
        sense=pyo.minimize,
    )

    def regra_nutriente(modelo, i):
        return sum(tabela_nutricional[j][i] * modelo.x[j] for j in alimentos) >= requisito_minimo[i]

    modelo.restricoes = pyo.Constraint(nutrientes, rule=regra_nutriente)
    return modelo


def criar_solver(nome_solver):
    solver = pyo.SolverFactory(nome_solver)
    if solver is None or not solver.available(False):
        return None
    return solver


def extrair_porcoes_ativas(modelo):
    return {
        j: round(pyo.value(modelo.x[j]), 4)
        for j in alimentos
        if pyo.value(modelo.x[j]) is not None and pyo.value(modelo.x[j]) > 0.001
    }


def resolver_modelo(nome_solver):
    modelo = criar_modelo()
    solver = criar_solver(nome_solver)

    if solver is None:
        return "solver_indisponivel", None, None, None

    try:
        inicio = time.perf_counter()
        resultado = solver.solve(modelo)
        fim = time.perf_counter()
    except Exception:
        return "erro_execucao", None, None, None

    status = str(resultado.solver.termination_condition)
    tempo_ms = round((fim - inicio) * 1000, 3)

    if status == "optimal":
        custo_total = round(pyo.value(modelo.objetivo), 4)
        porcoes_ativas = extrair_porcoes_ativas(modelo)
    else:
        custo_total = None
        porcoes_ativas = None

    return status, custo_total, porcoes_ativas, tempo_ms


def executar_n_vezes(nome_solver, n):
    resolver_modelo(nome_solver)  # warm-up descartado

    tempos = []
    custo_total = None
    porcoes_ativas = None
    status = None

    for _ in range(n):
        status, custo_total, porcoes_ativas, tempo_ms = resolver_modelo(nome_solver)
        if tempo_ms is not None:
            tempos.append(tempo_ms)

    media = round(statistics.mean(tempos), 3) if tempos else None
    desvio = round(statistics.stdev(tempos), 3) if len(tempos) > 1 else 0.0

    return status, custo_total, porcoes_ativas, tempos, media, desvio


def exibir_resultado(nome, status, custo_total, porcoes_ativas, media, desvio, n):
    print(f"\n{nome}")
    print(f"  Status:      {status}")
    print(f"  Custo total: {f'R$ {custo_total:.4f}' if custo_total is not None else '—'}")
    print(f"  Tempo médio: {f'{media} ms (+/- {desvio} ms, n={n})' if media is not None else '—'}")
    if porcoes_ativas:
        print(f"  Porções:     {porcoes_ativas}")


def validar_consistencia(resultados):
    otimos = [r for r in resultados if r["status"] == "optimal" and r["custo_total"] is not None]
    if len(otimos) != len(resultados):
        return False, "Nem todos os solvers retornaram solução ótima."

    referencia = otimos[0]["custo_total"]
    consistentes = all(abs(r["custo_total"] - referencia) <= TOLERANCIA_CUSTO for r in otimos)
    if not consistentes:
        return False, "Os custos ótimos diferem entre os solvers."

    return True, f"Todos os solvers encontraram o mesmo custo ótimo ({referencia:.4f})."


def salvar_resultados(resultados_detalhados, consistencia):
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    caminho_csv = os.path.join(PASTA_RESULTADOS, f"dieta_{timestamp}.csv")
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "solver", "status", "custo_total", "tempo_medio_ms",
                "desvio_ms", "n_repeticoes", "tempos_individuais"
            ],
        )
        writer.writeheader()
        for r in resultados_detalhados:
            writer.writerow({
                "solver": r["solver"],
                "status": r["status"],
                "custo_total": r["custo_total"] if r["custo_total"] is not None else "",
                "tempo_medio_ms": r["media"] if r["media"] is not None else "",
                "desvio_ms": r["desvio"],
                "n_repeticoes": r["n"],
                "tempos_individuais": r["tempos"],
            })

    caminho_json = os.path.join(PASTA_RESULTADOS, f"dieta_{timestamp}.json")
    payload = {
        "problema": "dieta",
        "tipo": "PL",
        "n_repeticoes": N_REPETICOES,
        "consistencia": consistencia,
        "resultados": resultados_detalhados,
    }
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\nResultados salvos em: {PASTA_RESULTADOS}")


def executar():
    print("=" * 60)
    print("PROBLEMA DA DIETA — Programação Linear (PL)")
    print("=" * 60)
    print(f"Alimentos: {len(alimentos)} | Nutrientes: {len(nutrientes)}")
    print(f"Repetições por solver: {N_REPETICOES} (+ 1 warm-up descartado)")

    resultados_detalhados = []
    resumo = []

    for nome_solver in SOLVERS:
        status, custo_total, porcoes_ativas, tempos, media, desvio = executar_n_vezes(nome_solver, N_REPETICOES)
        exibir_resultado(nome_solver.upper(), status, custo_total, porcoes_ativas, media, desvio, N_REPETICOES)
        resumo.append((nome_solver.upper(), status, custo_total, media, desvio))
        resultados_detalhados.append({
            "solver": nome_solver.upper(),
            "status": status,
            "custo_total": custo_total,
            "porcoes_ativas": porcoes_ativas,
            "media": media,
            "desvio": desvio,
            "n": N_REPETICOES,
            "tempos": tempos,
        })

    consistente, mensagem = validar_consistencia(resultados_detalhados)

    print("\n" + "-" * 65)
    print(f"{'Solver':<10} {'Status':<20} {'Custo (R$)':<12} {'Média (ms)':<14} {'Desvio (ms)'}")
    print("-" * 65)
    for nome, status, custo_total, media, desvio in resumo:
        custo_str = f"{custo_total:.4f}" if custo_total is not None else "—"
        media_str = f"{media}" if media is not None else "—"
        print(f"{nome:<10} {status:<20} {custo_str:<12} {media_str:<14} {desvio}")

    print("\nValidação final:", mensagem)
    salvar_resultados(resultados_detalhados, {"consistente": consistente, "mensagem": mensagem})


if __name__ == "__main__":
    executar()
