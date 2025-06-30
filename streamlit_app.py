
import streamlit as st
import pandas as pd

def buscar_factura(row, fact_df):
    for _, f in fact_df.iterrows():
        if str(f["Nro Factura"]) in row["Descripción"] and abs(f["Monto"] - row["Monto"]) < 0.01:
            return f["Nro Factura"]
    return None

st.title("🤖 Conciliador de Facturas y Pagos")

facturas_file = st.file_uploader("📄 Subí archivo de facturas (.xlsx)", type=["xlsx"])
pagos_file = st.file_uploader("🏦 Subí archivo de pagos (.xlsx o .csv)", type=["xlsx", "csv"])

if facturas_file and pagos_file:
    facturas = pd.read_excel(facturas_file)
    pagos = pd.read_csv(pagos_file) if pagos_file.name.endswith(".csv") else pd.read_excel(pagos_file)

    pagos["Factura Relacionada"] = pagos.apply(buscar_factura, axis=1, fact_df=facturas)
    facturas["Estado"] = facturas["Nro Factura"].apply(
        lambda n: "PAGADA" if n in pagos["Factura Relacionada"].values else "PENDIENTE"
    )

    st.subheader("📋 Resultado: Facturas")
    st.dataframe(facturas)

    st.subheader("🏷️ Resultado: Pagos")
    st.dataframe(pagos)

    st.download_button("⬇️ Descargar conciliación de facturas", facturas.to_csv(index=False), "facturas_resultado.csv", "text/csv")
    st.download_button("⬇️ Descargar conciliación de pagos", pagos.to_csv(index=False), "pagos_resultado.csv", "text/csv")
