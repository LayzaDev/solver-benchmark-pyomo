# Comparação de Desempenho entre Solvers de Otimização

Este projeto faz parte de um Trabalho de Conclusão de Curso (TCC) cujo objetivo é comparar o desempenho de solvers open-source em problemas de otimização matemática.

---

## Objetivo

Comparar o desempenho dos seguintes solvers open-source:

- GLPK
- CBC
- HiGHS
- SCIP

Os experimentos são realizados em problemas de:

- Programação Linear (PL)
- Programação Inteira (PI)

A modelagem é feita utilizando **Pyomo**, que atua como uma interface unificada para todos os solvers.

---

## Estrutura do Projeto

```
fase1_verificacao/
  verificacao_ambiente.py        — teste de sanidade: resolve min x + y nos 4 solvers

fase2_pequena_escala/
  dieta.py                       — Problema da Dieta (PL): 12 alimentos × 6 nutrientes
  mochila.py                     — Problema da Mochila (PI): 8 itens, variáveis binárias
  resultados/                    — JSONs gerados automaticamente

fase3_maior_escala/
  gerar_instancias_dieta.py      — gera instâncias sintéticas da Dieta (100, 200, 500, 1000 alimentos)
  dieta_grande.py                — benchmark da Dieta em escala maior
  mochila_grande.py              — benchmark da Mochila com instâncias Pisinger (100–1000 itens)
  gerar_graficos.py              — gera 7 gráficos PNG a partir dos JSONs de resultados
  instancias/                    — instâncias sintéticas (dieta) e Pisinger (mochila)
  resultados/                    — JSONs gerados automaticamente
  graficos/                      — PNGs gerados automaticamente
```

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
python fase1_verificacao/verificacao_ambiente.py
```

Saída esperada:

```
VERIFICAÇÃO DO AMBIENTE

[✓] GLPK     Status: optimal | Valor ótimo: 10.0 | Tempo: 118.765 ms
[✓] CBC      Status: optimal | Valor ótimo: 10.0 | Tempo: 83.992 ms
[✓] HIGHS    Status: optimal | Valor ótimo: 10.0 | Tempo: 852.059 ms
[✓] SCIP     Status: optimal | Valor ótimo: 10.0 | Tempo: 117.872 ms

Solvers funcionando: 4/4
Ambiente configurado com sucesso.
```

---

## Execução dos Experimentos (Fase 2)

Executar os problemas de teste:

**Problema da Dieta**
```bash
python fase2_pequena_escala/dieta.py
```

**Problema da Mochila**
```bash
python fase2_pequena_escala/mochila.py
```

Os resultados são salvos automaticamente em `fase2_pequena_escala/resultados/` no formato JSON.

---

## Execução dos Experimentos (Fase 3)

### 1. Gerar instâncias sintéticas da Dieta

```bash
python fase3_maior_escala/gerar_instancias_dieta.py
```

Gera 4 instâncias em `fase3_maior_escala/instancias/dieta/`.

### 2. Executar benchmarks

**Problema da Dieta (PL)**
```bash
python fase3_maior_escala/dieta_grande.py
```

**Problema da Mochila (PI)**

As instâncias Pisinger devem estar em `fase3_maior_escala/instancias/knapsack-01-instances/`.

```bash
python fase3_maior_escala/mochila_grande.py
```

Os resultados são salvos em `fase3_maior_escala/resultados/` no formato JSON.

### 3. Gerar gráficos

```bash
python fase3_maior_escala/gerar_graficos.py
```

Gera 7 gráficos PNG em `fase3_maior_escala/graficos/`:

- `dieta_escalabilidade.png` — tempo médio por solver (PL)
- `dieta_desvio.png` — desvio padrão por solver (PL)
- `mochila_tipo1_escalabilidade.png` — tempo médio, instâncias não correlacionadas (PI)
- `mochila_tipo1_desvio.png` — desvio padrão, instâncias não correlacionadas (PI)
- `mochila_tipo2_escalabilidade.png` — tempo médio, instâncias fracamente correlacionadas (PI)
- `mochila_tipo2_desvio.png` — desvio padrão, instâncias fracamente correlacionadas (PI)
- `comparativo_pl_pi_1000.png` — comparativo PL vs PI a 1000 elementos

---

## Ambiente de Referência

Os experimentos deste trabalho foram executados no seguinte ambiente:

| Componente          | Versão                                 |
|---------------------|----------------------------------------|
| Sistema Operacional | Linux 6.6.87.2-microsoft-standard-WSL2 |
| Arquitetura         | x86_64                                 |
| Python              | 3.12.12                                |
| Pyomo               | 6.10.0                                 |
| HiGHS (highspy)     | 1.13.1                                 |
| SCIP                | 10.0.1                                 |
| GLPK                | 5.0                                    |
| CBC                 | 2.10.11                                |
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
