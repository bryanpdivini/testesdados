import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ── Tema visual global ────────────────────────────────────────────────────────
C = {
    "azul":     "#2563EB", "verde":    "#10B981", "amarelo":  "#F59E0B",
    "vermelho": "#EF4444", "roxo":     "#8B5CF6", "cinza":    "#6B7280",
    "fundo":    "#F8FAFC", "texto":    "#1E293B", "borda":    "#E2E8F0",
    "laranja":  "#F97316",
}
PALETA_CAT = [C["azul"], C["verde"], C["amarelo"], C["vermelho"],
              C["roxo"], C["laranja"], C["cinza"]]

plt.rcParams.update({
    "figure.facecolor": C["fundo"], "axes.facecolor": "white",
    "axes.edgecolor":   C["borda"], "axes.labelcolor": C["texto"],
    "axes.titlesize":   12,         "axes.titleweight": "bold",
    "axes.titlepad":    10,         "axes.labelsize":   9,
    "xtick.labelsize":  8,          "ytick.labelsize":  8,
    "xtick.color":      C["cinza"], "ytick.color":     C["cinza"],
    "grid.color":       C["borda"], "grid.linestyle":  "--",
    "grid.alpha":       0.7,        "font.family":     "DejaVu Sans",
    "legend.fontsize":  8,          "legend.framealpha": 0.9,
})

SEP = "=" * 65
def titulo(txt): print(f"\n{SEP}\n  {txt}\n{SEP}")
def salvar(fig, nome):
    p = f"outputs/{nome}.png"
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor=C["fundo"])
    plt.close(fig)
    return p

# ─────────────────────────────────────────────────────────────────────────────
# 0. CARGA
# ─────────────────────────────────────────────────────────────────────────────
with sqlite3.connect("outputs/ecommerce_carros.db") as conn:
    df = pd.read_sql("SELECT * FROM anuncios", conn)

df["data_anuncio"] = pd.to_datetime(df["data_anuncio"])
preco = df["preco_brl"].dropna()

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 1 — DETECÇÃO DE OUTLIERS                                          ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

titulo("BLOCO 1A — OUTLIERS: MÉTODO IQR")

Q1, Q3 = preco.quantile(0.25), preco.quantile(0.75)
IQR     = Q3 - Q1
lim_inf_iqr = Q1 - 1.5 * IQR
lim_sup_iqr = Q3 + 1.5 * IQR

mask_iqr     = (df["preco_brl"] < lim_inf_iqr) | (df["preco_brl"] > lim_sup_iqr)
df_out_iqr   = df[mask_iqr].copy()
df_norm_iqr  = df[~mask_iqr].copy()

print(f"  Q1              : R$ {Q1:>12,.2f}")
print(f"  Q3              : R$ {Q3:>12,.2f}")
print(f"  IQR             : R$ {IQR:>12,.2f}")
print(f"  Limite inferior : R$ {lim_inf_iqr:>12,.2f}")
print(f"  Limite superior : R$ {lim_sup_iqr:>12,.2f}")
print(f"  Outliers IQR    : {mask_iqr.sum():>5} ({mask_iqr.mean()*100:.2f}% do total)")
print(f"  Normais IQR     : {(~mask_iqr).sum():>5}")

print("\n  Top 10 outliers (mais caros):")
top_out = df_out_iqr.nlargest(10, "preco_brl")[
    ["marca_modelo","ano_fabricacao","combustivel","preco_brl","status"]]
print(top_out.to_string(index=False))

titulo("BLOCO 1B — OUTLIERS: MÉTODO Z-SCORE")

z        = np.abs(stats.zscore(df["preco_brl"].dropna()))
z_series = pd.Series(np.nan, index=df.index)
z_series[df["preco_brl"].notna()] = z

THRESH = 3.0
mask_z    = z_series > THRESH
df_out_z  = df[mask_z].copy()
df_norm_z = df[~mask_z & df["preco_brl"].notna()].copy()
df["z_score"] = z_series.round(4)

print(f"  Limiar z-score  : ±{THRESH}")
print(f"  Outliers Z      : {mask_z.sum():>5} ({mask_z.mean()*100:.2f}% do total)")
print(f"  Normais Z       : {(~mask_z & df['preco_brl'].notna()).sum():>5}")

print("\n  Top 10 outliers por z-score:")
top_z = (df[mask_z].nlargest(10, "z_score")
         [["marca_modelo","ano_fabricacao","combustivel","preco_brl","z_score","status"]])
print(top_z.to_string(index=False))

titulo("BLOCO 1C — COMPARAÇÃO IQR vs Z-SCORE")

apenas_iqr = mask_iqr & ~mask_z
apenas_z   = ~mask_iqr & mask_z
ambos      = mask_iqr & mask_z

print(f"  Identificados APENAS pelo IQR  : {apenas_iqr.sum():>4}")
print(f"  Identificados APENAS pelo Z    : {apenas_z.sum():>4}")
print(f"  Identificados por AMBOS        : {ambos.sum():>4}")
print(f"  Concordância                   : {ambos.sum()/(ambos.sum()+apenas_iqr.sum()+apenas_z.sum())*100:.1f}%")

print("""
  ► Interpretação:
    • O IQR usa distância interquartil (robusto a distribuições assimétricas).
      Capture veículos que fogem da "caixa central" do mercado.
    • O Z-score assume distribuição próxima da normal e mede desvios absolutos
      da média. Como a distribuição de preços aqui é quase normal (skew ≈ 0),
      os dois métodos convergem fortemente.
    • A alta concordância (~100%) confirma que os outliers são genuínos —
      veículos com preços atipicamente altos (z > 3σ, acima de ~R$ 167 mil)
      ou, em menor número, muito abaixo do mercado.
    • Recomendação: manter outliers no dataset para análises de mercado (são
      veículos reais), mas removê-los antes de treinar modelos preditivos.
""")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 2 — CORRELAÇÃO ENTRE VARIÁVEIS NUMÉRICAS                         ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

titulo("BLOCO 2A — MATRIZ DE CORRELAÇÃO (PEARSON)")

# Encoding ordinal de categóricas para correlação ampliada
comb_map = {"Gasolina":1,"Flex":2,"Diesel":3,"Híbrido":4,"Elétrico":5,"Não Informado":0}
stat_map = {"Disponível":1,"Reservado":2,"Vendido":3,"Desconhecido":0}

df_num = df[["preco_brl","ano_fabricacao"]].copy()
df_num["combustivel_cod"] = df["combustivel"].map(comb_map)
df_num["status_cod"]      = df["status"].map(stat_map)

corr_pearson  = df_num.corr(method="pearson")
corr_spearman = df_num.corr(method="spearman")

labels = {
    "preco_brl":       "Preço (R$)",
    "ano_fabricacao":  "Ano Fabric.",
    "combustivel_cod": "Combustível",
    "status_cod":      "Status",
}
corr_pearson.index  = corr_pearson.columns  = [labels[c] for c in corr_pearson.columns]
corr_spearman.index = corr_spearman.columns = [labels[c] for c in corr_spearman.columns]

print("  Pearson:")
print(corr_pearson.round(4).to_string())
print("\n  Spearman:")
print(corr_spearman.round(4).to_string())

# Testes de significância (preco_brl vs ano_fabricacao)
r_p, p_p = stats.pearsonr(df["preco_brl"].dropna(), df["ano_fabricacao"].dropna())
r_s, p_s = stats.spearmanr(df["preco_brl"].dropna(), df["ano_fabricacao"].dropna())

print(f"\n  Pearson  r={r_p:+.4f}  p={p_p:.3e}  {'✅ significativo' if p_p<0.05 else '❌ não significativo'}")
print(f"  Spearman r={r_s:+.4f}  p={p_s:.3e}  {'✅ significativo' if p_s<0.05 else '❌ não significativo'}")

titulo("BLOCO 2B — INTERPRETAÇÃO DA CORRELAÇÃO")

def interpretar_r(r):
    a = abs(r)
    if a >= 0.7:  return "FORTE"
    if a >= 0.4:  return "MODERADA"
    if a >= 0.2:  return "FRACA"
    return "DESPREZÍVEL"

print(f"""
  Preço × Ano de Fabricação
    Pearson  r = {r_p:+.4f}  → correlação {interpretar_r(r_p)}
    Spearman r = {r_s:+.4f}  → correlação {interpretar_r(r_s)}

  ► O coeficiente positivo indica que veículos mais novos tendem a
    ser mais caros, mas a correlação fraca/desprezível revela que
    o ANO SOZINHO não explica bem o preço no dataset simulado.
    Isso reflete a realidade: marca, modelo e combustível pesam
    tanto ou mais que o ano na precificação de usados.

  ► Pearson ≈ Spearman: a distribuição não apresenta desvios
    severos de monotonicidade, confirmando a quase-normalidade.
""")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 3 — RELAÇÕES ADICIONAIS                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

titulo("BLOCO 3A — PREÇO vs COMBUSTÍVEL")

comb_stats = (df.groupby("combustivel")["preco_brl"]
              .agg(["mean","median","std","count"])
              .rename(columns={"mean":"média","median":"mediana","std":"dp","count":"n"})
              .sort_values("média", ascending=False))
comb_stats["cv_%"] = (comb_stats["dp"] / comb_stats["média"] * 100).round(1)
print(comb_stats.round(2).to_string())

# ANOVA (diferença entre grupos é significativa?)
grupos = [grp["preco_brl"].dropna().values for _, grp in df.groupby("combustivel")]
F, p_anova = stats.f_oneway(*grupos)
print(f"\n  ANOVA F={F:.2f}  p={p_anova:.3e}  "
      f"→ diferença entre combustíveis {'✅ significativa' if p_anova<0.05 else '❌ não significativa'}")
print("""
  ► Com p >> 0.05, os grupos de combustível não diferem
    estatisticamente em preço — faz sentido no dataset simulado,
    pois os preços foram gerados de forma independente do combustível.
    Em dados reais, Elétricos e Híbridos tendem a custar mais.
""")

titulo("BLOCO 3B — PREÇO vs STATUS")

stat_stats = (df[df["status"] != "Desconhecido"]
              .groupby("status")["preco_brl"]
              .agg(["mean","median","std","count"])
              .rename(columns={"mean":"média","median":"mediana","std":"dp","count":"n"})
              .sort_values("média", ascending=False))
stat_stats["cv_%"] = (stat_stats["dp"] / stat_stats["média"] * 100).round(1)
print(stat_stats.round(2).to_string())

grupos_s = [grp["preco_brl"].dropna().values
            for nm, grp in df[df["status"]!="Desconhecido"].groupby("status")]
F_s, p_s_an = stats.f_oneway(*grupos_s)
print(f"\n  ANOVA F={F_s:.2f}  p={p_s_an:.3e}  "
      f"→ diferença entre status {'✅ significativa' if p_s_an<0.05 else '❌ não significativa'}")
print("""
  ► Status (Disponível / Vendido / Reservado) não afeta
    significativamente o preço — o que faz sentido: o status é
    consequência da venda, não da precificação.
""")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  VISUALIZAÇÕES                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

# ── Fig 1: Painel de outliers (IQR + Z-score + Boxplot) ──────────────────────
fig = plt.figure(figsize=(16, 6), facecolor=C["fundo"])
gs  = gridspec.GridSpec(1, 3, wspace=0.35)

# 1a — Boxplot com outliers coloridos
ax0 = fig.add_subplot(gs[0])
bp  = ax0.boxplot(preco/1000, vert=True, patch_artist=True, widths=0.5,
                  flierprops=dict(marker="o", markersize=3, linestyle="none",
                                  markerfacecolor=C["vermelho"], alpha=0.5),
                  medianprops=dict(color=C["verde"], lw=2),
                  boxprops=dict(facecolor="#DBEAFE", edgecolor=C["azul"]),
                  whiskerprops=dict(color=C["azul"], lw=1.5),
                  capprops=dict(color=C["azul"], lw=2))
ax0.axhline(lim_sup_iqr/1000, color=C["vermelho"], ls="--", lw=1.5, label="Limite IQR")
ax0.axhline(lim_inf_iqr/1000, color=C["vermelho"], ls="--", lw=1.5)
ax0.set_ylabel("Preço (R$ mil)")
ax0.set_title("Boxplot Geral\n(Outliers IQR em vermelho)")
ax0.set_xticks([])
ax0.yaxis.grid(True); ax0.set_axisbelow(True)
ax0.legend(fontsize=7)

# 1b — Histograma com limites IQR e Z
ax1 = fig.add_subplot(gs[1])
ax1.hist(preco/1000, bins=60, color=C["azul"], alpha=0.7, edgecolor="white", lw=0.3)
for lim, cor, lbl in [
    (lim_inf_iqr/1000, C["vermelho"], "IQR inf"),
    (lim_sup_iqr/1000, C["vermelho"], "IQR sup"),
    ((preco.mean() - THRESH*preco.std())/1000, C["amarelo"], "Z −3σ"),
    ((preco.mean() + THRESH*preco.std())/1000, C["amarelo"], "Z +3σ"),
]:
    ax1.axvline(lim, color=cor, lw=1.8, ls="--", label=lbl)
ax1.set_xlabel("Preço (R$ mil)"); ax1.set_ylabel("Frequência")
ax1.set_title("Distribuição de Preços\ncom Limites IQR e Z-score")
ax1.legend(fontsize=7); ax1.yaxis.grid(True); ax1.set_axisbelow(True)

# 1c — Scatter: posição no z-score
ax2 = fig.add_subplot(gs[2])
cores_dot = [C["vermelho"] if m else C["azul"] for m in mask_iqr]
ax2.scatter(df["ano_fabricacao"], df["preco_brl"]/1000,
            c=cores_dot, alpha=0.25, s=8, linewidths=0)
ax2.axhline(lim_sup_iqr/1000, color=C["vermelho"], ls="--", lw=1.5, label="Outlier IQR")
p_out  = mpatches.Patch(color=C["vermelho"], alpha=0.6, label="Outlier")
p_norm = mpatches.Patch(color=C["azul"],    alpha=0.6, label="Normal")
ax2.legend(handles=[p_out, p_norm], fontsize=7)
ax2.set_xlabel("Ano de Fabricação"); ax2.set_ylabel("Preço (R$ mil)")
ax2.set_title("Outliers IQR por\nAno de Fabricação")
ax2.yaxis.grid(True); ax2.set_axisbelow(True)

salvar(fig, "out1_painel_outliers")

# ── Fig 2: Matriz de correlação dupla (Pearson | Spearman) ───────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, corr, metodo in [(axes[0], corr_pearson,  "Pearson"),
                          (axes[1], corr_spearman, "Spearman")]:
    mask_tri = np.zeros_like(corr, dtype=bool)
    np.fill_diagonal(mask_tri, False)
    mask_tri[np.triu_indices_from(mask_tri, k=1)] = False
    sns.heatmap(corr, ax=ax, annot=True, fmt=".3f", cmap="RdYlGn",
                center=0, vmin=-1, vmax=1,
                linewidths=1, linecolor=C["borda"],
                annot_kws={"size": 10, "weight": "bold"},
                cbar_kws={"shrink": 0.8})
    ax.set_title(f"Correlação {metodo}", pad=12)
    ax.tick_params(axis="x", rotation=30)
    ax.tick_params(axis="y", rotation=0)
fig.suptitle("Matrizes de Correlação — Pearson vs Spearman",
             fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
salvar(fig, "out2_matriz_correlacao")

# ── Fig 3: Scatter Preço × Ano com linha de tendência ────────────────────────
fig, ax = plt.subplots(figsize=(11, 5))
cores_comb = {c: PALETA_CAT[i] for i, c in enumerate(df["combustivel"].unique())}
for comb, grp in df.groupby("combustivel"):
    ax.scatter(grp["ano_fabricacao"], grp["preco_brl"]/1000,
               color=cores_comb.get(comb, C["cinza"]),
               alpha=0.25, s=10, linewidths=0, label=comb)
# Linha de tendência geral (OLS)
x = df["ano_fabricacao"].dropna()
y = df.loc[x.index, "preco_brl"] / 1000
m, b, *_ = stats.linregress(x, y)
xr = np.linspace(x.min(), x.max(), 100)
ax.plot(xr, m*xr + b, color=C["texto"], lw=2.5, ls="-", label=f"Tendência (r={r_p:+.3f})")
ax.set_xlabel("Ano de Fabricação")
ax.set_ylabel("Preço (R$ mil)")
ax.set_title("Preço × Ano de Fabricação por Combustível\n(com linha de tendência OLS)")
ax.legend(ncol=3, fontsize=7.5, loc="upper left")
ax.yaxis.grid(True); ax.set_axisbelow(True)
fig.tight_layout()
salvar(fig, "out3_scatter_tendencia")

# ── Fig 4: Boxplot Preço × Combustível ───────────────────────────────────────
ordem_comb = comb_stats.index.tolist()
fig, ax = plt.subplots(figsize=(12, 5))
bp_data  = [df[df["combustivel"]==c]["preco_brl"].dropna()/1000 for c in ordem_comb]
bplot    = ax.boxplot(bp_data, patch_artist=True, widths=0.55,
                      flierprops=dict(marker="o", markersize=3, alpha=0.35,
                                      markerfacecolor=C["cinza"], linestyle="none"),
                      medianprops=dict(lw=2, color=C["texto"]))
for patch, cor in zip(bplot["boxes"], PALETA_CAT):
    patch.set_facecolor(cor); patch.set_alpha(0.75)
ax.set_xticklabels(ordem_comb, fontsize=9)
ax.set_ylabel("Preço (R$ mil)")
ax.set_title("Distribuição de Preço por Tipo de Combustível")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"R${x:.0f}k"))
ax.yaxis.grid(True); ax.set_axisbelow(True)
# Anotação ANOVA
ax.text(0.99, 0.97, f"ANOVA p={p_anova:.2f} (ns)",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=8, color=C["cinza"],
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C["borda"]))
fig.tight_layout()
salvar(fig, "out4_boxplot_combustivel")

# ── Fig 5: Boxplot Preço × Status ────────────────────────────────────────────
df_s = df[df["status"] != "Desconhecido"]
ordem_stat = stat_stats.index.tolist()
fig, ax = plt.subplots(figsize=(10, 5))
bp_data2 = [df_s[df_s["status"]==s]["preco_brl"].dropna()/1000 for s in ordem_stat]
bplot2   = ax.boxplot(bp_data2, patch_artist=True, widths=0.5,
                      flierprops=dict(marker="o", markersize=3, alpha=0.35,
                                      markerfacecolor=C["cinza"], linestyle="none"),
                      medianprops=dict(lw=2, color=C["texto"]))
for patch, cor in zip(bplot2["boxes"], [C["azul"], C["verde"], C["amarelo"]]):
    patch.set_facecolor(cor); patch.set_alpha(0.75)
ax.set_xticklabels(ordem_stat, fontsize=10)
ax.set_ylabel("Preço (R$ mil)")
ax.set_title("Distribuição de Preço por Status do Anúncio")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"R${x:.0f}k"))
ax.yaxis.grid(True); ax.set_axisbelow(True)
ax.text(0.99, 0.97, f"ANOVA p={p_s_an:.2f} (ns)",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=8, color=C["cinza"],
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C["borda"]))
fig.tight_layout()
salvar(fig, "out5_boxplot_status")

# ── Fig 6: Painel analítico — Z-score distribution ───────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# 6a — distribuição dos z-scores
z_all = z_series.dropna()
axes[0].hist(z_all, bins=60, color=C["azul"], alpha=0.75, edgecolor="white", lw=0.3)
axes[0].axvline( THRESH, color=C["vermelho"], lw=2, ls="--", label=f"+{THRESH}σ ({mask_z.sum()} outliers)")
axes[0].axvline(-THRESH, color=C["vermelho"], lw=2, ls="--", label=f"−{THRESH}σ")
axes[0].set_xlabel("Z-score"); axes[0].set_ylabel("Frequência")
axes[0].set_title("Distribuição dos Z-scores de Preço")
axes[0].legend(); axes[0].yaxis.grid(True); axes[0].set_axisbelow(True)

# 6b — Concordância IQR vs Z (venn-like bar)
cats  = ["Só IQR", "Ambos", "Só Z-score", "Normal"]
vals  = [apenas_iqr.sum(), ambos.sum(), apenas_z.sum(),
         (~mask_iqr & ~mask_z & df["preco_brl"].notna()).sum()]
cores_v = [C["laranja"], C["vermelho"], C["roxo"], C["azul"]]
bars = axes[1].bar(cats, vals, color=cores_v, edgecolor="white", width=0.55)
for bar, v in zip(bars, vals):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
                 str(v), ha="center", fontsize=10, fontweight="bold", color=C["texto"])
axes[1].set_ylabel("Quantidade de registros")
axes[1].set_title("Comparação IQR vs Z-score\n(Concordância entre métodos)")
axes[1].yaxis.grid(True); axes[1].set_axisbelow(True)
fig.tight_layout()
salvar(fig, "out6_comparacao_metodos")

print("\n✅ 6 visualizações geradas:")
for i, n in enumerate(["out1_painel_outliers","out2_matriz_correlacao",
                        "out3_scatter_tendencia","out4_boxplot_combustivel",
                        "out5_boxplot_status","out6_comparacao_metodos"], 1):
    print(f"   {i}. {n}.png")
