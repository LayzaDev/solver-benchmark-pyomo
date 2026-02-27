# Fase 1 — Configuração do Ambiente de Testes

## TCC: Comparação de Desempenho entre Solvers de Otimização Linear e Inteira

**Objetivo:** instalar e verificar os 4 solvers (GLPK, CBC, HiGHS e SCIP) integrados ao Pyomo, garantindo um ambiente reproduzível antes dos experimentos.

---

## Requisitos

- Python 3.10 ou superior
- pip atualizado
- Terminal com permissão para instalar pacotes do sistema

---

## Instalação

### 1. Ambiente virtual

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

### 2. Dependências Python

O projeto inclui um `requirements.txt` com todas as dependências e versões exatas usadas nos experimentos. Para instalar:

```bash
pip install -r requirements.txt
```

### 3. Solvers do sistema (GLPK e CBC)

**Ubuntu/Debian:**
```bash
sudo apt install glpk-utils coinor-cbc
```

**macOS:**
```bash
brew install glpk
brew install coin-or-tools/coinor/cbc
```

**Windows (conda):**
```bash
conda install -c conda-forge glpk coincbc
```

---

## Verificação

Execute o script de sanidade para confirmar que os 4 solvers respondem corretamente via Pyomo:

```bash
python verificacao_ambiente.py
```

Resultado obtido no ambiente de referência:

```
VERIFICAÇÃO DO AMBIENTE

[✓] GLPK     Status: optimal   |  Valor ótimo: 10.0  |  Tempo: 133.36 ms
[✓] CBC      Status: optimal   |  Valor ótimo: 10.0  |  Tempo: 36.644 ms
[✓] HiGHS    Status: optimal   |  Valor ótimo: 10.0  |  Tempo: 1309.296 ms
[✓] SCIP     Status: optimal   |  Valor ótimo: 10.0  |  Tempo: 16.946 ms

Solvers funcionando: 4/4
✓ Ambiente configurado com sucesso.
```

---

## Ambiente de referência

Os experimentos deste TCC foram executados no seguinte ambiente:

| Componente        | Versão / Especificação                  |
|-------------------|-----------------------------------------|
| Sistema Operacional | Linux 6.6.87.2-microsoft-standard-WSL2 |
| Arquitetura       | x86_64                                  |
| Python            | 3.12.12 (GCC 13.3.0)                    |
| Pyomo             | 6.10.0                                  |
| HiGHS (highspy)   | 1.13.1                                  |
| SCIP (pyscipopt)  | 6.1.0                                   |
| GLPK              | 5.0                                     |
| CBC               | 2.10.11                                 |
| pandas            | 3.0.1                                   |
| scipy             | 1.17.1                                  |

---

## Solução de problemas

### GLPK ou CBC: executável não encontrado

```bash
# Verifique se está no PATH:
which glpsol
which cbc

# Se não retornar nada, localize e adicione ao PATH:
find / -name "glpsol" 2>/dev/null
export PATH=$PATH:/caminho/encontrado   # ajuste conforme o retorno acima
```

Para tornar permanente, adicione a linha `export PATH=...` ao `~/.bashrc` e rode `source ~/.bashrc`.

### SCIP: "Unable to locate package scip"

Não instale via `apt` — o SCIP está embutido no pacote Python:

```bash
pip install pyscipopt
```

### CBC retorna status diferente de "optimal"

Especifique o caminho do executável explicitamente:

```python
solver = pyo.SolverFactory("cbc", executable="/usr/bin/cbc")
# Ajuste o caminho conforme o retorno de: which cbc
```
