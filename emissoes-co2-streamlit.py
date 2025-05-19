import pandas as pd
import streamlit as st
import plotly.express as px

# 1. Abrir e ler a tabela
caminho_arquivo = 'co2estados(1970-2023).csv'
df = pd.read_csv(caminho_arquivo)

# 2. Padronizar o nome da coluna de estados
df.rename(columns={df.columns[0]: 'estado'}, inplace=True)
df['estado'] = df['estado'].str.strip().str.title()

# Dicionário de siglas dos estados (necessário para o mapa)
siglas_estados = {
    'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA',
    'Ceará': 'CE', 'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO',
    'Maranhão': 'MA', 'Mato Grosso': 'MT', 'Mato Grosso Do Sul': 'MS', 'Minas Gerais': 'MG',
    'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE', 'Piauí': 'PI',
    'Rio De Janeiro': 'RJ', 'Rio Grande Do Norte': 'RN', 'Rio Grande Do Sul': 'RS',
    'Rondônia': 'RO', 'Roraima': 'RR', 'Santa Catarina': 'SC', 'São Paulo': 'SP',
    'Sergipe': 'SE', 'Tocantins': 'TO'
}
df['sigla'] = df['estado'].map(siglas_estados)

# Título do app
st.title("📊 Emissões de CO2 por Estado (1970–2023)")
st.markdown("Fonte: [SEEG](https://seeg.eco/)")

# 3. Inputs do usuário
estados = sorted(df['estado'].unique())
anos = sorted([col for col in df.columns if col not in ['estado', 'sigla']])

estado_usuario = st.selectbox("Escolha o estado:", estados, key="estado_selectbox")
ano_usuario = st.selectbox("Escolha o ano:", anos, key="ano_selectbox")

# 4. Exibir dados do estado selecionado
if estado_usuario and ano_usuario:
    try:
        valor_estado = df.loc[df['estado'] == estado_usuario, ano_usuario].values[0]
        media_nacional = df[ano_usuario].mean()

        st.markdown(f"### {estado_usuario} emitiu **{round(valor_estado, 2)} CO2e** no ano de **{ano_usuario}**.")

        if media_nacional == 0:
            st.warning("A média nacional é zero, comparação não é possível.")
        else:
            razao = valor_estado / media_nacional

            if razao > 1:
                diferenca = round(razao, 2)
                st.info(f"🔺 Acima da média nacional em **{diferenca}x** ({round(media_nacional, 2)} CO2e).")
            elif razao < 1:
                diferenca = round(1 / razao, 2)
                st.info(f"🔻 Abaixo da média nacional em **{diferenca}x** ({round(media_nacional, 2)} CO2e).")
            else:
                st.info("📊 O valor está igual à média nacional.")

    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")

# 5. Mapa interativo de emissões de CO2 por estado no ano selecionado
st.markdown("---")
st.subheader(f"🗺️ Mapa de emissões de CO2 por estado em {ano_usuario}")

df_mapa = df[['estado', 'sigla', ano_usuario]].copy()
df_mapa.rename(columns={ano_usuario: 'emissao'}, inplace=True)

fig = px.choropleth(
    df_mapa,
    locations='sigla',
    locationmode='USA-states',  # funciona com códigos de 2 letras
    geojson='https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson',
    featureidkey="properties.sigla",
    color='emissao',
    color_continuous_scale='Reds',
    labels={'emissao': 'CO2e'},
    scope='south america',
    title=f"Emissões de CO2 por estado - {ano_usuario}"
)
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})

st.plotly_chart(fig, use_container_width=True)
