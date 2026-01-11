import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import google.generativeai as genai
from PIL import Image
import io

# --- CONFIGURAÇÃO DA IA (MANTENHA SUA CHAVE AQUI) ---
API_KEY = "AIzaSyAvcMp8boF5empfQwnECNAYnwxNIefYZIg" # <-- Não esqueça de colocar sua chave aqui novamente!
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Configuração da Página (Estilo Dashboard)
st.set_page_config(page_title="JPAgro | GIS Platform", layout="wide", initial_sidebar_state="expanded")

# CSS para customização visual (Estilo QGIS/Software Técnico)
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #d1d5db; }
    .stChatFloatingInputContainer { bottom: 20px; }
    section[data-testid="stSidebar"] { background-color: #263238; color: white; }
    .st-emotion-cache-16idsys p { color: white; } /* Texto da sidebar */
    h1, h2, h3 { color: #1a2e1a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

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

# --- INTERFACE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚜 JPAgro - Login")
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Acessar Sistema"):
        st.session_state.logged_in = True
        st.rerun()
else:
    # BARRA LATERAL (FERRAMENTAS)
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2942/2942531.png", width=80 )
        st.title("JPAgro GIS")
        st.divider()
        
        st.subheader("📸 Agrônomo Digital")
        foto = st.file_uploader("Diagnóstico por Imagem", type=['jpg', 'png', 'jpeg'])
        if foto:
            img = Image.open(foto)
            st.image(img, use_container_width=True)
            if st.button("🔍 Analisar Praga"):
                with st.spinner("Processando imagem..."):
                    prompt_ia = "Você é um agrônomo especialista. Analise esta foto de uma cultura agrícola. Identifique se há pragas ou doenças, dê o diagnóstico e sugira o manejo e produtos para tratamento de forma simples para um produtor."
                    response = model.generate_content([prompt_ia, img])
                    st.info(response.text)
        
        st.divider()
        st.subheader("🗺️ Camadas")
        st.checkbox("Satélite (Esri)", value=True)
        st.checkbox("Talhões", value=True)
        st.checkbox("Mapa de Calor (NDVI)", value=False)

    # PAINEL SUPERIOR (INDICADORES)
    clima = buscar_clima(-20.945, -48.620)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Temperatura", f"{clima['temp']}°C")
    with c2: st.metric("Vento", f"{clima['vento']} km/h")
    with c3: st.metric("Prob. Chuva", f"{clima['chuva_prob']}%")
    with c4: st.metric("Operação", "Pulverização OK" if clima['vento'] < 15 else "Vento Forte", delta_color="inverse")

    st.divider()

    # ÁREA CENTRAL (MAPA E CHAT)
    col_map, col_chat = st.columns([2, 1])

    with col_map:
        st.subheader("🌐 Visualizador Geográfico")
        m = folium.Map(location=[-20.945, -48.620], zoom_start=16, 
                       tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                       attr='Esri' )
        
        # Desenhar talhões com estilo técnico
        for i in range(5):
            offset = i * 0.0015
            folium.Rectangle(
                bounds=[[-20.946, -48.621 + offset], [-20.944, -48.619 + offset]],
                color='#ffffff', weight=1, fill=True, fill_color='#4caf50', fill_opacity=0.2,
                popup=f"Talhão {i+1}"
            ).add_to(m)
        st_folium(m, width=850, height=500)

    with col_chat:
        st.subheader("💬 Assistente IA")
        container = st.container(height=430)
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with container.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Pergunte ao Cientista de Dados..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with container.chat_message("user"):
                st.markdown(prompt)

            with container.chat_message("assistant"):
                contexto = f"O produtor está em Monte Azul Paulista. O clima atual é {clima['temp']}°C, vento de {clima['vento']}km/h. Responda de forma técnica e direta: {prompt}"
                response = model.generate_content(contexto)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
