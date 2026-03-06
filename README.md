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
  verificacao_ambiente.py   — teste de sanidade: resolve min x + y nos 4 solvers

fase2_pequena_escala/
  dieta.py                  — Problema da Dieta (PL): 12 alimentos × 6 nutrientes
  mochila.py                — Problema da Mochila (PI): 8 itens, variáveis binárias
  resultados/               — CSVs e JSONs gerados automaticamente
```

---

## Requisitos

- Python 3.12.x
- pip atualizado
- Terminal com permissão para instalar pacotes do sistema

---

## Instalação

### 1. Criar ambiente virtual

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

Os resultados são salvos automaticamente em:

```
fase2_pequena_escala/resultados/
```

Arquivos gerados:

- **CSV** — resumo dos resultados
- **JSON** — resultados detalhados

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
| pandas              | 3.0.1                                  |
| scipy               | 1.17.1                                 |

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
