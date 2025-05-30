import pandas as pd
import folium
import json
import streamlit as st
from streamlit_folium import st_folium
from branca.element import Template, MacroElement

# 1. Carregar o GeoJSON com as siglas
with open("br_states.json", encoding="utf-8") as f:
    geojson_data = json.load(f)

# 2. Carregar o CSV com dados de CO₂
df = pd.read_csv("co2estados(1972-2023).csv")
df.rename(columns={df.columns[0]: "estado"}, inplace=True)
df['estado'] = df['estado'].str.strip().str.title()

# 3. Mapeamento nome do estado -> sigla
estado_para_sigla = {
    'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA',
    'Ceará': 'CE', 'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO',
    'Maranhão': 'MA', 'Mato Grosso': 'MT', 'Mato Grosso Do Sul': 'MS', 'Minas Gerais': 'MG',
    'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE', 'Piauí': 'PI',
    'Rio De Janeiro': 'RJ', 'Rio Grande Do Norte': 'RN', 'Rio Grande Do Sul': 'RS',
    'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC', 'São Paulo': 'SP',
    'Sergipe': 'SE', 'Tocantins': 'TO'
}
# Também criar o mapeamento inverso de sigla para estado
sigla_para_estado = {v: k for k, v in estado_para_sigla.items()}
df['sigla'] = df['estado'].map(estado_para_sigla)

# 4. Interface Streamlit
st.set_page_config(layout="wide", page_title="Emissões de CO2 no Brasil")
st.title(" 🇧🇷 Emissões de CO₂ por Estado Brasileiro (1972–2023)")
st.markdown("""
    Este painel apresenta dados históricos de emissões de gases de efeito estufa por estado brasileiro.
    Os valores são expressos em Milhões de Toneladas (Mt) de CO₂ equivalente (CO₂e).
    """)
st.markdown("📊 **Fonte:** [SEEG](https://seeg.eco.br/dados/)")

# Seleção de estado e ano - sem colunas
estados = sorted(df['estado'].unique())
anos = sorted([col for col in df.columns if col not in ['estado', 'sigla']])

estado_usuario = st.selectbox("Escolha o estado:", estados)
ano_usuario = st.selectbox("Escolha o ano:", anos)

if estado_usuario and ano_usuario:
    valor_estado = df.loc[df['estado'] == estado_usuario, ano_usuario].values[0]
    media_nacional = df[ano_usuario].mean()
    valor_max = df[ano_usuario].max()
    estado_max = df.loc[df[ano_usuario] == valor_max, 'estado'].values[0]

    st.metric(
        label=f"Emissões em {estado_usuario} ({ano_usuario})",
        value=f"{round(valor_estado):,} Mt CO₂e",
        delta=f"{round(valor_estado - media_nacional, 1)} Mt vs. média nacional"
    )

    ranking = df[[ano_usuario, 'estado']].sort_values(by=ano_usuario, ascending=False).reset_index(drop=True)
    posicao = ranking[ranking['estado'] == estado_usuario].index[0] + 1
    st.markdown(f"### Comparação Nacional ({ano_usuario})")
    st.markdown(f"- **Média nacional:** {round(media_nacional, 1):,} Mt CO₂e")
    st.markdown(f"- **Maior emissor:** {estado_max} ({round(valor_max):,} Mt CO₂e)")
    st.markdown(f"- **Posição no ranking:** {posicao}º de {len(estados)} estados")

    if int(ano_usuario) > 1970:
        ano_anterior = str(int(ano_usuario) - 1)
        if ano_anterior in df.columns:
            valor_anterior = df.loc[df['estado'] == estado_usuario, ano_anterior].values[0]
            variacao = ((valor_estado - valor_anterior) / valor_anterior) * 100
            st.markdown(f"- **Variação desde {ano_anterior}:** {variacao:.1f}%")

# Mapa interativo - sem colunas
st.markdown("### 🗺️ Mapa Interativo")

# Criar DataFrame para o ano selecionado com siglas e valores
data_para_mapa = df[['sigla', 'estado', ano_usuario]].copy()
data_para_mapa.columns = ['UF', 'Estado', 'valor']
data_para_mapa['valor'] = data_para_mapa['valor'].round(2)  # Arredonda os valores

# Coordenadas dos limites do Brasil para garantir foco adequado
brasil_bounds = [
    [-33.8, -73.9],  # Sudoeste (mais ao sul e oeste)
    [5.2, -34.8]     # Nordeste (mais ao norte e leste)
]

# Criar mapa com configurações otimizadas para o Brasil
mapa = folium.Map(
    location=[-14.2350, -51.9253],  # Centro geográfico do Brasil
    zoom_start=4,
    tiles='cartodbpositron',
    # Configurações para manter o foco no Brasil
    max_bounds=True,
    min_zoom=3,
    max_zoom=8,
    zoom_control=True,
    scrollWheelZoom=True,
    dragging=True
)

# Forçar o mapa a se ajustar aos limites do Brasil
mapa.fit_bounds(brasil_bounds, padding=(20, 20))

# Preparar o tooltip com formatação adequada
tooltip = folium.features.GeoJsonTooltip(
    fields=['id', 'valor_co2'],
    aliases=['Estado:', 'Emissões de CO₂:'],
    style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"),
    sticky=True
)

# Criar o choropleth e adicionar interatividade com tooltip
choropleth = folium.Choropleth(
    geo_data=geojson_data,
    data=data_para_mapa,
    columns=['UF','valor'],
    key_on='feature.id',
    legend_title=None,
    fill_color='YlGnBu',
    fill_opacity=0.7,
    line_opacity=0.5,
    highlight=True,
    line_color='black',
).add_to(mapa)

# Adicionar os dados de emissão para cada estado no GeoJSON
for feature in choropleth.geojson.data['features']:
    state_id = feature['id']
    if state_id in data_para_mapa['UF'].values:
        valor = data_para_mapa.loc[data_para_mapa['UF'] == state_id, 'valor'].values[0]
        nome_estado = sigla_para_estado.get(state_id, state_id)
        feature['properties']['valor_co2'] = f"{int(round(valor)):,} Mt CO₂e"
        feature['properties']['nome_estado'] = nome_estado

# Adicionar o tooltip ao choropleth
folium.GeoJsonTooltip(
    fields=['nome_estado', 'valor_co2'],
    aliases=['Estado:', 'Emissões:'],
    style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"),
    sticky=True
).add_to(choropleth.geojson)

# Configurar o st_folium com altura responsiva baseada na largura da tela
# Usando uma proporção de aspecto adequada para o Brasil
map_data = st_folium(
    mapa, 
    width="100%",  # Usar largura total disponível
    height=600,    # Altura fixa adequada
    returned_objects=["last_object_clicked_popup"],
    use_container_width=True  # Importante para responsividade
)

# Adicionar JavaScript personalizado para garantir que o mapa sempre volte ao Brasil
st.markdown("""
<script>
// Função para resetar o foco do mapa no Brasil
function resetMapToBrazil() {
    // Coordenadas dos limites do Brasil
    var brazilBounds = [[-33.8, -73.9], [5.2, -34.8]];
    
    // Se houver um mapa disponível, aplicar os limites
    if (window.foliumMap) {
        window.foliumMap.fitBounds(brazilBounds, {padding: [20, 20]});
    }
}

// Executar quando a página carregar
document.addEventListener('DOMContentLoaded', resetMapToBrazil);
</script>
""", unsafe_allow_html=True)

# Legenda customizada com as cores corretas do esquema 'YlGnBu'
st.markdown("#### Legenda do Mapa")
st.markdown(f"""
<div style="line-height: 1.6; display: flex; justify-content: center; text-align: center; margin-bottom: 20px;">
    <div>
    <b>Escala de Cores para Emissões em {ano_usuario}:</b>
    <div style="display: flex; justify-content: center; gap: 10px; margin-top: 5px; flex-wrap: wrap;">
        <span style='background-color:#ffffd9;color:#000;padding:2px 10px;border:1px solid #ddd; margin: 2px;'>Mais baixo</span>
        <span style='background-color:#c7e9b4;color:#000;padding:2px 10px;border:1px solid #ddd; margin: 2px;'>Baixo</span>
        <span style='background-color:#7fcdbb;color:#000;padding:2px 10px;border:1px solid #ddd; margin: 2px;'>Médio</span>
        <span style='background-color:#41b6c4;color:#fff;padding:2px 10px;border:1px solid #ddd; margin: 2px;'>Alto</span>
        <span style='background-color:#1d91c0;color:#fff;padding:2px 10px;border:1px solid #ddd; margin: 2px;'>Muito Alto</span>
        <span style='background-color:#225ea8;color:#fff;padding:2px 10px;border:1px solid #ddd; margin: 2px;'>Extremo</span>
    </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Adicional
st.markdown("""
## ℹ️ Sobre os Dados
Os dados representam as emissões de gases de efeito estufa (GEE) convertidas em CO₂ equivalente (CO₂e).  
Essa medida considera o potencial de aquecimento global de diferentes gases em relação ao CO₂.

- **Toneladas de CO₂e**: Quantidade de gases com o mesmo impacto de aquecimento global que uma tonelada de CO₂  
- Os valores são expressos em **milhões de toneladas** (Mt)
- Inclui setores como: energia, agropecuária, uso da terra, resíduos e indústria

Feito por [Arquivo Alternativo](https://www.arquivoalternativo.com/)
""")
