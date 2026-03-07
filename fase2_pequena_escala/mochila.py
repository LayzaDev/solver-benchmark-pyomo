# Problema da Mochila — Programação Inteira (PI)
#
# Objetivo: selecionar itens para maximizar o valor total,
# sem ultrapassar a capacidade máxima da mochila.

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

# ==== DADOS DO PROBLEMA ====
itens = ["Notebook", "Câmera", "Livro", "Garrafa", "Fone", "Carregador", "Lanche", "Casaco"]

peso = {
    "Notebook": 2.5,
    "Câmera": 1.2,
    "Livro": 0.8,
    "Garrafa": 0.6,
    "Fone": 0.3,
    "Carregador": 0.4,
    "Lanche": 0.5,
    "Casaco": 1.0,
}

valor = {
    "Notebook": 80,
    "Câmera": 60,
    "Livro": 20,
    "Garrafa": 15,
    "Fone": 40,
    "Carregador": 35,
    "Lanche": 25,
    "Casaco": 30,
}

capacidade = 4.0


# ==== CONSTRUÇÃO DO MODELO ====
def criar_modelo():
    modelo = pyo.ConcreteModel()
    modelo.x = pyo.Var(itens, domain=pyo.Binary)

    modelo.objetivo = pyo.Objective(
        expr=sum(valor[j] * modelo.x[j] for j in itens),
        sense=pyo.maximize,
    )

    modelo.capacidade = pyo.Constraint(
        expr=sum(peso[j] * modelo.x[j] for j in itens) <= capacidade
    )
    return modelo


def criar_solver(nome_solver):
    solver = pyo.SolverFactory(nome_solver)
    if solver is None or not solver.available(False):
        return None
    return solver


def resolver_modelo(nome_solver):
    modelo = criar_modelo()
    solver = criar_solver(nome_solver)

    if solver is None:
        return "solver_indisponivel", None, None, None, None

    try:
        inicio = time.perf_counter()
        resultado = solver.solve(modelo)
        fim = time.perf_counter()
    except Exception:
        return "erro_execucao", None, None, None, None

    status = str(resultado.solver.termination_condition)
    tempo_ms = round((fim - inicio) * 1000, 3)

    if status == "optimal":
        selecionados = [j for j in itens if pyo.value(modelo.x[j]) > 0.5]
        valor_total = round(sum(valor[j] for j in selecionados), 2)
        peso_total = round(sum(peso[j] for j in selecionados), 2)
    else:
        valor_total = None
        selecionados = None
        peso_total = None

    return status, valor_total, selecionados, peso_total, tempo_ms


def executar_n_vezes(nome_solver, n):
    resolver_modelo(nome_solver)  # warm-up descartado

    tempos = []
    valor_total = None
    selecionados = None
    peso_total = None
    status = None

    for _ in range(n):
        status, valor_total, selecionados, peso_total, tempo_ms = resolver_modelo(nome_solver)
        if tempo_ms is not None:
            tempos.append(tempo_ms)

    media = round(statistics.mean(tempos), 3) if tempos else None
    desvio = round(statistics.stdev(tempos), 3) if len(tempos) > 1 else 0.0

    return status, valor_total, selecionados, peso_total, tempos, media, desvio


def exibir_resultado(nome, status, valor_total, selecionados, peso_total, media, desvio, n):
    print(f"\n{nome}")
    print(f"  Status:      {status}")
    print(f"  Valor total: {f'{valor_total} pontos' if valor_total is not None else '—'}")
    print(f"  Peso usado:  {f'{peso_total} kg / {capacidade} kg' if peso_total is not None else '—'}")
    print(f"  Tempo médio: {f'{media} ms (+/- {desvio} ms, n={n})' if media is not None else '—'}")
    if selecionados:
        print(f"  Itens:       {', '.join(selecionados)}")


def validar_consistencia(resultados):
    otimos = [r for r in resultados if r["status"] == "optimal" and r["valor_total"] is not None]
    if len(otimos) != len(resultados):
        return False, "Nem todos os solvers retornaram solução ótima."

    ref_valor = otimos[0]["valor_total"]
    ref_peso = otimos[0]["peso_total"]
    ref_itens = sorted(otimos[0]["selecionados"])

    consistentes = all(
        r["valor_total"] == ref_valor and
        r["peso_total"] == ref_peso and
        sorted(r["selecionados"]) == ref_itens
        for r in otimos
    )
    if not consistentes:
        return False, "As soluções inteiras diferem entre os solvers."

    return True, f"Todos os solvers encontraram a mesma solução ótima (valor {ref_valor}, peso {ref_peso})."


def salvar_resultados(resultados_detalhados, consistencia):
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    caminho_csv = os.path.join(PASTA_RESULTADOS, f"mochila_{timestamp}.csv")
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "solver", "status", "valor_total", "peso_total",
                "tempo_medio_ms", "desvio_ms", "n_repeticoes", "tempos_individuais"
            ],
        )
        writer.writeheader()
        for r in resultados_detalhados:
            writer.writerow({
                "solver": r["solver"],
                "status": r["status"],
                "valor_total": r["valor_total"] if r["valor_total"] is not None else "",
                "peso_total": r["peso_total"] if r["peso_total"] is not None else "",
                "tempo_medio_ms": r["media"] if r["media"] is not None else "",
                "desvio_ms": r["desvio"],
                "n_repeticoes": r["n"],
                "tempos_individuais": r["tempos"],
            })

    caminho_json = os.path.join(PASTA_RESULTADOS, f"mochila_{timestamp}.json")
    payload = {
        "problema": "mochila",
        "tipo": "PI",
        "n_repeticoes": N_REPETICOES,
        "consistencia": consistencia,
        "resultados": resultados_detalhados,
    }
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\nResultados salvos em: {PASTA_RESULTADOS}")


def executar():
    print("=" * 60)
    print("PROBLEMA DA MOCHILA — Programação Inteira (PI)")
    print("=" * 60)
    print(f"Itens: {len(itens)} | Capacidade: {capacidade} kg")
    print(f"Repetições por solver: {N_REPETICOES} (+ 1 warm-up descartado)")

    resultados_detalhados = []
    resumo = []

    for nome_solver in SOLVERS:
        status, valor_total, selecionados, peso_total, tempos, media, desvio = executar_n_vezes(nome_solver, N_REPETICOES)
        exibir_resultado(nome_solver.upper(), status, valor_total, selecionados, peso_total, media, desvio, N_REPETICOES)
        resumo.append((nome_solver.upper(), status, valor_total, media, desvio))
        resultados_detalhados.append({
            "solver": nome_solver.upper(),
            "status": status,
            "valor_total": valor_total,
            "selecionados": selecionados,
            "peso_total": peso_total,
            "media": media,
            "desvio": desvio,
            "n": N_REPETICOES,
            "tempos": tempos,
        })

    consistente, mensagem = validar_consistencia(resultados_detalhados)

    print("\n" + "-" * 65)
    print(f"{'Solver':<10} {'Status':<20} {'Valor (pts)':<14} {'Média (ms)':<14} {'Desvio (ms)'}")
    print("-" * 65)
    for nome, status, valor_total, media, desvio in resumo:
        valor_str = f"{valor_total}" if valor_total is not None else "—"
        media_str = f"{media}" if media is not None else "—"
        print(f"{nome:<10} {status:<20} {valor_str:<14} {media_str:<14} {desvio}")

    print("\nValidação final:", mensagem)
    salvar_resultados(resultados_detalhados, {"consistente": consistente, "mensagem": mensagem})


if __name__ == "__main__":
    executar()
