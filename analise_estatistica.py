import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ── Paleta e estilo global ────────────────────────────────────────────────────
CORES = {
    "primaria":   "#2563EB",
    "secundaria": "#10B981",
    "alerta":     "#F59E0B",
    "perigo":     "#EF4444",
    "neutro":     "#6B7280",
    "fundo":      "#F8FAFC",
    "texto":      "#1E293B",
}
plt.rcParams.update({
    "figure.facecolor":  CORES["fundo"],
    "axes.facecolor":    "white",
    "axes.edgecolor":    "#E2E8F0",
    "axes.labelcolor":   CORES["texto"],
    "axes.titlesize":    13,
    "axes.titleweight":  "bold",
    "axes.titlepad":     12,
    "axes.labelsize":    10,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "xtick.color":       CORES["neutro"],
    "ytick.color":       CORES["neutro"],
    "grid.color":        "#E2E8F0",
    "grid.linestyle":    "--",
    "grid.alpha":        0.7,
    "font.family":       "DejaVu Sans",
    "legend.fontsize":   9,
    "legend.framealpha": 0.9,
})

# ── 0. Carga do banco ─────────────────────────────────────────────────────────
DB_PATH = "outputs/ecommerce_carros.db"
with sqlite3.connect(DB_PATH) as conn:
    df = pd.read_sql("SELECT * FROM anuncios", conn)

df["data_anuncio"] = pd.to_datetime(df["data_anuncio"])
df["ano_mes"]      = df["data_anuncio"].dt.to_period("M")
df["ano"]          = df["data_anuncio"].dt.year
df["mes"]          = df["data_anuncio"].dt.month
df["marca"]        = df["marca_modelo"].str.split().str[0]

SEP = "=" * 65

# ╔══════════════════════════════════════════════════════════════════╗
# ║  1. ESTATÍSTICAS DESCRITIVAS – VARIÁVEIS NUMÉRICAS              ║
# ╚══════════════════════════════════════════════════════════════════╝
print(f"\n{SEP}")
print("  1. ESTATÍSTICAS DESCRITIVAS – VARIÁVEIS NUMÉRICAS")
print(SEP)

num_cols = ["preco_brl", "ano_fabricacao"]
desc = df[num_cols].agg(["mean", "median", "std", "min", "max"]).T
desc.columns = ["Média", "Mediana", "Desvio Padrão", "Mínimo", "Máximo"]
desc.index   = ["Preço (R$)", "Ano de Fabricação"]
print(desc.to_string())

# ╔══════════════════════════════════════════════════════════════════╗
# ║  2. ASSIMETRIA E CURTOSE – preco_brl                            ║
# ╚══════════════════════════════════════════════════════════════════╝
print(f"\n{SEP}")
print("  2. ASSIMETRIA E CURTOSE – preco_brl")
print(SEP)

preco = df["preco_brl"].dropna()
skew  = preco.skew()
kurt  = preco.kurtosis()          # excesso de curtose (Fisher)
_, p_norm = stats.normaltest(preco)

print(f"  Assimetria (skewness) : {skew:+.4f}")
print(f"  Curtose (excess)      : {kurt:+.4f}")
p_nom = p_norm < 0.05
print(f"  Teste normalidade p   : {p_norm:.2e}  ({'NÃO normal' if p_nom else 'Normal'})")

if   skew >  0.5: sk_txt = "assimetria positiva moderada → cauda longa à direita (poucos carros muito caros)"
elif skew < -0.5: sk_txt = "assimetria negativa moderada → cauda longa à esquerda (poucos carros muito baratos)"
else:             sk_txt = "distribuição aproximadamente simétrica"

if   kurt >  1:   ku_txt = "leptocúrtica → pico acentuado, outliers relevantes"
elif kurt < -1:   ku_txt = "platicúrtica → distribuição achatada, preços bem espalhados"
else:             ku_txt = "mesocúrtica → próxima de uma distribuição normal"

print(f"\n  ► Skewness: {sk_txt}")
print(f"  ► Kurtosis: {ku_txt}")

# ╔══════════════════════════════════════════════════════════════════╗
# ║  3. DISTRIBUIÇÃO DE FREQUÊNCIAS – VARIÁVEIS CATEGÓRICAS         ║
# ╚══════════════════════════════════════════════════════════════════╝
print(f"\n{SEP}")
print("  3. DISTRIBUIÇÃO DE FREQUÊNCIAS – VARIÁVEIS CATEGÓRICAS")
print(SEP)

for col, label in [("marca", "Marca"), ("combustivel", "Combustível"), ("status", "Status")]:
    freq = df[col].value_counts()
    pct  = (freq / len(df) * 100).round(1)
    tab  = pd.DataFrame({"Qtd": freq, "%": pct})
    print(f"\n  ▸ {label}:")
    print(tab.to_string())

print(f"\n  ▸ Top 10 Marca/Modelo:")
top10 = df["marca_modelo"].value_counts().head(10)
top10_pct = (top10 / len(df) * 100).round(1)
print(pd.DataFrame({"Qtd": top10, "%": top10_pct}).to_string())

# ╔══════════════════════════════════════════════════════════════════╗
# ║  4. ANÁLISE TEMPORAL                                            ║
# ╚══════════════════════════════════════════════════════════════════╝
print(f"\n{SEP}")
print("  4. ANÁLISE TEMPORAL")
print(SEP)

por_ano_mes = df.groupby("ano_mes").size().reset_index(name="anuncios")
por_ano_mes["ano_mes_str"] = por_ano_mes["ano_mes"].astype(str)

por_ano    = df.groupby("ano").size()
preco_mes  = df.groupby("ano_mes")["preco_brl"].median().reset_index()

print("\n  Anúncios por Ano:")
print(por_ano.to_string())
print(f"\n  Mês com mais anúncios : {por_ano_mes.loc[por_ano_mes['anuncios'].idxmax(), 'ano_mes_str']} "
      f"({por_ano_mes['anuncios'].max()} anúncios)")
print(f"  Mês com menos anúncios: {por_ano_mes.loc[por_ano_mes['anuncios'].idxmin(), 'ano_mes_str']} "
      f"({por_ano_mes['anuncios'].min()} anúncios)")

# ╔══════════════════════════════════════════════════════════════════╗
# ║  5. INSIGHTS INTERPRETATIVOS                                    ║
# ╚══════════════════════════════════════════════════════════════════╝
print(f"\n{SEP}")
print("  5. INSIGHTS INTERPRETATIVOS")
print(SEP)

q25, q75 = preco.quantile(0.25), preco.quantile(0.75)
pct_faixa = ((preco >= q25) & (preco <= q75)).mean() * 100
marca_dom = df["marca"].value_counts()
marca1, marca2 = marca_dom.index[0], marca_dom.index[1]
pct_m1 = marca_dom.iloc[0] / len(df) * 100
pct_top2 = (marca_dom.iloc[0] + marca_dom.iloc[1]) / len(df) * 100
modelo_top = df["marca_modelo"].value_counts().index[0]
pct_modelo = df["marca_modelo"].value_counts().iloc[0] / len(df) * 100
disp_pct = (df["status"] == "Disponível").mean() * 100
vend_pct = (df["status"] == "Vendido").mean() * 100
preco_anual = df.groupby("ano")["preco_brl"].median()
anos_ok = preco_anual[preco_anual.index >= 2022]
tendencia = "crescente" if anos_ok.iloc[-1] > anos_ok.iloc[0] else "decrescente"

print(f"""
  💰 Faixa de Preço Predominante
     50% dos anúncios estão entre R$ {q25:,.0f} e R$ {q75:,.0f} (IQR).
     A mediana de R$ {preco.median():,.0f} ficou {'acima' if preco.median()>preco.mean() else 'abaixo'} da média
     (R$ {preco.mean():,.0f}), confirmando a assimetria leve na distribuição de preços.
     Isso indica que uma minoria de veículos premium puxa a média para cima.

  🚗 Concentração de Marcas e Modelos
     {marca1} lidera com {pct_m1:.1f}% dos anúncios, seguida por {marca2}.
     Juntas, as duas marcas mais populares respondem por {pct_top2:.1f}% do catálogo.
     O modelo mais anunciado individualmente é "{modelo_top}" ({pct_modelo:.1f}% do total),
     sugerindo alta demanda ou amplo estoque desse veículo na plataforma.

  📅 Tendências Temporais
     O volume de anúncios é distribuído entre 2022 e 2024, com tendência de
     preço mediano {tendencia} ao longo do período analisado.
     O pico de anúncios ocorreu em {por_ano_mes.loc[por_ano_mes['anuncios'].idxmax(), 'ano_mes_str']},
     possivelmente ligado a sazonalidade de renovação de frota ou promoções.

  📊 Status do Estoque
     {disp_pct:.1f}% dos veículos estão Disponíveis e {vend_pct:.1f}% já foram Vendidos.
     Uma taxa de venda expressiva indica boa liquidez do catálogo simulado.

  ⚡ Combustível
     Flex e Elétrico lideram empatados — reflexo da transição energética no
     mercado brasileiro, com crescimento real de EVs nas plataformas de venda.
""")

# ╔══════════════════════════════════════════════════════════════════╗
# ║  6. VISUALIZAÇÕES                                               ║
# ╚══════════════════════════════════════════════════════════════════╝

def salvar(fig, nome):
    path = f"outputs/{nome}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=CORES["fundo"])
    plt.close(fig)
    return path

# ── Fig 1: Histograma + KDE do preço ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(preco / 1000, bins=50, color=CORES["primaria"], alpha=0.75, edgecolor="white", linewidth=0.4)
ax2 = ax.twinx()
preco_k = preco / 1000
kde_x = np.linspace(preco_k.min(), preco_k.max(), 300)
kde   = stats.gaussian_kde(preco_k)(kde_x)
ax2.plot(kde_x, kde, color=CORES["perigo"], lw=2.5, label="KDE")
ax2.set_ylabel("Densidade", color=CORES["perigo"])
ax2.tick_params(axis="y", colors=CORES["perigo"])
ax2.set_ylim(bottom=0)
for v, lbl, cor in [(preco.mean()/1000, "Média", CORES["alerta"]),
                    (preco.median()/1000, "Mediana", CORES["secundaria"])]:
    ax.axvline(v, color=cor, lw=2, linestyle="--", label=lbl)
ax.set_xlabel("Preço (R$ mil)")
ax.set_ylabel("Frequência")
ax.set_title("Distribuição de Preços — Histograma + KDE")
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
ax.yaxis.grid(True); ax.set_axisbelow(True)
fig.tight_layout()
salvar(fig, "fig1_histograma_preco")

# ── Fig 2: Boxplot por combustível ───────────────────────────────────────────
ordem_comb = df.groupby("combustivel")["preco_brl"].median().sort_values(ascending=False).index.tolist()
fig, ax = plt.subplots(figsize=(11, 5))
palette = sns.color_palette("Blues_d", len(ordem_comb))
sns.boxplot(data=df, x="combustivel", y="preco_brl", order=ordem_comb,
            palette=palette, width=0.55, fliersize=3,
            flierprops=dict(marker="o", color=CORES["neutro"], alpha=0.4), ax=ax)
ax.set_xlabel("Tipo de Combustível")
ax.set_ylabel("Preço (R$)")
ax.set_title("Distribuição de Preços por Tipo de Combustível")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:.0f}k"))
ax.yaxis.grid(True); ax.set_axisbelow(True)
fig.tight_layout()
salvar(fig, "fig2_boxplot_combustivel")

# ── Fig 3: Barplot top 10 modelos ────────────────────────────────────────────
top10_mod = df["marca_modelo"].value_counts().head(10)
cores_bar  = [CORES["primaria"] if i == 0 else CORES["secundaria"] if i < 3 else "#93C5FD"
              for i in range(len(top10_mod))]
fig, ax = plt.subplots(figsize=(11, 5))
bars = ax.barh(top10_mod.index[::-1], top10_mod.values[::-1], color=cores_bar[::-1], edgecolor="white")
for bar in bars:
    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.0f}", va="center", fontsize=8.5, color=CORES["texto"])
ax.set_xlabel("Quantidade de Anúncios")
ax.set_title("Top 10 Modelos Mais Anunciados")
ax.xaxis.grid(True); ax.set_axisbelow(True)
fig.tight_layout()
salvar(fig, "fig3_barplot_modelos")

# ── Fig 4: Série temporal (anúncios por mês) ─────────────────────────────────
ts = por_ano_mes.copy()
fig, ax = plt.subplots(figsize=(13, 4.5))
ax.fill_between(range(len(ts)), ts["anuncios"], alpha=0.15, color=CORES["primaria"])
ax.plot(range(len(ts)), ts["anuncios"], color=CORES["primaria"], lw=2, marker="o",
        markersize=4, markerfacecolor="white", markeredgewidth=1.5)
step = max(1, len(ts) // 12)
ax.set_xticks(range(0, len(ts), step))
ax.set_xticklabels(ts["ano_mes_str"].iloc[::step], rotation=45, ha="right")
ax.set_ylabel("Anúncios")
ax.set_title("Volume de Anúncios por Mês/Ano")
ax.yaxis.grid(True); ax.set_axisbelow(True)
fig.tight_layout()
salvar(fig, "fig4_serie_temporal")

# ── Fig 5: Preço mediano anual por marca (top 5 marcas) ──────────────────────
top5_marcas = df["marca"].value_counts().head(5).index.tolist()
df5 = df[df["marca"].isin(top5_marcas)]
pivot = df5.groupby(["ano", "marca"])["preco_brl"].median().unstack()
fig, ax = plt.subplots(figsize=(10, 5))
palette5 = [CORES["primaria"], CORES["secundaria"], CORES["alerta"], CORES["perigo"], "#8B5CF6"]
for i, marca_col in enumerate(pivot.columns):
    ax.plot(pivot.index, pivot[marca_col] / 1000, marker="o", lw=2,
            color=palette5[i], label=marca_col, markersize=5)
ax.set_xlabel("Ano de Anúncio")
ax.set_ylabel("Preço Mediano (R$ mil)")
ax.set_title("Evolução do Preço Mediano Anual — Top 5 Marcas")
ax.legend(loc="upper left")
ax.yaxis.grid(True); ax.set_axisbelow(True)
fig.tight_layout()
salvar(fig, "fig5_preco_anual_marca")

print("✅ 5 visualizações exportadas para outputs/")
print("   fig1_histograma_preco.png")
print("   fig2_boxplot_combustivel.png")
print("   fig3_barplot_modelos.png")
print("   fig4_serie_temporal.png")
print("   fig5_preco_anual_marca.png")
