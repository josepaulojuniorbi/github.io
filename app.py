import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import google.generativeai as genai
from PIL import Image
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA IA (MANTENHA SUA CHAVE AQUI) ---
API_KEY = "AIzaSyAvcMp8boF5empfQwnECNAYnwxNIefYZIg" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Configuração da Página
st.set_page_config(page_title="JPAgro | Monitoramento Verde", layout="wide")

# CSS PARA TEMA VERDE CLARO E LIMPO
st.markdown("""
    <style>
    /* Fundo Geral */
    .main { background-color: #f4f7f4; }
    
    /* Barra Lateral Verde */
    section[data-testid="stSidebar"] {
        background-color: #2e7d32 !important;
        color: white !important;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span {
        color: white !important;
    }

    /* Quadrados de Indicadores (Brancos com borda verde) */
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        border-left: 5px solid #4caf50 !important;
        padding: 15px !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
    }
    
    /* Cores dos Textos nos Indicadores */
    [data-testid="stMetricLabel"] { color: #555555 !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #2e7d32 !important; font-weight: 800 !important; }

    /* Botões Verdes */
    .stButton>button {
        background-color: #4caf50 !important;
        color: white !important;
        border-radius: 20px !important;
        border: none !important;
    }
    
    /* Títulos */
    h1, h2, h3 { color: #1b5e20 !important; font-family: 'Segoe UI', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# Função para simular histórico de NDVI
def gerar_historico_ndvi(talhao_nome):
    datas = [datetime.now() - timedelta(days=i*15) for i in range(12)]
    datas.reverse()
    base = 0.75 if "03" not in talhao_nome else 0.80
    valores = [base + np.random.uniform(-0.05, 0.05) for _ in range(12)]
    if "03" in talhao_nome:
        valores[-3:] = [v - 0.15 for v in valores[-3:]]
    return pd.DataFrame({"Data": datas, "NDVI": valores})

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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚜 JPAgro - Bem-vindo")
    with st.container():
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.button("Entrar no Painel"):
            st.session_state.logged_in = True
            st.rerun()
else:
    # BARRA LATERAL VERDE
    with st.sidebar:
        st.title("JPAgro")
        st.write("Inteligência no Campo")
        st.divider()
        st.subheader("📸 Agrônomo Digital")
        foto = st.file_uploader("Analisar praga por foto", type=['jpg', 'png', 'jpeg'])
        if foto:
            img = Image.open(foto)
            st.image(img, use_container_width=True)
            if st.button("🔍 Iniciar Diagnóstico"):
                with st.spinner("IA analisando..."):
                    response = model.generate_content(["Analise esta foto agrícola e sugira manejo:", img])
                    st.success("Diagnóstico Concluído")
                    st.write(response.text)

    # INDICADORES (LIMPOS E VERDES)
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
        st.subheader("🗺️ Mapa de Satélite")
        m = folium.Map(location=[-20.945, -48.620], zoom_start=16, 
                       tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                       attr='Esri' )
        
        for i in range(5):
            offset = i * 0.0015
            nome_t = f"Talhão {i+1}"
            cor = '#ffeb3b' if i == 2 else '#4caf50'
            folium.Rectangle(
                bounds=[[-20.946, -48.621 + offset], [-20.944, -48.619 + offset]],
                color='white', weight=2, fill=True, fill_color=cor, fill_opacity=0.3,
                tooltip=f"Clique para ver histórico do {nome_t}"
            ).add_to(m)
        
        map_data = st_folium(m, width=700, height=450, use_container_width=True)

    with col_info:
        talhao_selecionado = "Talhão 03"
        if map_data['last_object_clicked_tooltip']:
            talhao_selecionado = map_data['last_object_clicked_tooltip'].split("do ")[-1]

        st.subheader(f"📈 NDVI: {talhao_selecionado}")
        df_ndvi = gerar_historico_ndvi(talhao_selecionado)
        
        fig = px.line(df_ndvi, x="Data", y="NDVI")
        fig.update_traces(line_color='#2e7d32', line_width=3)
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=30, b=0), height=300)
        st.plotly_chart(fig, use_container_width=True)
        st.write(f"Status: {'⚠️ Atenção' if '03' in talhao_selecionado else '✅ Estável'}")

    # CHAT IA
    st.divider()
    st.subheader("💬 Consultoria JPAgro")
    prompt = st.chat_input("Pergunte algo ao seu cientista de dados...")
    if prompt:
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            res = model.generate_content(f"Produtor em Monte Azul Paulista pergunta sobre {talhao_selecionado}: {prompt}")
            st.write(res.text)
