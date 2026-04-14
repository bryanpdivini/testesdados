import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import re

# ─────────────────────────────────────────────
# 1. GERAÇÃO DO DATASET SIMULADO (5.000 linhas)
# ─────────────────────────────────────────────
np.random.seed(42)
random.seed(42)

N = 5000

marcas_modelos = {
    "Toyota": ["Corolla", "Hilux", "Yaris", "SW4"],
    "Honda": ["Civic", "HR-V", "Fit", "CR-V"],
    "Volkswagen": ["Gol", "Polo", "T-Cross", "Virtus"],
    "Chevrolet": ["Onix", "Tracker", "Cruze", "S10"],
    "Hyundai": ["HB20", "Creta", "Tucson", "i30"],
    "Ford": ["Ka", "EcoSport", "Ranger", "Territory"],
    "Fiat": ["Argo", "Uno", "Toro", "Pulse"],
    "Renault": ["Kwid", "Sandero", "Duster", "Logan"],
}

combustiveis = ["Gasolina", "Flex", "Diesel", "Elétrico", "Híbrido",
                "gasolina", "flex", "DIESEL", None, "Eletrico"]  # ruído intencional

status_lista = ["Disponível", "Vendido", "Reservado", "disponivel",
                "VENDIDO", "reservado", None, "Disponivel"]

base_date = datetime(2022, 1, 1)

registros = []
for i in range(N):
    marca = random.choice(list(marcas_modelos.keys()))
    modelo = random.choice(marcas_modelos[marca])
    ano = random.randint(2010, 2024)

    # Preço com ruído: nulos, negativos, texto, formato BRL, formato USD
    r_preco = random.random()
    if r_preco < 0.04:
        preco_raw = None
    elif r_preco < 0.06:
        preco_raw = -abs(np.random.normal(80000, 30000))
    elif r_preco < 0.08:
        preco_raw = f"R$ {np.random.normal(80000, 30000):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    elif r_preco < 0.10:
        preco_raw = f"${np.random.normal(80000, 30000):.2f}"
    else:
        preco_raw = round(abs(np.random.normal(80000, 30000)), 2)

    # Data com ruído: nulos, formatos variados
    dias = random.randint(0, 1000)
    data_base = base_date + timedelta(days=dias)
    r_data = random.random()
    if r_data < 0.04:
        data_raw = None
    elif r_data < 0.07:
        data_raw = data_base.strftime("%d/%m/%Y")
    elif r_data < 0.10:
        data_raw = data_base.strftime("%Y/%m/%d")
    elif r_data < 0.12:
        data_raw = data_base.strftime("%m-%d-%Y")
    else:
        data_raw = data_base.strftime("%Y-%m-%d")

    combustivel = random.choice(combustiveis)
    status = random.choice(status_lista)

    registros.append({
        "marca_modelo": f"{marca} {modelo}",
        "ano_fabricacao": ano if random.random() > 0.03 else None,
        "preco_brl":      preco_raw,
        "data_anuncio":   data_raw,
        "combustivel":    combustivel,
        "status":         status,
    })

# Inserir duplicatas intencionais (~3%)
indices_dup = np.random.choice(N, size=int(N * 0.03), replace=False)
registros.extend([registros[i] for i in indices_dup])

df = pd.DataFrame(registros)
print(f"Dataset bruto: {df.shape[0]} linhas × {df.shape[1]} colunas")
print(f"Nulos por coluna:\n{df.isnull().sum()}\n")
print(f"Duplicatas: {df.duplicated().sum()}\n")

# ─────────────────────────────────────────────
# 2. TRATAMENTO DE DADOS
# ─────────────────────────────────────────────

# 2.1 Remoção de duplicatas
df.drop_duplicates(inplace=True)
df.reset_index(drop=True, inplace=True)
print(f"Após remover duplicatas: {df.shape[0]} linhas")

# 2.2 Coluna: marca_modelo – preenchimento de nulos com 'Desconhecido'
df["marca_modelo"] = df["marca_modelo"].fillna("Desconhecido").str.strip().str.title()

# 2.3 Coluna: ano_fabricacao
df["ano_fabricacao"] = pd.to_numeric(df["ano_fabricacao"], errors="coerce")
mediana_ano = df["ano_fabricacao"].median()
df["ano_fabricacao"] = df["ano_fabricacao"].fillna(mediana_ano).astype(int)
# Remover anos impossíveis
df = df[(df["ano_fabricacao"] >= 1980) & (df["ano_fabricacao"] <= datetime.now().year)]

# 2.4 Coluna: preco_brl – limpeza e conversão
def limpar_preco(valor):
    if pd.isnull(valor):
        return np.nan
    s = str(valor).strip()
    # Remove símbolos de moeda
    s = re.sub(r"[R$\s]", "", s)
    # Normaliza separadores: formato BR (1.234,56) → float
    if re.search(r"\d{1,3}(\.\d{3})+,\d{2}", s):
        s = s.replace(".", "").replace(",", ".")
    # Formato USD (1,234.56)
    elif re.search(r"\d{1,3}(,\d{3})+\.\d{2}", s):
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan

df["preco_brl"] = df["preco_brl"].apply(limpar_preco)
# Remover preços negativos ou zero
df = df[df["preco_brl"].isna() | (df["preco_brl"] > 0)]
# Preencher nulos com a mediana
mediana_preco = df["preco_brl"].median()
df["preco_brl"] = df["preco_brl"].fillna(mediana_preco).round(2)

# 2.5 Coluna: data_anuncio – múltiplos formatos → datetime padronizado
formatos = ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y"]

def parse_data(valor):
    if pd.isnull(valor):
        return pd.NaT
    for fmt in formatos:
        try:
            return datetime.strptime(str(valor).strip(), fmt)
        except ValueError:
            continue
    return pd.NaT

df["data_anuncio"] = df["data_anuncio"].apply(parse_data)
# Preencher nulos com a data mais frequente (moda)
moda_data = df["data_anuncio"].mode()[0]
df["data_anuncio"] = df["data_anuncio"].fillna(moda_data)

# 2.6 Coluna: combustivel – padronização e nulos
df["combustivel"] = (
    df["combustivel"]
    .fillna("Não Informado")
    .str.strip()
    .str.title()
)
# Unificar variações
mapa_combustivel = {
    "Eletrico": "Elétrico",
    "Electrico": "Elétrico",
}
df["combustivel"] = df["combustivel"].replace(mapa_combustivel)

# 2.7 Coluna: status – padronização e nulos
df["status"] = (
    df["status"]
    .fillna("Desconhecido")
    .str.strip()
    .str.title()
)
mapa_status = {
    "Disponivel": "Disponível",
}
df["status"] = df["status"].replace(mapa_status)

# ─────────────────────────────────────────────
# 3. PADRONIZAÇÃO DE FORMATOS FINAIS
# ─────────────────────────────────────────────

# Data → string no formato BR padrão
df["data_anuncio"] = df["data_anuncio"].dt.strftime("%d/%m/%Y")

# Preço → string formatado em BRL (R$ 1.234,56)
df["preco_brl"] = df["preco_brl"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

# ─────────────────────────────────────────────
# 4. EXPORTAÇÃO
# ─────────────────────────────────────────────
output_path = "outputs/dataset_ecommerce_carros.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"\n✅ Dataset tratado: {df.shape[0]} linhas × {df.shape[1]} colunas")
print(f"📁 Arquivo salvo em: {output_path}")
print("\nAmostra final:")
print(df.head(10).to_string(index=False))
print("\nNulos restantes:")
print(df.isnull().sum())
print("\nDistribuição de Status:")
print(df["status"].value_counts())
print("\nDistribuição de Combustível:")
print(df["combustivel"].value_counts())
