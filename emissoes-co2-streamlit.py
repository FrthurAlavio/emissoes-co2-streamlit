import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import streamlit as st

# 1. Ler o CSV
caminho_arquivo = 'co2estados(1970-2023).csv'
df = pd.read_csv(caminho_arquivo)
df.rename(columns={df.columns[0]: 'estado'}, inplace=True)
df['estado'] = df['estado'].str.strip().str.title()

st.title("🌀 Emissões de CO2 por Estado (1970-2023)")
st.markdown("📊 Fonte: [SEEG](https://seeg.eco.br/dados/)")

# Dropdowns para seleção
estados = sorted(df['estado'].unique())
anos = sorted([col for col in df.columns if col != 'estado'])

estado_usuario = st.selectbox("Escolha o estado:", estados)
ano_usuario = st.selectbox("Escolha o ano:", anos)

if estado_usuario and ano_usuario:
    valor_estado = df.loc[df['estado'] == estado_usuario, ano_usuario].values[0]
    media_nacional = df[ano_usuario].mean()

    st.markdown(f"### {estado_usuario} emitiu **{round(valor_estado):,} Milhões de Toneladas de CO₂e** em {ano_usuario}.")
    st.markdown(f"Média nacional de CO2e em {ano_usuario}: **{round(media_nacional, 2)}** Milhões de Toneladas.")

# 2. Carregar mapa GeoJSON dos estados do Brasil
@st.cache_data
def carregar_mapa_estados():
    url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
    mapa = gpd.read_file(url)
    mapa['estado'] = mapa['name'].str.title()
    return mapa

mapa = carregar_mapa_estados()

# 3. Fazer merge dos dados
df_mapa = df[['estado', ano_usuario]].copy()
df_mapa[ano_usuario] = pd.to_numeric(df_mapa[ano_usuario], errors='coerce')
mapa_merged = mapa.merge(df_mapa, on='estado', how='left')

# 4. Limpar o GeoDataFrame para deixar só as colunas necessárias antes de gerar geojson
mapa_merged_limpo = mapa_merged[['estado', ano_usuario, 'geometry']].copy()
mapa_merged_limpo[ano_usuario] = pd.to_numeric(mapa_merged_limpo[ano_usuario], errors='coerce')

# 5. Gerar GeoJSON para usar no Folium
geojson_data = mapa_merged_limpo.to_json()

# 6. Criar mapa interativo com Folium
m = folium.Map(location=[-15.78, -47.93], zoom_start=4)

folium.Choropleth(
    geo_data=geojson_data,
    name='choropleth',
    data=mapa_merged_limpo,
    columns=['estado', ano_usuario],
    key_on='feature.properties.estado',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=f'Emissões de CO₂e em {ano_usuario} (Milhões de Toneladas)'
).add_to(m)

# Adicionar controle de camadas
folium.LayerControl().add_to(m)

# 7. Exibir mapa no Streamlit
st.markdown(f"## 🗺️ Mapa interativo de emissões de CO₂ por estado ({ano_usuario})")
st_data = st_folium(m, width=700, height=500)
