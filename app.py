import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import google.generativeai as genai
from PIL import Image
import pandas as pd
import plotly.express as px
import numpy as np
import json
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA IA (CHAVE INTEGRADA) ---
API_KEY = "AIzaSyAvcMp8boF5empfQwnECNAYnwxNIefYZIg" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Configuração da Página
st.set_page_config(page_title="JPAgro | Inteligência no Campo", layout="wide")

# CSS PARA TEMA VERDE CLARO E CONTRASTE PROFISSIONAL
st.markdown("""
    <style>
    .main { background-color: #f4f7f4; }
    section[data-testid="stSidebar"] { background-color: #2e7d32 !important; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { 
        color: #000000 !important; font-weight: 800 !important;
    }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label { 
        color: #ffffff !important; font-weight: 500 !important;
    }
    [data-testid="stMetric"] { 
        background-color: #ffffff !important; 
        border-left: 5px solid #4caf50 !important; 
        padding: 15px !important; 
        border-radius: 8px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
    }
    [data-testid="stMetricLabel"] { color: #555555 !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #2e7d32 !important; font-weight: 800 !important; }
    .stButton>button { background-color: #4caf50 !important; color: white !important; border-radius: 20px !important; }
    h1, h2, h3 { color: #1b5e20 !important; }
    </style>
    """, unsafe_allow_html=True)

# Funções de Suporte
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
        return {
            "temp": data['current_weather']['temperature'],
            "vento": data['current_weather']['windspeed'],
            "chuva_prob": data['hourly']['precipitation_probability'][0]
        }
    except:
        return {"temp": "--", "vento": "--", "chuva_prob": "--"}

# --- INTERFACE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚜 JPAgro - Acesso")
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar no Painel"):
        st.session_state.logged_in = True
        st.rerun()
else:
    # BARRA LATERAL
    with st.sidebar:
        st.title("JPAgro")
        st.divider()
        st.subheader("📂 Importar Mapa")
        mapa_file = st.file_uploader("Suba o arquivo .geojson", type=['geojson'])
        
        st.divider()
        st.subheader("📸 Agrônomo Digital")
        foto = st.file_uploader("Foto da praga/doença", type=['jpg', 'png', 'jpeg'])
        if foto:
            img = Image.open(foto)
            st.image(img, use_container_width=True)
            if st.button("🔍 Analisar"):
                try:
                    with st.spinner("IA analisando imagem..."):
                        prompt_ia = "Você é um agrônomo especialista. Analise esta foto agrícola. Identifique pragas ou doenças e sugira o manejo."
                        response = model.generate_content([prompt_ia, img])
                        st.info(response.text)
                except Exception as e:
                    st.error(f"Erro na análise: {str(e)}")

    # INDICADORES
    clima = buscar_clima(-20.945, -48.620)
    st.subheader("📊 Monitoramento: Monte Azul Paulista")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{clima['temp']}°C")
    c2.metric("Vento", f"{clima['vento']} km/h")
    c3.metric("Prob. Chuva", f"{clima['chuva_prob']}%")
    c4.metric("Operação", "Ideal" if clima['vento'] < 15 else "Alerta Vento")

    st.divider()

    # ÁREA CENTRAL
    col_map, col_info = st.columns([1.6, 1])

    with col_map:
        st.subheader("🗺️ Mapa de Satélite Real")
        m = folium.Map(location=[-20.945, -48.620], zoom_start=15, 
                       tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                       attr='Esri' )
        
        talhao_clicado = "Nenhum"
        if mapa_file:
            data = json.load(mapa_file)
            folium.GeoJson(data, name="Talhões Reais",
                style_function=lambda x: {'fillColor': '#4caf50', 'color': 'white', 'weight': 2, 'fillOpacity': 0.4},
                tooltip=folium.GeoJsonTooltip(fields=['nome', 'cultura'], aliases=['Talhão:', 'Cultura:'])
            ).add_to(m)
        else:
            st.info("Aguardando upload do arquivo .geojson.")

        map_data = st_folium(m, width=700, height=450, use_container_width=True)

    with col_info:
        st.subheader("📈 Análise de NDVI")
        if map_data['last_object_clicked_tooltip']:
            try:
                talhao_clicado = map_data['last_object_clicked_tooltip'].split("Talhão: ")[1].split("\n")[0]
            except:
                talhao_clicado = "Selecionado"
            st.write(f"**Analisando: {talhao_clicado}**")
            df_ndvi = gerar_historico_ndvi(talhao_clicado)
            fig = px.line(df_ndvi, x="Data", y="NDVI")
            fig.update_traces(line_color='#2e7d32', line_width=3)
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Clique em um talhão no mapa.")

    # CHAT IA
    st.divider()
    st.subheader("💬 Consultoria JPAgro")
    prompt = st.chat_input("Pergunte algo...")
    if prompt:
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            try:
                res = model.generate_content(f"Produtor em Monte Azul Paulista pergunta sobre {talhao_clicado}: {prompt}")
                st.write(res.text)
            except Exception as e:
                st.error(f"Erro no chat: {str(e)}")
