import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="Vale S.A. - Machine Learning", layout="wide")

# ============================================================
# CONVERSORES
# ============================================================

def para_bilhoes(val, limite_mm=100):
    if pd.isna(val):
        return np.nan
    try:
        v = float(str(val).replace(",", ".").strip())
    except ValueError:
        return np.nan
    return v / 1000.0 if abs(v) > limite_mm else v


def conv_preco(val):
    if pd.isna(val):
        return None
    val_str = (
        str(val)
        .replace("US$", "").replace("US", "").replace("R$", "")
        .replace("$", "").replace("€", "").replace("\x80", "")
        .strip().replace(",", "."))
    try:
        return float(val_str)
    except ValueError:
        return None


def conv_moeda(val):
    if pd.isna(val):
        return None
    val_str = str(val).replace("US$", "").replace("R$", "").replace("$", "").strip()
    if "," in val_str and "." in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    elif "," in val_str:
        val_str = val_str.replace(",", ".")
    try:
        return float(val_str)
    except ValueError:
        return None


def _conv_bi_inv(val):
    if pd.isna(val):
        return 0.0
    v = float(str(val).replace(",", ".").strip())
    return v / 1000.0 if abs(v) > 100.0 else v


def _conv_preco_inv(val):
    if pd.isna(val):
        return np.nan
    s = str(val).replace("US$", "").replace("R$", "").replace("$", "").replace(",", ".").strip()
    try:
        return float(s)
    except ValueError:
        return np.nan


def marcacao_preta():
    st.markdown(
        '<hr style="border: 1px solid #444; margin-top: 20px; margin-bottom: 20px;">',
        unsafe_allow_html=True)

# ============================================================
# CARREGAMENTO DOS CSVs
# ============================================================

totais_excluir = [
    "Total Norte", "Total Sudeste:", "Total Sul", "Total Centro-Oeste",
    "Produção Total de Minério de Ferro", "Total Canadá", "Produção Total de Níquel",
    "Total Brasil", "Produção Total de Cobre", "Total Sudeste", "Produção Pelotas",
    "Produção Total de Cobalto"]


@st.cache_data
def carregar_tri_financas():
    caminho = BASE_DIR / "dados_vale(Tri Financeiro)(2).csv"
    df = pd.read_csv(caminho, encoding="ISO-8859-1", sep=";", decimal=".")
    df.columns = df.columns.str.strip()
    df = df.dropna(axis=1, how="all").dropna(subset=["Trimestre"]).copy()
    cols_valor = ["Receita Líquida", "EBITDA", "Lucro Líquido",
                  "Fluxo de Caixa Operacional", "Fluxo de Caixa Livre",
                  "EBIT/ Resultado Operacional", "Dívida Líquida (MM)"]
    for c in cols_valor:
        if c in df.columns:
            df[c] = df[c].apply(para_bilhoes)
    return df


@st.cache_data
def carregar_tri_producao():
    caminho = BASE_DIR / "dados_vale(Tri Produção)(2).csv"
    df = pd.read_csv(caminho, encoding="ISO-8859-1", sep=";", decimal=".")
    df.columns = df.columns.str.strip()
    df = df.dropna(axis=1, how="all").dropna(subset=["Trimestre"]).copy()
    df["Produto"] = df["Produto"].astype(str).str.strip()
    df["Local"] = df["Local"].astype(str).str.strip()
    col_ext = df["Extração (Mil Toneladas Métricas)"].astype(str).str.replace(",", ".").str.strip()
    df["Extração (Mil Toneladas Métricas)"] = pd.to_numeric(col_ext, errors="coerce").fillna(0.0)
    return df


@st.cache_data
def carregar_tri_mercado():
    caminho = BASE_DIR / "dados_vale(Tri Mercado e Economia)(2).csv"
    df = pd.read_csv(caminho, encoding="ISO-8859-1", sep=";", decimal=".")
    df.columns = df.columns.str.strip()
    df = df.dropna(axis=1, how="all").dropna(subset=["Trimestre"]).copy()
    return df


def normalizar_producao(df):
    # minério de ferro trimestral vem em Mt em alguns trimestres; converte para kt
    col = "Extração (Mil Toneladas Métricas)"
    df = df.copy()
    folhas = ~df["Local"].isin(totais_excluir)
    fe = df["Produto"] == "Minério de Ferro"
    soma_fe = df[folhas & fe].groupby("Trimestre")[col].sum()
    tri_em_mt = soma_fe[soma_fe < 1000].index
    mascara = fe & df["Trimestre"].isin(tri_em_mt)
    df.loc[mascara, col] = df.loc[mascara, col] * 1000
    return df


tri_financas = carregar_tri_financas()
tri_producao = normalizar_producao(carregar_tri_producao())
tri_mercado = carregar_tri_mercado()

# ============================================================
# PÁGINA 1: ML FINANÇAS
# ============================================================

def pagina_financas():
    st.title("Machine Learning - Finanças")
    st.subheader("Previsões & Inteligência Preditiva (Simulador ML)")
    st.markdown("##### Simulador Financeiro Multi-Variável com Regressão Linear & Análise de Sensibilidade")

    @st.cache_data
    def treinar_modelo_financeiro_avancado(tabela_fin, tabela_merc, tabela_prod):
        tabela_f = tabela_fin.copy()
        tabela_f["Rec_Bi"] = tabela_f["Receita Líquida"].astype(float)
        tabela_f["Lucro_Bi"] = tabela_f["Lucro Líquido"].astype(float)
        tabela_f["EBITDA_Bi"] = tabela_f["EBITDA"].astype(float)

        tabela_m = tabela_merc.copy()
        tabela_m["Dolar_Num"] = tabela_m["Média Trimestral Dólar (BRL)"].apply(conv_preco)
        tabela_m["Minério_Num"] = tabela_m["Preço Realizado Ferro/t"].apply(conv_preco)

        sub_fe = tabela_prod[(tabela_prod["Produto"] == "Minério de Ferro") & (~tabela_prod["Local"].isin(totais_excluir))].copy()
        sub_fe["Vol_Mt"] = sub_fe["Extração (Mil Toneladas Métricas)"].astype(float) / 1000
        tabela_p_agg = sub_fe.groupby("Trimestre")["Vol_Mt"].sum().reset_index()

        m1 = pd.merge(tabela_f[["Trimestre", "Rec_Bi", "Lucro_Bi", "EBITDA_Bi"]], tabela_m[["Trimestre", "Dolar_Num", "Minério_Num"]], on="Trimestre")
        tabela_merged = pd.merge(m1, tabela_p_agg, on="Trimestre").dropna()

        X = tabela_merged[["Dolar_Num", "Minério_Num", "Vol_Mt"]]
        m_rec = LinearRegression().fit(X, tabela_merged["Rec_Bi"])
        m_ebitda = LinearRegression().fit(X, tabela_merged["EBITDA_Bi"])
        m_lucro = LinearRegression().fit(X, tabela_merged["Lucro_Bi"])

        r2_rec = m_rec.score(X, tabela_merged["Rec_Bi"])
        r2_ebitda = m_ebitda.score(X, tabela_merged["EBITDA_Bi"])
        r2_lucro = m_lucro.score(X, tabela_merged["Lucro_Bi"])

        u_dolar = float(tabela_merged["Dolar_Num"].iloc[-1])
        u_minerio = float(tabela_merged["Minério_Num"].iloc[-1])
        u_vol = float(tabela_merged["Vol_Mt"].iloc[-1])

        return m_rec, m_ebitda, m_lucro, u_dolar, u_minerio, u_vol, (r2_rec, r2_ebitda, r2_lucro), tabela_merged

    m_rec, m_ebitda, m_lucro, u_dolar, u_minerio, u_vol, (r2_rec, r2_ebitda, r2_lucro), tabela_treino = (
        treinar_modelo_financeiro_avancado(tri_financas, tri_mercado, tri_producao))

    def aplicar_cenario_base():
        st.session_state["slider_pred_dol"] = float(round(u_dolar, 2))
        st.session_state["slider_pred_min"] = float(round(u_minerio, 2))
        st.session_state["slider_pred_vol"] = float(max(round(u_vol, 1), 40.0))

    def aplicar_cenario_otimista():
        st.session_state["slider_pred_dol"] = float(round(u_dolar * 1.05, 2))
        st.session_state["slider_pred_min"] = float(round(u_minerio * 1.15, 2))
        st.session_state["slider_pred_vol"] = float(max(round(u_vol * 1.05, 1), 40.0))

    def aplicar_stress_test():
        st.session_state["slider_pred_dol"] = float(round(u_dolar * 0.95, 2))
        st.session_state["slider_pred_min"] = float(round(u_minerio * 0.75, 2))
        st.session_state["slider_pred_vol"] = float(max(round(u_vol * 0.95, 1), 40.0))

    def aplicar_alta_dolar():
        st.session_state["slider_pred_dol"] = float(6.20)
        st.session_state["slider_pred_min"] = float(round(u_minerio, 2))
        st.session_state["slider_pred_vol"] = float(max(round(u_vol, 1), 40.0))

    if "slider_pred_dol" not in st.session_state:
        st.session_state["slider_pred_dol"] = float(round(u_dolar, 2))
    if "slider_pred_min" not in st.session_state:
        st.session_state["slider_pred_min"] = float(round(u_minerio, 2))
    if "slider_pred_vol" not in st.session_state:
        st.session_state["slider_pred_vol"] = float(max(round(u_vol, 1), 40.0))
    else:
        st.session_state["slider_pred_vol"] = float(max(st.session_state["slider_pred_vol"], 40.0))

    st.markdown("### Cenários Estressados de Mercado")
    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.button("Cenário Base (Atual)", on_click=aplicar_cenario_base, use_container_width=True)
    cc2.button("Cenário Otimista (+15% Minério)", on_click=aplicar_cenario_otimista, use_container_width=True)
    cc3.button("Stress Test (-25% Minério)", on_click=aplicar_stress_test, use_container_width=True)
    cc4.button("Alta do Câmbio (Dólar R\\$ 6,20)", on_click=aplicar_alta_dolar, use_container_width=True)

    st.subheader("Ajuste Fino de Parâmetros de Simulação")
    s1, s2, s3 = st.columns(3)
    with s1:
        sim_dolar = st.slider("Cotação Estimada do Dólar (USD/BRL):", min_value=3.50, max_value=7.50,
                              step=0.05, format="R\\$ %.2f", key="slider_pred_dol")
    with s2:
        sim_minerio = st.slider("Preço do Minério de Ferro (USD/t):", min_value=50.0, max_value=220.0,
                                step=1.0, format="US\\$ %.2f", key="slider_pred_min")
    with s3:
        sim_vol = st.slider("Volume de Extração de Minério (Mt):", min_value=40.0, max_value=110.0,
                            step=0.5, format="%.1f Mt", key="slider_pred_vol")

    X_pred = pd.DataFrame([[sim_dolar, sim_minerio, sim_vol]], columns=["Dolar_Num", "Minério_Num", "Vol_Mt"])
    rec_prevista = m_rec.predict(X_pred)[0]
    ebitda_previsto = m_ebitda.predict(X_pred)[0]
    lucro_previsto = m_lucro.predict(X_pred)[0]

    st.subheader("Projeção do Resultado Financeiro Estimado")
    m1, m2, m3, m4 = st.columns(4)
    rec_ult = tabela_treino["Rec_Bi"].iloc[-1]
    ebitda_ult = tabela_treino["EBITDA_Bi"].iloc[-1]
    lucro_ult = tabela_treino["Lucro_Bi"].iloc[-1]

    with m1:
        st.metric("Receita Líquida Estimada", f"R\\$ {rec_prevista:,.2f} Bi",
                  delta=f"{((rec_prevista / rec_ult) - 1) * 100:+.1f}% vs. Último Tri")
    with m2:
        st.metric("EBITDA Estimado", f"R\\$ {ebitda_previsto:,.2f} Bi",
                  delta=f"{((ebitda_previsto / ebitda_ult) - 1) * 100:+.1f}% vs. Último Tri")
    with m3:
        st.metric("Lucro Líquido Estimado", f"R\\$ {lucro_previsto:,.2f} Bi",
                  delta=f"{((lucro_previsto / lucro_ult) - 1) * 100:+.1f}% vs. Último Tri")
    with m4:
        margem = (ebitda_previsto / rec_prevista * 100) if rec_prevista > 0 else 0.0
        st.metric("Margem EBITDA Estimada", f"{margem:.1f}%")

    with st.expander("Métricas de Acurácia Estatística dos Modelos (R² Score)"):
        a1, a2, a3 = st.columns(3)
        a1.write(f"**R² Receita Líquida:** `{r2_rec*100:.1f}%`")
        a2.write(f"**R² EBITDA:** `{r2_ebitda*100:.1f}%`")
        a3.write(f"**R² Lucro Líquido:** `{r2_lucro*100:.1f}%`")

    st.subheader("Comparativo Visual: Histórico Real vs. Simulação ML")
    tp = tabela_treino.copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tp["Trimestre"], y=tp["Rec_Bi"], mode="lines+markers",
                             name="Receita Real (Bi)", line=dict(color="#00529B", width=2.5)))
    fig.add_trace(go.Scatter(x=["Projeção (Simulada)"], y=[rec_prevista], mode="markers",
                             name="Receita Projetada", marker=dict(color="#2563EB", size=15, symbol="star")))
    fig.add_trace(go.Scatter(x=tp["Trimestre"], y=tp["EBITDA_Bi"], mode="lines+markers",
                             name="EBITDA Real (Bi)", line=dict(color="#F59E0B", width=2.5)))
    fig.add_trace(go.Scatter(x=["Projeção (Simulada)"], y=[ebitda_previsto], mode="markers",
                             name="EBITDA Projetado", marker=dict(color="#D97706", size=15, symbol="star")))
    fig.add_trace(go.Scatter(x=tp["Trimestre"], y=tp["Lucro_Bi"], mode="lines+markers",
                             name="Lucro Real (Bi)", line=dict(color="#00A859", width=2.5)))
    fig.add_trace(go.Scatter(x=["Projeção (Simulada)"], y=[lucro_previsto], mode="markers",
                             name="Lucro Projetado", marker=dict(color="#10B981", size=15, symbol="star")))
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1, title=""),
                      xaxis_title="Trimestre", yaxis_title="R\\$ (Bilhões)", height=420)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PÁGINA 2: ML MERCADO
# ============================================================

def pagina_mercado():
    st.title("Machine Learning - Mercado")
    st.subheader("Previsão de Mercado & Inteligência Preditiva (ML)")
    st.markdown("##### Modelo Preditivo de Preço Realizado Vale vs. Cotações Internacionais & Câmbio")

    @st.cache_data
    def treinar_modelo_mercado(tabela_merc_tri):
        df_m = tabela_merc_tri.copy()
        cols_num = df_m.columns.drop("Trimestre")
        for c in cols_num:
            df_m[c] = df_m[c].apply(conv_moeda)
        df_m = df_m.dropna().reset_index(drop=True)

        trimestres_unicos = df_m["Trimestre"].tolist()
        mapa_tempo = {tri: i for i, tri in enumerate(trimestres_unicos)}
        df_m["Tempo_Idx"] = df_m["Trimestre"].map(mapa_tempo)

        X_fe = df_m[["Minério de Ferro", "Média Trimestral Dólar (BRL)"]]
        mdl_fe = LinearRegression().fit(X_fe, df_m["Preço Realizado Ferro/t"])
        r2_fe = max(0.0, mdl_fe.score(X_fe, df_m["Preço Realizado Ferro/t"]))

        X_cu = df_m[["Cobre", "Média Trimestral Dólar (BRL)"]]
        mdl_cu = LinearRegression().fit(X_cu, df_m["Preço Realizado Cobre/t"])
        r2_cu = max(0.0, mdl_cu.score(X_cu, df_m["Preço Realizado Cobre/t"]))

        X_ni = df_m[["Níquel", "Média Trimestral Dólar (BRL)"]]
        mdl_ni = LinearRegression().fit(X_ni, df_m["Preço Realizado Níquel/t"])
        r2_ni = max(0.0, mdl_ni.score(X_ni, df_m["Preço Realizado Níquel/t"]))

        u_merc_fe = float(df_m["Minério de Ferro"].iloc[-1])
        u_real_fe = float(df_m["Preço Realizado Ferro/t"].iloc[-1])
        u_merc_cu = float(df_m["Cobre"].iloc[-1])
        u_real_cu = float(df_m["Preço Realizado Cobre/t"].iloc[-1])
        u_merc_ni = float(df_m["Níquel"].iloc[-1])
        u_real_ni = float(df_m["Preço Realizado Níquel/t"].iloc[-1])
        u_dolar_m = float(df_m["Média Trimestral Dólar (BRL)"].iloc[-1])

        modelos = {"Minério de Ferro": mdl_fe, "Cobre": mdl_cu, "Níquel": mdl_ni}
        r2_scores = {"Minério de Ferro": r2_fe, "Cobre": r2_cu, "Níquel": r2_ni}
        return modelos, r2_scores, df_m, (u_merc_fe, u_real_fe, u_merc_cu, u_real_cu, u_merc_ni, u_real_ni, u_dolar_m)

    modelos_merc, r2_merc, df_merc_clean, ultimos_m = treinar_modelo_mercado(tri_mercado)
    u_merc_fe, u_real_fe, u_merc_cu, u_real_cu, u_merc_ni, u_real_ni, u_dolar_m = ultimos_m

    max_dolar_slider = max(8.0, float(np.ceil(u_dolar_m * 1.2)))
    max_fe_slider = max(250.0, float(np.ceil(u_merc_fe * 1.3 / 10) * 10))
    max_cu_slider = max(20000.0, float(np.ceil(u_merc_cu * 1.3 / 500) * 500))
    max_ni_slider = max(45000.0, float(np.ceil(u_merc_ni * 1.3 / 1000) * 1000))

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

    if "slider_m_dol" not in st.session_state:
        st.session_state["slider_m_dol"] = float(round(u_dolar_m, 2))
    if "slider_m_fe" not in st.session_state:
        st.session_state["slider_m_fe"] = float(round(u_merc_fe, 2))
    if "slider_m_cu" not in st.session_state:
        st.session_state["slider_m_cu"] = float(round(u_merc_cu, 2))
    if "slider_m_ni" not in st.session_state:
        st.session_state["slider_m_ni"] = float(round(u_merc_ni, 2))
    st.session_state["slider_m_cu"] = min(float(st.session_state["slider_m_cu"]), max_cu_slider)

    st.markdown("### Simulação de Cenários Globais de Commodities")
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.button("Cenário Base (Atual)", on_click=aplicar_cenario_mercado_base, use_container_width=True)
    c_m2.button("Superciclo de Commodities (+20% Minério)", on_click=aplicar_cenario_mercado_otimista, use_container_width=True)
    c_m3.button("Retração na Demanda Chinesa (-20% Minério)", on_click=aplicar_cenario_mercado_pessimista, use_container_width=True)

    st.subheader("Ajuste de Cotações Globais e Câmbio")
    sm1, sm2, sm3, sm4 = st.columns(4)
    with sm1:
        sim_m_dol = st.slider("Cotação Dólar (USD/BRL):", min_value=3.50, max_value=max_dolar_slider,
                              step=0.05, format="R\\$ %.2f", key="slider_m_dol")
    with sm2:
        sim_m_fe = st.slider("Minério de Ferro Mundial (USD/t):", min_value=50.0, max_value=max_fe_slider,
                             step=1.0, format="US\\$ %.2f", key="slider_m_fe")
    with sm3:
        sim_m_cu = st.slider("Cobre Mundial (USD/t):", min_value=4000.0, max_value=max_cu_slider,
                             step=100.0, format="US\\$ %.0f", key="slider_m_cu")
    with sm4:
        sim_m_ni = st.slider("Níquel Mundial (USD/t):", min_value=5000.0, max_value=max_ni_slider,
                             step=250.0, format="US\\$ %.0f", key="slider_m_ni")

    X_fe_pred = pd.DataFrame([[sim_m_fe, sim_m_dol]], columns=["Minério de Ferro", "Média Trimestral Dólar (BRL)"])
    X_cu_pred = pd.DataFrame([[sim_m_cu, sim_m_dol]], columns=["Cobre", "Média Trimestral Dólar (BRL)"])
    X_ni_pred = pd.DataFrame([[sim_m_ni, sim_m_dol]], columns=["Níquel", "Média Trimestral Dólar (BRL)"])

    pred_real_fe = float(modelos_merc["Minério de Ferro"].predict(X_fe_pred)[0])
    pred_real_cu = float(modelos_merc["Cobre"].predict(X_cu_pred)[0])
    pred_real_ni = float(modelos_merc["Níquel"].predict(X_ni_pred)[0])

    st.subheader("Estimativa de Preços Realizados pela Vale S.A.")
    km1, km2, km3 = st.columns(3)
    premio_fe = ((pred_real_fe / sim_m_fe) - 1) * 100 if sim_m_fe > 0 else 0.0
    premio_cu = ((pred_real_cu / sim_m_cu) - 1) * 100 if sim_m_cu > 0 else 0.0
    premio_ni = ((pred_real_ni / sim_m_ni) - 1) * 100 if sim_m_ni > 0 else 0.0

    with km1:
        st.metric("Realizado Estimado — Minério de Ferro", f"US\\$ {pred_real_fe:,.2f}/t",
                  delta=f"{premio_fe:+.1f}% vs Preço Spot Mundial")
    with km2:
        st.metric("Realizado Estimado — Cobre", f"US\\$ {pred_real_cu:,.2f}/t",
                  delta=f"{premio_cu:+.1f}% vs Preço Spot Mundial")
    with km3:
        st.metric("Realizado Estimado — Níquel", f"US\\$ {pred_real_ni:,.2f}/t",
                  delta=f"{premio_ni:+.1f}% vs Preço Spot Mundial")

    with st.expander("Métricas de Ajuste Estatístico dos Modelos de Mercado (R² Score)"):
        mc1, mc2, mc3 = st.columns(3)
        mc1.write(f"**R² Minério de Ferro:** `{r2_merc['Minério de Ferro']*100:.1f}%`")
        mc2.write(f"**R² Cobre:** `{r2_merc['Cobre']*100:.1f}%`")
        mc3.write(f"**R² Níquel:** `{r2_merc['Níquel']*100:.1f}%`")

    st.subheader("Comparativo Preditivo: Mercado Spot vs. Preço Realizado Vale")
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        mineral_sel = st.selectbox("Selecione o Mineral para Visualizar no Gráfico:",
                                   options=["Minério de Ferro", "Cobre", "Níquel"],
                                   key="sb_merc_graf_mineral")

    if mineral_sel == "Minério de Ferro":
        col_spot, col_real, pred_val = "Minério de Ferro", "Preço Realizado Ferro/t", pred_real_fe
    elif mineral_sel == "Cobre":
        col_spot, col_real, pred_val = "Cobre", "Preço Realizado Cobre/t", pred_real_cu
    else:
        col_spot, col_real, pred_val = "Níquel", "Preço Realizado Níquel/t", pred_real_ni

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_merc_clean["Trimestre"], y=df_merc_clean[col_spot], mode="lines+markers",
                             name=f"{mineral_sel} Spot Mundial", line=dict(color="#00A859", width=2)))
    fig.add_trace(go.Scatter(x=df_merc_clean["Trimestre"], y=df_merc_clean[col_real], mode="lines+markers",
                             name=f"{mineral_sel} Realizado Vale", line=dict(color="#00529B", width=2.5)))
    fig.add_trace(go.Scatter(x=["Simulação Preditiva"], y=[pred_val], mode="markers",
                             name="Realizado Projetado ML",
                             marker=dict(color="#2563EB", size=15, symbol="star")))
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1, title=""),
                      xaxis_title="Trimestre", yaxis_title="US\\$ / Tonelada", height=420)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PÁGINA 3: ML PRODUÇÃO
# ============================================================

def pagina_producao():
    st.title("Machine Learning - Produção")
    st.subheader("Previsão de Operações & Inteligência Preditiva (ML)")
    st.markdown("##### Projeção Preditiva de Volume de Extração por Mineral (Sazonalidade & Tendência)")

    @st.cache_data
    def treinar_modelo_producao(tabela_prod_tri):
        df_p = tabela_prod_tri.copy()
        df_p["Vol_Mt"] = df_p["Extração (Mil Toneladas Métricas)"].astype(float)
        df_clean = df_p[~df_p["Local"].isin(totais_excluir)].copy()

        agg = df_clean.groupby(["Trimestre", "Produto"])["Vol_Mt"].sum().reset_index()

        trimestres_unicos = df_p["Trimestre"].dropna().unique().tolist()
        mapa_tempo = {tri: i for i, tri in enumerate(trimestres_unicos)}

        agg["Tempo_Idx"] = agg["Trimestre"].map(mapa_tempo)
        agg["Trimestre_Num"] = agg["Trimestre"].apply(lambda x: int(str(x)[0]) if str(x)[0].isdigit() else 1)

        modelos, r2_scores, ultimos_valores = {}, {}, {}
        for prod in agg["Produto"].unique():
            sub = agg[agg["Produto"] == prod].sort_values("Tempo_Idx")
            if len(sub) >= 4:
                X = sub[["Tempo_Idx", "Trimestre_Num"]]
                y = sub["Vol_Mt"]
                mdl = LinearRegression().fit(X, y)
                modelos[prod] = mdl
                r2_scores[prod] = max(0.0, mdl.score(X, y))
                ultimos_valores[prod] = y.iloc[-1]

        return modelos, r2_scores, ultimos_valores, trimestres_unicos, agg

    modelos_prod, r2_prod, ultimos_vols, tri_historicos, df_agg_prod = treinar_modelo_producao(tri_producao)

    col_ml1, col_ml2 = st.columns([1, 2])

    with col_ml1:
        st.markdown("#### Parâmetros da Projeção")
        prod_ml_sel = st.selectbox("Selecione o Mineral para Previsão:",
                                   options=list(modelos_prod.keys()), key="sb_prod_ml_sel")
        qtd_tri_futuro = st.slider("Horizonte de Previsão (Trimestres à Frente):",
                                   min_value=1, max_value=4, value=2, step=1,
                                   key="slider_horizonte_prod")

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

        with col_ml2:
            st.markdown(f"#### Projeção Estimada - {prod_ml_sel}")
            cols_kpi = st.columns(len(df_futuro))
            vol_ult = ultimos_vols.get(prod_ml_sel, 1.0)

            for i, row in df_futuro.iterrows():
                v_est = row["Vol_Mt"]
                var_pct = ((v_est / vol_ult) - 1) * 100 if vol_ult > 0 else 0.0
                with cols_kpi[i]:
                    st.metric(f"Estimativa {row['Trimestre']}", f"{v_est:,.1f} kt",
                              delta=f"{var_pct:+.1f}% vs Último Tri")

            st.caption(f"**Acurácia Histórica (R² Score) para {prod_ml_sel}:** `{r2_prod.get(prod_ml_sel, 0)*100:.1f}%`")

        st.subheader(f"Evolução Histórica e Linha Preditiva ({prod_ml_sel})")
        sub_hist = df_agg_prod[df_agg_prod["Produto"] == prod_ml_sel].sort_values("Tempo_Idx")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sub_hist["Trimestre"], y=sub_hist["Vol_Mt"], mode="lines+markers",
                                 name="Produção Real (kt)", line=dict(color="#00529B", width=2.5)))
        x_proj = [sub_hist["Trimestre"].iloc[-1]] + df_futuro["Trimestre"].tolist()
        y_proj = [sub_hist["Vol_Mt"].iloc[-1]] + df_futuro["Vol_Mt"].tolist()
        fig.add_trace(go.Scatter(x=x_proj, y=y_proj, mode="lines+markers", name="Projeção ML (kt)",
                                 line=dict(color="#00A859", width=2.5, dash="dash"),
                                 marker=dict(size=9, symbol="star")))
        fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1, title=""),
                          xaxis_title="Trimestre", yaxis_title="Volume Extraído (kt)", height=400)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PÁGINA 4: ML INVESTIDORES
# ============================================================

def pagina_investidores():
    st.title("Machine Learning - Investidores")
    st.subheader("Modelo Preditivo de Valuation - Preço Justo Estimado (VALE3 & VALE ADR)")
    st.markdown("##### Regressão Linear Múltipla treinada com Fundamentos Trimestrais (Minério, Câmbio, Receita e FCL)")

    def treinar_valuation_ml(t_fin, t_merc):
        df_f = t_fin.dropna(subset=["Trimestre"]).copy()
        df_f["Rec_Bi"] = df_f["Receita Líquida"].apply(_conv_bi_inv)
        df_f["FCL_Bi"] = df_f["Fluxo de Caixa Livre"].apply(_conv_bi_inv)
        df_f["VALE3"] = df_f["VALE3 (B3 - BRL)"].apply(_conv_preco_inv)
        df_f["VALE_USD"] = df_f["VALE (NYSE - USD)"].apply(_conv_preco_inv)

        df_m = t_merc.dropna(subset=["Trimestre"]).copy()
        df_m["Ferro"] = df_m["Preço Realizado Ferro/t"].apply(_conv_preco_inv)
        df_m["Dolar"] = df_m["Média Trimestral Dólar (BRL)"].apply(_conv_preco_inv)

        df_ml = pd.merge(
            df_f[["Trimestre", "Rec_Bi", "FCL_Bi", "VALE3", "VALE_USD"]],
            df_m[["Trimestre", "Ferro", "Dolar"]],
            on="Trimestre").dropna()

        X = df_ml[["Ferro", "Dolar", "Rec_Bi", "FCL_Bi"]]
        mdl_v3 = LinearRegression().fit(X, df_ml["VALE3"])
        mdl_usd = LinearRegression().fit(X, df_ml["VALE_USD"])
        r2_v3 = mdl_v3.score(X, df_ml["VALE3"])
        r2_usd = mdl_usd.score(X, df_ml["VALE_USD"])
        return mdl_v3, mdl_usd, r2_v3, r2_usd, df_ml

    mdl_v3, mdl_usd, r2_v3, r2_usd, df_ml_inv = treinar_valuation_ml(tri_financas, tri_mercado)

    ult_ferro = float(df_ml_inv["Ferro"].iloc[-1])
    ult_dolar = float(df_ml_inv["Dolar"].iloc[-1])
    ult_rec = float(df_ml_inv["Rec_Bi"].iloc[-1])
    ult_fcl = float(df_ml_inv["FCL_Bi"].iloc[-1])
    cotacao_atual_v3 = float(df_ml_inv["VALE3"].iloc[-1])
    cotacao_atual_usd = float(df_ml_inv["VALE_USD"].iloc[-1])

    def _set_val_conservador():
        st.session_state["inv_sim_ferro"] = float(round(ult_ferro * 0.80, 1))
        st.session_state["inv_sim_dolar"] = float(round(ult_dolar * 0.95, 2))
        st.session_state["inv_sim_rec"] = float(round(ult_rec * 0.85, 1))
        st.session_state["inv_sim_fcl"] = float(round(ult_fcl * 0.80, 1))

    def _set_val_base():
        st.session_state["inv_sim_ferro"] = float(round(ult_ferro, 1))
        st.session_state["inv_sim_dolar"] = float(round(ult_dolar, 2))
        st.session_state["inv_sim_rec"] = float(round(ult_rec, 1))
        st.session_state["inv_sim_fcl"] = float(round(ult_fcl, 1))

    def _set_val_superciclo():
        st.session_state["inv_sim_ferro"] = float(round(ult_ferro * 1.25, 1))
        st.session_state["inv_sim_dolar"] = float(round(ult_dolar * 1.05, 2))
        st.session_state["inv_sim_rec"] = float(round(ult_rec * 1.20, 1))
        st.session_state["inv_sim_fcl"] = float(round(ult_fcl * 1.30, 1))

    if "inv_sim_ferro" not in st.session_state:
        _set_val_base()

    b1, b2, b3 = st.columns(3)
    b1.button("Cenário Conservador (-20% Ferro)", on_click=_set_val_conservador, use_container_width=True)
    b2.button("Cenário Base (Premissas Atuais)", on_click=_set_val_base, use_container_width=True)
    b3.button("Superciclo Commodities (+25% Ferro)", on_click=_set_val_superciclo, use_container_width=True)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        p_ferro = st.slider("Minério Realizado (US$/t):", 50.0, 200.0, step=1.0, key="inv_sim_ferro")
    with s2:
        p_dolar = st.slider("Câmbio (USD/BRL):", 3.50, 7.50, step=0.05, key="inv_sim_dolar")
    with s3:
        p_rec = st.slider("Receita Trimestral (R$ Bi):", 25.0, 100.0, step=1.0, key="inv_sim_rec")
    with s4:
        p_fcl = st.slider("Fluxo Caixa Livre (R$ Bi):", 0.0, 35.0, step=0.5, key="inv_sim_fcl")

    X_cenario = pd.DataFrame([[p_ferro, p_dolar, p_rec, p_fcl]], columns=["Ferro", "Dolar", "Rec_Bi", "FCL_Bi"])
    preco_justo_v3 = max(10.0, float(mdl_v3.predict(X_cenario)[0]))
    preco_justo_usd = max(2.0, float(mdl_usd.predict(X_cenario)[0]))

    upside_v3 = ((preco_justo_v3 / cotacao_atual_v3) - 1) * 100
    upside_usd = ((preco_justo_usd / cotacao_atual_usd) - 1) * 100

    st.markdown("#### Resultado do Valuation Estimado vs. Cotação Atual")
    v1, v2, v3, v4 = st.columns(4)
    with v1:
        st.metric("Cotação Atual VALE3 (B3)", f"R$ {cotacao_atual_v3:,.2f}")
    with v2:
        st.metric("Preço Justo VALE3 (ML)", f"R$ {preco_justo_v3:,.2f}", delta=f"{upside_v3:+.1f}% Potencial (Upside)")
    with v3:
        st.metric("Preço Justo VALE ADR (NYSE)", f"US$ {preco_justo_usd:,.2f}", delta=f"{upside_usd:+.1f}% Potencial (Upside)")
    with v4:
        st.metric("Aderência do Modelo (R²)", f"{r2_v3 * 100:.1f}%",
                  help="Percentual da variação histórica de VALE3 explicada pelos fundamentos.")

    df_ml_inv["VALE3_Modelo_Hist"] = mdl_v3.predict(df_ml_inv[["Ferro", "Dolar", "Rec_Bi", "FCL_Bi"]])

    fig_val = go.Figure()
    fig_val.add_trace(go.Scatter(x=df_ml_inv["Trimestre"], y=df_ml_inv["VALE3"], mode="lines+markers",
                                 name="Cotação Real VALE3 (R$)", line=dict(color="#00529B", width=2.5)))
    fig_val.add_trace(go.Scatter(x=df_ml_inv["Trimestre"], y=df_ml_inv["VALE3_Modelo_Hist"], mode="lines",
                                 name="Preço Justo Histórico (Modelo ML)",
                                 line=dict(color="#94A3B8", width=2, dash="dash")))
    fig_val.add_trace(go.Scatter(x=["Cenário Simulado"], y=[preco_justo_v3], mode="markers+text",
                                 text=[f"R$ {preco_justo_v3:.2f}"], textposition="top center",
                                 name="Preço-Alvo Projetado (ML)",
                                 marker=dict(color="#00A859", size=16, symbol="star")))
    fig_val.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.12, title=""),
                          xaxis_title="Trimestre", yaxis_title="Preço da Ação VALE3 (R$)", height=420)
    st.plotly_chart(fig_val, use_container_width=True)

    marcacao_preta()

    st.subheader("Simulador de Aporte do Investidor")
    c_ap1, c_ap2, c_ap3 = st.columns(3)
    with c_ap1:
        valor_aporte = st.number_input("Valor do Investimento Inicial (R$):", min_value=100.0,
                                       max_value=10000000.0, value=10000.0, step=1000.0)

    qtd_acoes = valor_aporte / cotacao_atual_v3
    valor_projetado = qtd_acoes * preco_justo_v3
    lucro_estimado = valor_projetado - valor_aporte

    with c_ap2:
        st.metric("Quantidade Estimada de Ações", f"{qtd_acoes:,.1f} ações VALE3")
    with c_ap3:
        st.metric("Patrimônio Projetado no Cenário", f"R$ {valor_projetado:,.2f}",
                  delta=f"R$ {lucro_estimado:+,.2f} ({upside_v3:+.1f}%)")

# ============================================================
# NAVEGAÇÃO
# ============================================================

st.sidebar.title("Machine Learning - Vale S.A.")
pagina = st.sidebar.radio(
    "Escolha uma página:",
    ["ML Finanças", "ML Mercado", "ML Produção", "ML Investidores"])

st.sidebar.markdown("---")
st.sidebar.write("Todos os dados foram retirados de fontes oficiais da Vale S.A.")

if pagina == "ML Finanças":
    pagina_financas()
elif pagina == "ML Mercado":
    pagina_mercado()
elif pagina == "ML Produção":
    pagina_producao()
else:
    pagina_investidores()
