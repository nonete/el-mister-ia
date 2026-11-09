import streamlit as st

st.title("⚽ El Míster IA")
st.write("¡Hola mundo! Mi primera web sobre LaLiga.")

equipo = st.text_input("¿Cuál es tu equipo?")
if equipo:
    st.success(f"¡Aúpa {equipo}!")
