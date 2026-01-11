import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json
import base64
from PIL import Image
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import io

# --- CONFIGURACAO DA IA ---
API_KEY = "AIzaSyCKZGDTzGVyE39UJqXTJcZxmMlP-kYuVqc"

def chamar_gemini_direto(prompt, imagem_base64=None):
    # Usando modelos estaveis para evitar erro 404
    model_text = "gemini-pro"
    model_vision = "gemini-pro-vision"
    headers = {"Content-Type": "application/json"}
    
    if imagem_base64:
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_vision}:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": imagem_base64}}
                ]
            }]
        }
    else:
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_text}:generateContent?key={API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload ))
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"Erro na IA: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Erro de conexao: {str(e)}"

# Configuracao da Pagina
st.set_page_config(page_title="JPAgro | Inteligencia no Campo", layout="wide")

# CSS PARA TEMA VERDE
st.markdown("""
    <style>
    .main { background-color: #f4f7f4; }
    section[data-testid="stSidebar"] { background-color: #2e7d32 !important; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { 
        color: #ffffff !important; font-weight: 800 !important;
    }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label { 
        color: #ffffff !important; font-weight: 500 !important;
    }
    [data-testid="stMetric"] { background-color: #ffffff !important; border-left: 5px solid #4caf50 !important; padding: 15px !important; border-radius: 8px !important; }
    [data-testid="stMetricValue"] { color: #1b5e20 !important; font-weight: bold; }
    .stButton>button { background-color: #4caf50 !important; color: white !important; border-radius: 20px !important; }
    h1, h2, h3 { color: #1b5e20 !important; }
    </style>
    """, unsafe_allow_html=True)

# Funcoes de Suporte
def gerar_historico_ndvi(talhao_nome):
    datas = [datetime.now() - timedelta(days=i*15) for i in range(12)]
    datas.reverse()
    base = 0.78 if "A" in talhao_nome else 0.72
    valores = [base + np.random.uniform(-0.04, 0.04) for _ in range(12)]
    return pd.DataFrame({"Data": datas, "NDVI": valores})

def buscar_clima(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation_probability"
        response = requests.get(url )
        data = response.json()
        return {"temp": data["current_weather"]["temperature"], "vento": data["current_weather"]["windspeed"], "chuva_prob": data["hourly"]["precipitation_probability"][0]}
    except:
        return {"temp": "--", "vento": "--", "chuva_prob": "--"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("JPAgro - Acesso")
    user = st.text_input("Usuario")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Credenciais incorretas.")
else:
    with st.sidebar:
        st.title("JPAgro")
        st.divider()
        st.subheader("Importar Mapa")
        mapa_file = st.file_uploader("Arquivo .geojson", type=["geojson"])
        st.divider()
        st.subheader("Agronomo Digital")
        foto = st.file_uploader("Foto da praga/doenca", type=["jpg", "png", "jpeg"])
        if foto:
            img = Image.open(foto)
            st.image(img, use_container_width=True)
            if st.button("Analisar"):
                with st.spinner("Analisando..."):
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    res = chamar_gemini_direto("Analise esta foto de planta e sugira o manejo em portugues.", img_str)
                    st.info(res)
        if st.button("Sair"):
            st.session_state.logged_in = False
            st.rerun()

    st.subheader("Monitoramento: Monte Azul Paulista")
    clima = buscar_clima(-20.945, -48.620)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{clima['temp']}C")
    c2.metric("Vento", f"{clima['vento']} km/h")
    c3.metric("Chuva", f"{clima['chuva_prob']}%")
    c4.metric("Status", "Ideal" if clima['vento'] < 20 else "Alerta")

    st.divider()
    col_map, col_info = st.columns([1.6, 1])

    with col_map:
        st.subheader("Mapa de Satelite")
        m = folium.Map(location=[-20.945, -48.620], zoom_start=15, 
                       tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                       attr='Esri' )
        talhao_clicado = "Nenhum"
        if mapa_file:
            data = json.load(mapa_file)
            folium.GeoJson(data, name="Talhoes",
                style_function=lambda x: {"fillColor": "#4caf50", "color": "white", "weight": 2, "fillOpacity": 0.4},
                tooltip=folium.GeoJsonTooltip(fields=["nome", "cultura"], aliases=["Talhao:", "Cultura:"])
            ).add_to(m)
        map_data = st_folium(m, width=700, height=450, use_container_width=True)

    with col_info:
        st.subheader("Analise de NDVI")
        if map_data and map_data.get("last_object_clicked_tooltip"):
            try:
                talhao_clicado = map_data["last_object_clicked_tooltip"].split("Talhao: ")[1].split("\n")[0]
            except:
                talhao_clicado = "Selecionado"
            st.write(f"Talhao: {talhao_clicado}")
            df_ndvi = gerar_historico_ndvi(talhao_clicado)
            fig = px.line(df_ndvi, x="Data", y="NDVI")
            fig.update_traces(line_color='#2e7d32')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Clique em um talhao no mapa.")

    st.divider()
    st.subheader("Consultoria JPAgro")
    prompt = st.chat_input("Pergunte ao agronomo...")
    if prompt:
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            res = chamar_gemini_direto(f"Agronomo em Monte Azul Paulista responde sobre {talhao_clicado}: {prompt}")
            st.write(res)
