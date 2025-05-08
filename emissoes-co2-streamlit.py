import pandas as pd
import streamlit as st

# 1. Abrir e ler a tabela
caminho_arquivo = r'C:\Users\Arthur\OneDrive\Área de Trabalho\vscodepython\co2estados(1970-2023).csv'
df = pd.read_csv(caminho_arquivo)

# 2. Padronizar o nome da coluna de estados
df.rename(columns={df.columns[0]: 'estado'}, inplace=True)
df['estado'] = df['estado'].str.strip().str.title()

# Título do app
st.title("Emissões de CO2 por Estado (1970-2023)")

# 3. Inputs do usuário com dropdowns (agora com `key` únicos)
estados = sorted(df['estado'].unique())
anos = sorted([col for col in df.columns if col != 'estado'])

estado_usuario = st.selectbox("Escolha o estado:", estados, key="estado_selectbox")
ano_usuario = st.selectbox("Escolha o ano:", anos, key="ano_selectbox")

# 4. Lógica de análise e exibição
if estado_usuario and ano_usuario:
    try:
        valor_estado = df.loc[df['estado'] == estado_usuario, ano_usuario].values[0]
        media_nacional = df[ano_usuario].mean()

        st.markdown(f"### {estado_usuario} emitiu {round(valor_estado)} CO2e no ano de {ano_usuario}.")

        if media_nacional == 0:
            st.warning("A média nacional é zero, comparação não é possível.")
        else:
            razao = valor_estado / media_nacional

            if razao > 1:
                diferenca = round(razao, 2)
                st.info(f"O valor está **{diferenca}x acima da média nacional** ({round(media_nacional, 2)} CO2e).")
            elif razao < 1:
                diferenca = round(1 / razao, 2)
                st.info(f"O valor está **{diferenca}x abaixo da média nacional** ({round(media_nacional, 2)} CO2e).")
            else:
                st.info("O valor está igual à média nacional.")

            st.markdown(f"Média nacional de CO2e em {ano_usuario}: **{round(media_nacional, 2)}**")

    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")
