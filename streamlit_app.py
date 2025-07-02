import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date

# ---------------------------------------------------------
# 📦 Utilidades
# ---------------------------------------------------------

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

# ---------------------------------------------------------
# 🔑 Algoritmo de conciliación con mora
# ---------------------------------------------------------

def conciliar(facturas: pd.DataFrame, pagos: pd.DataFrame):
    facturas["Monto"] = facturas["Monto"].astype(float)
    pagos["Monto"] = pagos["Monto"].astype(float)

    facturas["Pagado"] = 0.0
    facturas["Saldo"] = facturas["Monto"]

    asignaciones = []

    def allocate(inv_idx: int, monto: float, pago_idx: int):
        saldo = facturas.at[inv_idx, "Saldo"]
        if saldo <= 0.01 or monto <= 0:
            return 0.0
        aplicado = min(saldo, monto)
        facturas.at[inv_idx, "Pagado"] += aplicado
        facturas.at[inv_idx, "Saldo"] -= aplicado
        asignaciones.append({
            "Pago_idx": pago_idx,
            "Nro Factura": facturas.at[inv_idx, "Nro Factura"],
            "Asignado": aplicado
        })
        return aplicado

    for p_idx, pago in pagos.iterrows():
        restante = pago["Monto"]
        descripcion = str(pago.get("Descripción", "")).upper()

        for inv_idx, inv in facturas.iterrows():
            if inv["Saldo"] > 0 and str(inv["Nro Factura"]).upper() in descripcion:
                restante -= allocate(inv_idx, restante, p_idx)
                if restante < 0.01:
                    break

        if restante > 0.01 and "Cliente" in pagos.columns and "Cliente" in facturas.columns:
            same_client_inv = facturas[(facturas["Cliente"] == pago["Cliente"]) & (facturas["Saldo"] > 0)]
            for inv_idx in same_client_inv.sort_values("Fecha Emisión").index:
                restante -= allocate(inv_idx, restante, p_idx)
                if restante < 0.01:
                    break

        if restante > 0.01:
            for inv_idx in facturas[facturas["Saldo"] > 0].sort_values("Fecha Emisión").index:
                restante -= allocate(inv_idx, restante, p_idx)
                if restante < 0.01:
                    break

        pagos.at[p_idx, "No Asignado"] = round(restante, 2)

    def estado(row):
        if row["Saldo"] <= 0.01:
            return "PAGADA"
        elif row["Pagado"] > 0:
            return "PARCIAL"
        return "PENDIENTE"

    def dias_mora(row):
        if row.get("Tipo Documento") == "FACT" and row["Saldo"] > 0 and pd.notnull(row.get("Fecha Vencimiento")):
            venc = pd.to_datetime(row["Fecha Vencimiento"]).date()
            atraso = (date.today() - venc).days
            return max(atraso, 0)
        return 0

    facturas["Estado"] = facturas.apply(estado, axis=1)
    facturas["Días Mora"] = facturas.apply(dias_mora, axis=1)

    asignaciones_df = pd.DataFrame(asignaciones)
    return facturas, pagos, asignaciones_df

# ---------------------------------------------------------
# 🎛️ Interfaz Streamlit
# ---------------------------------------------------------

st.set_page_config(page_title="Conciliador IA v1.2", page_icon="📅", layout="centered")
st.title("🤖 Conciliador de Facturas y Pagos (v1.2)")

st.markdown("""
Cargá los dos archivos para generar la conciliación.  
- **Facturas**: columnas `Nro Factura`, `Cliente`, `Monto`, `Fecha Emisión`, `Tipo Documento`, `Fecha Vencimiento`.  
- **Pagos**: columnas `Descripción`, `Monto`, `Cliente`, `Fecha`.
""")

col1, col2 = st.columns(2)
facturas_file = col1.file_uploader("📄 Archivo de facturas (.xlsx)", type=["xlsx"], key="fact")
pagos_file = col2.file_uploader("🏦 Archivo de pagos (.xlsx o .csv)", type=["xlsx", "csv"], key="pay")

if facturas_file and pagos_file:
    try:
        facturas_df = pd.read_excel(facturas_file)
        pagos_df = pd.read_csv(pagos_file) if pagos_file.name.endswith(".csv") else pd.read_excel(pagos_file)
    except Exception as e:
        st.error(f"Error al leer archivos: {e}")
        st.stop()

    facturas_out, pagos_out, asignaciones_out = conciliar(facturas_df.copy(), pagos_df.copy())

    st.success("✔️ Conciliación completada")

    st.subheader("📋 Facturas")
    st.dataframe(facturas_out, use_container_width=True)

    st.subheader("🏷️ Pagos")
    st.dataframe(pagos_out, use_container_width=True)

    with st.expander("🔗 Detalle de asignaciones Pago ←→ Factura"):
        st.dataframe(asignaciones_out, use_container_width=True)

    colA, colB, colC = st.columns(3)
    colA.download_button("⬇️ Facturas conciliadas", data=to_csv_bytes(facturas_out), file_name="facturas_conciliadas.csv", mime="text/csv")
    colB.download_button("⬇️ Pagos consolidados",   data=to_csv_bytes(pagos_out),   file_name="pagos_conciliados.csv",   mime="text/csv")
    colC.download_button("⬇️ Detalle asignaciones", data=to_csv_bytes(asignaciones_out), file_name="detalle_asignaciones.csv", mime="text/csv")
else:
    st.info("Cargá ambos archivos para iniciar la conciliación.")
