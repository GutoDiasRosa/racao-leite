# Balanceamento de rações — vacas em lactação

App web em **Python + Streamlit** que monta a dieta diária ("ração") de um lote de vacas leiteiras,
seguindo o trabalho da disciplina de nutrição animal. Este README explica **o problema** (para quem não é
da área), **cada tela do app**, **as contas** por trás de cada uma e **como o código está organizado**.

> Resumo em uma frase: o app descobre **quantos kg de cada alimento** dar por vaca por dia para que a
> soma dos nutrientes chegue no que a vaca precisa, respeitando alguns limites de saúde e, se possível,
> gastando o mínimo.

---

## Sumário

1. [Como rodar](#1-como-rodar)
2. [O problema, explicado para leigos](#2-o-problema-explicado-para-leigos)
3. [Glossário (as siglas que aparecem no app)](#3-glossário-as-siglas-que-aparecem-no-app)
4. [O que o trabalho pede](#4-o-que-o-trabalho-pede)
5. [Tour pelas telas](#5-tour-pelas-telas)
6. [Os três métodos de balanceamento](#6-os-três-métodos-de-balanceamento)
7. [O silo e a lavoura](#7-o-silo-e-a-lavoura)
8. [Como o código está organizado](#8-como-o-código-está-organizado)
9. [Dados, arquivos e persistência](#9-dados-arquivos-e-persistência)
10. [Como mudar ou estender](#10-como-mudar-ou-estender)
11. [Limitações e cuidados](#11-limitações-e-cuidados)

---

## 1. Como rodar

Na pasta do projeto (Windows):

```bash
python -m venv .venv
```
```bash
.venv\Scripts\python -m pip install -r requirements.txt
```
```bash
.venv\Scripts\python -m streamlit run app.py
```

O navegador abre em http://localhost:8501. Para rodar os testes:

```bash
.venv\Scripts\python -m pytest -q
```

> Use uma pasta de caminho curto (como `C:\Projetos\racao-leite`). No Windows, o pandas não consegue
> carregar uma de suas bibliotecas quando o caminho fica muito longo.

Dependências (`requirements.txt`): `streamlit` (interface), `pandas` (tabelas), `numpy`, `scipy`
(otimizador), `openpyxl` (exportar Excel) e `pytest` (testes).

---

## 2. O problema, explicado para leigos

Pense na dieta da vaca como uma **receita** que precisa bater várias metas ao mesmo tempo:

- **Quantidade total**: a vaca só consegue comer um tanto por dia (como o "tamanho do estômago").
- **Proteína**: para produzir leite e manter o corpo.
- **Energia**: o "combustível" — vaca que produz 40 kg de leite gasta muita energia.
- **Minerais** (cálcio e fósforo): o leite tem muito cálcio; ossos também precisam.
- **Fibra mínima**: a vaca é **ruminante** — tem um estômago enorme (rúmen) cheio de micróbios que
  fermentam a comida. Esses micróbios precisam de fibra (capim, silagem) para funcionar e para a vaca
  ruminar ("mastigar de novo"). Pouca fibra = rúmen doente.
- **Limites máximos**: gordura demais atrapalha os micróbios; **amido** demais (grãos) fermenta rápido,
  acidifica o rúmen e causa **acidose** (uma espécie de "azia grave" que derruba a saúde e o leite).

Os ingredientes disponíveis têm composições diferentes: a **silagem** é rica em fibra e pobre em proteína;
o **farelo de soja** é muito proteico; o **milho** é energético e cheio de amido; o **calcário** é quase
só cálcio. Balancear = **combinar quantidades** desses ingredientes para que **todas as metas sejam
atendidas ao mesmo tempo**. É, no fundo, um problema de **sistema de equações / otimização linear**.

### Matéria seca × matéria natural (a pegadinha principal)

Todo alimento tem água. **Matéria natural (MN)** é o alimento como ele é (com água); **matéria seca
(MS)** é o que sobra se tirar toda a água. As exigências e a composição dos alimentos são dadas
**em MS**, porque a água não alimenta.

Exemplo: a silagem de milho tem 31% de MS. Se a ração pede **12 kg de MS** de silagem, o tratador precisa
pôr no cocho **12 ÷ 0,31 ≈ 38,7 kg** de silagem "como sai do silo". O app calcula tudo em MS e mostra a
conversão para MN quando é útil (fórmula, compra, silo).

---

## 3. Glossário (as siglas que aparecem no app)

| Sigla | Nome | Em linguagem simples |
|---|---|---|
| **MS** | Matéria seca | O alimento sem a água. Base de todas as contas. |
| **MN** | Matéria natural | O alimento como é, com água (o que vai para o cocho). |
| **IMS** | Ingestão de matéria seca | Quanto de MS a vaca come por dia. No trabalho: 4,12% do peso → 590 × 0,0412 = **24,31 kg MS/dia**. |
| **PC** | Peso corporal | Peso médio da vaca (590 kg). |
| **DEL** | Dias em lactação | Há quantos dias a vaca pariu e está dando leite (120). |
| **PB** | Proteína bruta | Proteína total do alimento. Meta: 4,00 kg/dia (= 16,46% da MS). |
| **NDT** | Nutrientes digestíveis totais | Medida de **energia**: a parte do alimento que a vaca consegue digerir. Meta: 17,52 kg/dia (= 72,08% da MS). |
| **FDN** | Fibra em detergente neutro | A **fibra** (parede das células das plantas). Mínimo de 29% da MS, para a saúde do rúmen. |
| **EE** | Extrato etéreo | A **gordura** do alimento. Máximo de 5% da MS. |
| **Ca / P** | Cálcio / Fósforo | Minerais. Metas: 0,61% e 0,36% da MS. |
| **Amido** | — | Carboidrato dos grãos; energia rápida, mas em excesso causa acidose. Máximo de 26% da MS (só na ração 3). |
| **Volumoso** | — | Alimento fibroso e "volumoso": silagem, feno, capim. |
| **Concentrado** | — | Alimento denso em energia (milho, polpa cítrica) ou proteína (farelo de soja). |
| **Silagem** | — | Planta inteira (ex.: milho) picada e fermentada sem ar dentro de um silo; conserva a comida para o ano todo. |
| **Aditivo** | — | Ingrediente usado em gramas, não pelo valor nutritivo, mas por um efeito (tamponar o rúmen, melhorar a fermentação etc.). |
| **LCG 4%** | Leite corrigido para 4% de gordura | Converte a produção para um padrão de 4% de gordura, para comparar vacas. |
| **ELL** | Energia líquida de lactação | Outra forma de medir energia (em Mcal), usada pelo NRC. |
| **NRC** | National Research Council | Livro americano de referência com as equações de exigência dos animais. |
| **CQBAL** | Tabelas Brasileiras de Composição de Alimentos | Banco de dados online com a composição dos alimentos brasileiros ([cqbal.com.br](https://www.cqbal.com.br/#!/)). |

---

## 4. O que o trabalho pede

Lote de **130 vacas**, 120 dias de lactação, 590 kg, IMS de 4,12% do peso, **40 kg de leite/dia** com 3,7%
de gordura e 3,3% de proteína. Fazer **três rações**:

1. por **tentativa e erro**;
2. por **processo algébrico**;
3. **no computador**, com a regra extra de **amido ≤ 26% da MS**.

Regras para todas: PB 4,00 kg/d, NDT 17,52 kg/d, Ca 0,61%, P 0,36%, FDN ≥ 29%, EE ≤ 5%; **pelo menos 4
alimentos** (minerais e vitaminas não contam); **pelo menos 2 aditivos justificados**; a **silagem de milho**
tem que ser um dos volumosos, com o cálculo do **silo**, da **fatia diária** e da **área a plantar**.

O app já vem preenchido com esses dados, e cada tela tem um **checklist** com essas regras.

---

## 5. Tour pelas telas

A barra lateral tem o menu, um resumo do lote e a seção **Projeto** (baixar/abrir/restaurar).

### 🐄 Animal e exigências — `paginas/1_animal.py`
Onde entram os dados do lote e as metas. Mostra a IMS por vaca e do lote, e uma tabela com cada exigência
em **kg/vaca/dia**, **% da MS** e **kg/dia do lote**.
No quadro **"Estimativa pelo NRC (2001)"** o app *estima* IMS e energia a partir de peso, leite, gordura e
proteína (equações abaixo), só como **referência** — o balanceamento usa sempre os números digitados.

- LCG 4% = 0,4 × leite + 15 × (leite × gordura%)
- IMS prevista = (0,372 × LCG + 0,0968 × PC^0,75) × (1 − e^(−0,192 × (semana de lactação + 3,67)))
- ELL mantença = 0,08 × PC^0,75; ELL do leite = leite × (0,0929 × G% + 0,0547 × P% + 0,0395 × 4,85)
- NDT equivalente: ELL (Mcal/kg MS) = 0,0245 × NDT% − 0,12

### 🌽 Alimentos — `paginas/2_alimentos.py`
Tabela editável com cada ingrediente: categoria, MS (% da MN), PB, NDT, FDN, EE, Ca, P, amido (% da MS),
preço (R$/kg MN) e fonte. Os valores padrão vêm do **CQBAL 4.0**. Dá para editar, adicionar e apagar
linhas, exportar/importar **CSV** e restaurar o padrão.
A **categoria** importa: *Mineral/vitamínico* e *Aditivo* **não contam** para a regra dos 4 alimentos;
*Aditivo* aparece na tela de Aditivos.

### 🧪 Aditivos — `paginas/6_aditivos.py`
Escolha os aditivos (padrão: bicarbonato de sódio e monensina), a **dose em gramas por vaca/dia** e o
**texto de justificativa** (já vem um texto pronto, editável). Os aditivos escolhidos entram
**automaticamente, com dose fixa, nas três rações**.

### ✏️ 1. Tentativa e erro — `paginas/3_tentativa_erro.py`
Você escolhe os alimentos e digita os kg de MS de cada um. A cada mudança aparecem:
- **cartões** com MS, PB, NDT, FDN e custo (com a diferença para a meta);
- a **tabela exigido × fornecido**, com barra de "% atendido" e status por cores
  (🟢 atende, 🟡 quase / excesso, 🔴 não atende);
- **dicas** do tipo "faltam 0,393 kg de PB ≈ +0,80 kg MS de farelo de soja";
- o **checklist** do trabalho e a **fórmula** (kg MN, kg MS, % da MS, quantidade para o lote, custo).

O botão **Salvar tentativa** grava a tentativa num histórico — útil para mostrar ao professor o caminho até
a ração final.

### ➗ 2. Processo algébrico — `paginas/4_algebrico.py`
Monta e resolve um **sistema de equações** (detalhes na seção 6). A tela mostra: as variáveis (x₁, x₂…),
a montagem de cada equação, a matriz, **cada passo** da eliminação de Gauss-Jordan, a solução e a
conferência da ração completa. O botão **"Carregar exemplo clássico"** monta um sistema 5×5 pronto.

### 💻 3. Computador (PL) — `paginas/5_computador.py`
O computador procura a **ração de menor custo** que respeita todas as regras (detalhes na seção 6).
Você escolhe quais alimentos ele pode usar e, se quiser, **mínimos e máximos** por alimento (o padrão força
pelo menos 40% da IMS de silagem de milho). Mostra a fórmula ótima, custo por vaca, por lote e por kg de
leite, a avaliação, o checklist e um **relatório do otimizador**.

### 🏗️ Silo e lavoura — `paginas/7_silo.py`
Pega a quantidade de silagem de milho da ração escolhida e calcula o tamanho do silo, a fatia diária e a
área de milho a plantar, com a **memória de cálculo** passo a passo (seção 7).

### 📄 Relatório final — `paginas/8_relatorio.py`
Junta tudo: dados do animal, as três rações (fórmula, nutrientes, checklist), histórico de tentativas,
relatório do otimizador, aditivos com justificativas e o silo. Baixa em **HTML** (abra no navegador e use
*Imprimir → Salvar como PDF*) ou em **Excel** (uma aba por tabela, para copiar para o modelo do professor).

---

## 6. Os três métodos de balanceamento

Em todos, a variável é **quantos kg de MS de cada alimento** entram por vaca por dia. Cada nutriente
fornecido é uma **soma**: `kg do alimento × (% do nutriente ÷ 100)`.

### 6.1 Tentativa e erro
Não há algoritmo: é você ajustando. O app só faz as contas de soma e compara com as metas.
Critérios de cor (`core/nutricao.py → status_meta`):

| Tipo de meta | 🟢 Atende | 🟡 Quase | 🔴 Não atende |
|---|---|---|---|
| Mínimo (PB, NDT, Ca, P, FDN) | ≥ 100% (🟡 "excesso" se passar muito: PB/NDT +10%, Ca +60%, P +40%) | 97% a 100% | < 97% |
| Máximo (EE, amido) | ≤ 100% | até 103% | > 103% |
| Total de MS (IMS) | ± 1% | ± 3% | fora disso |

### 6.2 Processo algébrico (sistema de equações)
Ideia: se eu quero acertar **n metas exatamente**, escolho **n alimentos** cujas quantidades são as
incógnitas e escrevo **uma equação por meta**. Os demais alimentos ficam com quantidade **fixa** e o que
eles fornecem é descontado do lado direito.

Exemplo pequeno (2 alimentos, 2 metas): milho (x, 9% PB) e farelo de soja (y, 49% PB), querendo 10 kg de MS
com 2 kg de PB:

```
x +      y = 10        (MS)
0,09x + 0,49y = 2      (PB)
→ y = 2,75 kg e x = 7,25 kg
```

O app generaliza para até **5×5**. O exemplo clássico usa silagem, milho, farelo de soja, calcário e fosfato
como incógnitas e as equações de MS, PB, NDT, Ca e P (caroço de algodão e aditivos fixos). A resolução é por
**Gauss-Jordan com pivoteamento parcial** (`core/algebrico.py → gauss_jordan`), registrando cada operação
de linha (`L2 ← L2 − 0,09·L1`, etc.).
Cuidados que o app avisa: **quantidade negativa** (a matemática fecha, mas não existe "−2 kg de milho" →
troque alimentos) e **sistema sem solução única** (alimentos com composição proporcional ou equações
redundantes). FDN, EE e amido **não** entram como equação: são conferidos depois.

### 6.3 Computador: programação linear (PL) de mínimo custo
É o que os softwares comerciais de formulação fazem. Formulação (`core/otimizacao.py → otimizar`):

- **Variáveis**: kg de MS de cada alimento liberado.
- **Objetivo**: minimizar o custo = Σ (preço por kg de MS × kg). Preço por kg de MS = preço por kg MN ÷ MS.
- **Restrições**:
  - Σ kg = IMS (a vaca come exatamente a IMS);
  - PB ≥ meta, NDT ≥ meta, Ca ≥ meta, P ≥ meta, FDN ≥ mínimo;
  - EE ≤ máximo, **amido ≤ 26%** (pode desligar);
  - **Ca e P ≤ meta + 15%** (pode mudar ou desligar — ver abaixo);
  - limites mínimo/máximo por alimento; aditivos com quantidade fixa.
- **Solver**: `scipy.optimize.linprog` com o método HiGHS.

Três detalhes importantes:

1. **Restrições "elásticas"**: cada meta nutricional ganha uma variável de folga com custo altíssimo
   (R$ 10.000 por kg não atendido). Assim o otimizador **sempre** devolve uma ração e, se for impossível
   atender tudo com os alimentos escolhidos, diz **qual meta falhou e por quanto** — em vez de só
   responder "inviável".
2. **Teto de Ca e P**: sem ele, o calcário (barato e sem energia) virava "enchimento" para completar a IMS
   — chegou a dar 1,27% de Ca, o dobro da meta. O teto padrão é +15%.
3. **Relatório do otimizador**:
   - **Situação "ativa"**: a restrição está no limite e é ela que "segura" a fórmula.
   - **Valor marginal (preço-sombra)**: quanto o custo por vaca/dia muda se aquela meta aumentar 1 kg.
     Ex.: se PB tem valor marginal R$ 2,89/kg, exigir 1 kg a mais de PB encareceria a ração em ~R$ 2,89.
   - **Redução de preço para entrar**: para um alimento que ficou de fora, quanto o preço dele teria que
     cair para valer a pena usá-lo.

---

## 7. O silo e a lavoura

Silo trincheira: uma "vala" onde a silagem é compactada; todo dia se corta uma **fatia** da frente
(o painel). Contas (`core/silo.py → calcular_silo`), com padrões editáveis:

| Etapa | Conta | Padrão |
|---|---|---|
| Silagem por vaca (MN) | kg MS da ração ÷ MS% da silagem | — |
| Consumo do lote por dia | por vaca × nº de vacas | 130 vacas |
| Consumo no período | por dia × dias | 365 dias |
| Silagem a produzir | consumo ÷ (1 − perdas) | 15% de perdas |
| Volume do silo | silagem ÷ densidade | 600 kg/m³ |
| Área do painel | volume diário ÷ espessura da fatia | 0,25 m/dia |
| Largura (retangular) ou bases (trapézio) | área ÷ altura; no trapézio, fundo = (A − i·H²) ÷ H | altura 2,5 m, inclinação 0,25 |
| Comprimento | volume ÷ área do painel | divide em 2+ silos se passar de 60 m |
| Área a plantar | silagem (t) ÷ produtividade; recomendada com margem | 45 t/ha, margem 10% |

Por que a fatia importa: abrir o silo expõe a silagem ao ar; se a frente avançar devagar (< 15 cm/dia), ela
esquenta e estraga. Por isso o painel é dimensionado **a partir da fatia mínima**.

---

## 8. Como o código está organizado

```
racao-leite/
├── app.py               # ponto de entrada: menu (st.navigation), barra lateral, autosave
├── estado.py            # estado do projeto: valores padrão, salvar/abrir, campos que "lembram" o valor
├── comum.py             # cálculos que várias páginas usam + componentes de tabela/cartões
├── core/                # LÓGICA PURA — não importa Streamlit, é toda testada
│   ├── alimentos_padrao.py  # biblioteca de alimentos (CQBAL) e aditivos com justificativas
│   ├── nutricao.py          # Animal, Exigencias, metas, composição, avaliação, dicas, checklist, NRC
│   ├── algebrico.py         # monta o sistema e resolve por Gauss-Jordan registrando passos
│   ├── otimizacao.py        # programação linear de mínimo custo (scipy/HiGHS)
│   ├── silo.py              # dimensionamento do silo e da lavoura
│   ├── relatorio.py         # tabelas finais + exportação HTML e XLSX
│   └── formatar.py          # números no formato brasileiro (1.234,56)
├── paginas/             # uma tela por arquivo (só interface; as contas vêm de core/ e comum.py)
├── tests/               # pytest: cálculos + "teste de fumaça" que abre cada página sem navegador
├── dados/projeto.json   # projeto salvo automaticamente
├── .streamlit/config.toml   # tema (verde) e barra de ferramentas simplificada
├── .claude/launch.json      # usado pelo Claude para abrir o app no painel do navegador (pode ignorar)
└── requirements.txt, pytest.ini, .gitignore
```

### Fluxo de dados

```
 páginas (widgets)  ──escrevem──▶  st.session_state["projeto"]  ──autosave──▶  dados/projeto.json
        │                                   │
        │                          estado.animal(), estado.exig(), estado.alimentos()
        ▼                                   ▼
   comum.py  ──chama──▶  core/ (funções puras: dicionários entram, números/tabelas saem)
        │
        ▼
   tabelas, cartões, checklist, relatório
```

- **Representação**: uma ração é só um dicionário `{"nome do alimento": kg de MS}`; os alimentos são
  `{"nome": {"MS": ..., "PB": ..., ...}}`. Isso deixa `core/` simples e fácil de testar.
- **Por que `core/` não usa Streamlit**: para dar para testar as contas com `pytest` e reaproveitá-las em
  outra interface (ex.: uma API) sem reescrever nada.
- **Streamlit roda o script inteiro a cada clique.** Por isso tudo é recalculado sempre (é rápido) e não há
  botão "calcular".
- **`estado.campo(...)`**: o Streamlit apaga o valor de um campo quando você sai da página. Essa função
  guarda o valor em `projeto` e o devolve ao campo quando você volta — por isso nada se perde ao navegar.
- **`app.py`** roda a página antes de desenhar a barra lateral, para o resumo já mostrar o valor recém
  digitado, e no fim chama `estado.salvar()` (só grava se algo mudou).

### Testes (`tests/`)

| Arquivo | O que garante |
|---|---|
| `test_nutricao.py` | IMS = 24,308; metas em kg e %; somas de nutrientes; aditivos; cores; dicas; NRC |
| `test_algebrico.py` | Gauss-Jordan bate com o `numpy`; detecta sistema singular e solução negativa; o exemplo 5×5 fecha MS/PB/NDT/Ca/P exatamente |
| `test_otimizacao.py` | a ração ótima respeita todas as restrições; mínimos garantem 4 alimentos; caso impossível aponta a meta; teto de Ca/P |
| `test_silo.py` | contas do silo (exemplo conferido à mão), trapézio, divisão em silos; exportação HTML/XLSX |
| `test_app.py` | abre **cada página** do app sem navegador (`streamlit.testing`) e verifica que não há erro; edita um campo e salva uma tentativa |

---

## 9. Dados, arquivos e persistência

- **Autosave**: tudo vai para `dados/projeto.json` a cada alteração. Ao reabrir o app, continua de onde
  parou. (Dá para apontar outro arquivo com a variável de ambiente `RACAO_PROJETO` — os testes usam isso
  para não sujar seus dados.)
- **Baixar / Abrir projeto (.json)** — barra lateral: o arquivo contém o projeto **inteiro** (animal,
  alimentos, aditivos, as três rações, silo, título do relatório). Serve para backup, comparar cenários ou
  passar para um colega. **Abrir substitui tudo**; baixe o atual antes, se quiser guardá-lo.
- **Restaurar exemplo do trabalho** — volta todos os dados aos valores da folha do trabalho.
- **CSV de alimentos** — na tela Alimentos: troca **só** a tabela de alimentos (separador `;`, decimal `,`).
- **Relatório** — HTML (para PDF) e XLSX, gerados na hora na tela Relatório final.

---

## 10. Como mudar ou estender

- **Adicionar/alterar um alimento padrão**: edite a lista em `core/alimentos_padrao.py`. Para quem já
  tem um projeto salvo, adicione pela tela Alimentos (ou use "Restaurar alimentos padrão").
- **Mudar textos/doses dos aditivos**: `ADITIVOS_INFO` no mesmo arquivo.
- **Acrescentar um nutriente** (ex.: sódio): inclua a coluna em `COLUNAS` e nos alimentos, em
  `NUTRIENTES` (`core/nutricao.py`), crie a meta em `Exigencias`/`metas()` e o campo na tela Animal. O
  otimizador e a avaliação passam a considerá-lo automaticamente.
- **Mudar as regras do checklist**: `checklist()` em `core/nutricao.py`.
- **Deixar o relatório igual ao modelo do professor**: colunas em `df_ingredientes`/`df_nutrientes`/
  `df_animal` e o layout em `gerar_html` (CSS no topo) — tudo em `core/relatorio.py`.
- **Nova tela**: crie `paginas/9_nome.py` e registre em `app.py` (`st.Page(...)`).

Depois de qualquer mudança: `.venv\Scripts\python -m pytest -q`.

---

## 11. Limitações e cuidados

- **Valores dos alimentos**: médias do CQBAL 4.0 (consultadas em 18/11/2026). O **NDT** é o valor
  *calculado* pelo CQBAL (equação BR-Corte 2016). Para o **caroço de algodão** ele dá **96%**, bem acima de
  tabelas como o NRC 2001 (~77–80%) — ajuste se o professor preferir. O amido do feno de Tifton (n = 1),
  do farelo de trigo (n = 5) e da silagem de sorgo (n = 3) vem de poucas amostras. A **ureia** não está no
  CQBAL (usada a composição química: 45% N × 6,25).
- **Preços** são apenas referência; o resultado da ração 3 depende muito deles.
- **A estimativa NRC** da primeira tela é simplificada e só cobre energia e IMS (não estima proteína).
- **Ferramenta didática**: segue o modelo do trabalho (exigências em PB e NDT). Não substitui um
  nutricionista nem softwares profissionais para formular dietas de rebanhos reais.
