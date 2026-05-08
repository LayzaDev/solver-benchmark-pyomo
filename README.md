# Comparação de Desempenho entre Solvers de Otimização

Este projeto faz parte de um Trabalho de Conclusão de Curso (TCC) desenvolvido na Universidade Federal de Uberlândia (UFU), como requisito para obtenção do título de Bacharel em Sistemas de Informação.

O objetivo é comparar o desempenho de solvers open-source em problemas de otimização matemática.

**Autora:** Layza Nauande de Paula Silva  
**Orientador:** Prof. Dr. Paulo Henrique Ribeiro Gabriel  
**Ano:** 2026

---

## Objetivo

Comparar o desempenho dos seguintes solvers open-source:

- GLPK
- CBC
- HiGHS
- SCIP

Os experimentos são realizados em problemas de:

- Programação Linear (PL) — Problema da Dieta
- Programação Inteira (PI) — Problema da Mochila 0-1

A modelagem é feita utilizando **Pyomo**, que atua como uma interface unificada para todos os solvers.

---

## Estrutura do Projeto

```
01_validation/
  coleta_especificacoes.py        — verifica e exibe versões dos solvers e do ambiente

02_small_scale/
  dieta.py                        — Problema da Dieta (PL): instância pequena
  mochila.py                      — Problema da Mochila (PI): instância pequena
  resultados/                     — JSONs gerados automaticamente

03_large_scale/
  gerar_instancias_dieta.py       — gera 18 instâncias sintéticas da Dieta (3 tipos × 6 tamanhos)
  dieta_grande.py                 — benchmark da Dieta em larga escala
  mochila_grande.py               — benchmark da Mochila com instâncias Pisinger
  gerar_graficos.py               — gera 15 gráficos PNG a partir dos JSONs de resultados
  instancias/
    dieta/                        — 18 JSONs gerados por gerar_instancias_dieta.py
    knapsack-01-instances/        — instâncias Pisinger (T1, T2, T3)
  resultados/                     — JSONs gerados automaticamente
  graficos/                       — PNGs gerados automaticamente
```

---

## Design Experimental (Fase 3)

Dois problemas, cada um com **18 instâncias** (3 tipos × 6 tamanhos), resolvidos por 4 solvers com **10 repetições + 1 warm-up** descartado e **limite de tempo de 5 s** por execução.

### Problema da Dieta (PL)

| Tipo | Nutrientes | Tamanhos (n_alimentos) |
|------|-----------|------------------------|
| A (sparse) | 10 | 100, 500, 1000, 2000, 5000, 10000 |
| B (medium) | 30 | 100, 500, 1000, 2000, 5000, 10000 |
| C (dense)  | 50 | 100, 500, 1000, 2000, 5000, 10000 |

Instâncias sintéticas geradas com semente fixa (`SEMENTE = 42`) para reprodutibilidade.

### Problema da Mochila 0-1 (PI)

| Tipo | Correlação | Tamanhos (n_itens) |
|------|-----------|----------------------|
| 1 (uncorrelated)        | pesos e valores independentes | 100, 500, 1000, 2000, 5000, 10000 |
| 2 (weakly correlated)   | correlação fraca              | 100, 500, 1000, 2000, 5000, 10000 |
| 3 (strongly correlated) | peso_i = valor_i + k (difícil)| 100, 500, 1000, 2000, 5000, 10000 |

Instâncias Pisinger (`knapPI_T_N_1000_1`). Referência: Pisinger, D. (2005). *Where are the hard knapsack problems?* Computers & Operations Research, 32(9), 2271–2284.

---

## Requisitos

- Python 3.12.x
- pip atualizado
- Terminal com permissão para instalar pacotes do sistema

---

## Instalação

### 1. Criar ambiente virtual

No Windows, entre no WSL a partir da pasta do projeto:

```bash
wsl -d Ubuntu-24.04
```

Criar o ambiente virtual:

```bash
python -m venv venv
```

Ativar ambiente:

```bash
source venv/bin/activate
```

### 2. Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 3. Instalar solvers do sistema

#### GLPK e CBC (Ubuntu / Debian / WSL2)

```bash
sudo apt install glpk-utils coinor-cbc
```

#### SCIP (Ubuntu 24.04 / WSL2)

O pacote `scip` não está disponível diretamente via `apt` no Ubuntu 24.04.
É necessário instalar o binário oficial.

1. Acesse: https://www.scipopt.org/index.php#download

2. Baixe o pacote correspondente ao sistema:
   - Ubuntu 24.04 → `scipoptsuite_10.0.1-1+noble_amd64.deb`

3. Instale:

```bash
sudo dpkg -i scipoptsuite_10.0.1-1+noble_amd64.deb
sudo apt-get install -f
```

4. Verifique a instalação:

```bash
which scip
scip --version
```

5. Confirmar integração com Pyomo:

```bash
python3 -c "
import pyomo.environ as pyo
s = pyo.SolverFactory('scip')
print('executable:', s.executable())
print('available: ', s.available())
"
```

---

## Verificação do Ambiente

Após instalar tudo, execute:

```bash
python 01_validation/coleta_especificacoes.py
```

Exibe as versões do Python, Pyomo e de cada solver disponível no ambiente.

---

## Execução dos Experimentos (Fase 2 — pequena escala)

```bash
python 02_small_scale/dieta.py
python 02_small_scale/mochila.py
```

Os resultados são salvos automaticamente em `02_small_scale/resultados/` no formato JSON.

---

## Execução dos Experimentos (Fase 3 — larga escala)

### 1. Gerar instâncias sintéticas da Dieta

```bash
python 03_large_scale/gerar_instancias_dieta.py
```

Gera 18 instâncias em `03_large_scale/instancias/dieta/`.

### 2. Executar benchmarks

**Problema da Dieta (PL)**
```bash
python 03_large_scale/dieta_grande.py
```

**Problema da Mochila (PI)**

As instâncias Pisinger devem estar em `03_large_scale/instancias/knapsack-01-instances/pisinger_instances_01_KP/large_scale/`.

```bash
python 03_large_scale/mochila_grande.py
```

Os resultados são salvos em `03_large_scale/resultados/` no formato JSON.

### 3. Gerar gráficos

```bash
python 03_large_scale/gerar_graficos.py
```

Gera 15 gráficos PNG em `03_large_scale/graficos/`:

**Dieta:**
- `dieta_tipo1_escalabilidade.png` / `dieta_tipo1_desvio.png`
- `dieta_tipo2_escalabilidade.png` / `dieta_tipo2_desvio.png`
- `dieta_tipo3_escalabilidade.png` / `dieta_tipo3_desvio.png` / `dieta_tipo3_otimalidade.png`

**Mochila:**
- `mochila_tipo1_escalabilidade.png` / `mochila_tipo1_desvio.png`
- `mochila_tipo2_escalabilidade.png` / `mochila_tipo2_desvio.png`
- `mochila_tipo3_escalabilidade.png` / `mochila_tipo3_desvio.png` / `mochila_tipo3_otimalidade.png`

**Comparativo:**
- `comparativo_pl_pi_10000.png` — tempo médio por solver a n=10000 (3 tipos PL + 3 tipos PI)

---

## Ambiente de Referência

Os experimentos deste trabalho foram executados no seguinte ambiente:

| Componente          | Versão                                 |
|---------------------|----------------------------------------|
| Sistema Operacional | Linux 6.6 (WSL2/Ubuntu 24.04)         |
| Arquitetura         | x86_64, 8 GB RAM                      |
| Python              | 3.12.12                                |
| Pyomo               | 6.10.0                                 |
| GLPK                | 5.0                                    |
| CBC                 | 2.10.11                                |
| HiGHS (highspy)     | 1.13.1                                 |
| SCIP                | 10.0.1                                 |
| matplotlib          | 3.10.8                                 |
| numpy               | 2.4.2                                  |

---

## Solução de Problemas

### GLPK ou CBC não encontrados

```bash
which glpsol
which cbc
```

Se não retornar nada:

```bash
sudo apt install glpk-utils coinor-cbc
```

### SCIP retorna `available: False`

O Pyomo localiza o solver pelo executável `scip`.

Verifique:

```bash
which scip
scip --version
```

Possíveis causas:

- `apt install scip` não funciona no Ubuntu 24.04
- Pacote `.tgz` baixado é código-fonte, não binário compilado
- Dependências faltando após `dpkg -i`

Para resolver dependências:

```bash
sudo apt-get install -f
```

### CBC retorna status diferente de `optimal`

Especifique explicitamente o executável:

```python
solver = pyo.SolverFactory("cbc", executable="/usr/bin/cbc")
```
