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

solvers = ["glpk", "cbc", "highs", "scip"]

print("\nVERIFICAÇÃO DO AMBIENTE\n")

resultados = []

for nome in solvers:
    try:
        model = criar_modelo()
        solver = pyo.SolverFactory(nome)

        inicio = time.perf_counter()
        resultado = solver.solve(model)
        fim = time.perf_counter()

        status = str(resultado.solver.termination_condition)
        valor_obj = pyo.value(model.obj)
        tempo = round((fim - inicio) * 1000, 3)

        ok = "✓" if status == "optimal" else "✗"
        print(f"[{ok}] {nome.upper():<8} Status: {status:<8}  |  Valor ótimo: {valor_obj}  |  Tempo: {tempo} ms")

        resultados.append({
            "solver": nome.upper(),
            "status": status,
            "valor_obj": valor_obj,
            "tempo_ms": tempo,
            "ok": status == "optimal"
        })

    except Exception as e:
        print(f"[✗] {nome.upper():<8} ERRO: {e}")
        resultados.append({
            "solver": nome.upper(),
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