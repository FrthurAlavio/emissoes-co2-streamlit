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

st.markdown(f"### {estado_usuario} emitiu **{round(valor_estado):,} Milhões de Toneladas de CO₂e** no ano de **{ano_usuario}**.")
