import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

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
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📍 Monitoramento por Satélite - Monte Azul Paulista/SP")
        
        # Criar o mapa com visão de SATÉLITE REAL (Esri World Imagery)
        m = folium.Map(
            location=[-20.945, -48.620], 
            zoom_start=16, 
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri'
         )
        
        # Desenhar os talhões sobre o satélite
        cores = ['#4caf50', '#4caf50', '#ffeb3b', '#4caf50', '#2e7d32']
        nomes = ['Talhão 01 - Laranja', 'Talhão 02 - Laranja', 'Talhão 03 - Cana (ALERTA)', 'Talhão 04 - Cana', 'Talhão 05 - Reserva']
        
        for i in range(5):
            offset = i * 0.0015 # Ajuste para ficarem mais próximos
            folium.Rectangle(
                bounds=[[-20.946, -48.621 + offset], [-20.944, -48.619 + offset]],
                color='white', # Borda branca para destacar no satélite escuro
                weight=2,
                fill=True,
                fill_color=cores[i],
                fill_opacity=0.4, # Mais transparente para ver a plantação por baixo
                popup=nomes[i]
            ).add_to(m)

        st_folium(m, width=800, height=500)

    with col2:
        st.subheader("🤖 Cientista de Dados JPAgro")
        st.info("Olá! Sou a IA da JPAgro. Note que no Talhão 03 a coloração do satélite está mais clara, confirmando a queda de vigor.")
        prompt = st.chat_input("Pergunte algo sobre a fazenda...")
        if prompt:
            st.chat_message("user").write(prompt)
            st.chat_message("assistant").write(f"Analisando '{prompt}'... Com base na imagem de satélite e no clima, recomendo vistoria no Talhão 03.")

    st.divider()
    clima = buscar_clima(-20.945, -48.620)
    st.subheader(f"🌤️ Clima Real em Monte Azul Paulista")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{clima['temp']}°C")
    c2.metric("Vento", f"{clima['vento']} km/h")
    c3.metric("Prob. Chuva", f"{clima['chuva_prob']}%")
    c4.metric("Status", "Bom para Pulverizar" if clima['vento'] < 15 else "Vento Forte")
