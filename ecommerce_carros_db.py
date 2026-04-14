import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import re
import sqlite3

# ─────────────────────────────────────────────
# 1. GERAÇÃO DO DATASET SIMULADO (5.000 linhas)
# ─────────────────────────────────────────────
np.random.seed(42)
random.seed(42)

N = 5000

marcas_modelos = {
    "Toyota":     ["Corolla", "Hilux", "Yaris", "SW4"],
    "Honda":      ["Civic", "HR-V", "Fit", "CR-V"],
    "Volkswagen": ["Gol", "Polo", "T-Cross", "Virtus"],
    "Chevrolet":  ["Onix", "Tracker", "Cruze", "S10"],
    "Hyundai":    ["HB20", "Creta", "Tucson", "i30"],
    "Ford":       ["Ka", "EcoSport", "Ranger", "Territory"],
    "Fiat":       ["Argo", "Uno", "Toro", "Pulse"],
    "Renault":    ["Kwid", "Sandero", "Duster", "Logan"],
}

combustiveis = ["Gasolina", "Flex", "Diesel", "Elétrico", "Híbrido",
                "gasolina", "flex", "DIESEL", None, "Eletrico"]

status_lista = ["Disponível", "Vendido", "Reservado", "disponivel",
                "VENDIDO", "reservado", None, "Disponivel"]

base_date = datetime(2022, 1, 1)

registros = []
for i in range(N):
    marca  = random.choice(list(marcas_modelos.keys()))
    modelo = random.choice(marcas_modelos[marca])
    ano    = random.randint(2010, 2024)

    r_preco = random.random()
    if r_preco < 0.04:
        preco_raw = None
    elif r_preco < 0.06:
        preco_raw = -abs(np.random.normal(80000, 30000))
    elif r_preco < 0.08:
        preco_raw = f"R$ {np.random.normal(80000, 30000):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    elif r_preco < 0.10:
        preco_raw = f"${np.random.normal(80000, 30000):.2f}"
    else:
        preco_raw = round(abs(np.random.normal(80000, 30000)), 2)

    dias      = random.randint(0, 1000)
    data_base = base_date + timedelta(days=dias)
    r_data    = random.random()
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

    registros.append({
        "marca_modelo":  f"{marca} {modelo}",
        "ano_fabricacao": ano if random.random() > 0.03 else None,
        "preco_brl":      preco_raw,
        "data_anuncio":   data_raw,
        "combustivel":    random.choice(combustiveis),
        "status":         random.choice(status_lista),
    })

indices_dup = np.random.choice(N, size=int(N * 0.03), replace=False)
registros.extend([registros[i] for i in indices_dup])

df = pd.DataFrame(registros)
print(f"Dataset bruto: {df.shape[0]} linhas × {df.shape[1]} colunas")
print(f"Nulos:\n{df.isnull().sum()}\nDuplicatas: {df.duplicated().sum()}\n")

# ─────────────────────────────────────────────
# 2. TRATAMENTO DE DADOS
# ─────────────────────────────────────────────

df.drop_duplicates(inplace=True)
df.reset_index(drop=True, inplace=True)

df["marca_modelo"] = df["marca_modelo"].fillna("Desconhecido").str.strip().str.title()

df["ano_fabricacao"] = pd.to_numeric(df["ano_fabricacao"], errors="coerce")
mediana_ano = df["ano_fabricacao"].median()
df["ano_fabricacao"] = df["ano_fabricacao"].fillna(mediana_ano).astype(int)
df = df[(df["ano_fabricacao"] >= 1980) & (df["ano_fabricacao"] <= datetime.now().year)]

def limpar_preco(valor):
    if pd.isnull(valor):
        return np.nan
    s = re.sub(r"[R$\s]", "", str(valor).strip())
    if re.search(r"\d{1,3}(\.\d{3})+,\d{2}", s):
        s = s.replace(".", "").replace(",", ".")
    elif re.search(r"\d{1,3}(,\d{3})+\.\d{2}", s):
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan

df["preco_brl"] = df["preco_brl"].apply(limpar_preco)
df = df[df["preco_brl"].isna() | (df["preco_brl"] > 0)]
df["preco_brl"] = df["preco_brl"].fillna(df["preco_brl"].median()).round(2)

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
df["data_anuncio"] = df["data_anuncio"].fillna(df["data_anuncio"].mode()[0])

df["combustivel"] = (df["combustivel"].fillna("Não Informado").str.strip().str.title()
                     .replace({"Eletrico": "Elétrico", "Electrico": "Elétrico"}))

df["status"] = (df["status"].fillna("Desconhecido").str.strip().str.title()
                .replace({"Disponivel": "Disponível"}))

# ─────────────────────────────────────────────
# 3. PREPARAR CÓPIA PARA O BANCO (tipos nativos)
# ─────────────────────────────────────────────
# No banco mantemos: data como ISO 8601 e preço como REAL (float)
df_db = df.copy()
df_db["data_anuncio"] = df_db["data_anuncio"].dt.strftime("%Y-%m-%d")  # ISO para SQLite DATE
# preco_brl já é float neste ponto

# ─────────────────────────────────────────────
# 4. EXPORTAÇÃO → SQLite (.db)
# ─────────────────────────────────────────────
DB_PATH = "outputs/ecommerce_carros.db"

with sqlite3.connect(DB_PATH) as conn:
    # 4.1 Cria tabela com tipos explícitos e chave primária auto
    conn.execute("DROP TABLE IF EXISTS anuncios")
    conn.execute("""
        CREATE TABLE anuncios (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            marca_modelo   TEXT    NOT NULL,
            ano_fabricacao INTEGER NOT NULL,
            preco_brl      REAL    NOT NULL,
            data_anuncio   TEXT    NOT NULL,   -- ISO 8601: YYYY-MM-DD
            combustivel    TEXT    NOT NULL,
            status         TEXT    NOT NULL
        )
    """)

    # 4.2 Insere os dados
    df_db.to_sql("anuncios", conn, if_exists="append", index=False)

    # 4.3 Cria índices úteis para consultas
    conn.execute("CREATE INDEX IF NOT EXISTS idx_status      ON anuncios(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_combustivel ON anuncios(combustivel)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ano         ON anuncios(ano_fabricacao)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_data        ON anuncios(data_anuncio)")

    # 4.4 Verifica
    total = conn.execute("SELECT COUNT(*) FROM anuncios").fetchone()[0]
    print(f"✅ {total} registros inseridos na tabela 'anuncios'")

    # 4.5 Exemplos de consultas de validação
    print("\n── Top 5 marcas por quantidade ──")
    q1 = pd.read_sql("""
        SELECT marca_modelo, COUNT(*) AS qtd
        FROM anuncios
        GROUP BY marca_modelo
        ORDER BY qtd DESC
        LIMIT 5
    """, conn)
    print(q1.to_string(index=False))

    print("\n── Preço médio por combustível ──")
    q2 = pd.read_sql("""
        SELECT combustivel,
               ROUND(AVG(preco_brl), 2) AS preco_medio,
               COUNT(*)                 AS qtd
        FROM anuncios
        GROUP BY combustivel
        ORDER BY preco_medio DESC
    """, conn)
    print(q2.to_string(index=False))

    print("\n── Distribuição de status ──")
    q3 = pd.read_sql("""
        SELECT status, COUNT(*) AS qtd
        FROM anuncios
        GROUP BY status
        ORDER BY qtd DESC
    """, conn)
    print(q3.to_string(index=False))

    print("\n── Anúncios mais recentes ──")
    q4 = pd.read_sql("""
        SELECT id, marca_modelo, ano_fabricacao, preco_brl, data_anuncio, status
        FROM anuncios
        ORDER BY data_anuncio DESC
        LIMIT 5
    """, conn)
    print(q4.to_string(index=False))

print(f"\n📁 Banco de dados salvo em: {DB_PATH}")
print("   Tabela  : anuncios")
print("   Índices : idx_status, idx_combustivel, idx_ano, idx_data")
