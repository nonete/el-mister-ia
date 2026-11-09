import requests
import streamlit as st

st.set_page_config(page_title="El Míster IA", page_icon="⚽")
st.title("⚽ El Míster IA")

@st.cache_data(ttl=3600)
def obtener_clasificacion():
    url = "https://api.football-data.org/v4/competitions/PD/standings"
    cabeceras = {"X-Auth-Token": st.secrets["FOOTBALL_API_KEY"]}
    respuesta = requests.get(url, headers=cabeceras, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()["standings"][0]["table"]

st.header("Clasificación de LaLiga")
try:
    tabla = obtener_clasificacion()
    filas = [
        {
            "Pos": f["position"],
            "Equipo": f["team"]["shortName"],
            "PJ": f["playedGames"],
            "G": f["won"],
            "E": f["draw"],
            "P": f["lost"],
            "DG": f["goalDifference"],
            "Pts": f["points"],
        }
        for f in tabla
    ]
    st.dataframe(filas, hide_index=True)
except Exception as e:
    st.error(f"No he podido cargar la clasificación: {e}")