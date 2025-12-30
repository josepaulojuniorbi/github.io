import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
import requests
import json

# Configuração da Página
st.set_page_config(page_title="JPAgro - Inteligência no Campo", layout="wide")

# Função para buscar clima real
def buscar_clima(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation_probability"
        response = requests.get(url )
        data = response.json()
        return {
            "temp": data['current_weather']['temperature'],
            "vento": data['current_weather']['windspeed'],
            "chuva_prob": data['hourly']['precipitation_probability'][0]
        }
    except:
        return {"temp": "--", "vento": "--", "chuva_prob": "--"}

# Título
st.title("🚜 JPAgro - Inteligência no Campo")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        st.session_state.logged_in = True
        st.rerun()
else:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📍 Mapa da Propriedade - Monte Azul Paulista/SP")
        # Mapa simplificado para o primeiro acesso web
        m = folium.Map(location=[-20.945, -48.620], zoom_start=15, tiles='OpenStreetMap')
        folium.Marker([-20.945, -48.620], popup="Sede Fazenda").add_to(m)
        st_folium(m, width=700, height=500)

    with col2:
        st.subheader("🤖 Cientista de Dados JPAgro")
        st.info("Olá! Sou a IA da JPAgro. Como posso ajudar hoje?")
        prompt = st.chat_input("Pergunte algo...")
        if prompt:
            st.write(f"Analisando: {prompt}")
            st.success("Análise concluída! O clima está favorável para as atividades hoje.")

    st.divider()
    clima = buscar_clima(-20.945, -48.620)
    st.subheader(f"🌤️ Clima Real em Monte Azul Paulista")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperatura", f"{clima['temp']}°C")
    c2.metric("Vento", f"{clima['vento']} km/h")
    c3.metric("Prob. Chuva", f"{clima['chuva_prob']}%")
