import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st

# 1. Abrir e ler a tabela
caminho_arquivo = 'co2estados(1970-2023).csv'
df = pd.read_csv(caminho_arquivo)

# 2. Padronizar o nome da coluna de estados
df.rename(columns={df.columns[0]: 'estado'}, inplace=True)
df['estado'] = df['estado'].str.strip().str.title()

# Título do app
st.title("🌀 Emissões de CO2 por Estado (1970-2023)")
st.markdown("📊 Fonte: [SEEG](https://seeg.eco.br/dados/)")

# 3. Inputs do usuário com dropdowns
estados = sorted(df['estado'].unique())
anos = sorted([col for col in df.columns if col != 'estado'])

estado_usuario = st.selectbox("Escolha o estado:", estados, key="estado_selectbox")
ano_usuario = st.selectbox("Escolha o ano:", anos, key="ano_selectbox")

# 4. Lógica de análise e exibição
if estado_usuario and ano_usuario:
    try:
        valor_estado = df.loc[df['estado'] == estado_usuario, ano_usuario].values[0]
        media_nacional = df[ano_usuario].mean()

        st.markdown(f"### {estado_usuario} emitiu **{round(valor_estado):,} Milhões de Toneladas de CO₂e** no ano de **{ano_usuario}**.")

        if media_nacional == 0:
            st.warning("A média nacional é zero, comparação não é possível.")
        else:
            razao = valor_estado / media_nacional

            if razao > 1:
                st.info(f"O valor está **{round(razao, 2)}x acima da média nacional**.")
            elif razao < 1:
                st.info(f"O valor está **{round(1 / razao, 2)}x abaixo da média nacional**.")
            else:
                st.info("O valor está igual à média nacional.")

        st.markdown(f"Média nacional de CO2e em {ano_usuario}: **{round(media_nacional, 2)}** Milhões de Toneladas.")
        
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")

# 5. Mapa por estado
@st.cache_data
def carregar_mapa_estados():
    url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
    mapa = gpd.read_file(url)
    mapa['estado'] = mapa['name'].str.title()
    return mapa

mapa = carregar_mapa_estados()

# Junta dados de CO2 ao mapa
df_mapa = df[['estado', ano_usuario]].copy()
df_mapa[ano_usuario] = pd.to_numeric(df_mapa[ano_usuario], errors='coerce')
mapa_merged = mapa.merge(df_mapa, on='estado', how='left')

# Plot do mapa
st.markdown(f"## 🗺️ Mapa de emissões de CO₂ por estado ({ano_usuario})")

fig, ax = plt.subplots(1, 1, figsize=(10, 8))
mapa_merged.plot(
    column=ano_usuario,
    ax=ax,
    cmap='Reds',
    legend=True,
    legend_kwds={'label': f"Emissões de CO₂e (toneladas)", 'orientation': "horizontal"},
    missing_kwds={"color": "lightgrey", "label": "Sem dados"}
)

ax.set_title(f"Emissões de CO₂e por Estado - {ano_usuario}", fontsize=14)
ax.axis('off')
st.pyplot(fig)
