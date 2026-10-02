import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

@st.cache_data
def carregar_tri_financas():
    tri_financas = pd.read_csv('dados_vale(Tri Financeiro).csv', encoding='ISO-8859-1', sep=';')

    tri_financas.columns = tri_financas.columns.str.strip() #remove espaços antes e depois dos nomes das colunas

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
   valor_formatado = condicao[valor] 
   card(titulo, valor_formatado)

def card_condicao_real(titulo, valor, condicao):
    valor_formatado = f"R$ {condicao[valor]}"
    card(titulo, valor_formatado)

def card_condicao_euro(titulo, valor, condicao):
    valor_formatado = f"€ {condicao[valor]}"
    card(titulo, valor_formatado)

def card_condicao_dolar(titulo, valor, condicao):
    valor_formatado = f"$ {condicao[valor]}"
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

if pagina == "Financeiro":

   tri_financas["Liquidez Corrente"] = tri_financas["Ativo Circulante"] / tri_financas["Passivo Circulante"] #dividindo duas colunas para criar a liquide corrente
   tri_financas['Liquidez Corrente'] = tri_financas['Liquidez Corrente'].replace([float('inf'), float('-inf')], 0).fillna(0) #substitui os casos de divisão por zero (infinito) e valores nulos por 0

   lista_trimestres_financas = tri_financas['Trimestre'].dropna().unique().tolist() #caixa de seleção 
   tri_selecionado = st.selectbox("Selecione o Trimestre (1T19 - 2T26):", options=lista_trimestres_financas) #valor escolhido fica em memória
   dados_tri = tri_financas[tri_financas['Trimestre'] == tri_selecionado].iloc[0] #filtra alinha correspondente ao trimestre selecionado
   
   col1, col2, col3, col4, col5 = st.columns(5) #cria colunas

   with col1:
      card_condicao_real("Receita Líquida", "Receita Líquida", dados_tri)

   with col2:
      card_condicao_real("EBITDA (LAJIDA)", "EBITDA", dados_tri)

   with col3:
      card_condicao_real("Lucro Líquido", "Lucro Líquido", dados_tri)

   with col4:
      card_condicao("Margem Bruta (%)", "Margem Bruta (%)", dados_tri)

   with col5:
      card(
         "Dívida Líquida (MM)",
         str(dados_tri["Dívida Líquida (MM)"]).replace(",00", "").strip(),)

   col6, col7, col8, col9, col10 = st.columns(5)

   dados_tri['Liquidez Corrente'] = round(dados_tri['Liquidez Corrente'], 3)
   with col6:
      card_condicao("Liquidez Corrente", "Liquidez Corrente", dados_tri)

   with col7:
      card_condicao_real("EBIT/Resultado Operacional", "EBIT/ Resultado Operacional", dados_tri)

   with col8:
      card_condicao("VALE3 (B3 - BRL)", "VALE3 (B3 - BRL)", dados_tri)

   with col9:
      card_condicao("VALE (NYSE - USD)", "VALE (NYSE - USD)", dados_tri)

   with col10:
      card_condicao_euro("XVALO (Latibex - EUR)", "XVALO (Latibex - EUR)", dados_tri)

   marcacao_preta()

   #filtra apenas linhas com trimestres válidos
   tabela_validos = tri_financas.dropna(subset=['Trimestre'])

   #FILTRO DE PERÍODO (SLIDER)
   qtd_trimestres = st.slider(
      "Selecione a quantidade de trimestres para visualizar nos gráficos:",
      min_value=4,
      max_value=len(tabela_validos),
      value=12,  # Valor padrão (12 trimestres)
      step=1,)

   tabela_periodo = tabela_validos.tail(qtd_trimestres)

   #correção de escala para valores sem ponto decimal no CSV
   def f_bilhoes(val):
      return (
         None
         if pd.isna(val)
         else (float(val) / 1000.0 if abs(float(val)) >= 100 else float(val)))

   #tabela dinâmica cortada com base na escolha do usuário
   df_periodo = tabela_validos.tail(qtd_trimestres)

   col11, col12 = st.columns(2)

   with col11:

      st.subheader("Evolução do Resultado (Receita, EBITDA e Lucro Líquido) \n Mil Milhões")

      #gráfico --------------------------------------------------
      #1. cria o DataFrame filtrado pelo slider de trimestres
      df_graf = tabela_periodo.assign(
         **{
            "Receita Líquida": tabela_periodo["Receita Líquida"].apply(f_bilhoes),
            "EBITDA": tabela_periodo["EBITDA"].apply(f_bilhoes),
            "Lucro Líquido": tabela_periodo["Lucro Líquido"].apply(f_bilhoes),})

      #2. gera o gráfico usando df_graf (respeitando o slider)
      fig_resultado = px.line(
         df_graf,
         x="Trimestre",
         y=["Receita Líquida", "EBITDA", "Lucro Líquido"],
         markers=True,
         labels={"value": "R$ (Bilhões)", "variable": "Indicador"},)

      #3. Formatação do layout
      fig_resultado.update_layout(
         hovermode="x unified",
         legend=dict(orientation="h", y=1.1, title=""),
         xaxis_title="Trimestre",
         yaxis_title="R$ (Bilhões)",)

      #4. Exibe o gráfico no Streamlit
      st.plotly_chart(fig_resultado, use_container_width=True)

      #gráfico 2 --------------------------------------------------
      st.subheader("Composição de Capital (Passivos e Patrimônio Líquido)")

      #gráfico de barras agrupadas lado a lado usando a tabela_periodo (conectada ao slider)
      fig_balanco = px.bar(
         tabela_periodo,
         x="Trimestre",
         y=["Passivo Circulante", "Passivo Não Circulante", "Patrimônio Líquido"],
         barmode="group",
         labels={"value": "R$ (Bilhões)", "variable": "Estrutura"},)

      fig_balanco.update_layout(
         bargap=0.15,
         hovermode="x unified",
         legend=dict(orientation="h", y=1.1, title=""),
         xaxis_title="Trimestre",
         yaxis_title="R$ (Bilhões)",)

      st.plotly_chart(fig_balanco, use_container_width=True)

   with col12:

      #grafico 3 -------------------
      st.subheader("Geração de Caixa: Operacional (FCO) vs. Livre (FCL)")

      #ajusta escala de possíveis valores sem ponto usando tabela_periodo (conectada ao slider)
      df_fcl = tabela_periodo.assign(
         **{
            "Fluxo de Caixa Livre": tabela_periodo["Fluxo de Caixa Livre"].apply(
                  f_bilhoes)})

      fig_caixa = go.Figure()

      #barra 1: Fluxo de Caixa Operacional
      fig_caixa.add_trace(
         go.Bar(
            x=df_fcl["Trimestre"],
            y=df_fcl["Fluxo de Caixa Operacional"],
            name="FCO (Operacional)",))

      # Barra 2: Fluxo de Caixa Livre
      fig_caixa.add_trace(
         go.Bar(
            x=df_fcl["Trimestre"],
            y=df_fcl["Fluxo de Caixa Livre"],
            name="FCL (Livre)",))

      fig_caixa.update_layout(
         barmode="group",
         bargap=0.15,
         hovermode="x unified",
         legend=dict(orientation="h", y=1.1, title=""),
         xaxis_title="Trimestre",
         yaxis_title="R$ (Bilhões)",)

      st.plotly_chart(fig_caixa, use_container_width=True)

      # Função para limpar e converter o texto das cotações em números
      def conv_preco(val):
         if pd.isna(val):
            return None
         return float(
            str(val)
            .replace("R$", "")
            .replace("$", "")
            .strip()
            .replace(",", "."))

      #gráfico 4 --------------------------------------------------
      st.subheader("Desempenho das Ações: VALE3 (B3 - R$) vs. VALE (NYSE - US$)")

      #prepara os dados numéricos de preços usando tabela_periodo (conectada ao slider)
      df_acoes = tabela_periodo.assign(
         VALE3_num=tabela_periodo["VALE3 (B3 - BRL)"].apply(conv_preco),
         VALE_USD_num=tabela_periodo["VALE (NYSE - USD)"].apply(conv_preco),)

      fig_acoes = go.Figure()

      #linha 1: VALE3 na B3 (Eixo Y Esquerdo)
      fig_acoes.add_trace(
         go.Scatter(
            x=df_acoes["Trimestre"],
            y=df_acoes["VALE3_num"],
            name="VALE3 (B3 - R$)",
            mode="lines+markers",
            line=dict(color="#00529B", width=2.5),))

      #linha 2: VALE na NYSE (Eixo Y Direito)
      fig_acoes.add_trace(
         go.Scatter(
            x=df_acoes["Trimestre"],
            y=df_acoes["VALE_USD_num"],
            name="VALE (NYSE - US$)",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color="#00A859", width=2.5),))

      fig_acoes.update_layout(
         hovermode="x unified",
         legend=dict(orientation="h", y=1.1, title=""),
         xaxis_title="Trimestre",
         yaxis=dict(title="Preço VALE3 (R$)"),
         yaxis2=dict(title="Preço VALE (US$)", overlaying="y", side="right"),)

      st.plotly_chart(fig_acoes, use_container_width=True)
