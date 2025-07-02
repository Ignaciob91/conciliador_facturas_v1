import streamlit as st
import pandas as pd

# ---------------------------
# Funciones auxiliares
# ---------------------------

def buscar_factura(row, fact_df):
    """Devuelve el Nro de factura coincidente por texto y monto exacto (versión simple)."""
    for _, f in fact_df.iterrows():
        if str(f["Nro Factura"]) in str(row["Descripción"]) and abs(f["Monto"] - row["Monto"]) < 0.01:
            return f["Nro Factura"]
    return None

# ---------------------------
# Interfaz Streamlit
# ---------------------------

st.set_page_config(page_title="Conciliador de Facturas", page_icon="💸")
st.title("🤖 Conciliador de Facturas y Pagos (v1.1)")

facturas_file = st.file_uploader("📄 Subí archivo de facturas (.xlsx)", type=["xlsx"])
pagos_file = st.file_uploader("🏦 Subí archivo de pagos (.xlsx o .csv)", type=["xlsx", "csv"])

# ---------------------------
# Procesamiento principal
# ---------------------------

if facturas_file and pagos_file:
    # 1) Cargar archivos
    facturas = pd.read_excel(facturas_file)
    pagos = pd.read_csv(pagos_file) if pagos_file.name.endswith(".csv") else pd.read_excel(pagos_file)

    # 2) Agregar columnas para versión con pagos parciales/múltiples
    facturas["Pagado"] = 0.0
    facturas["Saldo"] = facturas["Monto"]

    # 3) Conciliación básica (exacta) — se puede reemplazar por lógica parcial más adelante
    pagos["Factura Relacionada"] = pagos.apply(buscar_factura, axis=1, fact_df=facturas)

    # Actualizar Pagado / Saldo según coincidencias exactas
    for _, pago in pagos.dropna(subset=["Factura Relacionada"]).iterrows():
        nro = pago["Factura Relacionada"]
        idx = facturas.loc[facturas["Nro Factura"] == nro].index
        facturas.loc[idx, "Pagado"] += pago["Monto"]
        facturas.loc[idx, "Saldo"] = facturas.loc[idx, "Monto"] - facturas.loc[idx, "Pagado"]

    # 4) Determinar estado
    def estado(row):
        if row["Saldo"] <= 0.01:
            return "PAGADA"
        elif row["Pagado"] > 0:
            return "PARCIAL"
        else:
            return "PENDIENTE"

    facturas["Estado"] = facturas.apply(estado, axis=1)

    # 5) Mostrar resultados
    st.subheader("📋 Resultado: Facturas")
    st.dataframe(facturas, use_container_width=True)

    st.subheader("🏷️ Resultado: Pagos")
    st.dataframe(pagos, use_container_width=True)

    # 6) Descargas
    st.download_button("⬇️ Descargar conciliación de facturas", facturas.to_csv(index=False).encode(), "facturas_resultado.csv", "text/csv")
    st.download_button("⬇️ Descargar conciliación de pagos", pagos.to_csv(index=False).encode(), "pagos_resultado.csv", "text/csv")

else:
    st.info("Cargá ambos archivos para iniciar la conciliación.")
