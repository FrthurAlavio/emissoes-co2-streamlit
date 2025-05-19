import pandas as pd
import geopandas as gpd
import streamlit as st
import folium
from streamlit_folium import st_folium
from branca.colormap import linear

# 1. Abrir e ler a tabela
caminho_arquivo = 'co2estados(1970-2023).csv'
df = pd.read_csv(caminho_arquivo)

# 2. Padronizar o nome da coluna de estados
df.rename(columns={df.columns[0]: 'estado'}, inplace=True)
df['estado'] = df['estado'].str.strip().str.title()

# Título do app
st.title("🌀 Emissões de CO2 por Estado (1970-2023)")
st.markdown("📊 Fonte: [SEEG](https://seeg.eco.br/dados/)")

# Inputs do usuário
estados = sorted(df['estado'].unique())
anos = sorted([col for col in df.columns if col != 'estado'])

estado_usuario = st.selectbox("Escolha o estado:", estados)
ano_usuario = st.selectbox("Escolha o ano:", anos)

# Mostrar dados do estado selecionado
if estado_usuario and ano_usuario:
    valor_estado = df.loc[df['estado'] == estado_usuario, ano_usuario].values[0]
    st.markdown(f"### {estado_usuario} emitiu **{round(valor_estado):,} Milhões de Toneladas de CO₂e** no ano de **{ano_usuario}**.")

# Função para carregar mapa
@st.cache_data
def carregar_mapa_estados():
    url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
    mapa = gpd.read_file(url)
    mapa['estado'] = mapa['name'].str.title()
    return mapa

mapa = carregar_mapa_estados()

# Preparar dados para o mapa
df_mapa = df[['estado', ano_usuario]].copy()
df_mapa[ano_usuario] = pd.to_numeric(df_mapa[ano_usuario], errors='coerce')
mapa_merged = mapa.merge(df_mapa, on='estado', how='left')

# Criar mapa folium centralizado no Brasil
m = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)

# Criar colormap
min_val = mapa_merged[ano_usuario].min()
max_val = mapa_merged[ano_usuario].max()
colormap = linear.Reds_09.scale(min_val, max_val)
colormap.caption = f'Emissões de CO₂e (Milhões Toneladas) - {ano_usuario}'

# Adicionar Choropleth
folium.Choropleth(
    geo_data=mapa_merged,
    data=mapa_merged,
    columns=['estado', ano_usuario],
    key_on='feature.properties.estado',
    fill_color='Reds',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Emissões de CO₂e (Milhões Toneladas)',
    highlight=True,
    nan_fill_color='lightgrey'
).add_to(m)

# Adicionar popups com estado e valor
for _, row in mapa_merged.iterrows():
    estado = row['estado']
    valor = row[ano_usuario]
    if pd.notnull(valor):
        popup_text = f"{estado}: {round(valor,2):,} Milhões Toneladas"
    else:
        popup_text = f"{estado}: Sem dados"
    
    folium.GeoJson(
        row['geometry'],
        style_function=lambda x: {'fillColor': 'transparent', 'color': 'black', 'weight': 0.5},
        tooltip=popup_text
    ).add_to(m)

# Adicionar legenda (colormap)
colormap.add_to(m)

# Adicionar controle de camadas
folium.LayerControl().add_to(m)

# Exibir mapa no Streamlit
st.markdown(f"## 🗺️ Mapa interativo de emissões de CO₂ por estado ({ano_usuario})")
st_folium(m, width=700, height=500)
