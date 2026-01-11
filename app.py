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
st.set_page_config(page_title="JPAgro | NDVI Analytics", layout="wide")

# CSS para Visual Profissional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e5e7eb; }
    .plot-container { border-radius: 10px; background-color: white; padding: 10px; border: 1px solid #e5e7eb; }
    </style>
    """, unsafe_allow_html=True)

# Função para simular histórico de NDVI (Enquanto configuramos a API real)
def gerar_historico_ndvi(talhao_nome):
    datas = [datetime.now() - timedelta(days=i*15) for i in range(12)]
    datas.reverse()
    # Simula uma queda no Talhão 3 para teste
    base = 0.75 if "03" not in talhao_nome else 0.80
    valores = [base + np.random.uniform(-0.05, 0.05) for _ in range(12)]
    if "03" in talhao_nome:
        valores[-3:] = [v - 0.15 for v in valores[-3:]] # Simula queda recente
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
    st.title("🚜 JPAgro - Acesso")
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        st.session_state.logged_in = True
        st.rerun()
else:
    # BARRA LATERAL
    with st.sidebar:
        st.title("JPAgro GIS")
        st.caption("Monitoramento de Precisão")
        st.divider()
        st.subheader("📸 Diagnóstico de Campo")
        foto = st.file_uploader("Foto da praga/folha", type=['jpg', 'png', 'jpeg'])
        if foto:
            img = Image.open(foto)
            st.image(img, use_container_width=True)
            if st.button("🔍 Analisar com IA"):
                with st.spinner("Analisando..."):
                    response = model.generate_content(["Identifique pragas nesta foto agrícola e sugira manejo:", img])
                    st.info(response.text)

    # INDICADORES TOPO
    clima = buscar_clima(-20.945, -48.620)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{clima['temp']}°C")
    c2.metric("Vento", f"{clima['vento']} km/h")
    c3.metric("Prob. Chuva", f"{clima['chuva_prob']}%")
    c4.metric("Status", "Operação OK" if clima['vento'] < 15 else "Vento Forte")

    st.divider()

    # ÁREA CENTRAL: MAPA E ANÁLISE
    col_map, col_info = st.columns([1.5, 1])

    with col_map:
        st.subheader("🗺️ Mapa de Talhões (Clique para analisar)")
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
                popup=nome_t,
                tooltip=f"Clique para ver histórico do {nome_t}"
            ).add_to(m)
        
        map_data = st_folium(m, width=700, height=450, use_container_width=True)

    with col_info:
        # Lógica para mostrar dados do talhão clicado
        talhao_selecionado = "Talhão 03" # Padrão inicial ou baseado no clique
        if map_data['last_object_clicked_tooltip']:
            talhao_selecionado = map_data['last_object_clicked_tooltip'].split("do ")[-1]

        st.subheader(f"📈 Histórico NDVI: {talhao_selecionado}")
        df_ndvi = gerar_historico_ndvi(talhao_selecionado)
        
        fig = px.line(df_ndvi, x="Data", y="NDVI", title=f"Evolução do Vigor Vegetativo")
        fig.update_traces(line_color='#2e7d32', line_width=3)
        fig.add_hrect(y0=0, y1=0.3, fillcolor="red", opacity=0.1, annotation_text="Solo Exposto")
        fig.add_hrect(y0=0.7, y1=1.0, fillcolor="green", opacity=0.1, annotation_text="Vigor Alto")
        st.plotly_chart(fig, use_container_width=True)

        st.write(f"**Resumo {talhao_selecionado}:**")
        status = "⚠️ Atenção: Queda detectada" if "03" in talhao_selecionado else "✅ Estável"
        st.write(f"Status: {status}")

    st.divider()
    # CHAT IA NO RODAPÉ
    st.subheader("💬 Consultoria JPAgro")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte sobre o histórico de NDVI ou manejo..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            res = model.generate_content(f"O produtor pergunta sobre o {talhao_selecionado} em Monte Azul Paulista. O NDVI atual é {df_ndvi['NDVI'].iloc[-1]:.2f}. Responda: {prompt}")
            st.markdown(res.text)
            st.session_state.messages.append({"role": "assistant", "content": res.text})
