"""
app.py — Sistema Prates Sublimação v5
Leve, rápido e visual limpo.
Execute com: python -m streamlit run app.py
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime
import plotly.express as px
import plotly.graph_objects as go
import base64, os

from database import (
    init_db, get_parametros, set_parametro,
    get_fornecedores, update_fornecedor, get_preco_kg, add_fornecedor,
    get_faccionistas, update_faccionista, get_preco_costura,
    get_skus, upsert_sku,
    get_relatorio_mensal, add_registro_mensal, delete_registro_mensal,
    get_historico, add_historico,
)
from calculadora import (
    calcular_sku_completo, calcular_manual, calcular_lote,
    gerar_tabela_catalogo, resumo_dashboard,
)

st.set_page_config(
    page_title="Prates Sublimação",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_db()

@st.cache_data(show_spinner=False)
def get_logo():
    if os.path.exists("logo.png"):
        with open("logo.png","rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

_LOGO = get_logo()

# CSS limpo e leve
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0d1117; }
[data-testid="stSidebar"] * { color: #e6e6e6 !important; }
[data-testid="stAppViewContainer"] { background: #0a0e1a; }
.stButton > button {
    background: #00c04b; color: white; border: none;
    border-radius: 6px; font-weight: 600;
    transition: background 0.2s;
}
.stButton > button:hover { background: #00a03e; }
[data-testid="stMetric"] {
    background: #111827; border-radius: 8px;
    padding: 14px 16px; border: 1px solid #1e2d45;
}
[data-testid="stMetricValue"] { color: #e8f0fe !important; }
[data-testid="stMetricLabel"] { color: #6b7a90 !important; font-size: 12px !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #00c04b !important; border-bottom: 2px solid #00c04b !important;
}
.card-v { background:#0f1f12; border-radius:8px; padding:16px; border:1px solid #00c04b33; text-align:center; }
.card-v h4 { margin:0; font-size:11px; color:#4a7a5a; text-transform:uppercase; }
.card-v p  { margin:6px 0 0; font-size:22px; font-weight:700; color:#00c04b; }
.card-c { background:#111827; border-radius:8px; padding:16px; border:1px solid #1e2d45; text-align:center; }
.card-c h4 { margin:0; font-size:11px; color:#4a5a6a; text-transform:uppercase; }
.card-c p  { margin:6px 0 0; font-size:22px; font-weight:700; color:#c8d6e8; }
.card-a { background:#1f0f0f; border-radius:8px; padding:16px; border:1px solid #e05c5c33; text-align:center; }
.card-a h4 { margin:0; font-size:11px; color:#7a4a4a; text-transform:uppercase; }
.card-a p  { margin:6px 0 0; font-size:22px; font-weight:700; color:#e05c5c; }
.sec { font-size:13px; font-weight:600; color:#6b7a90; text-transform:uppercase; letter-spacing:1px; margin:16px 0 8px; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    if _LOGO:
        st.markdown(
            f'<div style="text-align:center;padding:12px 4px 4px">'
            f'<img src="data:image/png;base64,{_LOGO}" width="140" '
            f'style="border-radius:8px"></div>',
            unsafe_allow_html=True
        )
    st.markdown("---")
    pagina = st.radio("", [
        "📊 Dashboard","🧮 Simulador de Preço","🔄 Margem Reversa",
        "📦 Simulador de Lote","📤 Tabela para Cliente",
        "📈 Relatório Mensal","⚙️ Configurações",
        "📋 Histórico de Preços","📥 Importar Planilha",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.caption("Prates Sublimação · Macaé/RJ · v5.0")

# Helpers
def fmt(v):
    if v is None: return "—"
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
def fpct(v): return f"{v*100:.1f}%"
def cv(l,v): return f'<div class="card-v"><h4>{l}</h4><p>{fmt(v)}</p></div>'
def cc(l,v): return f'<div class="card-c"><h4>{l}</h4><p>{fmt(v)}</p></div>'
def ca(l,v): return f'<div class="card-a"><h4>{l}</h4><p>{fmt(v)}</p></div>'
def sec(t): st.markdown(f'<p class="sec">{t}</p>', unsafe_allow_html=True)
def titulo(t):
    st.markdown(f'<h2 style="color:#00c04b;border-bottom:2px solid #00c04b33;padding-bottom:8px;margin-bottom:20px">{t}</h2>', unsafe_allow_html=True)

@st.cache_data(ttl=30, show_spinner=False)
def catalogo_cache():
    return gerar_tabela_catalogo()

def get_opcoes():
    s = get_skus()
    return s, sorted(set(x['modelo'] for x in s)), sorted(set(x['tecido'] for x in s))
def cores(s,m,t): return sorted(set(x['cor'] for x in s if x['modelo']==m and x['tecido']==t))
def tams(s,m,t,c): return sorted(set(x['tamanho'] for x in s if x['modelo']==m and x['tecido']==t and x['cor']==c))

CHART = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
             font_color='#8899b0', height=220, margin=dict(l=10,r=10,t=30,b=10))

# ══ DASHBOARD ══════════════════════════════
if pagina=="📊 Dashboard":
    titulo("📊 Dashboard")
    kpis = resumo_dashboard()
    if not kpis:
        st.warning("Nenhum SKU cadastrado.")
    else:
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        c1.metric("Total SKUs", kpis['total_skus'])
        c2.metric("Menor Custo", fmt(kpis['menor_custo']))
        c3.metric("Maior Custo", fmt(kpis['maior_custo']))
        c4.metric("Menor SR", fmt(kpis['menor_sr']))
        c5.metric("Maior SR", fmt(kpis['maior_sr']))
        c6.metric("Margem SR Média", fmt(kpis['margem_sr_media']))
        st.markdown("---")
        df = pd.DataFrame(catalogo_cache())
        col1,col2 = st.columns(2)
        with col1:
            sec("Custo Médio × Super Revenda por Modelo")
            dm = df.groupby('Modelo').agg(Custo=('Custo Final','mean'),SR=('Super Revenda','mean')).reset_index().round(2)
            fig = go.Figure()
            fig.add_bar(x=dm['Modelo'],y=dm['Custo'],name='Custo',marker_color='#e05c5c')
            fig.add_bar(x=dm['Modelo'],y=dm['SR'],name='Super Revenda',marker_color='#00c04b')
            fig.update_layout(barmode='group',**CHART,legend=dict(orientation='h',y=1.1,font_color='#8899b0'))
            fig.update_xaxes(gridcolor='#1a2535'); fig.update_yaxes(gridcolor='#1a2535')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            sec("Margem SR por Tecido")
            dt = df.groupby('Tecido').agg(C=('Custo Final','mean'),S=('Super Revenda','mean')).reset_index()
            dt['Margem'] = (dt['S']-dt['C']).round(2)
            fig2 = px.bar(dt,x='Tecido',y='Margem',color='Tecido',
                         color_discrete_sequence=['#00c04b','#ff6b1a','#3b82f6','#f6c90e'])
            fig2.update_layout(**CHART,showlegend=False)
            fig2.update_xaxes(gridcolor='#1a2535'); fig2.update_yaxes(gridcolor='#1a2535')
            st.plotly_chart(fig2, use_container_width=True)
        col3,col4 = st.columns(2)
        with col3:
            sec("SKUs por Tecido")
            dp = df.groupby('Tecido').size().reset_index(name='SKUs')
            fig3 = px.pie(dp,names='Tecido',values='SKUs',hole=0.4,
                         color_discrete_sequence=['#00c04b','#ff6b1a','#3b82f6','#f6c90e'])
            fig3.update_layout(**CHART)
            st.plotly_chart(fig3, use_container_width=True)
        with col4:
            sec("Top 10 SKUs Mais Caros")
            st.dataframe(df.nlargest(10,'Custo Final')[['Modelo','Tecido','Cor','Tamanho','Custo Final']].reset_index(drop=True),
                        use_container_width=True, hide_index=True)
        st.markdown("---")
        sec("Costura Ativa por Modelo")
        st.dataframe(pd.DataFrame([{
            'Modelo':f['modelo'],'Faccionista':f['faccionista_ativa'],
            'Preço Ativo':fmt(get_preco_costura(f['modelo']))
        } for f in get_faccionistas()]), use_container_width=True, hide_index=True)

# ══ SIMULADOR ══════════════════════════════
elif pagina=="🧮 Simulador de Preço":
    titulo("🧮 Simulador de Preço")
    ta,tb = st.tabs(["📋 Produto do Catálogo","✏️ Produto Avulso"])
    with ta:
        st.info("Selecione o produto e veja custo + preços calculados automaticamente.")
        skus,mods,_ = get_opcoes()
        c1,c2 = st.columns(2)
        with c1:
            ma = st.selectbox("Modelo",mods,key="sa_m")
            ts = sorted(set(s['tecido'] for s in skus if s['modelo']==ma))
            ta_ = st.selectbox("Tecido",ts,key="sa_t")
        with c2:
            cr = cores(skus,ma,ta_)
            ca_ = st.selectbox("Cor",cr,key="sa_c") if cr else None
            tm = tams(skus,ma,ta_,ca_) if ca_ else []
            tm_ = st.selectbox("Tamanho",tm,key="sa_tam") if tm else None
        if ca_ and tm_:
            calc = calcular_sku_completo(ma,ta_,ca_,tm_)
            if calc:
                st.markdown("---")
                sec("Detalhamento do Custo")
                c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
                c1.metric("Peso",f"{calc['peso_g']}g")
                c2.metric("R$/kg",fmt(calc['preco_kg']))
                c3.metric("Tecido",fmt(calc['custo_tecido']))
                c4.metric("Costura",fmt(calc['costura']))
                c5.metric("Frete 5%",fmt(calc['frete']))
                c6.metric("Outros 3%",fmt(calc['outros']))
                c7.metric("Embalagem",fmt(calc['embalagem']))
                st.markdown("---")
                sec("Preços de Venda")
                p1,p2,p3,p4,p5 = st.columns(5)
                p1.markdown(cc("📋 Subtotal",calc['subtotal']),unsafe_allow_html=True)
                p2.markdown(cc("✅ Custo Final",calc['custo_final']),unsafe_allow_html=True)
                p3.markdown(cv("🟢 Super Revenda +20%",calc['super_revenda']),unsafe_allow_html=True)
                p4.markdown(cv("🔵 Atacado +35%",calc['atacado']),unsafe_allow_html=True)
                p5.markdown(cv("🔴 Varejo +50%",calc['varejo']),unsafe_allow_html=True)
                st.markdown("---")
                if st.button("📄 Gerar Ficha de Custo PDF"):
                    from pdf_gerador import gerar_pdf_ficha_custo
                    pdf = gerar_pdf_ficha_custo(calc)
                    st.download_button("⬇️ Baixar PDF",pdf,
                        file_name=f"ficha_{ma}_{ta_}_{ca_}_{tm_}.pdf".replace(" ","_"),
                        mime="application/pdf")
    with tb:
        st.info("Para produtos não cadastrados — informe os dados manualmente.")
        c1,c2 = st.columns(2)
        with c1:
            desc = st.text_input("Descrição","Ex: Blusa Polo")
            peso = st.number_input("Peso (g)",1.0,value=200.0,step=5.0)
            pkg  = st.number_input("Valor/kg (R$)",0.0,value=28.0,step=0.5)
        with c2:
            p = get_parametros()
            cost = st.number_input("Costura (R$/peça)",0.0,value=4.0,step=0.5)
            out  = st.number_input("Outros (%)",0.0,1.0,float(p.get('outros_pct',0.03)),0.01,format="%.2f")
            emb  = st.number_input("Embalagem (R$)",0.0,value=float(p.get('embalagem',0.0)),step=0.5)
        if st.button("🧮 Calcular",key="calc_b"):
            cb = calcular_manual(peso,pkg,cost,emb,out)
            st.markdown(f"---")
            sec(f"Resultado — {desc}")
            p1,p2,p3,p4 = st.columns(4)
            p1.markdown(cc("✅ Custo Final",cb['custo_final']),unsafe_allow_html=True)
            p2.markdown(cv("🟢 Super Revenda",cb['super_revenda']),unsafe_allow_html=True)
            p3.markdown(cv("🔵 Atacado",cb['atacado']),unsafe_allow_html=True)
            p4.markdown(cv("🔴 Varejo",cb['varejo']),unsafe_allow_html=True)

# ══ MARGEM REVERSA ══════════════════════════
elif pagina=="🔄 Margem Reversa":
    titulo("🔄 Margem Reversa")
    t1,t2 = st.tabs(["💬 Qual minha margem se cobrar R$X?","🎯 Quanto cobrar para ter X% de margem?"])
    skus,mods,_ = get_opcoes()
    with t1:
        st.info("Informe o preço que o cliente quer pagar e veja sua margem real.")
        c1,c2 = st.columns(2)
        with c1:
            m1 = st.selectbox("Modelo",mods,key="mr_m")
            ts1 = sorted(set(s['tecido'] for s in skus if s['modelo']==m1))
            t1_ = st.selectbox("Tecido",ts1,key="mr_t")
        with c2:
            cr1 = cores(skus,m1,t1_)
            c1_ = st.selectbox("Cor",cr1,key="mr_c") if cr1 else None
            tm1 = tams(skus,m1,t1_,c1_) if c1_ else []
            tm1_ = st.selectbox("Tamanho",tm1,key="mr_tam") if tm1 else None
        preco_cli = st.number_input("Preço que o cliente quer pagar (R$)",0.01,value=12.0,step=0.5)
        if c1_ and tm1_:
            calc = calcular_sku_completo(m1,t1_,c1_,tm1_)
            if calc:
                custo = calc['custo_final']
                lucro = round(preco_cli-custo,2)
                margem = round(lucro/preco_cli*100,1) if preco_cli else 0
                markup = round(lucro/custo*100,1) if custo else 0
                st.markdown("---")
                p1,p2,p3,p4 = st.columns(4)
                p1.markdown(cc("Custo Final",custo),unsafe_allow_html=True)
                p2.markdown(cc("Preço Cobrado",preco_cli),unsafe_allow_html=True)
                p3.markdown(cv("Lucro/Peça",lucro) if lucro>=0 else ca("⚠️ PREJUÍZO",lucro),unsafe_allow_html=True)
                p4.metric("Margem Real",f"{margem:.1f}%",delta=f"Markup: {markup:.1f}%")
                st.markdown("---")
                sec("Comparação com suas faixas padrão")
                dc = {'Faixa':['Super Revenda +20%','Atacado +35%','Varejo +50%','Preço do cliente'],
                      'Preço':[calc['super_revenda'],calc['atacado'],calc['varejo'],preco_cli],
                      'Lucro':[round(calc['super_revenda']-custo,2),round(calc['atacado']-custo,2),round(calc['varejo']-custo,2),lucro],
                      'Margem %':[round((calc['super_revenda']-custo)/calc['super_revenda']*100,1),
                                  round((calc['atacado']-custo)/calc['atacado']*100,1),
                                  round((calc['varejo']-custo)/calc['varejo']*100,1),margem]}
                st.dataframe(pd.DataFrame(dc),use_container_width=True,hide_index=True)
                if lucro<0: st.error(f"⚠️ Abaixo do custo! Mínimo sem prejuízo: {fmt(custo)}")
                elif margem<10: st.warning(f"⚠️ Margem muito baixa ({margem:.1f}%). SR padrão é 20%.")
                else: st.success(f"✅ Margem de {margem:.1f}% — dentro do esperado.")
    with t2:
        st.info("Arraste o slider e veja qual preço cobrar para atingir a margem desejada.")
        c1,c2 = st.columns(2)
        with c1:
            m2 = st.selectbox("Modelo",mods,key="mr2_m")
            ts2 = sorted(set(s['tecido'] for s in skus if s['modelo']==m2))
            t2_ = st.selectbox("Tecido",ts2,key="mr2_t")
        with c2:
            cr2 = cores(skus,m2,t2_)
            c2_ = st.selectbox("Cor",cr2,key="mr2_c") if cr2 else None
            tm2 = tams(skus,m2,t2_,c2_) if c2_ else []
            tm2_ = st.selectbox("Tamanho",tm2,key="mr2_tam") if tm2 else None
        mg_des = st.slider("Margem desejada (%)",5,100,20,1)
        if c2_ and tm2_:
            calc2 = calcular_sku_completo(m2,t2_,c2_,tm2_)
            if calc2:
                custo2 = calc2['custo_final']
                pnec = round(custo2/(1-mg_des/100),2)
                luc2 = round(pnec-custo2,2)
                st.markdown("---")
                p1,p2,p3,p4 = st.columns(4)
                p1.markdown(cc("Custo Final",custo2),unsafe_allow_html=True)
                p2.markdown(cv(f"Preço para {mg_des}% de margem",pnec),unsafe_allow_html=True)
                p3.markdown(cv("Lucro/Peça",luc2),unsafe_allow_html=True)
                p4.metric("Markup equivalente",f"{round(luc2/custo2*100,1):.1f}%")
                margens = list(range(5,65,5))
                precos = [round(custo2/(1-m_/100),2) for m_ in margens]
                fig = px.line(pd.DataFrame({'Margem (%)':margens,'Preço (R$)':precos}),
                              x='Margem (%)',y='Preço (R$)',markers=True,
                              color_discrete_sequence=['#00c04b'])
                fig.add_vline(x=mg_des,line_dash="dash",line_color="#ff6b1a",
                              annotation_text=f"  {mg_des}%",annotation_font_color="#ff6b1a")
                fig.update_layout(**CHART)
                fig.update_xaxes(gridcolor='#1a2535'); fig.update_yaxes(gridcolor='#1a2535')
                st.plotly_chart(fig,use_container_width=True)

# ══ LOTE ════════════════════════════════════
elif pagina=="📦 Simulador de Lote":
    titulo("📦 Simulador de Lote — Kg → Peças")
    st.info("Informe quantos kg vai comprar e veja quantas peças saem, o custo e o lucro.")
    skus,mods,_ = get_opcoes()
    if not skus: st.warning("Nenhum SKU cadastrado.")
    else:
        if 'll' not in st.session_state: st.session_state.ll = [{}]
        st.button("➕ Adicionar linha", on_click=lambda: st.session_state.ll.append({}))
        inputs = []
        for idx in range(len(st.session_state.ll)):
            c1,c2,c3,c4,c5,c6 = st.columns([2,2,2,2,2,1])
            tec = c1.selectbox("Tecido",sorted(set(s['tecido'] for s in skus)),key=f"lt_t{idx}")
            mod = c2.selectbox("Modelo",sorted(set(s['modelo'] for s in skus if s['tecido']==tec)),key=f"lt_m{idx}")
            cr = cores(skus,mod,tec); co = c3.selectbox("Cor",cr,key=f"lt_c{idx}") if cr else None
            tm = tams(skus,mod,tec,co) if co else []; ta__ = c4.selectbox("Tamanho",tm,key=f"lt_ta{idx}") if tm else None
            kg = c5.number_input("Kg",0.1,value=10.0,step=0.5,key=f"lt_k{idx}")
            if c6.button("✖",key=f"lt_r{idx}"): st.session_state.ll.pop(idx); st.rerun()
            if tec and mod and co and ta__: inputs.append((tec,co,mod,ta__,kg))
        if st.button("🧮 Calcular Lote") and inputs:
            res = []
            for tec,co,mod,ta__,kg in inputs:
                r = calcular_lote(tec,co,mod,ta__,kg)
                if r: res.append(r)
                else: st.warning(f"SKU não encontrado: {mod} {tec} {co} {ta__}")
            if res:
                st.markdown("---")
                df = pd.DataFrame(res); ds = df.copy()
                for col in ['custo_tecido_lote','custo_final_peca','custo_total_lote','faturamento_sr','lucro']:
                    ds[col] = ds[col].apply(fmt)
                ds['markup_pct'] = ds['markup_pct'].apply(fpct)
                ds['margem_pct'] = ds['margem_pct'].apply(fpct)
                ds.columns = ['Descrição','Kg','Peso/g','Qtd','C.Tecido','C/Peça','C.Total','Fat.SR','Lucro','Markup%','Margem%']
                st.dataframe(ds,use_container_width=True,hide_index=True)
                st.markdown("---")
                tkg=sum(r['kg'] for r in res); tpcs=sum(r['qtd_pecas'] for r in res)
                tct=sum(r['custo_total_lote'] for r in res); tft=sum(r['faturamento_sr'] for r in res)
                tlc=sum(r['lucro'] for r in res); mgr=tlc/tft if tft else 0
                c1,c2,c3,c4,c5,c6 = st.columns(6)
                c1.metric("Total Kg",f"{tkg:.1f}kg"); c2.metric("Total Peças",tpcs)
                c3.metric("Custo Total",fmt(tct)); c4.metric("Faturamento SR",fmt(tft))
                c5.metric("Lucro Total",fmt(tlc)); c6.metric("Margem Real",fpct(mgr))

# ══ TABELA CLIENTE ════════════════════════════
elif pagina=="📤 Tabela para Cliente":
    titulo("📤 Tabela de Preços para Cliente")
    cat = catalogo_cache()
    if not cat: st.warning("Nenhum SKU cadastrado.")
    else:
        df = pd.DataFrame(cat)
        c1,c2,c3 = st.columns(3)
        mf = c1.selectbox("Modelo",['Todos']+sorted(df['Modelo'].unique()))
        tf = c2.selectbox("Tecido",['Todos']+sorted(df['Tecido'].unique()))
        dff = df.copy()
        if mf!='Todos': dff = dff[dff['Modelo']==mf]
        if tf!='Todos': dff = dff[dff['Tecido']==tf]
        cf = c3.selectbox("Cor",['Todas']+sorted(dff['Cor'].unique()))
        if cf!='Todas': dff = dff[dff['Cor']==cf]
        fx = st.radio("Faixa de Preço para o Cliente:",["Super Revenda","Atacado","Varejo","Todas as Faixas"],horizontal=True)

        # Monta tabela SEM custo — cliente nunca vê o custo!
        ds = dff.copy()
        if fx=="Todas as Faixas":
            for c in ['Super Revenda','Atacado','Varejo']: ds[c]=ds[c].apply(fmt)
            cols = ['Modelo','Cor','Tecido','Tamanho','Super Revenda','Atacado','Varejo']
        else:
            ds['Preço'] = ds[fx].apply(fmt)
            cols = ['Modelo','Cor','Tecido','Tamanho','Preço']

        st.caption(f"{len(ds)} produtos — Faixa: **{fx}**")
        st.dataframe(ds[cols],use_container_width=True,hide_index=True)
        st.markdown("---")
        cp,cw,cc_ = st.columns(3)
        with cp:
            if st.button("📄 Gerar PDF para Cliente"):
                from pdf_gerador import gerar_pdf_tabela_precos
                # Passa apenas dados sem custo para o PDF
                dados_pdf = []
                for _,row in dff.iterrows():
                    if fx=="Todas as Faixas":
                        dados_pdf.append({
                            'Modelo':row['Modelo'],'Tecido':row['Tecido'],
                            'Cor':row['Cor'],'Tamanho':row['Tamanho'],
                            'Super Revenda':row['Super Revenda'],
                            'Atacado':row['Atacado'],'Varejo':row['Varejo'],
                        })
                    else:
                        dados_pdf.append({
                            'Modelo':row['Modelo'],'Tecido':row['Tecido'],
                            'Cor':row['Cor'],'Tamanho':row['Tamanho'],
                            'Faixa':fx,'Preço':row[fx],
                        })
                with st.spinner("Gerando PDF..."):
                    pdf = gerar_pdf_tabela_precos(dados_pdf, f"Modelo: {mf} | Tecido: {tf} | Cor: {cf} | Faixa: {fx}")
                st.download_button("⬇️ Baixar PDF",pdf,file_name=f"tabela_cliente_{date.today()}.pdf",mime="application/pdf")
        with cw:
            if st.button("📱 Texto WhatsApp"):
                lns = ["*Tabela de Preços — Prates Sublimação* 🧵",""]
                for _,row in dff.iterrows():
                    if fx=="Todas as Faixas":
                        lns.append(f"• {row['Modelo']} {row['Tecido']} {row['Cor']} ({row['Tamanho']}): SR {fmt(row['Super Revenda'])} | AT {fmt(row['Atacado'])} | VR {fmt(row['Varejo'])}")
                    else:
                        lns.append(f"• {row['Modelo']} {row['Tecido']} {row['Cor']} ({row['Tamanho']}): {fmt(row[fx])}")
                lns += ["","Pix ou Dinheiro | Retirada local — Macaé/RJ 😊"]
                st.text_area("Copie:","\n".join(lns),height=250)
        with cc_:
            # CSV também sem custo
            csv_cols = ['Modelo','Cor','Tecido','Tamanho'] + (['Super Revenda','Atacado','Varejo'] if fx=="Todas as Faixas" else [fx])
            if fx != "Todas as Faixas":
                dff_csv = dff[['Modelo','Cor','Tecido','Tamanho',fx]].copy()
                dff_csv.columns = ['Modelo','Cor','Tecido','Tamanho','Preço']
            else:
                dff_csv = dff[['Modelo','Cor','Tecido','Tamanho','Super Revenda','Atacado','Varejo']].copy()
            st.download_button("⬇️ CSV",dff_csv.to_csv(index=False).encode('utf-8-sig'),
                               file_name=f"tabela_cliente_{date.today()}.csv",mime="text/csv")

# ══ RELATÓRIO MENSAL ════════════════════════
elif pagina=="📈 Relatório Mensal":
    titulo("📈 Relatório Mensal")
    ms = st.sidebar.text_input("Mês (AAAA-MM)",datetime.today().strftime('%Y-%m'))
    tp,tr,ta = st.tabs(["📊 Painel","📋 Registros","➕ Novo Registro"])
    with tp:
        regs = get_relatorio_mensal(ms)
        if not regs: st.info(f"Nenhum registro para {ms}.")
        else:
            df = pd.DataFrame(regs)
            rec=df['receita'].sum(); cst=df['custo'].sum(); luc=df['lucro'].sum()
            c1,c2,c3,c4,c5,c6 = st.columns(6)
            c1.metric("Pedidos",len(df)); c2.metric("Peças",int(df['qtd_pecas'].sum()))
            c3.metric("Receita",fmt(rec)); c4.metric("Custo",fmt(cst))
            c5.metric("Lucro",fmt(luc)); c6.metric("Margem",fpct(luc/rec if rec else 0))
            col1,col2 = st.columns(2)
            with col1:
                dm = df.groupby('modelo')['receita'].sum().reset_index()
                fig = px.bar(dm,x='modelo',y='receita',color='modelo',
                             color_discrete_sequence=['#00c04b','#ff6b1a','#3b82f6','#f6c90e'])
                fig.update_layout(**CHART,title="Receita por Modelo",showlegend=False)
                fig.update_xaxes(gridcolor='#1a2535'); fig.update_yaxes(gridcolor='#1a2535')
                st.plotly_chart(fig,use_container_width=True)
            with col2:
                df2 = df.groupby('faixa')['receita'].sum().reset_index()
                fig2 = px.pie(df2,names='faixa',values='receita',hole=0.4,
                              color_discrete_sequence=['#00c04b','#ff6b1a','#3b82f6'])
                fig2.update_layout(**CHART,title="Receita por Faixa")
                st.plotly_chart(fig2,use_container_width=True)
    with tr:
        regs = get_relatorio_mensal(ms)
        if not regs: st.info("Nenhum registro.")
        else:
            df = pd.DataFrame(regs)
            st.dataframe(df[['data','numero_pedido','modelo','faixa','tecido','qtd_pecas','receita','custo','lucro','observacao']],
                        use_container_width=True,hide_index=True)
            rid = st.selectbox("Excluir ID:",df['id'].tolist())
            if st.button("🗑️ Excluir"): delete_registro_mensal(rid); st.rerun()
            st.download_button("⬇️ CSV",df.to_csv(index=False).encode('utf-8-sig'),
                               file_name=f"rel_{ms}.csv",mime="text/csv")
    with ta:
        skus,mods,_ = get_opcoes()
        c1,c2,c3 = st.columns(3)
        dr=c1.date_input("Data",date.today()); nr=c2.text_input("Nº Pedido"); fx_r=c3.selectbox("Faixa",["Super Revenda","Atacado","Varejo"])
        c4,c5,c6 = st.columns(3)
        mr_=c4.selectbox("Modelo",mods); tr_=c5.text_input("Tecido"); qr=c6.number_input("Qtd",1,value=10)
        c7,c8,c9 = st.columns(3)
        cor_r=c7.text_input("Cor"); rr=c8.number_input("Receita (R$)",0.0,step=0.01); cr_=c9.number_input("Custo (R$)",0.0,step=0.01)
        vr_=c1.text_input("Variante"); obs_r=st.text_area("Observação")
        if st.button("💾 Salvar"):
            add_registro_mensal(str(dr),nr,mr_,fx_r,vr_,tr_,qr,cor_r,rr,cr_,round(rr-cr_,2),obs_r)
            st.success("✅ Salvo!"); st.rerun()

# ══ CONFIGURAÇÕES ════════════════════════════
elif pagina=="⚙️ Configurações":
    titulo("⚙️ Configurações")
    tp,tf,tfa,ts = st.tabs(["🎛️ Parâmetros","🏭 Fornecedores","✂️ Faccionistas","📦 SKUs"])
    with tp:
        st.info("Altere aqui → todos os SKUs recalculam automaticamente.")
        p = get_parametros()
        c1,c2 = st.columns(2)
        with c1:
            fr=st.number_input("Frete (%)",0.0,1.0,float(p.get('frete_pct',0.05)),0.01,format="%.2f")
            ou=st.number_input("Outros Custos (%)",0.0,1.0,float(p.get('outros_pct',0.03)),0.01,format="%.2f")
            em=st.number_input("Embalagem/peça (R$)",0.0,value=float(p.get('embalagem',0.0)),step=0.5)
        with c2:
            ms_=st.number_input("Margem Super Revenda (%)",0.0,5.0,float(p.get('margem_sr',0.20)),0.01,format="%.2f")
            ma_=st.number_input("Margem Atacado (%)",0.0,5.0,float(p.get('margem_atacado',0.35)),0.01,format="%.2f")
            mv_=st.number_input("Margem Varejo (%)",0.0,5.0,float(p.get('margem_varejo',0.50)),0.01,format="%.2f")
        if st.button("💾 Salvar Parâmetros"):
            for k,v in [('frete_pct',fr),('outros_pct',ou),('embalagem',em),('margem_sr',ms_),('margem_atacado',ma_),('margem_varejo',mv_)]:
                set_parametro(k,v)
            catalogo_cache.clear()
            st.success("✅ Parâmetros salvos! Todos os preços foram atualizados."); st.rerun()
    with tf:
        st.info("Atualize o preço/kg. O Fornecedor Ativo é usado em todos os cálculos.")
        for fo in get_fornecedores():
            with st.expander(f"🧵 {fo['tecido']} — {fo['cor']}   |   Ativo: {fo['fornecedor_ativo']}   |   {fmt(get_preco_kg(fo['tecido'],fo['cor']))}/kg"):
                c1,c2,c3,c4 = st.columns(4)
                f1n=c1.text_input("Fornecedor 1",fo['f1_nome'],key=f"f1n{fo['id']}")
                f1p=c2.number_input("Preço F1",0.0,value=float(fo['f1_preco']),step=0.1,key=f"f1p{fo['id']}")
                f2n=c3.text_input("Fornecedor 2",fo['f2_nome'],key=f"f2n{fo['id']}")
                f2p=c4.number_input("Preço F2",0.0,value=float(fo['f2_preco']),step=0.1,key=f"f2p{fo['id']}")
                c5,c6,c7 = st.columns(3)
                f3n=c5.text_input("Fornecedor 3",fo['f3_nome'],key=f"f3n{fo['id']}")
                f3p=c6.number_input("Preço F3",0.0,value=float(fo['f3_preco']),step=0.1,key=f"f3p{fo['id']}")
                op=['Mais Barato',f1n,f2n,f3n]; ix=op.index(fo['fornecedor_ativo']) if fo['fornecedor_ativo'] in op else 0
                fa_=c7.selectbox("Ativo",op,index=ix,key=f"fa{fo['id']}")
                if st.button("💾 Salvar",key=f"sf{fo['id']}"):
                    ant=get_preco_kg(fo['tecido'],fo['cor'])
                    update_fornecedor(fo['id'],{'f1_nome':f1n,'f1_preco':f1p,'f2_nome':f2n,'f2_preco':f2p,'f3_nome':f3n,'f3_preco':f3p,'fornecedor_ativo':fa_})
                    novo=get_preco_kg(fo['tecido'],fo['cor'])
                    if abs(novo-ant)>0.001: add_historico('Tecido',f"{fo['tecido']} | {fo['cor']}",ant,novo,fa_,'')
                    catalogo_cache.clear()
                    st.success("✅ Atualizado!"); st.rerun()
        st.markdown("---")
        st.markdown("**➕ Novo Tecido/Cor**")
        c1,c2,c3 = st.columns(3)
        nt=c1.text_input("Tecido",key="nt"); nc=c2.text_input("Cor",key="nc"); np_=c3.number_input("Preço F1 (R$/kg)",0.0,step=0.1,key="np")
        if st.button("➕ Adicionar") and nt and nc:
            ok=add_fornecedor(nt,nc,'Fornecedor 1',np_)
            st.success("✅ Adicionado!") if ok else st.error("❌ Já existe.")
            st.rerun()
    with tfa:
        for f in get_faccionistas():
            with st.expander(f"✂️ {f['modelo']}   |   Ativa: {f['faccionista_ativa']}   |   {fmt(get_preco_costura(f['modelo']))}/peça"):
                c1,c2,c3,c4 = st.columns(4)
                fn1=c1.text_input("Faccionista 1",f['f1_nome'],key=f"fn1{f['id']}")
                fp1=c2.number_input("Preço F1",0.0,value=float(f['f1_preco']),step=0.1,key=f"fp1{f['id']}")
                fn2=c3.text_input("Faccionista 2",f['f2_nome'],key=f"fn2{f['id']}")
                fp2=c4.number_input("Preço F2",0.0,value=float(f['f2_preco']),step=0.1,key=f"fp2{f['id']}")
                c5,c6,c7 = st.columns(3)
                fn3=c5.text_input("Faccionista 3",f['f3_nome'],key=f"fn3{f['id']}")
                fp3=c6.number_input("Preço F3",0.0,value=float(f['f3_preco']),step=0.1,key=f"fp3{f['id']}")
                op=['Mais Barata',fn1,fn2,fn3]; ix=op.index(f['faccionista_ativa']) if f['faccionista_ativa'] in op else 0
                faa=c7.selectbox("Ativa",op,index=ix,key=f"faa{f['id']}")
                if st.button("💾 Salvar",key=f"sfac{f['id']}"):
                    ant=get_preco_costura(f['modelo'])
                    update_faccionista(f['id'],{'f1_nome':fn1,'f1_preco':fp1,'f2_nome':fn2,'f2_preco':fp2,'f3_nome':fn3,'f3_preco':fp3,'faccionista_ativa':faa})
                    novo=get_preco_costura(f['modelo'])
                    if abs(novo-ant)>0.001: add_historico('Costura',f['modelo'],ant,novo,faa,'')
                    catalogo_cache.clear()
                    st.success("✅ Atualizado!"); st.rerun()
    with ts:
        sk = get_skus()
        st.dataframe(pd.DataFrame(sk)[['id','modelo','tecido','cor','tamanho','peso_g']],
                    use_container_width=True,hide_index=True)
        st.caption(f"Total: {len(sk)} SKUs")
        st.markdown("---")
        st.markdown("**➕ Adicionar / Atualizar SKU**")
        c1,c2,c3,c4,c5 = st.columns(5)
        ms2=c1.text_input("Modelo","Adulto"); ts2=c2.text_input("Tecido","PP")
        cs2=c3.text_input("Cor"); tms2=c4.selectbox("Tamanho",["P-GG","XGG","1-14"])
        ps2=c5.number_input("Peso (g)",1.0,value=235.0,step=5.0)
        if st.button("💾 Salvar SKU"):
            upsert_sku(ms2,ts2,cs2,tms2,ps2)
            catalogo_cache.clear()
            st.success("✅ SKU salvo!"); st.rerun()

# ══ HISTÓRICO ════════════════════════════════
elif pagina=="📋 Histórico de Preços":
    titulo("📋 Histórico de Preços")
    tv,ta = st.tabs(["📋 Ver","➕ Registrar"])
    with tv:
        h = get_historico()
        if not h: st.info("Nenhum registro. O sistema registra automaticamente ao salvar em Configurações.")
        else:
            dh = pd.DataFrame(h)
            dh['variacao_pct'] = dh['variacao_pct'].apply(fpct)
            st.dataframe(dh[['data','tipo','tecido_modelo','preco_anterior','preco_novo',
                             'variacao_pct','fornecedor_faccionista','motivo']],
                        use_container_width=True,hide_index=True)
            st.download_button("⬇️ CSV",dh.to_csv(index=False).encode('utf-8-sig'),
                               file_name=f"historico_{date.today()}.csv",mime="text/csv")
    with ta:
        c1,c2 = st.columns(2)
        th=c1.selectbox("Tipo",["Tecido","Costura"]); tmh=c2.text_input("Tecido/Modelo")
        c3,c4,c5 = st.columns(3)
        ph1=c3.number_input("Preço Anterior",0.0,step=0.01)
        ph2=c4.number_input("Preço Novo",0.0,step=0.01)
        fh=c5.text_input("Fornecedor/Faccionista")
        mh=st.text_input("Motivo")
        if st.button("💾 Registrar") and tmh and ph2:
            add_historico(th,tmh,ph1,ph2,fh,mh); st.success("✅ Registrado!"); st.rerun()

# ══ IMPORTAR ════════════════════════════════
elif pagina=="📥 Importar Planilha":
    titulo("📥 Importar Planilha Excel")
    st.info("Faça upload do .xlsx para importar SKUs, fornecedores, faccionistas e parâmetros.")
    arq = st.file_uploader("Selecione o arquivo .xlsx",type=['xlsx'])
    if arq:
        import tempfile, os as _os
        with tempfile.NamedTemporaryFile(delete=False,suffix='.xlsx') as tmp:
            tmp.write(arq.read()); tp=tmp.name
        if st.button("🚀 Importar"):
            from importador import importar_xlsx
            with st.spinner("Importando..."): res=importar_xlsx(tp)
            if 'erro' in res: st.error(f"❌ Erro: {res['erro']}")
            else:
                catalogo_cache.clear()
                st.success(f"✅ SKUs: {res['skus']} | Fornecedores: {res['fornecedores']} | Parâmetros: {res['parametros']}")
            _os.unlink(tp)
    st.markdown("---")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("SKUs",len(get_skus())); c2.metric("Fornecedores",len(get_fornecedores()))
    c3.metric("Faccionistas",len(get_faccionistas())); c4.metric("Histórico",len(get_historico()))
