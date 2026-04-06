# Problema da Dieta — Fase 3: Instâncias de Maior Porte
#
# Lê instâncias sintéticas geradas por gerar_instancias_dieta.py
# e executa o benchmark comparativo entre os quatro solvers.
#
# Estrutura idêntica ao dieta.py da Fase 2, escalada para
# instâncias maiores com verificação de consistência entre solvers.

import json
import os
import statistics
import time
from datetime import datetime

import pyomo.environ as pyo

PASTA_INSTANCIAS = os.path.join(os.path.dirname(__file__), "instancias", "dieta")
PASTA_RESULTADOS = os.path.join(os.path.dirname(__file__), "resultados")

N_REPETICOES = 10
SOLVERS = ["glpk", "cbc", "highs", "scip"]
TOLERANCIA_CUSTO = 1e-4

INSTANCIAS = [
    "dieta_100x10.json",
    "dieta_200x12.json",
    "dieta_500x15.json",
    "dieta_1000x15.json",
]


def carregar_instancia(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def criar_modelo(inst):
    """Constrói o modelo de PL a partir dos dados da instância."""
    alimentos = inst["alimentos"]
    nutrientes = inst["nutrientes"]
    custo = inst["custo"]
    tabela = inst["tabela_nutricional"]
    requisitos = inst["requisito_minimo"]

    modelo = pyo.ConcreteModel()
    modelo.x = pyo.Var(alimentos, domain=pyo.NonNegativeReals)

    modelo.objetivo = pyo.Objective(
        expr=sum(custo[j] * modelo.x[j] for j in alimentos),
        sense=pyo.minimize,
    )

    def regra_nutriente(modelo, i):
        return (
            sum(tabela[j][i] * modelo.x[j] for j in alimentos)
            >= requisitos[i]
        )

    modelo.restricoes = pyo.Constraint(nutrientes, rule=regra_nutriente)
    return modelo


def criar_solver(nome_solver):
    solver = pyo.SolverFactory(nome_solver)
    if solver is None or not solver.available(False):
        return None
    return solver


def extrair_custo(modelo, alimentos, custo):
    return round(
        sum(custo[j] * pyo.value(modelo.x[j]) for j in alimentos
            if pyo.value(modelo.x[j]) is not None),
        4,
    )


def resolver_instancia(nome_solver, inst):
    modelo = criar_modelo(inst)
    solver = criar_solver(nome_solver)

    if solver is None:
        return "solver_indisponivel", None, None

    try:
        inicio = time.perf_counter()
        resultado = solver.solve(modelo)
        fim = time.perf_counter()
    except Exception:
        return "erro_execucao", None, None

    status = str(resultado.solver.termination_condition)
    tempo_ms = round((fim - inicio) * 1000, 3)

    if status == "optimal":
        custo_total = extrair_custo(modelo, inst["alimentos"], inst["custo"])
    else:
        custo_total = None

    return status, custo_total, tempo_ms


def executar_n_vezes(nome_solver, inst):
    resolver_instancia(nome_solver, inst) # Warm-up descartado

    tempos = []
    custo_otimo = None   # valor de referência (primeiro ótimo encontrado)
    execucoes_otimas = 0 # quantas das N execuções retornaram optimal
    status = None

    for _ in range(N_REPETICOES):
        status_exec, custo, tempo  = resolver_instancia(nome_solver, inst)
        if tempo is not None:
            tempos.append(tempo)
        if status_exec == "optimal":
            execucoes_otimas += 1
            if custo_otimo is None:
                custo_otimo = custo  # guarda o valor de referência
        if status is None:
            status = status_exec

    if status is None and tempos:
        status = status_exec

    media = round(statistics.mean(tempos), 3) if tempos else None
    desvio = round(statistics.stdev(tempos), 3) if len(tempos) > 1 else 0.0

    return status, custo_otimo, execucoes_otimas, tempos, media, desvio


def validar_consistencia(resultados):
    """Verifica se todos os solvers encontraram o mesmo custo ótimo."""
    otimos = [r for r in resultados if r["status"] == "optimal"
              and r["custo_otimo"] is not None]
    if not otimos:
        return False, "Nenhum solver retornou solução ótima."

    referencia = otimos[0]["custo_otimo"]
    consistentes = all(
        abs(r["custo_otimo"] - referencia) <= TOLERANCIA_CUSTO
        for r in otimos
    )
    if not consistentes:
        return False, "Os custos ótimos diferem entre os solvers."

    return True, f"Todos os solvers concordam com custo mínimo ≈ R$ {referencia:.4f}."


def exibir_resultado(solver, status, custo_otimo, execucoes_otimas, media, desvio):
    custo_str = f"R$ {custo_otimo:.4f}" if custo_otimo is not None else "—"
    tempo_str = f"{media} ms" if media is not None else "—"
    estab_str = f"{execucoes_otimas}/{N_REPETICOES} optimal"
    print(f"  {solver:<8} | status: {status:<20} | custo: {custo_str:<14} "
          f"| tempo: {tempo_str:<12} ± {desvio} ms | estab: {estab_str}")


def salvar_resultados(todos_resultados):
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    caminho_json = os.path.join(PASTA_RESULTADOS, f"dieta_grande_{timestamp}.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(todos_resultados, f, ensure_ascii=False, indent=2)

    print(f"\nResultados salvos em: {PASTA_RESULTADOS}")


def executar():
    print("=" * 70)
    print("PROBLEMA DA DIETA — Fase 3: Instâncias de Maior Porte")
    print("=" * 70)
    print(f"Repetições por solver por instância: {N_REPETICOES} (+ 1 warm-up)")
    print()

    todos_resultados = []

    for nome in INSTANCIAS:
        caminho = os.path.join(PASTA_INSTANCIAS, nome)

        if not os.path.exists(caminho):
            print(f"[AVISO] Arquivo não encontrado: {nome}")
            print(f"        Execute gerar_instancias_dieta.py primeiro.")
            continue

        inst = carregar_instancia(caminho)
        n_al = inst["n_alimentos"]
        n_nu = inst["n_nutrientes"]

        print(f"\nInstância: {nome}")
        print(f"  Alimentos: {n_al} | Nutrientes: {n_nu}")
        print(f"  {'-'*60}")

        resultados_instancia = []

        for nome_solver in SOLVERS:
            status, custo_otimo, execucoes_otimas, tempos, media, desvio = executar_n_vezes(
                nome_solver, inst
            )
            exibir_resultado(nome_solver.upper(), status, custo_otimo, execucoes_otimas, media, desvio)

            registro = {
                "instancia": nome,
                "n_alimentos": n_al,
                "n_nutrientes": n_nu,
                "solver": nome_solver.upper(),
                "status": status,
                "custo_otimo": custo_otimo,
                "tempo_medio_ms": media,
                "desvio_ms": desvio,
                "execucoes_otimas": execucoes_otimas,
                "n_repeticoes": N_REPETICOES,
                "tempos_individuais": tempos,
            }
            todos_resultados.append(registro)
            resultados_instancia.append(registro)

        consistente, msg = validar_consistencia(resultados_instancia)
        print(f"  Consistência: {msg}")

    salvar_resultados(todos_resultados)


if __name__ == "__main__":
    executar()