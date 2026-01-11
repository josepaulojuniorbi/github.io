import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import google.generativeai as genai
from PIL import Image
import io

# --- CONFIGURAÇÃO DA IA (COLOQUE SUA CHAVE AQUI) ---
API_KEY = "AIzaSyAvcMp8boF5empfQwnECNAYnwxNIefYZIg"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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
    st.subheader("Acesso ao Sistema")
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        st.session_state.logged_in = True
        st.rerun()
else:
    # Sidebar para Análise de Fotos
    st.sidebar.header("📸 Agrônomo Digital")
    foto = st.sidebar.file_uploader("Tire uma foto da praga/doença", type=['jpg', 'png', 'jpeg'])
    
    if foto:
        img = Image.open(foto)
        st.sidebar.image(img, caption="Foto enviada", use_container_width=True)
        if st.sidebar.button("Analisar Praga"):
            with st.sidebar:
                with st.spinner("Analisando..."):
                    prompt_ia = "Você é um agrônomo especialista. Analise esta foto de uma cultura agrícola. Identifique se há pragas ou doenças, dê o diagnóstico e sugira o manejo e produtos para tratamento de forma simples para um produtor."
                    response = model.generate_content([prompt_ia, img])
                    st.warning("📋 Diagnóstico da IA:")
                    st.write(response.text)

    # Dashboard Principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📍 Monitoramento por Satélite")
        m = folium.Map(location=[-20.945, -48.620], zoom_start=16, 
                       tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                       attr='Esri' )
        
        # Desenhar talhões
        for i in range(5):
            offset = i * 0.0015
            folium.Rectangle(
                bounds=[[-20.946, -48.621 + offset], [-20.944, -48.619 + offset]],
                color='white', weight=2, fill=True, fill_color='#4caf50', fill_opacity=0.3,
                popup=f"Talhão {i+1}"
            ).add_to(m)
        st_folium(m, width=700, height=450)

    with col2:
        st.subheader("🤖 Cientista de Dados")
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Pergunte sobre o manejo ou clima..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                clima = buscar_clima(-20.945, -48.620)
                contexto = f"O produtor está em Monte Azul Paulista. O clima atual é {clima['temp']}°C, vento de {clima['vento']}km/h e {clima['chuva_prob']}% de chance de chuva. Responda a pergunta dele de forma técnica mas simples: {prompt}"
                response = model.generate_content(contexto)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

    # Rodapé Clima
    st.divider()
    clima = buscar_clima(-20.945, -48.620)
    st.subheader(f"🌤️ Clima Real em Monte Azul Paulista")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{clima['temp']}°C")
    c2.metric("Vento", f"{clima['vento']} km/h")
    c3.metric("Prob. Chuva", f"{clima['chuva_prob']}%")
    c4.metric("Status", "Ideal para Pulverizar" if clima['vento'] < 15 else "Vento Forte")
