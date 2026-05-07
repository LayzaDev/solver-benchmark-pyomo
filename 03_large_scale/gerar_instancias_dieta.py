# Gerador de instâncias sintéticas para o Problema da Dieta
#
# Gera instâncias em escala crescente mantendo a estrutura do problema original: minimizar custo satisfazendo requisitos nutricionais mínimos.
#
# As instâncias são geradas com dados nutricionais realistas baseados em intervalos típicos de alimentos, com variação controlada por semente
# aleatória para garantir reprodutibilidade.

import json
import os
import random

PASTA_SAIDA = os.path.join(os.path.dirname(__file__), "instancias", "dieta")

# Cada tupla: (n_alimentos, n_nutrientes)
TAMANHOS = [
    # Tipo A — poucas restrições (10 nutrientes)
    (100,   10),
    (500,   10),
    (1000,  10),
    (2000,  10),
    (5000,  10),
    (10000, 10),
    # Tipo B — restrições médias (30 nutrientes)
    (100,   30),
    (500,   30),
    (1000,  30),
    (2000,  30),
    (5000,  30),
    (10000, 30),
    # Tipo C — muitas restrições (50 nutrientes)
    (100,   50),
    (500,   50),
    (1000,  50),
    (2000,  50),
    (5000,  50),
    (10000, 50),
]

SEMENTE = 42

def gerar_instancia(n_alimentos, n_nutrientes, semente):
    """Gera uma instância sintética do Problema da Dieta.

    Os parâmetros seguem intervalos realistas:
    - Custo por porção: R$ 0.50 a R$ 5.00
    - Conteúdo nutricional: valores típicos por porção de alimento
    - Requisitos mínimos: baseados em necessidades diárias adultas

    Retorna um dicionário com todos os dados da instância.
    """
    rng = random.Random(semente)

    alimentos = [f"alimento_{i+1:05d}" for i in range(n_alimentos)]
    nutrientes = [f"nutriente_{j+1:02d}" for j in range(n_nutrientes)]

    custo = {a: round(rng.uniform(0.50, 5.00), 2) for a in alimentos}

    tabela = {}
    for a in alimentos:
        tabela[a] = {}
        for j, n in enumerate(nutrientes):
            if j == 0:       # calorias: 20–400
                val = rng.uniform(20, 400)
            elif j == 1:     # proteína (g): 0–35
                val = rng.uniform(0, 35)
            elif j == 2:     # carboidratos (g): 0–60
                val = rng.uniform(0, 60)
            elif j == 3:     # gordura (g): 0–20
                val = rng.uniform(0, 20)
            elif j == 4:     # fibra (g): 0–10
                val = rng.uniform(0, 10)
            elif j == 5:     # cálcio (mg): 0–350
                val = rng.uniform(0, 350)
            elif j == 6:     # ferro (mg): 0–10
                val = rng.uniform(0, 10)
            elif j == 7:     # vitamina C (mg): 0–80
                val = rng.uniform(0, 80)
            elif j == 8:     # sódio (mg): 0–600
                val = rng.uniform(0, 600)
            elif j == 9:     # potássio (mg): 0–500
                val = rng.uniform(0, 500)
            elif j == 10:    # zinco (mg): 0–8
                val = rng.uniform(0, 8)
            elif j == 11:    # vitamina A (mcg): 0–200
                val = rng.uniform(0, 200)
            else:            # demais nutrientes genéricos
                val = rng.uniform(1, 100)
            tabela[a][n] = round(val, 2)

    requisitos = {}
    for j, n in enumerate(nutrientes):
        soma_total = sum(tabela[a][n] for a in alimentos)
        fracao = rng.uniform(0.05, 0.15)
        requisitos[n] = round(soma_total * fracao, 2)

    return {
        "n_alimentos": n_alimentos,
        "n_nutrientes": n_nutrientes,
        "semente": semente,
        "alimentos": alimentos,
        "nutrientes": nutrientes,
        "custo": custo,
        "tabela_nutricional": tabela,
        "requisito_minimo": requisitos,
    }


def salvar_instancia(instancia, caminho):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(instancia, f, ensure_ascii=False, indent=2)


def executar():
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    print("Gerando instâncias sintéticas do Problema da Dieta")
    print(f"Pasta de saída: {PASTA_SAIDA}")
    print()

    for n_alimentos, n_nutrientes in TAMANHOS:
        nome = f"dieta_{n_alimentos}x{n_nutrientes}.json"
        caminho = os.path.join(PASTA_SAIDA, nome)

        instancia = gerar_instancia(n_alimentos, n_nutrientes, SEMENTE)
        salvar_instancia(instancia, caminho)

        tamanho_kb = round(os.path.getsize(caminho) / 1024, 1)
        print(f"  {nome:<35} {n_alimentos:>6} alimentos × {n_nutrientes} nutrientes  [{tamanho_kb} KB]")

    print(f"\n{len(TAMANHOS)} instâncias geradas com sucesso.")


if __name__ == "__main__":
    executar()
