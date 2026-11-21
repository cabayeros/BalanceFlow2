import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="BalanceFlow | Consolidación Multiempresa",
    page_icon="📊",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

# Encabezado Principal
st.title(" BalanceFlow — Puente de Consolidación Financiera")
st.markdown("Normalización automática, **Aduana Financiera** y consolidación multiempresa sin cambiar tu ERP.")
st.divider()

# --- BARRA LATERAL: INGESTA DE DATOS POR SUCURSAL ---
with st.sidebar:
    st.header(" 1. Ingesta por Sucursal")
    empresa_id = st.selectbox(
        "Selecciona Empresa / Filial:",
        options=[1, 2, 3],
        format_func=lambda x: {
            1: "1 - Nexus Guatemala (Casa Matriz)",
            2: "2 - Nexus El Salvador (Filial)",
            3: "3 - Logística Centroamérica"
        }[x]
    )
    
    archivo = st.file_uploader("Sube reporte Excel o CSV", type=["csv", "xlsx", "xls"])
    
    if st.button(" Procesar y Enviar a Aduana", use_container_width=True):
        if archivo is not None:
            with st.spinner("Normalizando columnas con Pandas..."):
                files = {"file": (archivo.name, archivo.getvalue())}
                try:
                    res = requests.post(f"{API_URL}/api/empresas/{empresa_id}/upload", files=files)
                    if res.status_code == 200:
                        data = res.json()
                        st.success(f" {data['registros_importados']} registros importados.")
                        # Ejecutar Aduana Financiera automáticamente tras la carga
                        res_aud = requests.post(f"{API_URL}/api/empresas/{empresa_id}/auditar")
                        if res_aud.status_code == 200:
                            aud = res_aud.json()["auditoria"]
                            st.info(f" Aduana: {aud['validados']} válidos | {aud['en_cuarentena']} en cuarentena.")
                    else:
                        st.error(f"Error: {res.json().get('detail', 'Fallo en la carga')}")
                except Exception as e:
                    st.error("No se pudo conectar al backend. ¿Está encendido uvicorn?")
        else:
            st.warning("Por favor selecciona un archivo primero.")

# --- CUERPO PRINCIPAL: CONSOLIDACIÓN Y KPIs ---
st.header(" 2. Radiografía Financiera Consolidada")

if st.button(" Actualizar Consolidación del Grupo"):
    st.rerun()

try:
    response = requests.get(f"{API_URL}/api/consolidado")
    if response.status_code == 200:
        reporte = response.json()["reporte_consolidado"]
        
        # Métricas principales (KPIs)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ingresos / Activos Brutos", f"Q {reporte['volumen_bruto_total']:,.2f}")
        col2.metric("Gastos Operativos", f"Q {reporte['gastos_totales']:,.2f}")
        col3.metric("Eliminación Intercompany", f"- Q {reporte['intercompany_eliminado']:,.2f}", delta="Cruce limpio", delta_color="normal")
        col4.metric("Resultado Neto Consolidado", f"Q {reporte['resultado_financiero_neto']:,.2f}")
        
        st.divider()
        
        # Gráfico de desglose por sucursal
        desglose = reporte.get("desglose_por_empresa", {})
        if desglose:
            st.subheader(" Desempeño por Empresa / Filial")
            df_chart = pd.DataFrame([
                {
                    "Empresa": f"Filial {emp_id}",
                    "Ingresos": datos["ingresos_o_saldo"],
                    "Gastos": datos["gastos"]
                }
                for emp_id, datos in desglose.items()
            ])
            
            fig = px.bar(
                df_chart, 
                x="Empresa", 
                y=["Ingresos", "Gastos"], 
                barmode="group",
                color_discrete_sequence=["#00CC96", "#EF553B"]
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aún no hay transacciones consolidadas. Sube un archivo CSV/Excel desde el panel izquierdo.")
            
except Exception:
    st.warning(" Esperando conexión con el backend (`http://127.0.0.1:8000`).")