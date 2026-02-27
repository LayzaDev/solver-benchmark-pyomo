import pyomo.environ as pyo
import time

# Problema de teste: minimização simples com 2 variáveis

# min  x + y
# s.t. x + y >= 10
#      x, y >= 0

def criar_modelo():
    model = pyo.ConcreteModel()
    model.x = pyo.Var(domain=pyo.NonNegativeReals)
    model.y = pyo.Var(domain=pyo.NonNegativeReals)
    model.obj = pyo.Objective(expr=model.x + model.y, sense=pyo.minimize)
    model.restricao = pyo.Constraint(expr=model.x + model.y >= 10)
    return model

solvers = {
    "GLPK":  {"executable": "glpsol", "solver_io": "lp"},
    "CBC":   {"executable": "cbc",    "solver_io": "lp"},
    "HiGHS": {"executable": "highs",  "solver_io": "lp"},
}

print("\nVERIFICAÇÃO DO AMBIENTE\n")

resultados = []

for nome, config in solvers.items():
    try:
        model = criar_modelo()
        solver = pyo.SolverFactory(nome.lower())

        inicio = time.perf_counter()
        resultado = solver.solve(model)
        fim = time.perf_counter()

        status = str(resultado.solver.termination_condition)
        valor_obj = pyo.value(model.obj)
        tempo = round((fim - inicio) * 1000, 3)  # em milissegundos

        ok = "✓" if status == "optimal" else "✗"
        print(f"[{ok}] {nome:<8} Status: {status:<8}  |  Valor ótimo: {valor_obj}  |  Tempo: {tempo} ms")

        resultados.append({
            "solver": nome,
            "status": status,
            "valor_obj": valor_obj,
            "tempo_ms": tempo,
            "ok": status == "optimal"
        })

    except Exception as e:
        print(f"[✗] {nome:<8} ERRO: {e}")
        resultados.append({
            "solver": nome,
            "status": "ERRO",
            "valor_obj": None,
            "tempo_ms": None,
            "ok": False
        })

# Teste do SCIP via PySCIPOpt
try:
    from pyscipopt import Model as SCIPModel

    m = SCIPModel()
    m.hideOutput()
    x = m.addVar("x", lb=0)
    y = m.addVar("y", lb=0)
    m.addCons(x + y >= 10)
    m.setObjective(x + y, "minimize")

    inicio = time.perf_counter()
    m.optimize()
    fim = time.perf_counter()

    valor = m.getObjVal()
    tempo = round((fim - inicio) * 1000, 3)

    print(f"[✓] {'SCIP':<8} Status: {'optimal':<8}  |  Valor ótimo: {valor}  |  Tempo: {tempo} ms")

    resultados.append({
        "solver": "SCIP",
        "status": "optimal",
        "valor_obj": valor,
        "tempo_ms": tempo,
        "ok": True
    })

except Exception as e:
    print(f"[✗] {'SCIP':<8} ERRO: {e}")
    resultados.append({
        "solver": "SCIP",
        "status": "ERRO",
        "valor_obj": None,
        "tempo_ms": None,
        "ok": False
    })

# Resumo final
total_ok = sum(1 for r in resultados if r["ok"])
print(f"\nSolvers funcionando: {total_ok}/4")

if total_ok == 4:
    print("✓ Ambiente configurado com sucesso.\n")
else:
    print("✗ Alguns solvers precisam de atenção. Verifique os erros acima.\n")