import base64
from datetime import date
from pathlib import Path

import requests
import streamlit as st

API_URL = "https://api.football-data.org/v4"

st.set_page_config(page_title="El Míster IA", page_icon="⚽")

# Traducción de las posiciones que devuelve la API (en inglés).
# El orden del diccionario se usa también para ordenar la plantilla.
POSICIONES = {
    "Goalkeeper": "Portero",
    "Defence": "Defensa",
    "Centre-Back": "Defensa central",
    "Left-Back": "Lateral izquierdo",
    "Right-Back": "Lateral derecho",
    "Midfield": "Centrocampista",
    "Defensive Midfield": "Mediocentro defensivo",
    "Central Midfield": "Mediocentro",
    "Left Midfield": "Interior izquierdo",
    "Right Midfield": "Interior derecho",
    "Attacking Midfield": "Mediapunta",
    "Offence": "Delantero",
    "Left Winger": "Extremo izquierdo",
    "Right Winger": "Extremo derecho",
    "Centre-Forward": "Delantero centro",
}


# ---------- Datos (llamadas a la API) ----------

def pedir_api(ruta):
    """Hace una petición a football-data.org y devuelve la respuesta en JSON."""
    cabeceras = {"X-Auth-Token": st.secrets["FOOTBALL_API_KEY"]}
    respuesta = requests.get(f"{API_URL}{ruta}", headers=cabeceras, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


@st.cache_data(ttl=3600)  # se guarda 1 hora
def obtener_clasificacion():
    return pedir_api("/competitions/PD/standings")["standings"][0]["table"]


@st.cache_data(ttl=86400)  # la plantilla cambia poco: se guarda 1 día
def obtener_equipo(equipo_id):
    return pedir_api(f"/teams/{equipo_id}")


# ---------- Utilidades ----------

def calcular_edad(fecha_nacimiento):
    if not fecha_nacimiento:
        return None
    nacimiento = date.fromisoformat(fecha_nacimiento[:10])
    hoy = date.today()
    cumplido = (hoy.month, hoy.day) >= (nacimiento.month, nacimiento.day)
    return hoy.year - nacimiento.year - (0 if cumplido else 1)


def orden_posicion(posicion):
    orden = list(POSICIONES)
    return orden.index(posicion) if posicion in orden else len(orden)


# ---------- Bromas ----------

def svg_en_base64(nombre_archivo):
    """Lee un dibujo SVG del repositorio y lo convierte a base64,
    para poder mostrarlo dentro de la página con una etiqueta <img>."""
    ruta = Path(__file__).parent / nombre_archivo
    return base64.b64encode(ruta.read_bytes()).decode()


# Broma 1: tormenta sobre el escudo del Barça

BARCELONA_ID = 81  # id del FC Barcelona en football-data.org


def es_barcelona(equipo):
    return equipo.get("id") == BARCELONA_ID or "Barcelona" in equipo.get("name", "")


def mostrar_tormenta(escudo):
    rayo_b64 = svg_en_base64("rayo.svg")
    # La animación CSS hace que el rayo parpadee y que el escudo "tiemble".
    st.markdown(
        f"""
        <style>
          @keyframes destello {{ 0%,60%,100% {{opacity:1}} 30%,80% {{opacity:0.15}} }}
          @keyframes temblor  {{ 0%,100% {{transform:translateX(0)}}
                                 25% {{transform:translateX(-4px)}} 75% {{transform:translateX(4px)}} }}
          .tormenta {{ text-align:center; padding:12px; border-radius:16px;
                       background:linear-gradient(#1c1f2b,#3a3f52); }}
          .tormenta .rayo   {{ animation: destello 1.2s infinite; display:block; margin:0 auto -30px; }}
          .tormenta .escudo {{ animation: temblor 0.3s infinite; }}
        </style>
        <div class="tormenta">
          <img class="rayo" src="data:image/svg+xml;base64,{rayo_b64}" width="160">
          <img class="escudo" src="{escudo}" width="90">
          <p style="color:white; margin:8px 0 0;">⛈️ Alerta meteorológica en Can Barça ⛈️</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Broma 2: modo Cholo para el Atlético

ATLETICO_ID = 78  # id del Atlético de Madrid en football-data.org


def es_atletico(equipo):
    return equipo.get("id") == ATLETICO_ID or "Atlético" in equipo.get("name", "")


def mostrar_modo_cholo():
    st.balloons()
    svg_b64 = svg_en_base64("mascota.svg")
    st.markdown(
        f"""
        <div style="text-align:center; padding:16px; border-radius:16px;
                    background:linear-gradient(135deg,#d81e2c,#1f3a93); color:white;">
          <h2 style="color:white; margin:0;">🏆 Modo Cholo activado 🏆</h2>
          <img src="data:image/svg+xml;base64,{svg_b64}" width="180">
          <p style="font-size:1.3em; margin:0;"><b>Partido a partido</b> 💪</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Páginas ----------

def mostrar_clasificacion():
    st.title("⚽ El Míster IA")
    st.header("Clasificación de LaLiga")

    if st.button("🔄 Actualizar datos"):
        st.cache_data.clear()  # borra lo guardado y vuelve a pedirlo a la API

    try:
        tabla = obtener_clasificacion()
    except Exception as e:
        st.error(f"No he podido cargar la clasificación: {e}")
        return

    st.caption("Toca un equipo para ver su plantilla.")
    filas = [
        {
            "Pos": f["position"],
            "Escudo": f["team"]["crest"],
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
    seleccion = st.dataframe(
        filas,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={"Escudo": st.column_config.ImageColumn("", width="small")},
    )

    # Si se ha tocado una fila, guardamos el id del equipo en la URL (?equipo=...)
    if seleccion.selection.rows:
        fila = seleccion.selection.rows[0]
        st.query_params["equipo"] = str(tabla[fila]["team"]["id"])
        st.rerun()


def mostrar_equipo(equipo_id):
    if st.button("← Volver a la clasificación"):
        st.query_params.clear()
        st.rerun()

    try:
        equipo = obtener_equipo(equipo_id)
    except Exception as e:
        st.error(f"No he podido cargar el equipo: {e}")
        return

    if es_atletico(equipo):
        mostrar_modo_cholo()

    if es_barcelona(equipo):
        mostrar_tormenta(equipo.get("crest"))
    elif equipo.get("crest"):
        st.markdown(f'<img src="{equipo["crest"]}" width="72">', unsafe_allow_html=True)
    st.title(equipo.get("name", "Equipo"))

    detalles = []
    if equipo.get("founded"):
        detalles.append(f"Fundado en {equipo['founded']}")
    if equipo.get("venue"):
        detalles.append(f"Estadio: {equipo['venue']}")
    if (equipo.get("coach") or {}).get("name"):
        detalles.append(f"Entrenador: {equipo['coach']['name']}")
    if detalles:
        st.caption(" · ".join(detalles))

    plantilla = sorted(
        equipo.get("squad") or [],
        key=lambda j: (orden_posicion(j.get("position")), j.get("name", "")),
    )
    st.subheader(f"Plantilla ({len(plantilla)} jugadores)")

    if not plantilla:
        st.info("La API no tiene datos de plantilla para este equipo.")
        return

    filas = [
        {
            "Jugador": j.get("name"),
            "Posición": POSICIONES.get(j.get("position"), j.get("position") or "-"),
            "Edad": calcular_edad(j.get("dateOfBirth")),
            "Nacionalidad": j.get("nationality"),
        }
        for j in plantilla
    ]
    st.dataframe(
        filas,
        hide_index=True,
        column_config={"Edad": st.column_config.NumberColumn(format="%d")},
    )


# ---------- Qué página se muestra ----------
# Si la URL lleva ?equipo=123 se muestra ese equipo; si no, la clasificación.
equipo_id = st.query_params.get("equipo", "")
if equipo_id.isdigit():
    mostrar_equipo(int(equipo_id))
else:
    mostrar_clasificacion()
