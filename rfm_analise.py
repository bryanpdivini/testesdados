import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ── Paleta e helpers ──────────────────────────────────────────────────────────
C = {
    "azul":    "#2563EB", "verde":   "#10B981", "amarelo": "#F59E0B",
    "vermelho":"#EF4444", "roxo":    "#8B5CF6", "cinza":   "#6B7280",
    "fundo":   "#F8FAFC", "texto":   "#1E293B", "borda":   "#E2E8F0",
    "laranja": "#F97316", "indigo":  "#4F46E5", "rosa":    "#EC4899",
}
SEG_CORES = {
    "Premium":         C["roxo"],
    "Alto Volume":     C["azul"],
    "Econômico":       C["verde"],
    "Baixa Relevância":C["cinza"],
    "Emergente":       C["amarelo"],
}
plt.rcParams.update({
    "figure.facecolor": C["fundo"], "axes.facecolor": "white",
    "axes.edgecolor":   C["borda"], "axes.labelcolor": C["texto"],
    "axes.titlesize":   12,         "axes.titleweight": "bold",
    "axes.titlepad":    10,         "axes.labelsize":   9,
    "xtick.labelsize":  8,          "ytick.labelsize":  8,
    "xtick.color":      C["cinza"], "ytick.color":     C["cinza"],
    "grid.color":       C["borda"], "grid.linestyle":  "--",
    "grid.alpha":       0.7,        "font.family":     "DejaVu Sans",
    "legend.fontsize":  8,
})

def sep(txt="", w=65): print(f"\n{'═'*w}\n  {txt}\n{'═'*w}" if txt else f"\n{'─'*w}")
def salvar(fig, nome):
    p = f"outputs/{nome}.png"
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor=C["fundo"])
    plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
# 0. CARGA
# ─────────────────────────────────────────────────────────────────────────────
with sqlite3.connect("outputs/ecommerce_carros.db") as conn:
    df = pd.read_sql("SELECT * FROM anuncios", conn)

df["data_anuncio"] = pd.to_datetime(df["data_anuncio"])
df["marca"]        = df["marca_modelo"].str.split().str[0]
DATA_REF           = df["data_anuncio"].max() + pd.Timedelta(days=1)

sep("0. VISÃO GERAL DO DATASET")
print(f"  Registros   : {len(df):,}")
print(f"  Data ref.   : {DATA_REF.date()}  (dia seguinte ao último anúncio)")
print(f"  Marcas      : {df['marca'].nunique()}")
print(f"  Modelos     : {df['marca_modelo'].nunique()}")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 1 — CÁLCULO DAS MÉTRICAS RFM POR MARCA_MODELO                   ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
sep("BLOCO 1 — MÉTRICAS RFM BRUTAS POR MARCA/MODELO")

rfm = (df.groupby("marca_modelo")
         .agg(
             recency   = ("data_anuncio",
                          lambda x: (DATA_REF - x.max()).days),   # R: dias desde o anúncio mais recente
             frequency = ("id", "count"),                         # F: total de anúncios
             monetary  = ("preco_brl", "mean"),                   # M: preço médio (ticket)
             preco_max = ("preco_brl", "max"),
             preco_min = ("preco_brl", "min"),
             ano_medio = ("ano_fabricacao", "mean"),
         )
         .reset_index()
)
rfm["marca"] = rfm["marca_modelo"].str.split().str[0]

print(f"\n  {'Métrica':<12} {'Média':>10} {'Mediana':>10} {'Mín':>10} {'Máx':>10}")
print(f"  {'-'*54}")
for col, lbl in [("recency","Recency (d)"),("frequency","Frequency"),("monetary","Monetary R$")]:
    s = rfm[col]
    print(f"  {lbl:<12} {s.mean():>10.1f} {s.median():>10.1f} {s.min():>10.1f} {s.max():>10.1f}")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 2 — SCORES RFM (escala 1–5)                                      ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
sep("BLOCO 2 — NORMALIZAÇÃO E SCORES RFM (1–5)")

print("""
  Lógica de pontuação:
  • Recency  → score INVERSO: quanto MENOR o tempo (anúncio recente), MAIOR o score
  • Frequency→ score DIRETO : quanto MAIS anúncios, MAIOR o score
  • Monetary → score DIRETO : quanto MAIOR o preço médio, MAIOR o score
""")

def score_quintil(serie, inverso=False):
    """Atribui score 1–5 por quintil. Se inverso=True, menor valor = score 5."""
    labels = [5,4,3,2,1] if inverso else [1,2,3,4,5]
    return pd.qcut(serie, q=5, labels=labels, duplicates="drop").astype(int)

rfm["R_score"] = score_quintil(rfm["recency"],   inverso=True)
rfm["F_score"] = score_quintil(rfm["frequency"], inverso=False)
rfm["M_score"] = score_quintil(rfm["monetary"],  inverso=False)

# Score composto ponderado (M tem maior peso no contexto de e-commerce de carros)
PESO_R, PESO_F, PESO_M = 0.25, 0.30, 0.45
rfm["RFM_score"] = (
    rfm["R_score"] * PESO_R +
    rfm["F_score"] * PESO_F +
    rfm["M_score"] * PESO_M
).round(3)

# Normalização 0–1 para uso no K-Means
scaler = StandardScaler()
rfm[["R_norm","F_norm","M_norm"]] = scaler.fit_transform(
    rfm[["recency","frequency","monetary"]]
)
# Inverte R_norm (menor recency = melhor)
rfm["R_norm"] = -rfm["R_norm"]

print("  Pesos aplicados:")
print(f"    R (Recency)   → {PESO_R:.0%}")
print(f"    F (Frequency) → {PESO_F:.0%}")
print(f"    M (Monetary)  → {PESO_M:.0%}")

print(f"\n  Distribuição do RFM Score:")
print(rfm["RFM_score"].describe().round(3).to_string())

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 3 — SEGMENTAÇÃO RFM                                              ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
sep("BLOCO 3 — SEGMENTAÇÃO RFM")

def segmentar(row):
    R, F, M, rfm_s = row["R_score"], row["F_score"], row["M_score"], row["RFM_score"]
    if M >= 4 and rfm_s >= 3.2:           return "Premium"
    if F >= 4 and M <= 3:                  return "Alto Volume"
    if M <= 2 and rfm_s <= 2.5:           return "Econômico"
    if R >= 4 and F <= 2 and M >= 3:      return "Emergente"
    return "Baixa Relevância"

rfm["segmento_rfm"] = rfm.apply(segmentar, axis=1)

print("""
  Critérios de segmentação:
  ┌─────────────────────┬────────────────────────────────────────────────────┐
  │ Segmento            │ Critério                                           │
  ├─────────────────────┼────────────────────────────────────────────────────┤
  │ Premium             │ M_score ≥ 4 E RFM_score ≥ 3.2                     │
  │ Alto Volume         │ F_score ≥ 4 E M_score ≤ 3                         │
  │ Econômico           │ M_score ≤ 2 E RFM_score ≤ 2.5                     │
  │ Emergente           │ R_score ≥ 4 E F_score ≤ 2 E M_score ≥ 3          │
  │ Baixa Relevância    │ Demais casos                                       │
  └─────────────────────┴────────────────────────────────────────────────────┘
""")

dist_seg = rfm["segmento_rfm"].value_counts()
print("  Distribuição:")
for seg, n in dist_seg.items():
    pct = n / len(rfm) * 100
    bar = "█" * int(pct / 2)
    print(f"    {seg:<20} {n:>3}  ({pct:5.1f}%)  {bar}")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 4 — TABELA CONSOLIDADA E INSIGHTS                                ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
sep("BLOCO 4 — TABELA DE SEGMENTOS (ESTATÍSTICAS)")

seg_stats = (rfm.groupby("segmento_rfm")
               .agg(
                   modelos     = ("marca_modelo", "count"),
                   recency_med = ("recency",   "median"),
                   freq_med    = ("frequency", "median"),
                   preco_med   = ("monetary",  "median"),
                   rfm_medio   = ("RFM_score", "mean"),
               )
               .round(2)
               .sort_values("rfm_medio", ascending=False))
seg_stats.columns = ["Modelos","Recency (d)","Freq. Mediana","Preço Médio","RFM Score"]
print(seg_stats.to_string())

sep("BLOCO 4B — INSIGHTS ESTRATÉGICOS POR SEGMENTO")

# ── Premium
prem = rfm[rfm["segmento_rfm"]=="Premium"].sort_values("RFM_score", ascending=False)
print(f"""
  🏆 PREMIUM ({len(prem)} modelos)
     Top 5 modelos mais bem pontuados:""")
print(prem[["marca_modelo","R_score","F_score","M_score","RFM_score","monetary"]].head(5).to_string(index=False))
marcas_prem = prem["marca"].value_counts()
print(f"\n     Domínio por marca:")
for m, n in marcas_prem.items(): print(f"       {m:<15} {n} modelo(s)")

# ── Alto Volume
vol = rfm[rfm["segmento_rfm"]=="Alto Volume"].sort_values("frequency", ascending=False)
print(f"""
  📦 ALTO VOLUME ({len(vol)} modelos)
     Mais anunciados:""")
print(vol[["marca_modelo","frequency","monetary","RFM_score"]].head(5).to_string(index=False))

# ── Econômico
eco = rfm[rfm["segmento_rfm"]=="Econômico"].sort_values("monetary")
print(f"""
  💚 ECONÔMICO ({len(eco)} modelos)
     Ticket mais baixo — acessibilidade em destaque:""")
print(eco[["marca_modelo","monetary","frequency","RFM_score"]].head(5).to_string(index=False))

# ── Emergente
eme = rfm[rfm["segmento_rfm"]=="Emergente"].sort_values("R_score", ascending=False)
print(f"""
  🚀 EMERGENTE ({len(eme)} modelos)
     Novos entrantes com bom ticket — potencial de crescimento:""")
print(eme[["marca_modelo","recency","monetary","RFM_score"]].head(5).to_string(index=False))

# ── Baixa Relevância
br = rfm[rfm["segmento_rfm"]=="Baixa Relevância"].sort_values("RFM_score")
print(f"""
  ⚠️  BAIXA RELEVÂNCIA ({len(br)} modelos)
     Menor engajamento e ticket mediano — candidatos a revisão de estratégia:""")
print(br[["marca_modelo","recency","frequency","monetary","RFM_score"]].head(5).to_string(index=False))

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BLOCO 5 — K-MEANS (comparação com RFM)                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
sep("BLOCO 5 — CLUSTERIZAÇÃO K-MEANS")

X = rfm[["R_norm","F_norm","M_norm"]].values

# Método do cotovelo + silhouette
inercias, silhouettes = [], []
K_range = range(2, 9)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    lbl = km.fit_predict(X)
    inercias.append(km.inertia_)
    silhouettes.append(silhouette_score(X, lbl))

K_BEST = K_range[np.argmax(silhouettes)]
print(f"\n  K ótimo (maior silhouette): {K_BEST}")
for k, sil in zip(K_range, silhouettes):
    mark = " ◄ ótimo" if k == K_BEST else ""
    print(f"    k={k}  silhouette={sil:.4f}{mark}")

km_final = KMeans(n_clusters=K_BEST, random_state=42, n_init=10)
rfm["cluster_km"] = km_final.fit_predict(X)

# Caracteriza clusters
km_stats = (rfm.groupby("cluster_km")
              .agg(n=("marca_modelo","count"),
                   R=("recency","mean"),
                   F=("frequency","mean"),
                   M=("monetary","mean"),
                   rfm=("RFM_score","mean"))
              .round(2)
              .sort_values("M", ascending=False))
print(f"\n  Perfil dos {K_BEST} clusters K-Means:")
print(km_stats.to_string())

# Rótulos automáticos por centroide
def rotulo_cluster(row):
    if row["M"] >= rfm["monetary"].quantile(0.75):     return "KM-Premium"
    if row["F"] >= rfm["frequency"].quantile(0.75):    return "KM-Alto Volume"
    if row["M"] <= rfm["monetary"].quantile(0.25):     return "KM-Econômico"
    return "KM-Médio"

km_stats["rotulo"] = km_stats.apply(rotulo_cluster, axis=1)
mapa_km = km_stats["rotulo"].to_dict()
rfm["cluster_km_label"] = rfm["cluster_km"].map(mapa_km)

print(f"\n  Concordância RFM × K-Means (modelos em segmentos equivalentes):")
cross = pd.crosstab(rfm["segmento_rfm"], rfm["cluster_km_label"])
print(cross.to_string())

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  VISUALIZAÇÕES                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
sep("VISUALIZAÇÕES")

# ── Fig 1: Painel RFM Score – distribuições e segmentos ──────────────────────
fig = plt.figure(figsize=(16, 10), facecolor=C["fundo"])
gs  = gridspec.GridSpec(2, 3, hspace=0.42, wspace=0.35)

# 1a – Histograma RFM Score
ax = fig.add_subplot(gs[0, 0])
ax.hist(rfm["RFM_score"], bins=20, color=C["azul"], alpha=0.8, edgecolor="white")
ax.axvline(rfm["RFM_score"].mean(), color=C["vermelho"], lw=2, ls="--", label="Média")
ax.set_title("Distribuição do RFM Score"); ax.set_xlabel("RFM Score"); ax.set_ylabel("Qtd. Modelos")
ax.legend(); ax.yaxis.grid(True); ax.set_axisbelow(True)

# 1b – Barplot segmentos
ax = fig.add_subplot(gs[0, 1])
segs = rfm["segmento_rfm"].value_counts()
bars = ax.bar(segs.index, segs.values,
              color=[SEG_CORES.get(s, C["cinza"]) for s in segs.index],
              edgecolor="white", width=0.6)
for bar in bars:
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2,
            str(bar.get_height()), ha="center", fontsize=9, fontweight="bold")
ax.set_title("Modelos por Segmento RFM"); ax.set_ylabel("Qtd. Modelos")
ax.tick_params(axis="x", rotation=20); ax.yaxis.grid(True); ax.set_axisbelow(True)

# 1c – Boxplot RFM Score por segmento
ax = fig.add_subplot(gs[0, 2])
ordem = rfm.groupby("segmento_rfm")["RFM_score"].median().sort_values(ascending=False).index
bp_data = [rfm[rfm["segmento_rfm"]==s]["RFM_score"].values for s in ordem]
bp = ax.boxplot(bp_data, patch_artist=True, widths=0.5,
                medianprops=dict(color=C["texto"], lw=2),
                flierprops=dict(marker="o", markersize=3, alpha=0.4,
                                markerfacecolor=C["cinza"], linestyle="none"))
for patch, seg in zip(bp["boxes"], ordem):
    patch.set_facecolor(SEG_CORES.get(seg, C["cinza"])); patch.set_alpha(0.75)
ax.set_xticklabels([s.replace(" ","\n") for s in ordem], fontsize=7.5)
ax.set_title("RFM Score por Segmento"); ax.set_ylabel("RFM Score")
ax.yaxis.grid(True); ax.set_axisbelow(True)

# 1d – Scatter F × M colorido por segmento
ax = fig.add_subplot(gs[1, 0])
for seg, grp in rfm.groupby("segmento_rfm"):
    ax.scatter(grp["frequency"], grp["monetary"]/1000,
               color=SEG_CORES.get(seg, C["cinza"]),
               alpha=0.7, s=60, label=seg, edgecolors="white", lw=0.5)
ax.set_xlabel("Frequency (# anúncios)"); ax.set_ylabel("Monetary (R$ mil)")
ax.set_title("Frequency × Monetary\npor Segmento RFM")
ax.legend(fontsize=6.5, ncol=1); ax.yaxis.grid(True); ax.set_axisbelow(True)

# 1e – Scatter R × M
ax = fig.add_subplot(gs[1, 1])
for seg, grp in rfm.groupby("segmento_rfm"):
    ax.scatter(grp["recency"], grp["monetary"]/1000,
               color=SEG_CORES.get(seg, C["cinza"]),
               alpha=0.7, s=60, label=seg, edgecolors="white", lw=0.5)
ax.set_xlabel("Recency (dias)"); ax.set_ylabel("Monetary (R$ mil)")
ax.set_title("Recency × Monetary\npor Segmento RFM")
ax.legend(fontsize=6.5); ax.yaxis.grid(True); ax.set_axisbelow(True)

# 1f – Heatmap R/F/M médio por segmento (normalizado)
ax = fig.add_subplot(gs[1, 2])
pivot_heat = (rfm.groupby("segmento_rfm")[["R_score","F_score","M_score"]]
              .mean().round(2)
              .reindex([s for s in SEG_CORES.keys() if s in rfm["segmento_rfm"].values]))
pivot_heat.columns = ["R","F","M"]
sns.heatmap(pivot_heat, ax=ax, annot=True, fmt=".2f", cmap="YlOrRd",
            linewidths=1, linecolor=C["borda"],
            annot_kws={"size":10,"weight":"bold"},
            cbar_kws={"shrink":0.8})
ax.set_title("Score Médio R/F/M\npor Segmento")
ax.tick_params(axis="y", rotation=0)

salvar(fig, "rfm1_painel_segmentos")

# ── Fig 2: Radar chart por segmento ──────────────────────────────────────────
segs_radar = [s for s in SEG_CORES if s in rfm["segmento_rfm"].values]
n_segs     = len(segs_radar)
cats       = ["R Score","F Score","M Score"]
N          = len(cats)
angles     = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
angles    += angles[:1]

fig, axes = plt.subplots(1, n_segs, figsize=(4*n_segs, 4.5),
                          subplot_kw=dict(polar=True), facecolor=C["fundo"])
if n_segs == 1: axes = [axes]
for ax, seg in zip(axes, segs_radar):
    vals = rfm[rfm["segmento_rfm"]==seg][["R_score","F_score","M_score"]].mean().tolist()
    vals += vals[:1]
    cor = SEG_CORES.get(seg, C["cinza"])
    ax.plot(angles, vals, "o-", lw=2, color=cor)
    ax.fill(angles, vals, alpha=0.25, color=cor)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylim(0, 5); ax.set_yticks([1,2,3,4,5]); ax.set_yticklabels(["1","2","3","4","5"], fontsize=6)
    ax.set_title(seg, pad=15, fontsize=10, fontweight="bold", color=cor)
    ax.grid(color=C["borda"])
fig.suptitle("Perfil Médio R/F/M por Segmento (Radar)", fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
salvar(fig, "rfm2_radar_segmentos")

# ── Fig 3: K-Means – cotovelo, silhouette e PCA 2D ───────────────────────────
fig = plt.figure(figsize=(16, 5), facecolor=C["fundo"])
gs  = gridspec.GridSpec(1, 3, wspace=0.35)

# 3a – Cotovelo
ax = fig.add_subplot(gs[0])
ax.plot(list(K_range), inercias, "o-", color=C["azul"], lw=2, ms=7)
ax.axvline(K_BEST, color=C["vermelho"], ls="--", lw=1.8, label=f"k={K_BEST} (ótimo)")
ax.set_xlabel("Número de clusters (k)"); ax.set_ylabel("Inércia")
ax.set_title("Método do Cotovelo"); ax.legend(); ax.yaxis.grid(True); ax.set_axisbelow(True)

# 3b – Silhouette
ax = fig.add_subplot(gs[1])
cores_sil = [C["vermelho"] if k==K_BEST else C["azul"] for k in K_range]
bars = ax.bar(list(K_range), silhouettes, color=cores_sil, edgecolor="white", width=0.6)
for bar, s in zip(bars, silhouettes):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.002,
            f"{s:.3f}", ha="center", fontsize=8, fontweight="bold")
ax.set_xlabel("Número de clusters (k)"); ax.set_ylabel("Silhouette Score")
ax.set_title("Silhouette por k"); ax.yaxis.grid(True); ax.set_axisbelow(True)

# 3c – PCA 2D dos clusters
ax = fig.add_subplot(gs[2])
pca   = PCA(n_components=2, random_state=42)
coords= pca.fit_transform(X)
km_cores = [C["azul"],C["verde"],C["vermelho"],C["amarelo"],C["roxo"],C["laranja"],C["cinza"]]
for k in range(K_BEST):
    mask = rfm["cluster_km"] == k
    lbl  = mapa_km.get(k, f"Cluster {k}")
    ax.scatter(coords[mask, 0], coords[mask, 1],
               color=km_cores[k % len(km_cores)], alpha=0.65, s=50,
               label=lbl, edgecolors="white", lw=0.4)
# Centroides
centers_pca = pca.transform(km_final.cluster_centers_)
ax.scatter(centers_pca[:,0], centers_pca[:,1],
           color="black", marker="X", s=150, zorder=5, label="Centroide")
ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% var.)")
ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% var.)")
ax.set_title(f"K-Means k={K_BEST} — Projeção PCA 2D")
ax.legend(fontsize=7); ax.yaxis.grid(True); ax.set_axisbelow(True)
fig.suptitle("Análise K-Means: Seleção de k e Distribuição dos Clusters",
             fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
salvar(fig, "rfm3_kmeans_pca")

# ── Fig 4: Top modelos por segmento (barplot horizontal) ─────────────────────
fig, axes = plt.subplots(1, len(segs_radar), figsize=(4.5*len(segs_radar), 5),
                          facecolor=C["fundo"])
if len(segs_radar) == 1: axes = [axes]
for ax, seg in zip(axes, segs_radar):
    top = rfm[rfm["segmento_rfm"]==seg].nlargest(6,"RFM_score")
    cor = SEG_CORES.get(seg, C["cinza"])
    bars = ax.barh(top["marca_modelo"][::-1], top["RFM_score"][::-1],
                   color=cor, alpha=0.80, edgecolor="white")
    for bar in bars:
        ax.text(bar.get_width()-0.02, bar.get_y()+bar.get_height()/2,
                f"{bar.get_width():.2f}", va="center", ha="right",
                fontsize=8, fontweight="bold", color="white")
    ax.set_xlim(left=rfm["RFM_score"].min()-0.1)
    ax.set_title(f"{seg}\n(Top 6 por RFM Score)", color=cor, fontsize=10)
    ax.set_xlabel("RFM Score"); ax.xaxis.grid(True); ax.set_axisbelow(True)
fig.suptitle("Top Modelos por Segmento RFM", fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
salvar(fig, "rfm4_top_modelos_segmento")

# ── Fig 5: Tabela visual completa ────────────────────────────────────────────
tabela = (rfm.sort_values("RFM_score", ascending=False)
            [["marca_modelo","marca","R_score","F_score","M_score",
              "RFM_score","recency","frequency","monetary","segmento_rfm"]]
            .rename(columns={
                "marca_modelo":"Modelo","marca":"Marca",
                "R_score":"R","F_score":"F","M_score":"M",
                "RFM_score":"Score","recency":"Recency(d)",
                "frequency":"Freq","monetary":"Ticket R$",
                "segmento_rfm":"Segmento"})
          )
tabela["Ticket R$"] = tabela["Ticket R$"].round(0).astype(int)

fig, ax = plt.subplots(figsize=(16, 8), facecolor=C["fundo"])
ax.axis("off")
cols_show = ["Modelo","R","F","M","Score","Recency(d)","Freq","Ticket R$","Segmento"]
data_show = tabela[cols_show].head(20).values
col_colors  = [[C["azul"]] * len(cols_show)]
cell_colors = []
for _, row in tabela[cols_show].head(20).iterrows():
    cor = SEG_CORES.get(row["Segmento"], C["cinza"])
    cell_colors.append([cor if i == len(cols_show)-1 else "white"
                        for i in range(len(cols_show))])

tbl = ax.table(cellText=data_show, colLabels=cols_show,
               cellLoc="center", loc="center",
               cellColours=cell_colors)
tbl.auto_set_font_size(False); tbl.set_fontsize(8.5)
tbl.scale(1, 1.6)
for (row, col), cell in tbl.get_celld().items():
    cell.set_edgecolor(C["borda"])
    if row == 0:
        cell.set_facecolor(C["azul"]); cell.set_text_props(color="white", fontweight="bold")
    if col == len(cols_show)-1 and row > 0:
        cell.set_text_props(color="white", fontweight="bold")

ax.set_title("Top 20 Modelos — Tabela RFM Completa\n(colorido por segmento)",
             fontsize=13, fontweight="bold", pad=20)
salvar(fig, "rfm5_tabela_visual")

# ── Exporta CSV final
rfm.to_csv("outputs/rfm_resultados.csv", index=False)

sep("RESUMO FINAL")
print(f"""
  ✅ Dataset analisado: {len(rfm)} modelos únicos
  ✅ Segmentos RFM identificados: {rfm['segmento_rfm'].nunique()}
  ✅ Clusters K-Means: {K_BEST} (silhouette={max(silhouettes):.3f})

  INSIGHTS ESTRATÉGICOS:
  ────────────────────────────────────────────────────────────
  🏆 Premium         → {len(prem)} modelos com maior ticket médio e
                        presença recente. Foco: precificação alta,
                        anúncios exclusivos, campanha de valorização.

  📦 Alto Volume     → {len(vol)} modelos com muitos anúncios mas
                        ticket mediano. Foco: escala e giro de estoque.
                        São os "cavalos de batalha" da plataforma.

  💚 Econômico       → {len(eco)} modelos de menor ticket. Foco:
                        volume, acessibilidade e democratização.
                        Estratégia: menor margem, maior alcance.

  🚀 Emergente       → {len(eme)} modelos com anúncio recente mas
                        baixa frequência. Sinal de entrada nova ou
                        reposicionamento. Merecem monitoramento.

  ⚠️  Baixa Relev.   → {len(br)} modelos com score mais baixo.
                        Candidatos a revisão de precificação ou
                        redução de investimento em divulgação.
  ────────────────────────────────────────────────────────────

  Arquivos exportados:
    rfm_resultados.csv
    rfm1_painel_segmentos.png
    rfm2_radar_segmentos.png
    rfm3_kmeans_pca.png
    rfm4_top_modelos_segmento.png
    rfm5_tabela_visual.png
""")
