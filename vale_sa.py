import streamlit as st
import pandas as pd

@st.cache_data
def carregar_tri_financas():
    tri_financas = pd.read_csv('/home/fe007/VS Code/Apps Streamlit/dados_vale(Tri Financeiro).csv', encoding='ISO-8859-1', sep=';')

    return tri_financas

tri_financas = carregar_tri_financas()

#CRIAÇÃO DO APP ============================================================

st.set_page_config(layout="wide") #diminuir bordas e aumentar área utilizável ------------------------
st.markdown(""" ... """, unsafe_allow_html=True)

st.markdown("""
   <style>
       .main .block-container {
           max-width: 100%;
           padding-left: 0.5rem;
           padding-right: 0.5rem;
       }
   </style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.block-container {
   padding-top: 1rem;
   padding-bottom: 0rem;
}
</style>
""", unsafe_allow_html=True)
#------------------------------------

st.sidebar.title("Menu de Navegação")

st.markdown("""
<style>
[data-testid="stSidebar"] {
   width: 100px !important;}
</style>
""", unsafe_allow_html=True) #diminuir grossura do menu

pagina = st.sidebar.radio(
   "Escolha uma página:",
   ["Visão Geral", "Financeiro", "Produção", "Mercado"])

st.sidebar.write("Criado por Fernando Henrique M. Rossignolli, Israel Gomes Galdino, " \
                "Luis Felipe de Souza Ferreira e João Pedro Barreto de Almeida")

def card(titulo, valor):
   with st.container(border=True):
       st.metric(titulo, valor)

def card_condicao(titulo, valor, condicao):
   valor_formatado = f"R$ {condicao[valor]}" 
   card(titulo, valor_formatado)

def marcacao_preta():
   st.markdown("""
       <hr style="border: 1px solid #444; margin-top: 20px; margin-bottom: 20px;">
       """, unsafe_allow_html=True)

def marcacao_cinza():
   st.markdown("""
       <hr style="border: 1px solid #dddddd; margin-top: 20px; margin-bottom: 20px;">
       """, unsafe_allow_html=True)

#TRIMESTRE FINANCEIRO ========================================================================================================

lista_trimestres_financas = tri_financas['Trimestre'].dropna().unique().tolist() #caixa de seleção 
tri_selecionado = st.selectbox("Selecione o Trimestre (1T19 - 2T26):", options=lista_trimestres_financas) #valor escolhido fica em memória
dados_tri = tri_financas[tri_financas['Trimestre'] == tri_selecionado].iloc[0] #filtra alinha correspondente ao trimestre selecionado

col1, col2, col3, col4 = st.columns(4) #cria colunas

with col1:
   card_condicao("Receita Líquida", "Receita Líquida", dados_tri)

with col2:
   card_condicao("EBITDA", "EBITDA", dados_tri)

with col3:
   card_condicao("Lucro Líquido", "Lucro Líquido", dados_tri)

with col4:
   card_condicao("Margem Bruta (%)", "Margem Bruta (%)", dados_tri)

#MARGEM EBITDA OXODCEOIMEIMCEOICEMOECMCEOICMOCEMOICEMOCEMCEOIMCOICDEMOCDE

