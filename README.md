# 🚗 AutoMarket Analytics

> Pipeline de Análise de Dados Completo para E-Commerce Automotivo  
> Da geração sintética de dados à modelagem de Machine Learning e dashboard interativo

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=flat&logo=pandas)](https://pandas.pydata.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.x-F7931E?style=flat&logo=scikit-learn)](https://scikit-learn.org)
[![SQLite](https://img.shields.io/badge/SQLite-3.x-003B57?style=flat&logo=sqlite)](https://sqlite.org)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.x-FF6384?style=flat&logo=chart.js)](https://chartjs.org)

---

## 📋 Descrição Geral

**AutoMarket Analytics** é um projeto end-to-end de ciência de dados aplicado a um e-commerce de veículos. O projeto demonstra cada etapa de um pipeline analítico profissional:

1. **Geração e limpeza** de um dataset simulado com 5.000 registros e ruídos realistas
2. **Armazenamento** em banco de dados SQLite com índices e queries avançadas
3. **Análise exploratória** (EDA) com estatísticas descritivas e visualizações
4. **Modelagem preditiva** com Regressão Linear, Ridge, Lasso e Decision Tree
5. **Segmentação RFM** adaptada ao contexto de veículos + K-Means para comparação
6. **Dashboard interativo** em HTML/JS com filtros dinâmicos e Chart.js

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Tecnologias |
|-----------|-------------|
| **Linguagem** | Python 3.10+ |
| **Manipulação de Dados** | Pandas, NumPy |
| **Machine Learning** | scikit-learn (LinearRegression, Ridge, Lasso, DecisionTree, KMeans) |
| **Estatística** | SciPy |
| **Banco de Dados** | SQLite 3 (via `sqlite3` nativo) |
| **Visualização Python** | Matplotlib, Seaborn |
| **Dashboard** | HTML5, JavaScript ES6+, Chart.js 4.4 |
| **Documentação** | Markdown, Node.js + docx |

---

## 📁 Estrutura do Projeto

```
automarket-analytics/
│
├── 📄 ecommerce_carros.py          # Geração do dataset + tratamento de dados
├── 📄 ecommerce_carros_db.py       # Exportação para banco SQLite
├── 📄 analise_estatistica.py       # EDA completa + visualizações
├── 📄 consultas_avancadas.sql      # Queries SQL avançadas (GROUP BY, Window Fn, CTEs)
├── 📄 outliers_correlacao.py       # Detecção de outliers (IQR + Z-score) + correlações
├── 📄 rfm_analise.py               # Segmentação RFM + K-Means clustering
├── 📄 ml_regressao.py              # Modelos de Machine Learning + avaliação
├── 📄 dashboard.html               # Dashboard interativo (autocontido)
│
├── 🗄️ ecommerce_carros.db          # Banco SQLite (tabela: anuncios)
├── 📊 dataset_ecommerce_carros.csv # Dataset tratado
├── 📊 rfm_resultados.csv           # Scores e segmentos RFM por modelo
├── 📊 dashboard_data.json          # Dados pré-processados para o dashboard
├── 📄 insights_documento.docx      # Documentação de insights (storytelling)
│
└── 📁 outputs/                     # Visualizações geradas
    ├── fig1_histograma_preco.png
    ├── fig2_boxplot_combustivel.png
    ├── fig3_barplot_modelos.png
    ├── fig4_serie_temporal.png
    ├── fig5_preco_anual_marca.png
    ├── out1_painel_outliers.png
    ├── out2_matriz_correlacao.png
    ├── out3_scatter_tendencia.png
    ├── out4_boxplot_combustivel.png
    ├── out5_boxplot_status.png
    ├── out6_comparacao_metodos.png
    ├── rfm1_painel_segmentos.png
    ├── rfm2_radar_segmentos.png
    ├── rfm3_kmeans_pca.png
    ├── rfm4_top_modelos_segmento.png
    ├── rfm5_tabela_visual.png
    ├── ml1_painel_modelos.png
    ├── ml2_feature_importance.png
    ├── ml3_residuos.png
    └── ml4_crossval.png
```

---

## ⚙️ Como Executar

### Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

### 1. Instalação de Dependências

```bash
pip install pandas numpy scipy matplotlib seaborn scikit-learn
```

> **Nota:** O módulo `sqlite3` já é nativo do Python — não requer instalação.

### 2. Execução Passo a Passo

Execute os scripts na ordem abaixo. Cada etapa depende da anterior.

```bash
# Etapa 1: Gerar dataset + tratamento + exportar CSV
python ecommerce_carros.py

# Etapa 2: Exportar para banco SQLite (.db)
python ecommerce_carros_db.py

# Etapa 3: Análise Exploratória (EDA) + gráficos
python analise_estatistica.py

# Etapa 4: Outliers + correlações
python outliers_correlacao.py

# Etapa 5: Segmentação RFM + K-Means
python rfm_analise.py

# Etapa 6: Modelos de Machine Learning
python ml_regressao.py
```

### 3. Executar o Dashboard

O dashboard é um único arquivo HTML autocontido. Basta abrir no navegador:

```bash
# macOS
open dashboard.html

# Linux
xdg-open dashboard.html

# Windows
start dashboard.html
```

> Não requer servidor web. Todos os 4.892 registros estão embutidos como JSON no próprio HTML.

### 4. Consultas SQL (opcional)

```bash
sqlite3 ecommerce_carros.db < consultas_avancadas.sql
```

---

## 📊 Etapas do Projeto em Detalhe

### Etapa 1 — Geração e Limpeza de Dados (`ecommerce_carros.py`)

**Geração:**
- 5.000 registros simulados com 6 colunas: `marca_modelo`, `ano_fabricacao`, `preco_brl`, `data_anuncio`, `combustivel`, `status`
- Ruídos introduzidos: ~4% de nulos por coluna, ~3% de duplicatas, 4 formatos distintos de data, preços em BRL e USD, variações de grafia nas categóricas

**Tratamento aplicado:**
- Remoção de 150 duplicatas exatas
- Preenchimento de nulos com mediana (numéricos) e moda (datas)
- Normalização de textos: `str.strip().str.title()`
- Limpeza e conversão de preços (regex para BRL e USD)
- Padronização final: data no formato `DD/MM/YYYY`, preço como `R$ XX.XXX,XX`

**Resultado:** 4.892 linhas limpas, zero nulos

---

### Etapa 2 — Banco de Dados SQLite (`ecommerce_carros_db.py`)

- Tabela `anuncios` com tipos nativos: `INTEGER`, `REAL`, `TEXT`
- Data armazenada em ISO 8601 (`YYYY-MM-DD`) para compatibilidade com filtros SQL
- 4 índices criados: `idx_status`, `idx_combustivel`, `idx_ano`, `idx_data`

---

### Etapa 3 — Análise Exploratória (`analise_estatistica.py`)

| Análise | Resultado |
|---------|-----------|
| Preço médio | R$ 80.230 |
| Desvio padrão | R$ 29.071 |
| Assimetria (skewness) | +0,03 (simétrico) |
| Curtose | +0,03 (mesocúrtica) |
| Pico de anúncios | Fev/2023 (364 anúncios) |
| Marca líder | Ford (13,1%) |

**5 gráficos gerados:** histograma + KDE, boxplot por combustível, barplot de modelos, série temporal, evolução de preço por marca.

---

### Etapa 4 — Consultas SQL Avançadas (`consultas_avancadas.sql`)

10 queries organizadas em 4 blocos:

| Bloco | Técnicas |
|-------|----------|
| GROUP BY | Agregações com `HAVING`, `SUM() OVER()` |
| CTEs + JOIN | Segmentação por faixa de preço |
| Window Functions | `RANK()`, `DENSE_RANK()`, `PERCENT_RANK()`, `NTILE()`, `LAG()`, `LEAD()`, médias móveis |
| Analíticas | Top-N por categoria, pivô com `CASE WHEN`, Z-score em SQL puro |

---

### Etapa 5 — Outliers e Correlação (`outliers_correlacao.py`)

**Outliers:**
- IQR: 40 outliers (0,82%) — limite superior R$ 155.801
- Z-score (±3σ): 10 outliers (0,20%) — acima de R$ 167.000
- Concordância entre métodos: 100% nos 10 casos mais extremos

**Correlação:**
- Pearson (Preço × Ano): r = +0,016 (p=0,27) → desprezível, não significativo
- ANOVA Combustível: F=1,08, p=0,37 → sem diferença significativa entre grupos

---

### Etapa 6 — Segmentação RFM (`rfm_analise.py`)

**Metodologia:** adaptação da análise RFM de clientes para modelos de veículos.

| Dimensão | Proxy | Peso |
|----------|-------|------|
| Recency | Dias desde o último anúncio | 25% |
| Frequency | Total de anúncios do modelo | 30% |
| Monetary | Preço médio do modelo | 45% |

**Segmentos:** Premium (8), Econômico (8), Baixa Relevância (9), Alto Volume (7)

**K-Means:** k=6 ótimo por silhouette score (0,396). Alta concordância com RFM nos segmentos extremos.

---

### Etapa 7 — Machine Learning (`ml_regressao.py`)

**Target:** `preco_brl`  
**Features:** ano de fabricação, idade, sazonalidade (sin/cos do mês), OHE de combustível, status e marca_modelo  
**Validação:** 80/20 split + 5-Fold Cross-Validation

| Modelo | R² | MAE | RMSE |
|--------|----|-----|------|
| Regressão Linear | −0,007 | R$ 22.773 | R$ 28.944 |
| Ridge (α=1) | −0,007 | R$ 22.773 | R$ 28.944 |
| Lasso (α=10) | −0,008 | R$ 22.776 | R$ 28.952 |
| Decision Tree | −0,135 | R$ 23.932 | R$ 30.723 |

> R² negativo é esperado: preços no dataset simulado foram gerados independentemente das features. Em dados reais, espera-se R² entre 0,75 e 0,90.

---

### Etapa 8 — Dashboard (`dashboard.html`)

**KPIs em tempo real:**
- Faturamento Total (vendidos): R$ 101,5 M
- Ticket Médio: R$ 80.837
- Taxa de Conversão: 25,7%
- Taxa de Churn: 74,3%

**Filtros interativos:** período, marca, combustível, status — atualizam todos os 9 gráficos simultaneamente.

**Tecnologia:** Chart.js 4.4 + JavaScript puro, sem dependência de servidor.

---

## 📈 Principais Resultados

```
┌────────────────────────────────────────────────────────────┐
│  Dataset          4.892 anúncios limpos (de 5.150 brutos)  │
│  Faturamento      R$ 101,5 M (apenas vendidos)             │
│  Ticket Médio     R$ 80.837                                │
│  Conversão        25,7% (Vendido / Total)                  │
│  Outliers IQR     40 veículos (0,82%)                      │
│  Segmento Premium 8 modelos — liderados por Chevrolet      │
│  Melhor Modelo ML Ridge — baseline para dados reais        │
│  Dashboard        9 gráficos + 8 KPIs + 4 filtros dinâm.  │
└────────────────────────────────────────────────────────────┘
```

---

## 🖼️ Exemplos de Saída

### Dataset tratado (primeiras linhas)

| marca_modelo | ano_fabricacao | preco_brl | data_anuncio | combustivel | status |
|---|---|---|---|---|---|
| Honda Civic | 2021 | R$ 94.901,42 | 17/08/2022 | Flex | Vendido |
| Toyota Corolla | 2011 | R$ 75.852,07 | 02/06/2023 | Não Informado | Disponível |
| Volkswagen Polo | 2022 | R$ 125.690,90 | 05/04/2022 | Gasolina | Reservado |

### Segmentação RFM

| Segmento | Modelos | Score Médio | Preço Médio |
|---|---|---|---|
| 🏆 Premium | 8 | 4,10 | R$ 83.070 |
| 📦 Alto Volume | 7 | 3,16 | R$ 79.223 |
| 💚 Econômico | 8 | 2,03 | R$ 78.223 |
| ⚠️ Baixa Relevância | 9 | 2,72 | R$ 80.634 |

---

## 🔮 Melhorias Futuras

- [ ] **Features reais:** integrar tabela FIPE via API oficial para enriquecer a precificação
- [ ] **Modelos avançados:** XGBoost, LightGBM, Random Forest para capturar não-linearidades
- [ ] **Modelo de conversão:** classificador binário (Vendido / Não vendido) com features comportamentais
- [ ] **API REST:** FastAPI + Uvicorn para servir predições em tempo real
- [ ] **Dados reais:** pipeline de ingestão via scraping de OLX/iCarros/Webmotors
- [ ] **Deploy:** containerização com Docker + deploy no Railway/Render
- [ ] **MLOps:** versionamento de modelos com MLflow + monitoramento de drift
- [ ] **Dashboard avançado:** migração para Streamlit ou Dash para filtros mais ricos
- [ ] **Sazonalidade:** modelagem com Prophet ou SARIMA para previsão de volume

---

## 📚 Referências

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [SQLite Window Functions](https://www.sqlite.org/windowfunctions.html)
- [Chart.js Documentation](https://www.chartjs.org/docs/latest/)
- [Tabela FIPE API](https://deividfortuna.github.io/fipe/)
- [RFM Analysis — A Practical Guide](https://www.putler.com/rfm-analysis/)

---

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais e demonstração de técnicas de ciência de dados. Os dados são inteiramente sintéticos e não representam nenhuma empresa ou plataforma real.

---

<div align="center">
  <strong>AutoMarket Analytics</strong> · Pipeline de Dados End-to-End · 2024–2025
</div>
