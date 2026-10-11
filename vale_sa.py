import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import io
from fpdf import FPDF
from sklearn.linear_model import LinearRegression
import numpy as np

@st.cache_data
def carregar_tri_financas():
    tri_financas = pd.read_csv(
        "dados_vale(Tri Financeiro).csv", encoding="ISO-8859-1", sep=";",)
    tri_financas.columns = (tri_financas.columns.str.strip())  #remove espaços antes e depois dos nomes
    return tri_financas

@st.cache_data
def carregar_anual_financas():
    anual_financas = pd.read_csv(
        "dados_vale(Anual Financeiro).csv", encoding="ISO-8859-1", sep=";",)
    anual_financas.columns = anual_financas.columns.str.strip()
    #converte coluna de ano para texto limpo:
    anual_financas["Ano"] = (
        anual_financas["Ano"].dropna().astype(int).astype(str))
    return anual_financas

@st.cache_data
def carregar_tri_producao():
    tri_producao = pd.read_csv(
        "dados_vale(Tri Produção).csv", encoding="ISO-8859-1", sep=";",)
    tri_producao.columns = tri_producao.columns.str.strip() #remove espaços em branco no início e no final dos nomes das colunas
    tri_producao["Produto"] = tri_producao["Produto"].astype(str).str.strip() #converte a coluna para texto remove espaços em branco
    tri_producao["Local"] = tri_producao["Local"].astype(str).str.strip()
    return tri_producao #retorna a tabela limpa

@st.cache_data
def carregar_anual_producao():
    anual_prod = pd.read_csv(
        "dados_vale(Anual Produção).csv", encoding="ISO-8859-1", sep=";",)
    anual_prod.columns = anual_prod.columns.str.strip()
    anual_prod["Ano"] = anual_prod["Ano"].dropna().astype(int).astype(str)
    return anual_prod

@st.cache_data
def carregar_tri_mercado():
    tri_mercado = pd.read_csv(
        "dados_vale(Tri Mercado e Economia).csv", encoding="ISO-8859-1", sep=";")
    tri_mercado.columns = tri_mercado.columns.str.strip()
    return tri_mercado

@st.cache_data
def carregar_anual_mercado():
    anual_mercado = pd.read_csv(
        "dados_vale(Anual Mercado e Economia ).csv", encoding="ISO-8859-1", sep=";")
    anual_mercado.columns = anual_mercado.columns.str.strip()
    anual_mercado["Ano"] = anual_mercado["Ano"].dropna().astype(int).astype(str)
    return anual_mercado

tri_mercado = carregar_tri_mercado()
anual_mercado = carregar_anual_mercado()
anual_producao = carregar_anual_producao()
tri_producao = carregar_tri_producao()
tri_financas = carregar_tri_financas()
anual_financas = carregar_anual_financas()

#==========================================================

def conv_pct(val):
    if pd.isna(val): #verifica se o valor é nulo ou ausente
        return None #retorna None cao o valor seja nulo
    val_str = str(val).replace("%", "").replace(",", ".").strip()
    try: #tentativa de converter o texto em número decimal
        return float(val_str) #converte a string tratada para float
    except ValueError: #captura o erro caso o texto não seja um número válido
        return None

def conv_preco(val):
    if pd.isna(val):
        return None
    val_str = (
        str(val)
        .replace("US$", "")
        .replace("US", "")
        .replace("R$", "")
        .replace("$", "")
        .replace("€", "")
        .replace("\x80", "")
        .strip()
        .replace(",", "."))
    try:
        return float(val_str)
    except ValueError:
        return None

def f_bilhoes(val):
    if pd.isna(val):
        return None

    val_str = str(val).replace("(R$ bi)", "").replace("R$", "").strip()

    # Trata formato com vírgula (ex: "1.400,50" ou "1,400")
    if "," in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    else:
        # Se tem ponto, verifica os dígitos decimais/separador de milhar
        parts = val_str.split(".")
        if len(parts) == 2:
            # Se tem exatamente 3 dígitos após o ponto (ex: 1.400, 893.000, 5.921)
            # o ponto é separador de milhar, então removemos o ponto.
            if len(parts[1]) == 3:
                val_str = val_str.replace(".", "")

    try:
        num = float(val_str)
    except ValueError:
        return None

    # Se o valor numérico for >= 100 (ex: 893 ou 1400), está em Milhões e deve ser convertido para Bilhões
    if abs(num) >= 100:
        return num / 1000.0

    return num

#FUNÇÕES DE EXPORTAÇÃO DE DADOS ==========================

def gerar_excel_customizado(tabela, colunas_selecionadas):
    """Gera um arquivo Excel contendo apenas as colunas escolhidas."""
    tabela_filtrado = tabela[colunas_selecionadas].copy()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        tabela_filtrado.to_excel(writer, index=False, sheet_name="Relatorio")
    output.seek(0)
    return output

def gerar_pdf_customizado(tabela, colunas_selecionadas, titulo_relatorio):
    """Gera um relatório PDF simples com a tabela formatada."""
    tabela_filtrado = tabela[colunas_selecionadas].copy()
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, titulo_relatorio, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 8, "Relatorio Exportado via Dashboard Vale S.A.", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 9)
    largura_pagina = 277
    largura_col = max(20, largura_pagina / len(colunas_selecionadas))
    
    for col in colunas_selecionadas:
        col_nome = str(col)[:18] + ".." if len(str(col)) > 20 else str(col)
        pdf.cell(largura_col, 8, col_nome, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 8)
    for _, row in tabela_filtrado.iterrows():
        for col in colunas_selecionadas:
            val = str(row[col]) if pd.notna(row[col]) else "-"
            val_texto = val[:18] + ".." if len(val) > 20 else val
            pdf.cell(largura_col, 6, val_texto, border=1, align="C")
        pdf.ln()
    return bytes(pdf.output())

def renderizar_painel_exportacao_financeiro(tabela_tri, tabela_anual, titulo_relatorio, key_prefix):
    """Renderiza o painel expansível de exportação de dados financeiros com alternância entre Trimestral e Anual."""
    with st.expander("📥 Central de Exportação e Relatórios Customizados"):
        st.markdown(f"Configure e baixe dados do relatório **{titulo_relatorio}** em **Excel** ou **PDF**.")

        # 1. Escolha da granularidade temporal para a exportação
        tipo_base = st.radio(
            "Selecione a base de dados para exportação:",
            options=["Trimestral", "Anual"],
            horizontal=True,
            key=f"radio_export_tipo_{key_prefix}"
        )

        # Seleciona a tabela correspondente com todas as colunas originais
        tabela_export = tabela_tri.copy() if tipo_base == "Trimestral" else tabela_anual.copy()
        colunas_disponiveis = tabela_export.columns.tolist()

        # Colunas padrão iniciais
        col_tempo = "Trimestre" if tipo_base == "Trimestral" else "Ano"
        default_cols = [c for c in [col_tempo, "Receita Líquida", "EBITDA", "Lucro Líquido"] if c in colunas_disponiveis]
        if not default_cols:
            default_cols = colunas_disponiveis[:min(4, len(colunas_disponiveis))]

        # 2. Seleção de colunas dinâmicas
        colunas_selecionadas = st.multiselect(
            f"Selecione as colunas da base {tipo_base} que deseja incluir no relatório:",
            options=colunas_disponiveis,
            default=default_cols,
            key=f"export_cols_{key_prefix}_{tipo_base}"
        )

        # 3. Botões de download
        if colunas_selecionadas:
            nome_arquivo_prefixo = f"Relatorio_Financeiro_{tipo_base}"
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                st.download_button(
                    label=f"📊 Baixar Base {tipo_base} em Excel (.xlsx)",
                    data=gerar_excel_customizado(tabela_export, colunas_selecionadas),
                    file_name=f"{nome_arquivo_prefixo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"btn_excel_{key_prefix}_{tipo_base}"
                )
            with exp_col2:
                st.download_button(
                    label=f"📄 Baixar Relatório {tipo_base} em PDF (.pdf)",
                    data=gerar_pdf_customizado(tabela_export, colunas_selecionadas, f"{titulo_relatorio} ({tipo_base})"),
                    file_name=f"{nome_arquivo_prefixo}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"btn_pdf_{key_prefix}_{tipo_base}"
                )
        else:
            st.warning("Por favor, selecione pelo menos uma coluna para exportar.")

def renderizar_painel_exportacao_producao(tabela_tri, tabela_anual, titulo_relatorio, key_prefix):
    """Renderiza o painel expansível de exportação de dados de produção com alternância entre Trimestral e Anual."""
    with st.expander("📥 Central de Exportação e Relatórios Customizados"):
        st.markdown(f"Configure e baixe dados do relatório **{titulo_relatorio}** em **Excel** ou **PDF**.")

        tipo_base = st.radio(
            "Selecione a base de dados para exportação:",
            options=["Trimestral", "Anual"],
            horizontal=True,
            key=f"radio_export_tipo_{key_prefix}"
        )

        tabela_export = tabela_tri.copy() if tipo_base == "Trimestral" else tabela_anual.copy()
        colunas_disponiveis = tabela_export.columns.tolist()

        col_tempo = "Trimestre" if tipo_base == "Trimestral" else "Ano"
        default_cols = [c for c in [col_tempo, "Produto", "Local", "Extração (Mil Toneladas Métricas)"] if c in colunas_disponiveis]
        if not default_cols:
            default_cols = colunas_disponiveis[:min(4, len(colunas_disponiveis))]

        colunas_selecionadas = st.multiselect(
            f"Selecione as colunas da base {tipo_base} que deseja incluir no relatório:",
            options=colunas_disponiveis,
            default=default_cols,
            key=f"export_cols_{key_prefix}_{tipo_base}"
        )

        if colunas_selecionadas:
            nome_arquivo_prefixo = f"Relatorio_Producao_{tipo_base}"
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                st.download_button(
                    label=f"📊 Baixar Base {tipo_base} em Excel (.xlsx)",
                    data=gerar_excel_customizado(tabela_export, colunas_selecionadas),
                    file_name=f"{nome_arquivo_prefixo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"btn_excel_{key_prefix}_{tipo_base}"
                )
            with exp_col2:
                st.download_button(
                    label=f"📄 Baixar Relatório {tipo_base} em PDF (.pdf)",
                    data=gerar_pdf_customizado(tabela_export, colunas_selecionadas, f"{titulo_relatorio} ({tipo_base})"),
                    file_name=f"{nome_arquivo_prefixo}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"btn_pdf_{key_prefix}_{tipo_base}"
                )
        else:
            st.warning("Por favor, selecione pelo menos uma coluna para exportar.")


def renderizar_painel_exportacao_mercado(tabela_tri, tabela_anual, titulo_relatorio, key_prefix):
    """Renderiza o painel expansível de exportação de dados de mercado com alternância entre Trimestral e Anual."""
    with st.expander("📥 Central de Exportação e Relatórios Customizados"):
        st.markdown(f"Configure e baixe dados do relatório **{titulo_relatorio}** em **Excel** ou **PDF**.")

        tipo_base = st.radio(
            "Selecione a base de dados para exportação:",
            options=["Trimestral", "Anual"],
            horizontal=True,
            key=f"radio_export_tipo_{key_prefix}"
        )

        tabela_export = tabela_tri.copy() if tipo_base == "Trimestral" else tabela_anual.copy()
        colunas_disponiveis = tabela_export.columns.tolist()

        col_tempo = "Trimestre" if tipo_base == "Trimestral" else "Ano"
        default_cols = colunas_disponiveis[:min(4, len(colunas_disponiveis))]

        colunas_selecionadas = st.multiselect(
            f"Selecione as colunas da base {tipo_base} que deseja incluir no relatório:",
            options=colunas_disponiveis,
            default=default_cols,
            key=f"export_cols_{key_prefix}_{tipo_base}"
        )

        if colunas_selecionadas:
            nome_arquivo_prefixo = f"Relatorio_Mercado_{tipo_base}"
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                st.download_button(
                    label=f"📊 Baixar Base {tipo_base} em Excel (.xlsx)",
                    data=gerar_excel_customizado(tabela_export, colunas_selecionadas),
                    file_name=f"{nome_arquivo_prefixo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"btn_excel_{key_prefix}_{tipo_base}"
                )
            with exp_col2:
                st.download_button(
                    label=f"📄 Baixar Relatório {tipo_base} em PDF (.pdf)",
                    data=gerar_pdf_customizado(tabela_export, colunas_selecionadas, f"{titulo_relatorio} ({tipo_base})"),
                    file_name=f"{nome_arquivo_prefixo}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"btn_pdf_{key_prefix}_{tipo_base}"
                )
        else:
            st.warning("Por favor, selecione pelo menos uma coluna para exportar.")

#CARDS EXPANSÍVEIS =====================================

def _card_base(titulo, valor, coluna, tabela, key_slider, conversor, cor, col_tempo):
    with st.container(border=True):
        st.metric(titulo, valor)

        with st.expander("Histórico"):
            n = st.slider("Períodos:", 3, len(tabela), min(8, len(tabela)), key=key_slider) #slider para escolher o número de períodos

            tabela = tabela.tail(n).copy() #pega os últimos 'n' registros
            tabela[coluna] = tabela[coluna].apply(conversor) #converte os dados para número
            tabela[col_tempo] = tabela[col_tempo].astype(str) #converte para string

            fig = px.line(tabela, x=col_tempo, y=coluna, markers=True, #cria gráfico de linha
                          color_discrete_sequence=[cor])
            fig.update_layout(margin=dict(l=10, r=30, t=10, b=10), height=190,
                              xaxis_title="", yaxis_title="", hovermode="x unified") #remove títulos dos eixos e unifica os hovers
            fig.update_xaxes(tickangle=-45, tickfont=dict(size=10), #inclina rótulos do eixo X
                             type="category", automargin=True)
            fig.update_yaxes(automargin=False, ticklabelposition="inside", #coloca os valores do eixo Y para dentro
                             tickfont=dict(size=10))
            fig.update_traces(cliponaxis=False)

            st.plotly_chart(fig, use_container_width=True, #exibe gráfico na largura do card
                            config={"displayModeBar": False}) #oculta a barra de ferramentas do plotly

def card_expansivel_real(titulo, coluna, dados_tri, tabela_validos, key_slider, col_tempo="Trimestre"):
    valor = f"R$ {str(dados_tri[coluna]).replace(',00', '').strip()}" #remove os decimais
    _card_base(titulo, valor, coluna, tabela_validos, key_slider, f_bilhoes, "#00529B", col_tempo) #chama o card base com conversor de bilhões

def card_expansivel_geral(titulo, coluna, dados_tri, tabela_validos, key_slider, col_tempo="Trimestre"):
    _card_base(titulo, f"{dados_tri[coluna]}", coluna, tabela_validos, key_slider, conv_pct, "#00529B", col_tempo) #conversor de percentual

def card_expansivel_acao(titulo, coluna, dados_tri, tabela_validos, key_slider, simbolo="", col_tempo="Trimestre"):
    _card_base(titulo, f"{simbolo}{dados_tri[coluna]}", coluna, tabela_validos, key_slider, conv_preco, "#00A859", col_tempo) #conversor de preço e símbolo personalizável

def marcacao_preta():
    st.markdown(
        """
       <hr style="border: 1px solid #444; margin-top: 20px; margin-bottom: 20px;">
       """,
        unsafe_allow_html=True,)

#CONFIGURAÇÃO E SIDEBAR DA PÁGINA =========================================================

st.set_page_config(layout="wide")

st.markdown(
    """
   <style>
       .main .block-container {
           max-width: 100%;
           padding-left: 0.5rem;
           padding-right: 0.5rem;
           padding-top: 1rem;
           padding-bottom: 0rem;
       }
       [data-testid="stSidebar"] {
           width: 100px !important;
       }
       [data-testid="stExpander"] details > div {
           padding: 0.25rem 1rem 0.25rem 0.25rem;
       }
       [data-testid="stVerticalBlockBorderWrapper"] {
           padding: 0.5rem;
       }
   </style>
""",
    unsafe_allow_html=True,)

st.sidebar.title("Menu de Navegação")
pagina = st.sidebar.radio(
    "Escolha uma página:", ["Visão Geral", "Financeiro", "Produção", "Mercado"])

st.sidebar.write(
    "Criado por Fernando Henrique M. Rossignolli, Israel Gomes Galdino, "
    "Luis Felipe de Souza Ferreira e João Pedro Barreto de Almeida")

#PÁGINA VISÃO GERAL ===================================================================================================================

if pagina == "Visão Geral":
    st.title("Visão Geral — Vale S.A.")
    st.markdown("##### Resumo Executivo: Desempenho Financeiro, Operacional e de Mercado")

    #funções necessárias recriadas localmente ----------------------------------
    def local_f_bilhoes(val):
        if pd.isna(val):
            return None
        val_str = str(val).replace("(R$ bi)", "").replace("R$", "").strip()
        if "," in val_str:
            val_str = val_str.replace(".", "").replace(",", ".")
        else:
            parts = val_str.split(".")
            if len(parts) == 2 and len(parts[1]) == 3 and float(parts[0]) > 10:
                val_str = val_str.replace(".", "")
        try:
            num = float(val_str)
        except ValueError:
            return None
        if abs(num) >= 100:
            return num / 1000.0
        return num

    def local_conv_vol(val):
        if pd.isna(val):
            return 0.0
        val_str = str(val).strip()
        if "," in val_str:
            val_str = val_str.replace(".", "").replace(",", ".")
        try:
            num = float(val_str)
            if num >= 100 and "." not in val_str and "," not in str(val):
                return num / 1000.0
            return num
        except ValueError:
            return 0.0

    def local_conv_preco(val):
        if pd.isna(val):
            return None
        val_str = (
            str(val)
            .replace("US$", "")
            .replace("US", "")
            .replace("R$", "")
            .replace("$", "")
            .replace("€", "")
            .replace("\x80", "")
            .strip())
        if "," in val_str and "." in val_str:
            val_str = val_str.replace(".", "").replace(",", ".")
        elif "," in val_str:
            val_str = val_str.replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return None

    def local_layout(fig, col_tempo, **extra):
        fig.update_layout( #atualiza as configurações de layout da figura
            hovermode="x unified", #unifica as informações no balão ao passar o mouse pelo eixo X
            legend=dict(orientation="h", y=1.1, title=""), #posiciona a legenda na horizontal acima e oculta o título
            xaxis_title=col_tempo, #define título no eixo X
            **extra,)
        return fig

    def local_mostrar(fig):
        st.plotly_chart(fig, use_container_width=True)

    def local_marcacao():
        st.markdown(
            '<hr style="border: 1px solid #444; margin-top: 20px; margin-bottom: 20px;">',
            unsafe_allow_html=True,)

    #1. alinhamento de período -------------------------------------------------
    tabela_tri_f_valid = tri_financas.dropna(subset=["Trimestre"]).copy() #remove linhas sem trimestre
    periodos_list = tabela_tri_f_valid["Trimestre"].unique().tolist() #pega a lista de trimestres únicos disponíveis
    tri_sel = st.selectbox("Selecione o Trimestre para Análise:", options=periodos_list, index=len(periodos_list) - 1) #caixa de seleção de trimestre

    dados_fin = tabela_tri_f_valid[tabela_tri_f_valid["Trimestre"] == tri_sel].iloc[0] #pega a linha com os trimestres financeiros selecionado
    tabela_prod_tri = tri_producao[tri_producao["Trimestre"] == tri_sel].copy() #filtra a tabela de produção para o tri selescionado
    tabela_merc_tri = tri_mercado[tri_mercado["Trimestre"] == tri_sel].copy() #filtra a tabela de mercado para o tri selescionado

    #2. cards principais de destaque --------------------------------------------
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        rec_val = local_f_bilhoes(dados_fin["Receita Líquida"])
        st.metric("Receita Líquida", f"R$ {rec_val:,.2f} Bi" if rec_val else "N/A")

    with c2:
        lucro_val = local_f_bilhoes(dados_fin["Lucro Líquido"])
        st.metric("Lucro Líquido", f"R$ {lucro_val:,.2f} Bi" if lucro_val else "N/A")

    with c3:
        totais_excluir = [
            "Total Norte", "Total Sudeste:", "Total Sul", "Total Centro-Oeste",
            "Produção Total de Minério de Ferro", "Total Canadá", "Produção Total de Níquel",
            "Total Brasil", "Produção Total de Cobre", "Total Sudeste", "Produção Pelotas",
            "Produção Total de Cobalto",]
        sub_fe = tabela_prod_tri[(tabela_prod_tri["Produto"] == "Minério de Ferro") & (~tabela_prod_tri["Local"].isin(totais_excluir))] #filtra excluindo as linhas total e subtotal
        vol_fe = sub_fe["Extração (Mil Toneladas Métricas)"].apply(local_conv_vol).sum() if not sub_fe.empty else 0.0
        st.metric("Produção de Minério de Ferro", f"{vol_fe:,.1f} kt")

    with c4:
        if not tabela_merc_tri.empty:
            pr_fe = local_conv_preco(tabela_merc_tri.iloc[0]["Preço Realizado Ferro/t"])
            st.metric("Preço Realizado (Ferro)", f"US$ {pr_fe:,.2f}/t" if pr_fe else "N/A")
        else:
            st.metric("Preço Realizado (Ferro)", "N/A")

    local_marcacao()

    #3. profundidade histórica -------------------------------------------------
    qtd_p = st.slider("Selecione a quantidade de trimestres para visualização histórica:", min_value=3, max_value=len(tabela_tri_f_valid), value=min(8, len(tabela_tri_f_valid)), step=1)

    tabela_f_sub = tabela_tri_f_valid.tail(qtd_p).copy() #seleciona os últimos 'qtd_p' trimestres da tabela financeira para os gráficos
    tabela_m_sub = tri_mercado.tail(qtd_p).copy()

    #4. painel de gráficos cruzados (2x2) --------------------------------------
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("Evolução da Receita Líquida vs. Lucro Líquido")
        tabela_fin_bi = tabela_f_sub.assign( #cria colunas temporárias com o valor em bilhões
            Receita=tabela_f_sub["Receita Líquida"].apply(local_f_bilhoes),
            Lucro=tabela_f_sub["Lucro Líquido"].apply(local_f_bilhoes))

        fig_fin_vis = go.Figure([
            go.Bar(x=tabela_fin_bi["Trimestre"], y=tabela_fin_bi["Receita"], name="Receita Líquida", marker_color="#00529B"), #adiciona barras azuis da receita líquida
            go.Scatter(x=tabela_fin_bi["Trimestre"], y=tabela_fin_bi["Lucro"], name="Lucro Líquido", mode="lines+markers", line=dict(color="#00A859", width=3))]) #adiciona a linha verde do lucro liquido
        local_mostrar(local_layout(fig_fin_vis, "Trimestre", yaxis_title="R$ (Bilhões)", height=380))

        st.subheader("Preço Realizado Vale vs. Mercado (Minério de Ferro)")
        tabela_m_clean = tabela_m_sub.assign(
            Realizado=tabela_m_sub["Preço Realizado Ferro/t"].apply(local_conv_preco),
            Mercado=tabela_m_sub["Minério de Ferro"].apply(local_conv_preco))

        fig_merc_vis = go.Figure([
            go.Scatter(x=tabela_m_clean["Trimestre"], y=tabela_m_clean["Realizado"], name="Realizado Vale", mode="lines+markers", line=dict(color="#00529B", width=2.5)),
            go.Scatter(x=tabela_m_clean["Trimestre"], y=tabela_m_clean["Mercado"], name="Mercado Mundial", mode="lines+markers", line=dict(color="#D97706", width=2.5))])
        local_mostrar(local_layout(fig_merc_vis, "Trimestre", yaxis_title="USD / Tonelada", height=380))

    with g2:
        st.subheader(f"Mix de Produção por Mineral ({tri_sel})")
        tabela_prod_operacional = tabela_prod_tri[~tabela_prod_tri["Local"].isin(totais_excluir)].copy()
        tabela_prod_operacional["Vol"] = tabela_prod_operacional["Extração (Mil Toneladas Métricas)"].apply(local_conv_vol)
        tabela_mix = tabela_prod_operacional.groupby("Produto")["Vol"].sum().reset_index()

        fig_mix = px.pie(tabela_mix, values="Vol", names="Produto", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2) #cria o gráfico de rosca
        fig_mix.update_layout(height=380, margin=dict(l=0, r=0, t=20, b=0)) #limpa e converte a cotção do dólar para número
        st.plotly_chart(fig_mix, use_container_width=True)

        st.subheader("Desempenho VALE3 (B3) vs. Cotação Dólar (USD/BRL)")
        tabela_m_clean["Dolar"] = tabela_m_sub["Média Trimestral Dólar (USD/BRL)"].apply(local_conv_preco)
        tabela_m_clean["VALE3"] = tabela_f_sub.tail(len(tabela_m_clean))["VALE3 (B3 - BRL)"].apply(local_conv_preco).values

        fig_macro = go.Figure([
            go.Scatter(x=tabela_m_clean["Trimestre"], y=tabela_m_clean["VALE3"], name="VALE3 (R$)", mode="lines+markers", line=dict(color="#00A859", width=2.5)), #linha verde para o preço da vale3
            go.Scatter(x=tabela_m_clean["Trimestre"], y=tabela_m_clean["Dolar"], name="USD/BRL (R$)", mode="lines+markers", yaxis="y2", line=dict(color="#2563EB", width=2.5))]) #linha azul para cotação do dólar no eixo
        local_layout(fig_macro, "Trimestre", yaxis=dict(title="Preço VALE3 (R$)"), yaxis2=dict(title="Dólar (USD/BRL)", overlaying="y", side="right"), height=380) #configura os dois eixos y e o layout
        local_mostrar(fig_macro)

#PÁGINA FINANCEIRA ======================================================================================================================================

if pagina == "Financeiro":

    st.title("Dados Financeiros da Vale S.A.")

    visao = st.radio(
        "Selecione a Visão:", ["Trimestral", "Anual"], horizontal=True)

    if visao == "Trimestral":
        tabela_financas = tri_financas.copy()
        col_tempo = "Trimestre"
        col_ebit = "EBIT/ Resultado Operacional"
        col_vale3 = "VALE3 (B3 - BRL)"
        col_vale_usd = "VALE (NYSE - USD)"
        col_xvalo = "XVALO (Latibex - EUR)"
        col_divida = "Dívida Líquida (MM)"

        #liquidez corrente apenas no modo Trimestral
        tabela_financas["Liquidez Corrente"] = (
            tabela_financas["Ativo Circulante"]
            / tabela_financas["Passivo Circulante"])
        tabela_financas["Liquidez Corrente"] = (
            tabela_financas["Liquidez Corrente"]
            .replace([float("inf"), float("-inf")], 0)
            .fillna(0))
    else:
        tabela_financas = anual_financas.copy()
        col_tempo = "Ano"
        col_ebit = "EBIT"
        col_vale3 = "VALE3 (Fim do Ano)"
        col_vale_usd = "VALE (Fim do Ano)"
        col_xvalo = "XVALO (Fim do Ano)"
        col_divida = "Dívida Líquida"

    #garante a filtragem correta das linhas válidas do período ativo
    tabela_validos = tabela_financas.dropna(subset=[col_tempo]).copy()

    lista_periodos = tabela_validos[col_tempo].unique().tolist()
    periodo_selecionado = st.selectbox(
        f"Selecione o {col_tempo}:", options=lista_periodos)

    dados_tri = tabela_validos[tabela_validos[col_tempo] == periodo_selecionado].iloc[0] #seleciona a linha de dados escolhida

    #LINHA 1 DE CARDS --------------------------------------------------
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        card_expansivel_real(
            "Receita Líquida",
            "Receita Líquida",
            dados_tri,
            tabela_validos,
            "slider_rec",
            col_tempo=col_tempo,)

    with col2:
        card_expansivel_real(
            "EBITDA (LAJIDA)",
            "EBITDA",
            dados_tri,
            tabela_validos,
            "slider_ebitda",
            col_tempo=col_tempo,)

    with col3:
        card_expansivel_real(
            "Lucro Líquido",
            "Lucro Líquido",
            dados_tri,
            tabela_validos,
            "slider_lucro",
            col_tempo=col_tempo,)

    with col4:
        card_expansivel_geral(
            "Margem Bruta (%)",
            "Margem Bruta (%)",
            dados_tri,
            tabela_validos,
            "slider_margem",
            col_tempo=col_tempo,)

    with col5:
        card_expansivel_real(
            "Dívida Líquida",
            col_divida,
            dados_tri,
            tabela_validos,
            "slider_divliq",
            col_tempo=col_tempo,)

    #LINHA 2 DE CARDS --------------------------------------------------
    col6, col7, col8, col9, col10 = st.columns(5)

    with col6:
        if visao == "Trimestral":
            dados_tri_copy = dados_tri.copy()
            dados_tri_copy["Liquidez Corrente"] = round(
                dados_tri_copy["Liquidez Corrente"], 3)
            card_expansivel_real(
                "Liquidez Corrente",
                "Liquidez Corrente",
                dados_tri_copy,
                tabela_validos,
                "slider_liqcor",
                col_tempo=col_tempo,)
        else:
            card_expansivel_real(
                "Caixa e Equiv.",
                "Caixa e Equivalentes de Caixa",
                dados_tri,
                tabela_validos,
                "slider_caixa_eq",
                col_tempo=col_tempo,)

    with col7:
        card_expansivel_real(
            "EBIT / Res. Operacional",
            col_ebit,
            dados_tri,
            tabela_validos,
            "slider_resultoper",
            col_tempo=col_tempo,)

    with col8:
        card_expansivel_acao(
            "VALE3 (B3)",
            col_vale3,
            dados_tri,
            tabela_validos,
            "slider_vale3",
            col_tempo=col_tempo,)

    with col9:
            card_expansivel_acao(
                "VALE (NYSE)",
                col_vale_usd,
                dados_tri,
                tabela_validos,
                "slider_vale_usd",
                simbolo="US$ " if visao == "Trimestral" else "",
                col_tempo=col_tempo,)

    with col10:
        card_expansivel_acao(
            "XVALO (Latibex)",
            col_xvalo,
            dados_tri,
            tabela_validos,
            "slider_xvalo",
            simbolo="€",
            col_tempo=col_tempo,)

    marcacao_preta()

    #FILTRO DE PERÍODO (SLIDER GERAL)
    qtd_trimestres = st.slider(
        f"Selecione a quantidade de {col_tempo.lower()}s para visualizar nos gráficos:",
        min_value=3, #define o limite mínimo de 3 períodos
        max_value=len(tabela_validos), #define o máximo como o total de períodos disponíveis
        value=min(12 if visao == "Trimestral" else 6, len(tabela_validos)),
        step=1,)

    tabela_periodo = tabela_validos.tail(qtd_trimestres)

    #PAINEL INFERIOR COM 4 GRÁFICOS GRANDES ==========================================
    col11, col12 = st.columns(2)

    with col11:

        st.subheader("Evolução do Resultado (Receita, EBITDA e Lucro Líquido)")

        def _bi(tabela, cols):
            #converte as colunas existentes para bilhões
            return tabela.assign(**{c: tabela[c].apply(f_bilhoes) for c in cols if c in tabela.columns})

        def _layout(fig, col_tempo, **extra):
            fig.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title=col_tempo,
                **extra,)
            return fig

        def _mostrar(fig, key=None):
            st.plotly_chart(fig, use_container_width=True, key=key)

        #gráfico 1
        cols_res = ["Receita Líquida", "EBITDA", "Lucro Líquido"]
        fig_resultado = px.line(
            _bi(tabela_periodo, cols_res), x=col_tempo, y=cols_res, markers=True,
            labels={"value": "R$ (Bilhões)", "variable": "Indicador"},)
        _mostrar(_layout(fig_resultado, col_tempo, yaxis_title="R$ (Bilhões)"))

        #gráfico 2
        st.subheader("Composição de Capital / Estrutura")
        cols_balanco = (
            ["Passivo Circulante", "Passivo Não Circulante", "Patrimônio Líquido"]
            if visao == "Trimestral"
            else ["Dívida Bruta", "Dívida Líquida"])
        fig_balanco = px.bar(
            _bi(tabela_periodo, cols_balanco), x=col_tempo, y=cols_balanco, barmode="group",
            labels={"value": "R$ (Bilhões)", "variable": "Estrutura"},)
        _mostrar(_layout(fig_balanco, col_tempo, bargap=0.15, yaxis_title="R$ (Bilhões)"))

    with col12:

        #gráfico 3
        st.subheader("Geração de Caixa: Operacional (FCO) vs. Livre (FCL)")
        tabela_fcl = _bi(tabela_periodo, ["Fluxo de Caixa Operacional", "Fluxo de Caixa Livre"])

        fig_caixa = go.Figure([
            go.Bar(x=tabela_fcl[col_tempo], y=tabela_fcl["Fluxo de Caixa Operacional"], name="FCO (Operacional)"),
            go.Bar(x=tabela_fcl[col_tempo], y=tabela_fcl["Fluxo de Caixa Livre"], name="FCL (Livre)"),])
        _mostrar(_layout(fig_caixa, col_tempo, barmode="group", bargap=0.15, yaxis_title="R$ (Bilhões)"))

        #gráfico 4
        st.subheader("Desempenho das Ações: VALE3 (B3) vs. VALE (NYSE)")
        fig_acoes = go.Figure([
            go.Scatter(
                x=tabela_periodo[col_tempo], y=tabela_periodo[col].apply(conv_preco),
                name=nome, mode="lines+markers", yaxis=eixo,
                line=dict(color=cor, width=2.5),)
            for col, nome, eixo, cor in [
                (col_vale3, "VALE3 (B3)", "y", "#00529B"),
                (col_vale_usd, "VALE (NYSE)", "y2", "#00A859"),]])
        _layout(
            fig_acoes, col_tempo,
            yaxis=dict(title="Preço VALE3"),
            yaxis2=dict(title="Preço VALE (USD)", overlaying="y", side="right"),)
        _mostrar(fig_acoes)
        
    # PAINEL DE BRUMADINHO E CUSTOS OPERACIONAIS (TRIMESTRAL E ANUAL) ==================
    marcacao_preta()
    
    # Dicionários definidos diretamente no código
    custos_despesas_operacionais_anual = {
        "2019": 143.716,
        "2020": 151.025,  
        "2021": 142.221,  
        "2022": 140.861,   
        "2023": 130.695,  
        "2024": 147.956,  
        "2025": 153.020,}

    mapa_brum_tri = {
        "1T19": 17.315, "2T19": 5.921, "3T19": 0.893, "4T19": 4.689,
        "1T20": 0.708,  "2T20": 0.693, "3T20": 0.613, "4T20": 25.002,
        "1T21": 0.673,  "2T21": 0.953, "3T21": 0.847, "4T21": 11.942,
        "1T22": 0.832,  "2T22": 1.397, "3T22": 1.759, "4T22": 1.968,
        "1T23": 0.579,  "2T23": 1.327, "3T23": 1.495, "4T23": 1.947,
        "1T24": 0.201,  "2T24": 0.022, "3T24": 0.695, "4T24": 0.656,
        "1T25": 0.563,  "2T25": 0.219, "3T25": 0.173, "4T25": 1.334,
        "1T26": 0.339,  "2T26": 0.515}

    if visao == "Trimestral":
        st.subheader("⚠️ Análise de Impacto: Provisões de Brumadinho & Custos Operacionais")
        c_brum1, c_brum2 = st.columns(2)
        
        #1. ESQUERDA: Brumadinho Trimestral (Dicionário)
        with c_brum1:
            st.markdown("##### Provisões & Desembolsos com Brumadinho (R$ Bi)")
            
            tabela_brum = tabela_periodo[["Trimestre"]].copy()
            tabela_brum["Brumadinho_Bi"] = tabela_brum["Trimestre"].map(mapa_brum_tri)

            fig_brum = px.bar(
                tabela_brum, 
                x="Trimestre", 
                y="Brumadinho_Bi",
                color_discrete_sequence=["#DC2626"],
                labels={"Brumadinho_Bi": "R$ (Bilhões)", "Trimestre": "Trimestre"})
            _mostrar(_layout(fig_brum, "Trimestre", yaxis_title="R$ (Bilhões)"), key="fig_brum_painel_tri")
            
        #2. DIREITA: Custos Operacionais Trimestrais (Da base de dados)
        with c_brum2:
            st.markdown("##### Custos e Despesas Operacionais (R$ Bi)")
            
            def _tratar_custos_tri(val):
                if pd.isna(val):
                    return 0.0
                val_str = str(val).strip()
                # Remove pontos de milhar, sinais negativos e formatações textuais
                val_limpo = val_str.replace(".", "").replace(",", ".").replace("R$", "").strip()
                try:
                    num = float(val_limpo)
                    val_abs = abs(num)
                    # Ex: 5180000 -> 5.18 Bi (converte para bilhões)
                    if val_abs >= 1_000_000:
                        return val_abs / 1_000_000.0
                    elif val_abs >= 1_000:
                        return val_abs / 1_000.0
                    return val_abs
                except ValueError:
                    return 0.0

            if "Custos e Despesas Operacionais" in tabela_periodo.columns:
                tabela_custos_tri = tabela_periodo[["Trimestre", "Custos e Despesas Operacionais"]].copy()
                tabela_custos_tri["Custos_Bi"] = tabela_custos_tri["Custos e Despesas Operacionais"].apply(_tratar_custos_tri)

                fig_custos_tri = px.line(
                    tabela_custos_tri, 
                    x="Trimestre", 
                    y="Custos_Bi",
                    markers=True,
                    color_discrete_sequence=["#F59E0B"],
                    labels={"Custos_Bi": "R$ (Bilhões)", "Trimestre": "Trimestre"})
                _mostrar(_layout(fig_custos_tri, "Trimestre", yaxis_title="R$ (Bilhões)"), key="fig_custos_painel_tri")
            else:
                st.info("Coluna de Custos e Despesas Operacionais não encontrada nos dados trimestrais.")

    else:
        #VISÃO ANUAL: Ocupa a largura inteira (1 coluna)
        st.subheader("Custos e Despesas Operacionais Anuais")
        
        tabela_custos_anual = tabela_periodo[["Ano"]].copy()
        tabela_custos_anual["Custos_Anual_Bi"] = tabela_custos_anual["Ano"].astype(str).map(custos_despesas_operacionais_anual)

        fig_custos_anual = px.line(
            tabela_custos_anual, 
            x="Ano", 
            y="Custos_Anual_Bi",
            markers=True,
            color_discrete_sequence=["#F59E0B"],
            labels={"Custos_Anual_Bi": "R$ (Bilhões)", "Ano": "Ano"})
        _mostrar(_layout(fig_custos_anual, "Ano", yaxis_title="R$ (Bilhões)"), key="fig_custos_painel_anual")

    # PREVISÕES & INTELIGÊNCIA PREDITIVA (SIMULADOR ML AVANÇADO) ===================
    marcacao_preta()

    st.subheader("🔮 Previsões & Inteligência Preditiva (Simulador ML)")
    st.markdown("##### Simulador Financeiro Multi-Variável com Regressão Linear & Análise de Sensibilidade")

    @st.cache_data
    def treinar_modelo_financeiro_avancado(tabela_fin, tabela_merc, tabela_prod):
        #1. Tratamento da Tabela Financeira
        tabela_f = tabela_fin.copy()
        tabela_f["Rec_Bi"] = tabela_f["Receita Líquida"].apply(f_bilhoes)
        tabela_f["Lucro_Bi"] = tabela_f["Lucro Líquido"].apply(f_bilhoes)
        tabela_f["EBITDA_Bi"] = tabela_f["EBITDA"].apply(f_bilhoes)

        #2. Tratamento da Tabela de Mercado
        tabela_m = tabela_merc.copy()
        tabela_m["Dolar_Num"] = tabela_m["Média Trimestral Dólar (USD/BRL)"].apply(conv_preco)
        tabela_m["Minério_Num"] = tabela_m["Preço Realizado Ferro/t"].apply(conv_preco)

        #3. Tratamento de Produção (Agrupado por Trimestre)
        totais_excluir = [
            "Total Norte", "Total Sudeste:", "Total Sul", "Total Centro-Oeste",
            "Produção Total de Minério de Ferro", "Total Brasil", "Produção Pelotas"]
        sub_fe = tabela_prod[(tabela_prod["Produto"] == "Minério de Ferro") & (~tabela_prod["Local"].isin(totais_excluir))].copy()
        
        def _conv_vol_puro(val):
            if pd.isna(val): return 0.0
            val_s = str(val).replace(".", "").replace(",", ".").strip()
            try:
                n = float(val_s)
                return float(n / 1000.0) if n >= 1000 else float(n)
            except ValueError: return 0.0

        sub_fe["Vol_Mt"] = sub_fe["Extração (Mil Toneladas Métricas)"].apply(_conv_vol_puro)
        tabela_p_agg = sub_fe.groupby("Trimestre")["Vol_Mt"].sum().reset_index()

        #4. Merge Triplo
        m1 = pd.merge(tabela_f[["Trimestre", "Rec_Bi", "Lucro_Bi", "EBITDA_Bi"]], tabela_m[["Trimestre", "Dolar_Num", "Minério_Num"]], on="Trimestre")
        tabela_merged = pd.merge(m1, tabela_p_agg, on="Trimestre").dropna()

        #5. Variáveis X (Dólar, Minério e Volume Produzido) e y
        X = tabela_merged[["Dolar_Num", "Minério_Num", "Vol_Mt"]]
        
        m_rec = LinearRegression().fit(X, tabela_merged["Rec_Bi"])
        m_ebitda = LinearRegression().fit(X, tabela_merged["EBITDA_Bi"])
        m_lucro = LinearRegression().fit(X, tabela_merged["Lucro_Bi"])

        #métricas R2 Score
        r2_rec = m_rec.score(X, tabela_merged["Rec_Bi"])
        r2_ebitda = m_ebitda.score(X, tabela_merged["EBITDA_Bi"])
        r2_lucro = m_lucro.score(X, tabela_merged["Lucro_Bi"])

        u_dolar = float(tabela_merged["Dolar_Num"].iloc[-1])
        u_minerio = float(tabela_merged["Minério_Num"].iloc[-1])
        u_vol = float(tabela_merged["Vol_Mt"].iloc[-1])

        return m_rec, m_ebitda, m_lucro, u_dolar, u_minerio, u_vol, (r2_rec, r2_ebitda, r2_lucro), tabela_merged

    #executa o treino com histórico
    m_rec, m_ebitda, m_lucro, u_dolar, u_minerio, u_vol, (r2_rec, r2_ebitda, r2_lucro), tabela_treino = (
        treinar_modelo_financeiro_avancado(tri_financas, tri_mercado, tri_producao))

    #1. Funções de Callback para os botões (garantindo tipos float puros)
    def aplicar_cenario_base():
        st.session_state["slider_pred_dol"] = float(round(u_dolar, 2))
        st.session_state["slider_pred_min"] = float(round(u_minerio, 2))
        st.session_state["slider_pred_vol"] = float(round(u_vol, 1))

    def aplicar_cenario_otimista():
        st.session_state["slider_pred_dol"] = float(round(u_dolar * 1.05, 2))
        st.session_state["slider_pred_min"] = float(round(u_minerio * 1.15, 2))
        st.session_state["slider_pred_vol"] = float(round(u_vol * 1.05, 1))

    def aplicar_stress_test():
        st.session_state["slider_pred_dol"] = float(round(u_dolar * 0.95, 2))
        st.session_state["slider_pred_min"] = float(round(u_minerio * 0.75, 2))
        st.session_state["slider_pred_vol"] = float(round(u_vol * 0.95, 1))

    def aplicar_alta_dolar():
        st.session_state["slider_pred_dol"] = float(6.20)
        st.session_state["slider_pred_min"] = float(round(u_minerio, 2))
        st.session_state["slider_pred_vol"] = float(round(u_vol, 1))

    #2. Inicialização segura no session_state com float
    if "slider_pred_dol" not in st.session_state:
        st.session_state["slider_pred_dol"] = float(round(u_dolar, 2))
    if "slider_pred_min" not in st.session_state:
        st.session_state["slider_pred_min"] = float(round(u_minerio, 2))
    if "slider_pred_vol" not in st.session_state:
        st.session_state["slider_pred_vol"] = float(round(u_vol, 1))

    #3. Botões de Cenários Estressados
    st.markdown("### 🎛️ Cenários Estressados de Mercado")
    cenario_col1, cenario_col2, cenario_col3, cenario_col4 = st.columns(4)

    cenario_col1.button("🎯 Cenário Base (Atual)", on_click=aplicar_cenario_base, use_container_width=True)
    cenario_col2.button("🚀 Cenário Otimista (+15% Minério)", on_click=aplicar_cenario_otimista, use_container_width=True)
    cenario_col3.button("📉 Stress Test (-25% Minério)", on_click=aplicar_stress_test, use_container_width=True)
    cenario_col4.button("⚡ Alta do Câmbio (Dólar R\$ 6,20)", on_click=aplicar_alta_dolar, use_container_width=True)

    #4. Sliders com min/max/step estritamente tipados como float
    st.subheader("Ajuste Fino de Parâmetros de Simulação")
    col_s1, col_s2, col_s3 = st.columns(3)

    with col_s1:
        sim_dolar = st.slider(
            "Cotação Estimada do Dólar (USD/BRL):",
            min_value=float(3.50),
            max_value=float(7.50),
            step=float(0.05),
            format="R\$ %.2f",
            key="slider_pred_dol")

    with col_s2:
        sim_minerio = st.slider(
            "Preço do Minério de Ferro (USD/t):",
            min_value=float(50.0),
            max_value=float(220.0),
            step=float(1.0),
            format="US\$ %.2f",
            key="slider_pred_min")

    with col_s3:
        sim_vol = st.slider(
            "Volume de Extração de Minério (Mt):",
            min_value=float(40.0),
            max_value=float(110.0),
            step=float(0.5),
            format="%.1f Mt",
            key="slider_pred_vol")

    #5. Predição em tempo real com Scikit-Learn
    X_pred = pd.DataFrame([[sim_dolar, sim_minerio, sim_vol]], columns=["Dolar_Num", "Minério_Num", "Vol_Mt"])
    rec_prevista = m_rec.predict(X_pred)[0]
    ebitda_previsto = m_ebitda.predict(X_pred)[0]
    lucro_previsto = m_lucro.predict(X_pred)[0]

    #6. Exibição dos KPIs Estimados
    st.subheader("Projeção do Resultado Financeiro Estimado")
    m1, m2, m3, m4 = st.columns(4)

    rec_ult = tabela_treino["Rec_Bi"].iloc[-1]
    ebitda_ult = tabela_treino["EBITDA_Bi"].iloc[-1]
    lucro_ult = tabela_treino["Lucro_Bi"].iloc[-1]

    with m1:
        st.metric(
            label="Receita Líquida Estimada",
            value=f"R\$ {rec_prevista:,.2f} Bi",
            delta=f"{((rec_prevista / rec_ult) - 1) * 100:+.1f}% vs. Último Tri")

    with m2:
        st.metric(
            label="EBITDA Estimado",
            value=f"R\$ {ebitda_previsto:,.2f} Bi",
            delta=f"{((ebitda_previsto / ebitda_ult) - 1) * 100:+.1f}% vs. Último Tri")

    with m3:
        st.metric(
            label="Lucro Líquido Estimado",
            value=f"R\$ {lucro_previsto:,.2f} Bi",
            delta=f"{((lucro_previsto / lucro_ult) - 1) * 100:+.1f}% vs. Último Tri")

    with m4:
        margem_ebitda_est = (ebitda_previsto / rec_prevista * 100) if rec_prevista > 0 else 0.0
        st.metric(label="Margem EBITDA Estimada", value=f"{margem_ebitda_est:.1f}%")

    with st.expander("ℹ️ Métricas de Acurácia Estatística dos Modelos (R² Score)"):
        c_acc1, c_acc2, c_acc3 = st.columns(3)
        c_acc1.write(f"**R² Receita Líquida:** `{r2_rec*100:.1f}%`")
        c_acc2.write(f"**R² EBITDA:** `{r2_ebitda*100:.1f}%`")
        c_acc3.write(f"**R² Lucro Líquido:** `{r2_lucro*100:.1f}%`")

    #7. Gráfico Comparativo: Histórico Real vs. Simulação ML
    st.subheader("Comparativo Visual: Histórico Real vs. Simulação ML")

    tabela_plot = tabela_treino.copy()
    fig_sim = go.Figure()

    # Receita Real vs Projetada
    fig_sim.add_trace(go.Scatter(
        x=tabela_plot["Trimestre"], y=tabela_plot["Rec_Bi"],
        mode="lines+markers", name="Receita Real (Bi)", line=dict(color="#00529B", width=2.5)))

    fig_sim.add_trace(go.Scatter(
        x=["Projeção (Simulada)"], y=[rec_prevista],
        mode="markers", name="Receita Projetada",
        marker=dict(color="#2563EB", size=15, symbol="star")))

    #EBITDA Real vs Projetado
    fig_sim.add_trace(go.Scatter(
        x=tabela_plot["Trimestre"], y=tabela_plot["EBITDA_Bi"],
        mode="lines+markers", name="EBITDA Real (Bi)", line=dict(color="#F59E0B", width=2.5)))

    fig_sim.add_trace(go.Scatter(
        x=["Projeção (Simulada)"], y=[ebitda_previsto],
        mode="markers", name="EBITDA Projetado",
        marker=dict(color="#D97706", size=15, symbol="star")))

    #lucro Real vs Projetado
    fig_sim.add_trace(go.Scatter(
        x=tabela_plot["Trimestre"], y=tabela_plot["Lucro_Bi"],
        mode="lines+markers", name="Lucro Real (Bi)", line=dict(color="#00A859", width=2.5)))

    fig_sim.add_trace(go.Scatter(
        x=["Projeção (Simulada)"], y=[lucro_previsto],
        mode="markers", name="Lucro Projetado",
        marker=dict(color="#10B981", size=15, symbol="star")))

    fig_sim.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1, title=""),
        xaxis_title="Trimestre",
        yaxis_title="R\$ (Bilhões)",
        height=420)

    st.plotly_chart(fig_sim, use_container_width=True)

#PÁGINA PRODUÇÃO ===================================================================================================================

if pagina == "Produção":
    st.title("Produção e Operações da Vale S.A.")
    st.markdown("### Mil Toneladas Métricas (kt/Mt)")

    visao_prod = st.radio(
        "Selecione a Visão da Produção:", ["Trimestral", "Anual"], horizontal=True)

    def conv_num_limpo(val):
        if pd.isna(val):
            return 0.0
        val_str = str(val).replace(",", ".").strip()
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    #VISÃO ANUAL DE PRODUÇÃO ==============================================================

    if visao_prod == "Anual":
        tabela_anual_p = anual_producao.copy()
        
        cols_num = [c for c in tabela_anual_p.columns if c != "Ano"]
        for c in cols_num:
            tabela_anual_p[c] = tabela_anual_p[c].apply(conv_num_limpo)

        anos_list = tabela_anual_p["Ano"].unique().tolist()
        ano_sel = st.selectbox("Selecione o Ano:", options=anos_list, index=len(anos_list) - 1)

        dados_ano = tabela_anual_p[tabela_anual_p["Ano"] == ano_sel].iloc[0]

        #KPIs do Ano Selecionado
        st.markdown("### Resumo da Produção do Ano")
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.metric(
                "Minério de Ferro",
                f"{dados_ano['Produção Minério de Ferro']:,.1f} Mt",
                delta=f"Vendas: {dados_ano['Vendas de Minério de Ferro']:,.1f} Mt")
        with k2:
            st.metric(
                "Pelotas",
                f"{dados_ano['Produção de Pelotas']:,.1f} Mt",
                delta=f"Vendas: {dados_ano['Vendas de Pelotas']:,.1f} Mt")
        with k3:
            st.metric(
                "Cobre",
                f"{dados_ano['Produção de Cobre']:,.1f} kt",
                delta=f"Vendas: {dados_ano['Vendas de Cobre']:,.1f} kt")
        with k4:
            st.metric(
                "Níquel",
                f"{dados_ano['Produção de Níquel']:,.1f} kt",
                delta=f"Vendas: {dados_ano['Vendas de Níquel']:,.1f} kt")

        marcacao_preta()

        #gráficos de Produção vs Vendas
        g_col1, g_col2 = st.columns(2)

        with g_col1:
            st.subheader("Minério de Ferro: Produção vs. Vendas (Mt)")
            fig_fe = go.Figure([
                go.Bar(x=tabela_anual_p["Ano"], y=tabela_anual_p["Produção Minério de Ferro"], name="Produção (Mt)", marker_color="#00529B"),
                go.Bar(x=tabela_anual_p["Ano"], y=tabela_anual_p["Vendas de Minério de Ferro"], name="Vendas (Mt)", marker_color="#00A859")])
            fig_fe.update_layout(
                barmode="group", bargap=0.15, hovermode="x unified", #agrupa as barras lado a lado e determina o espaço entre elas
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano", yaxis_title="Milhões de Toneladas (Mt)", height=400)
            st.plotly_chart(fig_fe, use_container_width=True)

            st.subheader("Cobre: Produção vs. Vendas (kt)")
            fig_cu = go.Figure([
                go.Bar(x=tabela_anual_p["Ano"], y=tabela_anual_p["Produção de Cobre"], name="Produção (kt)", marker_color="#D97706"),
                go.Bar(x=tabela_anual_p["Ano"], y=tabela_anual_p["Vendas de Cobre"], name="Vendas (kt)", marker_color="#059669")])
            fig_cu.update_layout(
                barmode="group", bargap=0.15, hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano", yaxis_title="Mil Toneladas (kt)", height=400)
            st.plotly_chart(fig_cu, use_container_width=True)

        with g_col2:
            st.subheader("Pelotas: Produção vs. Vendas (Mt)")
            fig_pel = go.Figure([
                go.Bar(x=tabela_anual_p["Ano"], y=tabela_anual_p["Produção de Pelotas"], name="Produção (Mt)", marker_color="#2563EB"),
                go.Bar(x=tabela_anual_p["Ano"], y=tabela_anual_p["Vendas de Pelotas"], name="Vendas (Mt)", marker_color="#10B981")])
            fig_pel.update_layout(
                barmode="group", bargap=0.15, hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano", yaxis_title="Milhões de Toneladas (Mt)", height=400)
            st.plotly_chart(fig_pel, use_container_width=True)

            st.subheader("Níquel: Produção vs. Vendas (kt)")
            fig_ni = go.Figure([
                go.Bar(x=tabela_anual_p["Ano"], y=tabela_anual_p["Produção de Níquel"], name="Produção (kt)", marker_color="#7C3AED"),
                go.Bar(x=tabela_anual_p["Ano"], y=tabela_anual_p["Vendas de Níquel"], name="Vendas (kt)", marker_color="#EC4899")])
            fig_ni.update_layout(
                barmode="group", bargap=0.15, hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano", yaxis_title="Mil Toneladas (kt)", height=400)
            st.plotly_chart(fig_ni, use_container_width=True)

    #VISÃO TRIMESTRAL DE PRODUÇÃO ==========================================

    else:
        #dicionário de Coordenadas Geográficas das Unidades Operacionais
        coords_vale = {
            "Serra Norte e Leste": {
                "lat": -6.0658,
                "lon": -50.1772,
                "regiao": "PA, Brasil",},
            "S11D": {"lat": -6.4026, "lon": -50.3664, "regiao": "PA, Brasil"},
            "Itabira": {"lat": -19.6178, "lon": -43.2269, "regiao": "MG, Brasil"},
            "Minas Centrais": {
                "lat": -19.9833,
                "lon": -43.8333,
                "regiao": "MG, Brasil",},
            "Mariana": {"lat": -20.3778, "lon": -43.4161, "regiao": "MG, Brasil"},
            "Paraopeba": {"lat": -20.1481, "lon": -44.1350, "regiao": "MG, Brasil"},
            "Vargem Grande": {
                "lat": -20.1472,
                "lon": -43.9861,
                "regiao": "MG, Brasil",},
            "Minas Itabirito": {
                "lat": -20.2528,
                "lon": -43.8033,
                "regiao": "MG, Brasil",},
            "Corumbá": {"lat": -19.0089, "lon": -57.6528, "regiao": "MS, Brasil"},
            "Sossego": {"lat": -6.4350, "lon": -50.0570, "regiao": "PA, Brasil"},
            "Salobo": {"lat": -5.7860, "lon": -50.5370, "regiao": "PA, Brasil"},
            "São Luís": {"lat": -2.5297, "lon": -44.3028, "regiao": "MA, Brasil"},
            "Tubarão 1 e 2": {
                "lat": -20.2858,
                "lon": -40.2447,
                "regiao": "ES, Brasil",},
            "Sudbury, Canadá": {
                "lat": 46.4900,
                "lon": -80.9900,
                "regiao": "Canadá",},
            "Thompson, Canadá": {
                "lat": 55.7433,
                "lon": -97.8558,
                "regiao": "Canadá",},
            "Voisey's Bay, Canadá": {
                "lat": 56.3340,
                "lon": -62.0890,
                "regiao": "Canadá",},
            "Indonésia": {"lat": -2.5500, "lon": 121.3500, "regiao": "Indonésia"},
            "Nova Caledônia": {
                "lat": -22.2700,
                "lon": 166.4500,
                "regiao": "Oceania",},
            "Omã": {"lat": 24.3600, "lon": 56.7100, "regiao": "Omã"},}

        def conv_vol(val):
            if pd.isna(val):
                return 0.0
            val_str = str(val).strip()
            
            #trata vírgula como separador decimal
            if "," in val_str:
                val_str = val_str.replace(".", "").replace(",", ".")
            
            try:
                num = float(val_str)
                #se for um inteiro puro sem ponto/vírgula >= 100 (ex: 978, 909, 145, 200),
                #significa que está em toneladas puras e precisa ser dividido por 1000 para virar Mil Toneladas
                if num >= 100 and "." not in val_str and "," not in str(val):
                    return num / 1000.0
                return num
            except ValueError:
                return 0.0

        tri_producao["Volume_Num"] = tri_producao["Extração (Mil Toneladas Métricas)"].apply(conv_vol)

        #2. filtros Superiores do Mapa
        c_f1, c_f2, c_f3 = st.columns([1, 1, 1])

        with c_f1:
            tri_prod_list = tri_producao["Trimestre"].dropna().unique().tolist()
            tri_prod_sel = st.selectbox(
                "Selecione o Trimestre:",
                options=tri_prod_list, #lista com os trimestres
                index=len(tri_prod_list) - 1,) #seleciona por padrão o trimestre mais recente

        with c_f2:
            prod_list = [
                "Todos os Produtos"] + tri_producao["Produto"].dropna().unique().tolist()
            prod_sel = st.selectbox("Filtrar por Produto:", options=prod_list)

        with c_f3:
            foco_mapa = st.radio(
                "Foco do Mapa:", ["Brasil", "Mundo"], horizontal=True)

        #3. filtragem de dados
        tabela_tri_p = tri_producao[tri_producao["Trimestre"] == tri_prod_sel].copy()

        totais_excluir = [
            "Total Norte",
            "Total Sudeste:",
            "Total Sul",
            "Total Centro-Oeste",
            "Produção Total de Minério de Ferro",
            "Total Canadá",
            "Produção Total de Níquel",
            "Total Brasil",
            "Produção Total de Cobre",
            "Total Sudeste",
            "Produção Pelotas",
            "Produção Total de Cobalto",]

        #cards de Resumo (KPIs) dinâmicos por trimestre
        st.markdown("### Resumo da Produção do Trimestre")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        def obter_total_prod(produto_nome):
            sub = tabela_tri_p[tabela_tri_p["Produto"] == produto_nome]
            if not sub.empty:
                return sub[~sub["Local"].isin(totais_excluir)]["Volume_Num"].sum()
            return 0.0

        with kpi1:
            st.metric(
                "Minério de Ferro",
                f"{obter_total_prod('Minério de Ferro'):,.1f} kt")
        with kpi2:
            st.metric(
                "Pelotas",
                f"{obter_total_prod('Pelotas'):,.1f} kt")
        with kpi3:
            st.metric(
                "Cobre",
                f"{obter_total_prod('Cobre'):,.1f} kt")
        with kpi4:
            st.metric(
                "Níquel",
                f"{obter_total_prod('Níquel'):,.1f} kt")

        #aplica filtro de produto selecionado após cálculo dos KPIs
        if prod_sel != "Todos os Produtos":
            tabela_tri_p_filtro = tabela_tri_p[tabela_tri_p["Produto"] == prod_sel].copy()
        else:
            tabela_tri_p_filtro = tabela_tri_p.copy()

        tabela_mapa = tabela_tri_p_filtro[~tabela_tri_p_filtro["Local"].isin(totais_excluir)].copy()

        #mapeia coordenadas geográficas
        tabela_mapa["lat"] = tabela_mapa["Local"].apply(
            lambda x: coords_vale.get(x, {}).get("lat", None))
        tabela_mapa["lon"] = tabela_mapa["Local"].apply(
            lambda x: coords_vale.get(x, {}).get("lon", None))
        tabela_mapa["regiao"] = tabela_mapa["Local"].apply(
            lambda x: coords_vale.get(x, {}).get("regiao", "Global"))

        tabela_mapa_valid = tabela_mapa.dropna(subset=["lat", "lon"]).copy()
        tabela_mapa_valid = tabela_mapa_valid[tabela_mapa_valid["Volume_Num"] > 0]

        #escala visual ajustada para visibilidade dos metais valiosos (Níquel e Cobre)
        tabela_mapa_valid["Tamanho_Bolha"] = tabela_mapa_valid["Volume_Num"].apply(lambda x: (x**0.35) + 5)

        #4. renderização do Mapa Principal
        st.subheader(f"Mapa de Operações e Unidades de Extração ({tri_prod_sel})")

        if not tabela_mapa_valid.empty:
            if foco_mapa == "Brasil":
                #filtra pontos em território brasileiro
                tabela_mapa_br = tabela_mapa_valid[tabela_mapa_valid["regiao"].str.contains("Brasil")].copy()

                if not tabela_mapa_br.empty:
                    fig_mapa = px.scatter_geo(
                        tabela_mapa_br,
                        lat="lat",
                        lon="lon",
                        size="Tamanho_Bolha",
                        color="Produto",
                        hover_name="Local",
                        hover_data={
                            "Volume_Num": ":,.1f",
                            "regiao": True,
                            "Tamanho_Bolha": False,
                            "lat": False,
                            "lon": False,},
                        labels={
                            "Volume_Num": "Extração (Mil Ton)",
                            "regiao": "Estado",},
                        size_max=28,
                        scope="south america",)

                    #ajusta a câmera para enquadrar O BRASIL INTEIRO com estados
                    fig_mapa.update_geos(
                        visible=True,
                        resolution=50,
                        showcoastlines=True,
                        coastlinecolor="#777777",
                        showland=True,
                        landcolor="#f8f9fa",
                        showcountries=True,
                        countrycolor="#444444",
                        countrywidth=1.5,
                        showsubunits=True,  #exibe a divisão dos estados
                        subunitcolor="#a0a0a0",
                        subunitwidth=1.0,
                        lonaxis_range=[-74, -34],  #enquadra a longitude do Brasil inteiro
                        lataxis_range=[-34, 6],)    #enquadra a latitude do Brasil inteiro
                else:
                    st.info(
                        "Nenhum ponto no Brasil encontrado para os filtros selecionados.")
                    fig_mapa = None
            else:
                fig_mapa = px.scatter_geo(
                    tabela_mapa_valid,
                    lat="lat",
                    lon="lon",
                    size="Tamanho_Bolha",
                    color="Produto",
                    hover_name="Local",
                    hover_data={
                        "Volume_Num": ":,.1f",
                        "regiao": True,
                        "Tamanho_Bolha": False,
                        "lat": False,
                        "lon": False,},
                    labels={
                        "Volume_Num": "Extração (Mil Ton)",
                        "regiao": "Localização",},
                    size_max=28,
                    projection="natural earth",)

                fig_mapa.update_geos(
                    showcountries=True,
                    countrycolor="lightgray",
                    projection_scale=1.1,)

            if fig_mapa is not None:
                fig_mapa.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=520,
                    legend=dict(orientation="h", y=1.05, x=0),)
                st.plotly_chart(fig_mapa, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para os filtros selecionados.")

        marcacao_preta()

        #5. painel Inferior: gráficos complementares
        c_p1, c_p2 = st.columns(2)

        with c_p1:
            st.subheader("Ranking de Extração por Unidade")
            tabela_bar = (
                tabela_mapa_valid.groupby("Local")["Volume_Num"]
                .sum().reset_index().sort_values(by="Volume_Num", ascending=True))

            fig_bar_prod = px.bar(
                tabela_bar,
                x="Volume_Num",
                y="Local",
                orientation="h",
                labels={
                    "Volume_Num": "Mil Toneladas Métricas",
                    "Local": "Unidade Operacional",},
                color_discrete_sequence=["#00A859"],)
            fig_bar_prod.update_layout(
                height=400, margin=dict(l=0, r=20, t=20, b=0))
            st.plotly_chart(fig_bar_prod, use_container_width=True)

        with c_p2:
            st.subheader("Participação da Produção por Mineral")
            tabela_pie = (
                tabela_tri_p_filtro[~tabela_tri_p_filtro["Local"].isin(totais_excluir)]
                .groupby("Produto")["Volume_Num"].sum().reset_index())

            fig_pie = px.pie(
                tabela_pie,
                values="Volume_Num",
                names="Produto",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2,)
            fig_pie.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)

    #EXPORTAÇÃO - PRODUÇÃO
    tabela_export_prod = tabela_anual_p.copy() if visao_prod == "Anual" else tri_producao[tri_producao["Trimestre"] == tri_prod_sel].copy()
    sufixo_prod = ano_sel if visao_prod == "Anual" else tri_prod_sel

    #EXPORTAÇÃO - PRODUÇÃO
    renderizar_painel_exportacao_producao(
        tabela_tri=tri_producao,
        tabela_anual=anual_producao,
        titulo_relatorio="Produção e Operações Vale S.A.",
        key_prefix="producao")

    # PREVISÃO DE OPERAÇÕES & INTELIGÊNCIA PREDITIVA (ML DE PRODUÇÃO) ==============
    marcacao_preta()

    st.subheader("🔮 Previsão de Operações & Inteligência Preditiva (ML)")
    st.markdown("##### Projeção Preditiva de Volume de Extração por Mineral (Sazonalidade & Tendência)")

    @st.cache_data
    def treinar_modelo_producao(tabela_prod_tri):
        df_p = tabela_prod_tri.copy()
        
        totais_excluir_ml = [
            "Total Norte", "Total Sudeste:", "Total Sul", "Total Centro-Oeste",
            "Produção Total de Minério de Ferro", "Total Canadá", "Produção Total de Níquel",
            "Total Brasil", "Produção Total de Cobre", "Total Sudeste", "Produção Pelotas",
            "Produção Total de Cobalto"
        ]
        
        # Tratamento de escala padronizado em Mt (Milhões de Toneladas)
        def _conv_vol_normalizado(val):
            if pd.isna(val): return 0.0
            val_str = str(val).strip()
            if "," in val_str:
                val_str = val_str.replace(".", "").replace(",", ".")
            try:
                num = float(val_str)
                if num >= 1000:
                    return num / 1000.0
                elif num >= 100 and "." not in val_str and "," not in str(val):
                    return num / 1000.0
                return num
            except ValueError:
                return 0.0

        df_p["Vol_Mt"] = df_p["Extração (Mil Toneladas Métricas)"].apply(_conv_vol_normalizado)
        df_clean = df_p[~df_p["Local"].isin(totais_excluir_ml)].copy()
        
        agg = df_clean.groupby(["Trimestre", "Produto"])["Vol_Mt"].sum().reset_index()
        
        # Ordena e cria features temporais
        trimestres_unicos = df_p["Trimestre"].dropna().unique().tolist()
        mapa_tempo = {tri: i for i, tri in enumerate(trimestres_unicos)}
        
        agg["Tempo_Idx"] = agg["Trimestre"].map(mapa_tempo)
        agg["Trimestre_Num"] = agg["Trimestre"].apply(lambda x: int(str(x)[0]) if str(x)[0].isdigit() else 1)
        
        # Treina modelo individual por produto
        modelos = {}
        r2_scores = {}
        ultimos_valores = {}
        
        for prod in agg["Produto"].unique():
            sub = agg[agg["Produto"] == prod].sort_values("Tempo_Idx")
            if len(sub) >= 4:
                X = sub[["Tempo_Idx", "Trimestre_Num"]]
                y = sub["Vol_Mt"]
                
                mdl = LinearRegression().fit(X, y)
                r2 = mdl.score(X, y)
                
                modelos[prod] = mdl
                r2_scores[prod] = max(0.0, r2)
                ultimos_valores[prod] = y.iloc[-1]
        
        return modelos, r2_scores, ultimos_valores, trimestres_unicos, agg

    modelos_prod, r2_prod, ultimos_vols, tri_historicos, df_agg_prod = treinar_modelo_producao(tri_producao)

    # 1. Controles de Simulação de Produção
    col_ml1, col_ml2 = st.columns([1, 2])

    with col_ml1:
        st.markdown("#### 🎛️ Parâmetros da Projeção")
        prod_ml_sel = st.selectbox(
            "Selecione o Mineral para Previsão:",
            options=list(modelos_prod.keys()),
            key="sb_prod_ml_sel"
        )
        
        qtd_tri_futuro = st.slider(
            "Horizonte de Previsão (Trimestres à Frente):",
            min_value=1,
            max_value=4,
            value=2,
            step=1,
            key="slider_horizonte_prod"
        )

    # 2. Execução das Predições
    if prod_ml_sel in modelos_prod:
        mdl_ativo = modelos_prod[prod_ml_sel]
        idx_ultimo = len(tri_historicos) - 1
        
        novas_projecoes = []
        
        for f in range(1, qtd_tri_futuro + 1):
            idx_fut = idx_ultimo + f
            ultimo_tri_str = tri_historicos[-1]
            tri_num_ult = int(ultimo_tri_str[0]) if ultimo_tri_str[0].isdigit() else 1
            ano_ult = int(ultimo_tri_str[-2:]) if len(ultimo_tri_str) >= 4 and ultimo_tri_str[-2:].isdigit() else 26
            
            proximo_tri_num = ((tri_num_ult + f - 1) % 4) + 1
            anos_adicionais = (tri_num_ult + f - 1) // 4
            proximo_ano = ano_ult + anos_adicionais
            
            label_futuro = f"{proximo_tri_num}T{proximo_ano:02d} (Prev)"
            
            X_fut = pd.DataFrame([[idx_fut, proximo_tri_num]], columns=["Tempo_Idx", "Trimestre_Num"])
            vol_est = max(0.0, float(mdl_ativo.predict(X_fut)[0]))
            
            novas_projecoes.append({"Trimestre": label_futuro, "Vol_Mt": vol_est})

        df_futuro = pd.DataFrame(novas_projecoes)
        
        # 3. KPIs Estimados
        with col_ml2:
            st.markdown(f"#### 📊 Projeção Estimada — {prod_ml_sel}")
            
            cols_kpi_ml = st.columns(len(df_futuro))
            vol_ult = ultimos_vols.get(prod_ml_sel, 1.0)
            
            for i, row in df_futuro.iterrows():
                v_est = row["Vol_Mt"]
                var_pct = ((v_est / vol_ult) - 1) * 100 if vol_ult > 0 else 0.0
                
                with cols_kpi_ml[i]:
                    st.metric(
                        label=f"Estimativa {row['Trimestre']}",
                        value=f"{v_est:,.1f} Mt",
                        delta=f"{var_pct:+.1f}% vs Último Tri"
                    )
            
            st.caption(f"**Acurácia Histórica (R² Score) para {prod_ml_sel}:** `{r2_prod.get(prod_ml_sel, 0)*100:.1f}%`")

        # 4. Gráfico Visual: Histórico Real + Projeções ML
        st.subheader(f"Evolução Histórica e Linha Preditiva ({prod_ml_sel})")
        
        sub_hist = df_agg_prod[df_agg_prod["Produto"] == prod_ml_sel].sort_values("Tempo_Idx")
        
        fig_prod_ml = go.Figure()

        # Linha de Histórico Real
        fig_prod_ml.add_trace(go.Scatter(
            x=sub_hist["Trimestre"],
            y=sub_hist["Vol_Mt"],
            mode="lines+markers",
            name="Produção Real (Mt)",
            line=dict(color="#00529B", width=2.5)
        ))

        # Conexão e Projeção Futura
        x_proj = [sub_hist["Trimestre"].iloc[-1]] + df_futuro["Trimestre"].tolist()
        y_proj = [sub_hist["Vol_Mt"].iloc[-1]] + df_futuro["Vol_Mt"].tolist()

        fig_prod_ml.add_trace(go.Scatter(
            x=x_proj,
            y=y_proj,
            mode="lines+markers",
            name="Projeção ML (Mt)",
            line=dict(color="#00A859", width=2.5, dash="dash"),
            marker=dict(size=9, symbol="star")
        ))

        fig_prod_ml.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1, title=""),
            xaxis_title="Trimestre",
            yaxis_title="Volume Extraído (Mt)",
            height=400
        )

        st.plotly_chart(fig_prod_ml, use_container_width=True)

#PÁGINA MERCADO =====================================================================================================

if pagina == "Mercado":
    st.title("Mercado e Economia")

    def conv_moeda(val): #limpeza de moeda
        if pd.isna(val):
            return None
        val_str = (
            str(val)
            .replace("US$", "")
            .replace("R$", "")
            .replace("$", "")
            .strip())
        if "," in val_str and "." in val_str:
            val_str = val_str.replace(".", "").replace(",", ".")
        elif "," in val_str:
            val_str = val_str.replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return None

    visao_merc = st.radio(
        "Selecione a Visão:", ["Trimestral", "Anual"], horizontal=True)

    #VISÃO ANUAL =========================================================

    if visao_merc == "Anual":
        tabela_anual_m = anual_mercado.copy()

        cols_num = tabela_anual_m.columns.drop("Ano")
        tabela_anual_m[cols_num] = tabela_anual_m[cols_num].map(conv_moeda)

        anos_list = tabela_anual_m["Ano"].unique().tolist()
        ano_sel = st.selectbox(
            "Selecione o Ano:", options=anos_list, index=len(anos_list) - 1)

        idx_sel = tabela_anual_m[tabela_anual_m["Ano"] == ano_sel].index[0]
        dados_ano = tabela_anual_m.loc[idx_sel]
        dados_ano_ant = tabela_anual_m.loc[idx_sel - 1] if idx_sel > 0 else None

        def calc_delta(coluna, prefixo="US$"):
            val_atual = dados_ano[coluna]
            if dados_ano_ant is not None and pd.notna(val_atual):
                val_ant = dados_ano_ant[coluna]
                if pd.notna(val_ant) and val_ant != 0:
                    diff = val_atual - val_ant
                    pct = diff / val_ant * 100
                    return (
                        f"{diff:+,.2f} ({pct:+,.1f}%) vs {dados_ano_ant['Ano']}")
            return "Sem dados do ano anterior"

        st.markdown(f"### Indicadores Anuais ({ano_sel})")
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.metric(
                "USD/BRL Médio",
                f"R$ {dados_ano['USD/BRL Médio']:,.2f}",
                delta=calc_delta("USD/BRL Médio", "R$"),)
        with k2:
            st.metric(
                "Preço Realizado Ferro",
                f"US$ {dados_ano['Preço Realizado Ferro']:,.2f}/t",
                delta=calc_delta("Preço Realizado Ferro"),)
        with k3:
            st.metric(
                "Preço Realizado Cobre",
                f"US$ {dados_ano['Preço Realizado Cobre']:,.2f}/t",
                delta=calc_delta("Preço Realizado Cobre"),)
        with k4:
            st.metric(
                "Preço Realizado Níquel",
                f"US$ {dados_ano['Preço Realizado Níquel']:,.2f}/t",
                delta=calc_delta("Preço Realizado Níquel"),)

        marcacao_preta()

        #gráficos Anuais
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("Minério de Ferro: Realizado Vale vs. Média Mundial")
            fig_fe_a = go.Figure([
                go.Bar(
                    x=tabela_anual_m["Ano"],
                    y=tabela_anual_m["Preço Realizado Ferro"],
                    name="Realizado Vale (USD/t)",
                    marker_color="#00529B",),
                go.Bar(
                    x=tabela_anual_m["Ano"],
                    y=tabela_anual_m["Preço Médio do Ferro (Mundial)"],
                    name="Média Mundial (BRL/t)",
                    marker_color="#00A859",),])
            fig_fe_a.update_layout(
                barmode="group",
                bargap=0.15,
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano",
                yaxis_title="Preço",
                height=400,)
            st.plotly_chart(fig_fe_a, use_container_width=True)

            st.subheader("Cobre: Realizado Vale vs. Média Mundial (USD/t)")
            fig_cu_a = go.Figure([
                go.Bar(
                    x=tabela_anual_m["Ano"],
                    y=tabela_anual_m["Preço Realizado Cobre"],
                    name="Realizado Vale",
                    marker_color="#D97706",),
                go.Bar(
                    x=tabela_anual_m["Ano"],
                    y=tabela_anual_m["Preço Médio do Cobre (Mundial)"],
                    name="Média Mundial",
                    marker_color="#059669",),])
            fig_cu_a.update_layout(
                barmode="group",
                bargap=0.15,
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano",
                yaxis_title="USD / Tonelada",
                height=400,)
            st.plotly_chart(fig_cu_a, use_container_width=True)

        with g2:
            st.subheader("Evolução Anual da Cotação do Dólar (USD/BRL)")
            fig_usd_a = px.line(
                tabela_anual_m,
                x="Ano",
                y="USD/BRL Médio",
                markers=True,
                color_discrete_sequence=["#2563EB"],
                labels={"USD/BRL Médio": "Cotação (R$)"},)
            fig_usd_a.update_layout(hovermode="x unified", height=400)
            st.plotly_chart(fig_usd_a, use_container_width=True)

            st.subheader("Níquel: Realizado Vale vs. Média Mundial (USD/t)")
            fig_ni_a = go.Figure([
                go.Bar(
                    x=tabela_anual_m["Ano"],
                    y=tabela_anual_m["Preço Realizado Níquel"],
                    name="Realizado Vale",
                    marker_color="#7C3AED",),
                go.Bar(
                    x=tabela_anual_m["Ano"],
                    y=tabela_anual_m["Preço Médio do Níquel (Mundial)"],
                    name="Média Mundial",
                    marker_color="#EC4899",),])
            fig_ni_a.update_layout(
                barmode="group",
                bargap=0.15,
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                xaxis_title="Ano",
                yaxis_title="USD / Tonelada",
                height=400,)
            st.plotly_chart(fig_ni_a, use_container_width=True)

        with st.expander(
            "Visualizar Tabela de Dados Brutos de Mercado (Anual)"):
            st.dataframe(tabela_anual_m, use_container_width=True)

    #VISÃO TRIMESTRAL =====================================================

    else:
        tabela_tri_m = tri_mercado.copy()

        cols_num = tabela_tri_m.columns.drop("Trimestre")
        tabela_tri_m[cols_num] = tabela_tri_m[cols_num].map(conv_moeda)

        tri_list = tabela_tri_m["Trimestre"].dropna().unique().tolist()
        tri_sel = st.selectbox(
            "Selecione o Trimestre:", options=tri_list, index=len(tri_list) - 1)

        idx_sel = tabela_tri_m[tabela_tri_m["Trimestre"] == tri_sel].index[0]
        dados_tri_m = tabela_tri_m.loc[idx_sel]

        st.markdown(f"### Indicadores do Trimestre ({tri_sel})")
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            val_dol = dados_tri_m["Média Trimestral Dólar (USD/BRL)"]
            st.metric(
                "Dólar Médio",
                f"R$ {val_dol:,.2f}" if pd.notna(val_dol) else "N/A",)
        with k2:
            val_fe = dados_tri_m["Preço Realizado Ferro/t"]
            st.metric(
                "Realizado Ferro",
                f"US$ {val_fe:,.2f}/t" if pd.notna(val_fe) else "N/A",)
        with k3:
            val_cu = dados_tri_m["Preço Realizado Cobre/t"]
            st.metric(
                "Realizado Cobre",
                f"US$ {val_cu:,.2f}/t" if pd.notna(val_cu) else "N/A",)
        with k4:
            val_ni = dados_tri_m["Preço Realizado Níquel/t"]
            st.metric(
                "Realizado Níquel",
                f"US$ {val_ni:,.2f}/t" if pd.notna(val_ni) else "N/A",)

        marcacao_preta()

        qtd_tri_m = st.slider(
            "Selecione a quantidade de trimestres nos gráficos:",
            min_value=3,
            max_value=len(tabela_tri_m),
            value=min(12, len(tabela_tri_m)),
            step=1,)

        tabela_tri_m_sub = tabela_tri_m.tail(qtd_tri_m)

        g1, g2 = st.columns(2)

        with g1:
            st.subheader(
                "Minério de Ferro: Realizado Vale vs. Mercado (USD/t)")
            fig_fe_t = go.Figure([
                go.Scatter(
                    x=tabela_tri_m_sub["Trimestre"],
                    y=tabela_tri_m_sub["Preço Realizado Ferro/t"],
                    name="Realizado Vale",
                    mode="lines+markers",
                    line=dict(color="#00529B", width=2.5),),
                go.Scatter(
                    x=tabela_tri_m_sub["Trimestre"],
                    y=tabela_tri_m_sub["Minério de Ferro"],
                    name="Mercado Mundial",
                    mode="lines+markers",
                    line=dict(color="#00A859", width=2.5),),])
            fig_fe_t.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                height=400,)
            st.plotly_chart(fig_fe_t, use_container_width=True)

            st.subheader("Cobre: Realizado Vale vs. Mercado (USD/t)")
            fig_cu_t = go.Figure([
                go.Scatter(
                    x=tabela_tri_m_sub["Trimestre"],
                    y=tabela_tri_m_sub["Preço Realizado Cobre/t"],
                    name="Realizado Vale",
                    mode="lines+markers",
                    line=dict(color="#D97706", width=2.5),),
                go.Scatter(
                    x=tabela_tri_m_sub["Trimestre"],
                    y=tabela_tri_m_sub["Cobre"],
                    name="Mercado Mundial",
                    mode="lines+markers",
                    line=dict(color="#059669", width=2.5),),])
            fig_cu_t.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                height=400,)
            st.plotly_chart(fig_cu_t, use_container_width=True)

        with g2:
            st.subheader("Evolução do Câmbio USD/BRL")
            fig_usd_t = px.line(
                tabela_tri_m_sub,
                x="Trimestre",
                y="Média Trimestral Dólar (USD/BRL)",
                markers=True,
                color_discrete_sequence=["#2563EB"],
                labels={"Média Trimestral Dólar (USD/BRL)": "R$"},)
            fig_usd_t.update_layout(hovermode="x unified", height=400)
            st.plotly_chart(fig_usd_t, use_container_width=True)

            st.subheader("Níquel: Realizado Vale vs. Mercado (USD/t)")
            fig_ni_t = go.Figure([
                go.Scatter(
                    x=tabela_tri_m_sub["Trimestre"],
                    y=tabela_tri_m_sub["Preço Realizado Níquel/t"],
                    name="Realizado Vale",
                    mode="lines+markers",
                    line=dict(color="#7C3AED", width=2.5),),
                go.Scatter(
                    x=tabela_tri_m_sub["Trimestre"],
                    y=tabela_tri_m_sub["Níquel"],
                    name="Mercado Mundial",
                    mode="lines+markers",
                    line=dict(color="#EC4899", width=2.5),),])
            fig_ni_t.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", y=1.1, title=""),
                height=400,)
            st.plotly_chart(fig_ni_t, use_container_width=True)
    
    #EXPORTAÇÃO - MERCADO
    renderizar_painel_exportacao_mercado(
        tabela_tri=tri_mercado,
        tabela_anual=anual_mercado,
        titulo_relatorio="Mercado e Economia Vale S.A.",
        key_prefix="mercado")

    #PREVISÃO DE MERCADO & INTELIGÊNCIA PREDITIVA (ML DE MERCADO) ==================
    marcacao_preta()

    st.subheader("🔮 Previsão de Mercado & Inteligência Preditiva (ML)")
    st.markdown("##### Modelo Preditivo de Preço Realizado Vale vs. Cotações Internacionais & Câmbio")

    @st.cache_data
    def treinar_modelo_mercado(tabela_merc_tri):
        df_m = tabela_merc_tri.copy()
        
        # Limpeza e conversão numérica das colunas de mercado
        cols_num = df_m.columns.drop("Trimestre")
        for c in cols_num:
            df_m[c] = df_m[c].apply(conv_moeda)

        df_m = df_m.dropna().reset_index(drop=True)
        
        # Features Temporais
        trimestres_unicos = df_m["Trimestre"].tolist()
        mapa_tempo = {tri: i for i, tri in enumerate(trimestres_unicos)}
        df_m["Tempo_Idx"] = df_m["Trimestre"].map(mapa_tempo)
        
        # Treinamento de Modelos Preditivos de Regressão por Commodity
        X_fe = df_m[["Minério de Ferro", "Média Trimestral Dólar (USD/BRL)"]]
        y_fe = df_m["Preço Realizado Ferro/t"]
        mdl_fe = LinearRegression().fit(X_fe, y_fe)
        r2_fe = max(0.0, mdl_fe.score(X_fe, y_fe))

        X_cu = df_m[["Cobre", "Média Trimestral Dólar (USD/BRL)"]]
        y_cu = df_m["Preço Realizado Cobre/t"]
        mdl_cu = LinearRegression().fit(X_cu, y_cu)
        r2_cu = max(0.0, mdl_cu.score(X_cu, y_cu))

        X_ni = df_m[["Níquel", "Média Trimestral Dólar (USD/BRL)"]]
        y_ni = df_m["Preço Realizado Níquel/t"]
        mdl_ni = LinearRegression().fit(X_ni, y_ni)
        r2_ni = max(0.0, mdl_ni.score(X_ni, y_ni))

        # Últimos valores registrados no mercado
        u_merc_fe = float(df_m["Minério de Ferro"].iloc[-1])
        u_real_fe = float(df_m["Preço Realizado Ferro/t"].iloc[-1])
        u_merc_cu = float(df_m["Cobre"].iloc[-1])
        u_real_cu = float(df_m["Preço Realizado Cobre/t"].iloc[-1])
        u_merc_ni = float(df_m["Níquel"].iloc[-1])
        u_real_ni = float(df_m["Preço Realizado Níquel/t"].iloc[-1])
        u_dolar_m = float(df_m["Média Trimestral Dólar (USD/BRL)"].iloc[-1])

        modelos = {"Minério de Ferro": mdl_fe, "Cobre": mdl_cu, "Níquel": mdl_ni}
        r2_scores = {"Minério de Ferro": r2_fe, "Cobre": r2_cu, "Níquel": r2_ni}
        
        return modelos, r2_scores, df_m, (u_merc_fe, u_real_fe, u_merc_cu, u_real_cu, u_merc_ni, u_real_ni, u_dolar_m)

    # Treina o modelo com o histórico trimestral de mercado
    modelos_merc, r2_merc, df_merc_clean, ultimos_m = treinar_modelo_mercado(tri_mercado)
    u_merc_fe, u_real_fe, u_merc_cu, u_real_cu, u_merc_ni, u_real_ni, u_dolar_m = ultimos_m

    # Definição dinâmica dos limites máximos dos sliders via NumPy
    max_dolar_slider = max(8.0, float(np.ceil(u_dolar_m * 1.2)))
    max_fe_slider = max(250.0, float(np.ceil(u_merc_fe * 1.3 / 10) * 10))
    max_cu_slider = max(20000.0, float(np.ceil(u_merc_cu * 1.3 / 500) * 500))
    max_ni_slider = max(45000.0, float(np.ceil(u_merc_ni * 1.3 / 1000) * 1000))

    # 1. Callback Functions para Cenários de Mercado
    def aplicar_cenario_mercado_base():
        st.session_state["slider_m_dol"] = float(round(u_dolar_m, 2))
        st.session_state["slider_m_fe"] = float(round(u_merc_fe, 2))
        st.session_state["slider_m_cu"] = float(round(u_merc_cu, 2))
        st.session_state["slider_m_ni"] = float(round(u_merc_ni, 2))

    def aplicar_cenario_mercado_otimista():
        st.session_state["slider_m_dol"] = float(round(u_dolar_m * 1.05, 2))
        st.session_state["slider_m_fe"] = float(min(round(u_merc_fe * 1.20, 2), max_fe_slider))
        st.session_state["slider_m_cu"] = float(min(round(u_merc_cu * 1.15, 2), max_cu_slider))
        st.session_state["slider_m_ni"] = float(min(round(u_merc_ni * 1.15, 2), max_ni_slider))

    def aplicar_cenario_mercado_pessimista():
        st.session_state["slider_m_dol"] = float(round(u_dolar_m * 0.95, 2))
        st.session_state["slider_m_fe"] = float(round(u_merc_fe * 0.80, 2))
        st.session_state["slider_m_cu"] = float(round(u_merc_cu * 0.85, 2))
        st.session_state["slider_m_ni"] = float(round(u_merc_ni * 0.85, 2))

    # 2. Inicialização do Session State
    if "slider_m_dol" not in st.session_state:
        st.session_state["slider_m_dol"] = float(round(u_dolar_m, 2))
    if "slider_m_fe" not in st.session_state:
        st.session_state["slider_m_fe"] = float(round(u_merc_fe, 2))
    if "slider_m_cu" not in st.session_state:
        st.session_state["slider_m_cu"] = float(round(u_merc_cu, 2))
    if "slider_m_ni" not in st.session_state:
        st.session_state["slider_m_ni"] = float(round(u_merc_ni, 2))

    # Ajuste de segurança no slider do Cobre
    st.session_state["slider_m_cu"] = min(float(st.session_state["slider_m_cu"]), max_cu_slider)

    # 3. Botões de Cenários de Mercado
    st.markdown("### 🎛️ Simulação de Cenários Globais de Commodities")
    c_m1, c_m2, c_m3 = st.columns(3)

    c_m1.button("🎯 Cenário Base (Atual)", on_click=aplicar_cenario_mercado_base, use_container_width=True)
    c_m2.button("🚀 Superciclo de Commodities (+20% Minério)", on_click=aplicar_cenario_mercado_otimista, use_container_width=True)
    c_m3.button("📉 Retração na Demanda Chinesa (-20% Minério)", on_click=aplicar_cenario_mercado_pessimista, use_container_width=True)

    # 4. Sliders de Parâmetros Globais
    st.subheader("Ajuste de Cotações Globais e Câmbio")
    sm_col1, sm_col2, sm_col3, sm_col4 = st.columns(4)

    with sm_col1:
        sim_m_dol = st.slider(
            "Cotação Dólar (USD/BRL):",
            min_value=float(3.50),
            max_value=max_dolar_slider,
            step=float(0.05),
            format="R\$ %.2f",
            key="slider_m_dol"
        )

    with sm_col2:
        sim_m_fe = st.slider(
            "Minério de Ferro Mundial (USD/t):",
            min_value=float(50.0),
            max_value=max_fe_slider,
            step=float(1.0),
            format="US\$ %.2f",
            key="slider_m_fe"
        )

    with sm_col3:
        sim_m_cu = st.slider(
            "Cobre Mundial (USD/t):",
            min_value=float(4000.0),
            max_value=max_cu_slider,
            step=float(100.0),
            format="US\$ %.0f",
            key="slider_m_cu"
        )

    with sm_col4:
        sim_m_ni = st.slider(
            "Níquel Mundial (USD/t):",
            min_value=float(5000.0),
            max_value=max_ni_slider,
            step=float(250.0),
            format="US\$ %.0f",
            key="slider_m_ni"
        )

    # 5. Predições em Tempo Real
    X_fe_pred = pd.DataFrame([[sim_m_fe, sim_m_dol]], columns=["Minério de Ferro", "Média Trimestral Dólar (USD/BRL)"])
    X_cu_pred = pd.DataFrame([[sim_m_cu, sim_m_dol]], columns=["Cobre", "Média Trimestral Dólar (USD/BRL)"])
    X_ni_pred = pd.DataFrame([[sim_m_ni, sim_m_dol]], columns=["Níquel", "Média Trimestral Dólar (USD/BRL)"])

    pred_real_fe = float(modelos_merc["Minério de Ferro"].predict(X_fe_pred)[0])
    pred_real_cu = float(modelos_merc["Cobre"].predict(X_cu_pred)[0])
    pred_real_ni = float(modelos_merc["Níquel"].predict(X_ni_pred)[0])

    # 6. Exibição dos KPIs Previstos
    st.subheader("Estimativa de Preços Realizados pela Vale S.A.")
    km1, km2, km3 = st.columns(3)

    premio_fe = ((pred_real_fe / sim_m_fe) - 1) * 100 if sim_m_fe > 0 else 0.0
    premio_cu = ((pred_real_cu / sim_m_cu) - 1) * 100 if sim_m_cu > 0 else 0.0
    premio_ni = ((pred_real_ni / sim_m_ni) - 1) * 100 if sim_m_ni > 0 else 0.0

    with km1:
        st.metric(
            label="Realizado Estimado — Minério de Ferro",
            value=f"US\$ {pred_real_fe:,.2f}/t",
            delta=f"{premio_fe:+.1f}% vs Preço Spot Mundial"
        )

    with km2:
        st.metric(
            label="Realizado Estimado — Cobre",
            value=f"US\$ {pred_real_cu:,.2f}/t",
            delta=f"{premio_cu:+.1f}% vs Preço Spot Mundial"
        )

    with km3:
        st.metric(
            label="Realizado Estimado — Níquel",
            value=f"US\$ {pred_real_ni:,.2f}/t",
            delta=f"{premio_ni:+.1f}% vs Preço Spot Mundial"
        )

    with st.expander("ℹ️ Métricas de Ajuste Estatístico dos Modelos de Mercado (R² Score)"):
        mc1, mc2, mc3 = st.columns(3)
        mc1.write(f"**R² Minério de Ferro:** `{r2_merc['Minério de Ferro']*100:.1f}%`")
        mc2.write(f"**R² Cobre:** `{r2_merc['Cobre']*100:.1f}%`")
        mc3.write(f"**R² Níquel:** `{r2_merc['Níquel']*100:.1f}%`")

    # 7. Gráfico Preditivo Interativo com Seletor de Mineral
    st.subheader("Comparativo Preditivo: Mercado Spot vs. Preço Realizado Vale")
    
    col_sel_graf, _ = st.columns([1, 2])
    with col_sel_graf:
        mineral_graf_sel = st.selectbox(
            "Selecione o Mineral para Visualizar no Gráfico:",
            options=["Minério de Ferro", "Cobre", "Níquel"],
            key="sb_merc_graf_mineral"
        )

    fig_m_proj = go.Figure()

    if mineral_graf_sel == "Minério de Ferro":
        col_spot = "Minério de Ferro"
        col_real = "Preço Realizado Ferro/t"
        pred_val = pred_real_fe
    elif mineral_graf_sel == "Cobre":
        col_spot = "Cobre"
        col_real = "Preço Realizado Cobre/t"
        pred_val = pred_real_cu
    else:
        col_spot = "Níquel"
        col_real = "Preço Realizado Níquel/t"
        pred_val = pred_real_ni

    # Linha Spot Mundial
    fig_m_proj.add_trace(go.Scatter(
        x=df_merc_clean["Trimestre"], y=df_merc_clean[col_spot],
        mode="lines+markers", name=f"{mineral_graf_sel} Spot Mundial", line=dict(color="#00A859", width=2)
    ))

    # Linha Realizado Vale
    fig_m_proj.add_trace(go.Scatter(
        x=df_merc_clean["Trimestre"], y=df_merc_clean[col_real],
        mode="lines+markers", name=f"{mineral_graf_sel} Realizado Vale", line=dict(color="#00529B", width=2.5)
    ))

    # Ponto de Projeção Simulada
    fig_m_proj.add_trace(go.Scatter(
        x=["Simulação Preditiva"], y=[pred_val],
        mode="markers", name="Realizado Projetado ML",
        marker=dict(color="#2563EB", size=15, symbol="star")
    ))

    fig_m_proj.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1, title=""),
        xaxis_title="Trimestre",
        yaxis_title="US\$ / Tonelada",
        height=420
    )

    st.plotly_chart(fig_m_proj, use_container_width=True)
