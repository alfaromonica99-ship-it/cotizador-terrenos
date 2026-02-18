import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Cotizador de Terrenos", layout="centered")

@st.cache_data
def cargar_lotes(path="data/lotes.csv"):
    df = pd.read_csv(path)
    # Normaliza columnas esperadas (ajusta a tu CSV)
    df["estado"] = df["estado"].fillna("disponible").str.lower()
    return df

def pago_mensual_frances(monto, tasa_anual, meses):
    """Cuota fija (sistema francés). Si tasa_anual=0, cuota = monto/meses."""
    if meses <= 0:
        return 0.0
    if tasa_anual <= 0:
        return monto / meses
    i = (tasa_anual / 100) / 12
    return monto * (i * (1 + i) ** meses) / ((1 + i) ** meses - 1)

def tabla_amortizacion(monto, tasa_anual, meses):
    if meses <= 0:
        return pd.DataFrame()
    i = (tasa_anual / 100) / 12 if tasa_anual > 0 else 0.0
    cuota = pago_mensual_frances(monto, tasa_anual, meses)

    saldo = monto
    rows = []
    for m in range(1, meses + 1):
        interes = saldo * i
        capital = cuota - interes
        saldo = max(0.0, saldo - capital)
        rows.append({
            "Mes": m,
            "Cuota": round(cuota, 2),
            "Interés": round(interes, 2),
            "Capital": round(capital, 2),
            "Saldo": round(saldo, 2),
        })
    return pd.DataFrame(rows)

def money(q):
    return f"Q {q:,.2f}"

st.title("Cotizador de Terrenos")
st.caption("Abre este link desde tu teléfono. Sin instalar nada.")

df = cargar_lotes()

# Filtro de disponibilidad
df_disp = df[df["estado"].isin(["disponible", "reservable", "disponible "])].copy()
if df_disp.empty:
    st.warning("No hay lotes disponibles en el archivo de datos.")
    st.stop()

# UI: selección por proyecto/etapa
proyecto = st.selectbox("Proyecto", sorted(df_disp["proyecto"].dropna().unique()))
df_p = df_disp[df_disp["proyecto"] == proyecto]

etapa = st.selectbox("Etapa", sorted(df_p["etapa"].dropna().unique()))
df_e = df_p[df_p["etapa"] == etapa]

lote_id = st.selectbox("Lote", df_e["lote"].astype(str).tolist())
row = df_e[df_e["lote"].astype(str) == str(lote_id)].iloc[0]

# Datos base del lote
precio_lista = float(row.get("precio_lista", 0))
area = float(row.get("area_m2", 0))
enganche_min_pct = float(row.get("enganche_min_pct", 20))
gastos_admin = float(row.get("gastos_admin", 0))
tasa_anual = float(row.get("tasa_anual", 0))

st.subheader("Datos del lote")
c1, c2, c3 = st.columns(3)
c1.metric("Área", f"{area:.2f} m²")
c2.metric("Precio lista", money(precio_lista))
c3.metric("Gastos admin.", money(gastos_admin))

st.divider()
st.subheader("Arma tu cotización")

# Entradas
col1, col2 = st.columns(2)
enganche_pct = col1.slider("Enganche (%)", 0, 100, int(enganche_min_pct))
plazo = col2.selectbox("Plazo (meses)", [12, 24, 36, 48, 60, 72, 84])

# Reglas dinámicas (ejemplo)
descuento_pct = st.slider("Descuento (%)", 0, 20, 0)
precio_con_desc = precio_lista * (1 - descuento_pct / 100)

enganche = precio_con_desc * enganche_pct / 100
saldo_financiar = max(0.0, precio_con_desc - enganche)

# Cuota
cuota = pago_mensual_frances(saldo_financiar, tasa_anual, plazo)

# Resumen
st.subheader("Resumen")
r1, r2 = st.columns(2)
r1.metric("Precio final", money(precio_con_desc))
r1.metric("Enganche", money(enganche))
r2.metric("Saldo a financiar", money(saldo_financiar))
r2.metric("Cuota mensual estimada", money(cuota))

total_estimado = enganche + gastos_admin + (cuota * plazo)
st.info(f"Total estimado (enganche + gastos + cuotas): **{money(total_estimado)}**")

# Tabla
with st.expander("Ver tabla de pagos"):
    st.caption("Si la tasa es 0%, es división simple. Si no, es cuota fija (sistema francés).")
    st.dataframe(tabla_amortizacion(saldo_financiar, tasa_anual, plazo), use_container_width=True)

st.divider()
st.caption("Tip: en teléfono, usa el menú del navegador → 'Agregar a pantalla de inicio' para tenerlo como ícono (sin instalar apps).")