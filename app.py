import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import google.generativeai as genai
from PIL import Image
import io

# --- CONFIGURAÇÃO DA IA (MANTENHA SUA CHAVE AQUI) ---
API_KEY = "AIzaSyAvcMp8boF5empfQwnECNAYnwxNIefYZIg" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Configuração da Página
st.set_page_config(page_title="JPAgro | Monitoramento Inteligente", layout="wide")

# CSS para Visual Profissional (Clean & Tech)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #2e7d32; }
    [data-testid="stMetricLabel"] { font-size: 1rem; color: #4b5563; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
    }
    section[data-testid="stSidebar"] { 
        background-color: #1f2937; 
        border-right: 1px solid #e5e7eb;
    }
    .st-emotion-cache-16idsys p { color: #f3f4f6; }
    h1, h2, h3 { color: #111827; font-weight: 700; }
    .stChatFloatingInputContainer { background-color: transparent; }
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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚜 JPAgro - Acesso")
    with st.form("login"):
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar no Sistema"):
            st.session_state.logged_in = True
            st.rerun()
else:
    # BARRA LATERAL
    with st.sidebar:
        st.title("JPAgro")
        st.caption("v2.0 | Inteligência Agronômica")
        st.divider()
        
        st.subheader("📸 Diagnóstico de Pragas")
        foto = st.file_uploader("Enviar foto do campo", type=['jpg', 'png', 'jpeg'])
        if foto:
            img = Image.open(foto)
            st.image(img, use_container_width=True)
            if st.button("🔍 Analisar com IA"):
                with st.spinner("IA analisando..."):
                    prompt_ia = "Você é um agrônomo especialista. Analise esta foto de uma cultura agrícola. Identifique se há pragas ou doenças, dê o diagnóstico e sugira o manejo e produtos para tratamento de forma simples para um produtor."
                    response = model.generate_content([prompt_ia, img])
                    st.success("Diagnóstico Concluído")
                    st.write(response.text)
        
        st.divider()
        st.subheader("🗺️ Camadas do Mapa")
        st.checkbox("Satélite de Alta Resolução", value=True)
        st.checkbox("Limites dos Talhões", value=True)

    # PAINEL DE INDICADORES (LIMPO E LEGÍVEL)
    clima = buscar_clima(-20.945, -48.620)
    st.subheader("📊 Condições em Tempo Real - Monte Azul Paulista")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{clima['temp']}°C")
    c2.metric("Vento", f"{clima['vento']} km/h")
    c3.metric("Prob. Chuva", f"{clima['chuva_prob']}%")
    c4.metric("Status Operação", "Ideal" if clima['vento'] < 15 else "Alerta Vento")

    st.divider()

    # ÁREA CENTRAL
    col_map, col_chat = st.columns([1.8, 1])

    with col_map:
        st.subheader("🗺️ Visualizador de Talhões")
        m = folium.Map(location=[-20.945, -48.620], zoom_start=16, 
                       tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                       attr='Esri' )
        
        # Talhões com bordas brancas finas e preenchimento suave
        for i in range(5):
            offset = i * 0.0015
            folium.Rectangle(
                bounds=[[-20.946, -48.621 + offset], [-20.944, -48.619 + offset]],
                color='#ffffff', weight=1.5, fill=True, fill_color='#4caf50', fill_opacity=0.25,
                popup=f"Talhão {i+1}"
            ).add_to(m)
        st_folium(m, width=800, height=520, use_container_width=True)

    with col_chat:
        st.subheader("💬 Assistente Agronômico")
        # Container de chat com altura fixa e scroll
        chat_container = st.container(height=450)
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Olá! Sou seu assistente JPAgro. Como posso ajudar com sua fazenda hoje?"}]

        for message in st.session_state.messages:
            with chat_container.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Pergunte sobre manejo, clima ou pragas..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container.chat_message("user"):
                st.markdown(prompt)

            with chat_container.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    contexto = f"O produtor está em Monte Azul Paulista. Clima: {clima['temp']}°C, vento {clima['vento']}km/h. Responda de forma técnica e prática: {prompt}"
                    response = model.generate_content(contexto)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
