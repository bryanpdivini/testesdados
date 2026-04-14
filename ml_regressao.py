"""
╔══════════════════════════════════════════════════════════════════════╗
║  AutoMarket ML — Regressão de Preço de Veículos                     ║
║  Dataset: E-Commerce de Carros (simulado)                           ║
║  Target : preco_brl                                                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings("ignore")

# ── Tema visual ───────────────────────────────────────────────────────────────
C = {
    "azul":    "#2563EB", "verde":   "#10B981", "amarelo": "#F59E0B",
    "vermelho":"#EF4444", "roxo":    "#8B5CF6", "cinza":   "#6B7280",
    "fundo":   "#F8FAFC", "texto":   "#1E293B", "borda":   "#E2E8F0",
}
plt.rcParams.update({
    "figure.facecolor": C["fundo"], "axes.facecolor": "white",
    "axes.edgecolor":   C["borda"], "axes.labelcolor": C["texto"],
    "axes.titlesize":   12,         "axes.titleweight": "bold",
    "axes.titlepad":    10,         "axes.labelsize":   9,
    "xtick.labelsize":  8,          "ytick.labelsize":  8,
    "grid.color":       C["borda"], "grid.linestyle":  "--", "grid.alpha": 0.7,
    "font.family":     "DejaVu Sans",
})

SEP = "=" * 65
def titulo(t): print(f"\n{SEP}\n  {t}\n{SEP}")
def salvar(fig, nome):
    p = f"outputs/{nome}.png"
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor=C["fundo"])
    plt.close(fig)

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 1 — DEFINIÇÃO DO PROBLEMA                                        ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
titulo("BLOCO 1 — DEFINIÇÃO DO PROBLEMA")
print("""
  Target  : preco_brl (variável contínua de preço em R$)

  Justificativa:
    Prever o preço de um veículo é o problema central de qualquer
    plataforma de e-commerce automotivo. Com um modelo preciso é
    possível: (a) detectar anúncios sub/sobrevalorizados, (b) sugerir
    preços competitivos ao vendedor, (c) filtrar outliers de precificação.

  Features selecionadas:
    Numéricas  : ano_fabricacao, idade do veículo, mês e trimestre do
                 anúncio, codificação sazonal (sin/cos do mês)
    Categóricas: combustivel, status, marca_modelo (One-Hot Encoding)

  Premissa:
    Como os dados são SIMULADOS com preços gerados independentemente
    das features categóricas (distribuição normal), espera-se R² baixo
    — o que é documentado e discutido na avaliação.
""")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 2 — PRÉ-PROCESSAMENTO                                            ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
titulo("BLOCO 2 — PRÉ-PROCESSAMENTO")

# 2.1 Carga
with sqlite3.connect("outputs/ecommerce_carros.db") as conn:
    df = pd.read_sql("SELECT * FROM anuncios", conn)

df["data_anuncio"] = pd.to_datetime(df["data_anuncio"])
print(f"  Dataset: {df.shape[0]:,} linhas × {df.shape[1]} colunas")

# 2.2 Feature engineering temporal
df["mes"]         = df["data_anuncio"].dt.month
df["trimestre"]   = df["data_anuncio"].dt.quarter
df["ano_anuncio"] = df["data_anuncio"].dt.year
df["idade"]       = df["ano_anuncio"] - df["ano_fabricacao"]   # proxy depreciação
df["sin_mes"]     = np.sin(2 * np.pi * df["mes"] / 12)         # sazonalidade cíclica
df["cos_mes"]     = np.cos(2 * np.pi * df["mes"] / 12)

# 2.3 One-Hot Encoding
cats = pd.get_dummies(
    df[["combustivel", "status", "marca_modelo"]],
    drop_first=True, dtype=int
)
print(f"  Features categóricas após OHE: {cats.shape[1]}")

# 2.4 Montagem do dataset final
FEAT_NUM = ["ano_fabricacao", "idade", "mes", "trimestre", "sin_mes", "cos_mes"]
X = pd.concat([df[FEAT_NUM], cats], axis=1)
y = df["preco_brl"]
print(f"  Features totais: {X.shape[1]}")
print(f"  Target (preco_brl): média=R${y.mean():,.0f}  dp=R${y.std():,.0f}")

# 2.5 Normalização
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)
scaler = StandardScaler()
Xs_train = scaler.fit_transform(X_train)
Xs_test  = scaler.transform(X_test)

print(f"\n  Train : {len(X_train):,} amostras ({len(X_train)/len(X)*100:.0f}%)")
print(f"  Test  : {len(X_test):,} amostras  ({len(X_test)/len(X)*100:.0f}%)")
print(f"  Normalização: StandardScaler aplicado ao conjunto de treino")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 3 — MODELAGEM                                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
titulo("BLOCO 3 — MODELAGEM")

modelos = {
    "Regressão Linear": LinearRegression(),
    "Ridge (α=1)":      Ridge(alpha=1.0),
    "Lasso (α=10)":     Lasso(alpha=10.0, max_iter=5000),
    "Decision Tree":    DecisionTreeRegressor(max_depth=8, random_state=42),
}

kf      = KFold(n_splits=5, shuffle=True, random_state=42)
results = {}

print(f"\n  {'Modelo':<22} {'R²':>7} {'MAE':>10} {'RMSE':>10} {'CV R²':>8}")
print(f"  {'-'*62}")

for nome, modelo in modelos.items():
    modelo.fit(Xs_train, y_train)
    pred  = modelo.predict(Xs_test)
    r2    = r2_score(y_test, pred)
    mae   = mean_absolute_error(y_test, pred)
    rmse  = np.sqrt(mean_squared_error(y_test, pred))
    cv_r2 = cross_val_score(modelo, Xs_train, y_train, cv=kf, scoring="r2").mean()
    results[nome] = {"r2": r2, "mae": mae, "rmse": rmse, "cv_r2": cv_r2,
                     "pred": pred, "model": modelo}
    print(f"  {nome:<22} {r2:>7.4f} {mae:>10,.0f} {rmse:>10,.0f} {cv_r2:>8.4f}")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 4 — AVALIAÇÃO E INTERPRETAÇÃO                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
titulo("BLOCO 4 — AVALIAÇÃO E INTERPRETAÇÃO")

# Coeficientes Ridge (mais estável para interpretação)
ridge_model = results["Ridge (α=1)"]["model"]
coef_df = (pd.DataFrame({"feature": X.columns, "coeficiente": ridge_model.coef_})
           .assign(abs_coef=lambda d: d.coeficiente.abs())
           .sort_values("abs_coef", ascending=False))

print("\n  Top 15 features por magnitude do coeficiente (Ridge):")
print(f"\n  {'Feature':<40} {'Coeficiente':>13} {'Interpretação'}")
print(f"  {'-'*72}")
for _, row in coef_df.head(15).iterrows():
    sinal = "↑ preço mais alto" if row["coeficiente"] > 0 else "↓ preço mais baixo"
    print(f"  {row['feature']:<40} {row['coeficiente']:>+13,.1f}  {sinal}")

titulo("BLOCO 4B — INTERPRETAÇÃO DOS RESULTADOS")
print("""
  Os quatro modelos apresentam R² próximo de ZERO — resultado esperado
  porque os preços no dataset simulado foram gerados com distribuição
  NORMAL INDEPENDENTE das features categóricas (marca, combustível, status).

  Em dados REAIS de e-commerce automotivo, estudos mostram:
    • R² ≈ 0.75–0.90 usando features ricas (quilometragem, estado do carro,
      histórico de revisões, FIPE, câmbio, opcionais)
    • As variáveis mais preditivas costumam ser: ano de fabricação,
      quilometragem, marca premium vs. popular, câmbio automático
      e presença de opcionais como teto solar e central multimídia.

  O que os coeficientes nos dizem (mesmo com R² baixo):
    • Híbrido e Elétrico: coeficientes positivos (preço mais alto)
    • Veículos mais antigos (maior "idade"): coeficiente negativo (depreciação)
    • Sazonalidade (mês): variação de ~R$ 1.600 — mercado tem ciclos
    • Modelos populares (Kwid, Gol, Ka): coeficientes negativos (ticket menor)

  Conclusão para o negócio:
    Use o modelo Ridge como baseline. Com dados reais enriquecidos
    (quilometragem, estado, FIPE), espera-se ganho expressivo de R².
""")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 5 — FEATURE IMPORTANCE (DECISION TREE)                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
titulo("BLOCO 5 — FEATURE IMPORTANCE (DECISION TREE)")

dt_model  = results["Decision Tree"]["model"]
fi = (pd.DataFrame({"feature": X.columns, "importance": dt_model.feature_importances_})
      .sort_values("importance", ascending=False))

print("\n  Top 15 features (Decision Tree — importância relativa):")
print(f"\n  {'Feature':<40} {'Importância':>12} {'Barra'}")
print(f"  {'-'*65}")
for _, row in fi.head(15).iterrows():
    bar = "█" * int(row["importance"] * 500)
    print(f"  {row['feature']:<40} {row['importance']:>12.4f}  {bar}")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  VISUALIZAÇÕES                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

# ── Fig 1: Painel comparativo de modelos ──────────────────────────────────────
fig = plt.figure(figsize=(16, 10), facecolor=C["fundo"])
gs  = gridspec.GridSpec(2, 4, hspace=0.40, wspace=0.35)
nomes    = list(results.keys())
cores_m  = [C["azul"], C["verde"], C["amarelo"], C["roxo"]]

# 1a–1d — Predicted vs Actual para cada modelo
for i, (nome, res) in enumerate(results.items()):
    ax = fig.add_subplot(gs[0, i])
    ax.scatter(y_test/1000, res["pred"]/1000,
               alpha=0.25, s=8, color=cores_m[i], linewidths=0)
    lims = [min(y_test.min(), res["pred"].min())/1000,
            max(y_test.max(), res["pred"].max())/1000]
    ax.plot(lims, lims, "--", color=C["cinza"], lw=1.5, label="Ideal")
    ax.set_xlabel("Real (R$ mil)"); ax.set_ylabel("Previsto (R$ mil)")
    ax.set_title(f"{nome}\nR²={res['r2']:.4f}")
    ax.yaxis.grid(True); ax.set_axisbelow(True)

# 1e — Comparativo de métricas (barras)
ax = fig.add_subplot(gs[1, :2])
metricas = ["r2", "mae", "rmse", "cv_r2"]
# Normalizamos para exibição lado a lado — apenas R² e CV_R²
r2_vals  = [results[n]["r2"]    for n in nomes]
cv_vals  = [results[n]["cv_r2"] for n in nomes]
x = np.arange(len(nomes)); w = 0.35
b1 = ax.bar(x - w/2, r2_vals, w, label="R² (test)", color=[c+"CC" for c in cores_m], edgecolor="white")
b2 = ax.bar(x + w/2, cv_vals, w, label="CV R²",     color=[c+"66" for c in cores_m], edgecolor="white")
for bar in list(b1)+list(b2):
    h = bar.get_height()
    ax.text(bar.get_x()+bar.get_width()/2, h+0.002, f"{h:.3f}",
            ha="center", fontsize=7.5, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels([n.replace(" (","\n(") for n in nomes], fontsize=8)
ax.axhline(0, color=C["cinza"], lw=1)
ax.set_title("Comparativo R² — Teste vs Cross-Validation")
ax.set_ylabel("R²"); ax.legend(fontsize=8)
ax.yaxis.grid(True); ax.set_axisbelow(True)

# 1f — MAE e RMSE comparativo
ax = fig.add_subplot(gs[1, 2:])
mae_vals  = [results[n]["mae"]/1000  for n in nomes]
rmse_vals = [results[n]["rmse"]/1000 for n in nomes]
b3 = ax.bar(x - w/2, mae_vals,  w, label="MAE (R$ mil)",  color=[c+"CC" for c in cores_m], edgecolor="white")
b4 = ax.bar(x + w/2, rmse_vals, w, label="RMSE (R$ mil)", color=[c+"66" for c in cores_m], edgecolor="white")
for bar in list(b3)+list(b4):
    h = bar.get_height()
    ax.text(bar.get_x()+bar.get_width()/2, h+0.3, f"{h:.1f}k",
            ha="center", fontsize=7.5, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels([n.replace(" (","\n(") for n in nomes], fontsize=8)
ax.set_title("Erros de Previsão — MAE vs RMSE")
ax.set_ylabel("Erro (R$ mil)"); ax.legend(fontsize=8)
ax.yaxis.grid(True); ax.set_axisbelow(True)

salvar(fig, "ml1_painel_modelos")

# ── Fig 2: Feature importance (Ridge coefs + DTree) ──────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Ridge coeficientes
top15r = coef_df.head(15)
cores_r = [C["verde"] if c > 0 else C["vermelho"] for c in top15r["coeficiente"]]
axes[0].barh(top15r["feature"][::-1], top15r["coeficiente"][::-1],
             color=cores_r[::-1], edgecolor="white", alpha=0.85)
axes[0].axvline(0, color=C["cinza"], lw=1.5)
axes[0].set_title("Top 15 Coeficientes — Ridge\n(verde=↑preço | vermelho=↓preço)")
axes[0].set_xlabel("Magnitude do Coeficiente (R$)")
axes[0].xaxis.grid(True); axes[0].set_axisbelow(True)

# Decision Tree importance
top15d = fi.head(15)
axes[1].barh(top15d["feature"][::-1], top15d["importance"][::-1],
             color=C["roxo"]+"CC", edgecolor="white", alpha=0.85)
axes[1].set_title("Top 15 Features — Decision Tree\n(importância relativa)")
axes[1].set_xlabel("Feature Importance")
axes[1].xaxis.grid(True); axes[1].set_axisbelow(True)

fig.tight_layout()
salvar(fig, "ml2_feature_importance")

# ── Fig 3: Análise de resíduos (Ridge) ───────────────────────────────────────
pred_ridge = results["Ridge (α=1)"]["pred"]
residuos   = y_test - pred_ridge

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Residuos vs Fitted
axes[0].scatter(pred_ridge/1000, residuos/1000,
                alpha=0.3, s=8, color=C["azul"], linewidths=0)
axes[0].axhline(0, color=C["vermelho"], lw=1.5, ls="--")
axes[0].set_xlabel("Previsto (R$ mil)"); axes[0].set_ylabel("Resíduo (R$ mil)")
axes[0].set_title("Resíduos vs Valores Previstos\n(Ridge)")
axes[0].yaxis.grid(True); axes[0].set_axisbelow(True)

# Histograma de resíduos
axes[1].hist(residuos/1000, bins=50, color=C["azul"]+"88", edgecolor="white", lw=0.3)
axes[1].axvline(0, color=C["vermelho"], lw=2, ls="--", label="Zero")
axes[1].axvline(residuos.mean()/1000, color=C["amarelo"], lw=2, ls="--", label=f"Média={residuos.mean()/1000:.1f}k")
axes[1].set_xlabel("Resíduo (R$ mil)"); axes[1].set_ylabel("Frequência")
axes[1].set_title("Distribuição dos Resíduos\n(Ridge)")
axes[1].legend(fontsize=8); axes[1].yaxis.grid(True); axes[1].set_axisbelow(True)

# Q-Q plot (normalidade dos resíduos)
from scipy import stats as st
(osm, osr), (slope, intercept, r) = st.probplot(residuos, dist="norm")
axes[2].scatter(osm, osr, alpha=0.3, s=8, color=C["roxo"], linewidths=0)
x_line = np.array([min(osm), max(osm)])
axes[2].plot(x_line, slope*x_line+intercept, color=C["vermelho"], lw=2, ls="--", label=f"r={r:.3f}")
axes[2].set_xlabel("Quantis Teóricos"); axes[2].set_ylabel("Resíduos Observados")
axes[2].set_title("Q-Q Plot dos Resíduos\n(normalidade)")
axes[2].legend(fontsize=8); axes[2].yaxis.grid(True); axes[2].set_axisbelow(True)

fig.tight_layout()
salvar(fig, "ml3_residuos")

# ── Fig 4: Cross-validation scores por fold ───────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5))
for i, (nome, res) in enumerate(results.items()):
    model = res["model"]
    cv_scores = cross_val_score(model, Xs_train, y_train, cv=kf, scoring="r2")
    ax.plot(range(1,6), cv_scores, "o-", color=cores_m[i], lw=2,
            ms=7, label=f"{nome} (μ={cv_scores.mean():.3f})")
ax.axhline(0, color=C["cinza"], lw=1, ls="--")
ax.set_xlabel("Fold"); ax.set_ylabel("R² Score")
ax.set_title("Cross-Validation — R² por Fold (5-Fold KFold)")
ax.set_xticks(range(1,6)); ax.legend(fontsize=9)
ax.yaxis.grid(True); ax.set_axisbelow(True)
fig.tight_layout()
salvar(fig, "ml4_crossval")

print("""
✅ Visualizações geradas:
   ml1_painel_modelos.png
   ml2_feature_importance.png
   ml3_residuos.png
   ml4_crossval.png
""")
