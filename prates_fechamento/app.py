"""
app.py — Sistema Fechamento Mensal · Grupo Prates v2
Checklist + Apuração + Metas + Igreja & Retiradas + Resumo WhatsApp
"""
import streamlit as st
from supabase import create_client
from datetime import date, datetime
import pandas as pd
import hashlib, os, base64

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(show_spinner=False)
def get_logo_b64():
    for nome in ["logo.jpeg","logo.jpg","logo.png"]:
        if os.path.exists(nome):
            with open(nome,"rb") as f:
                return base64.b64encode(f.read()).decode()
    return None

st.set_page_config(
    page_title="Fechamento Mensal · Grupo Prates",
    page_icon="📋", layout="wide",
    initial_sidebar_state="expanded",
)

TAREFAS = [
    ("RELATÓRIOS E LANÇAMENTOS", [
        "Relatório — Conferir e Lançar Prates Eletrônico",
        "Relatório — Lançar Sobras e Faltas Caixa Prates Eletrônico",
        "Relatório — Conferir e Lançar Prates Sublimação",
        "Relatório — Lançar Sobras e Faltas Caixa Prates Sublimação",
    ]),
    ("DOCUMENTOS E VERIFICAÇÕES FINANCEIRAS", [
        "Boletos",
        "Papéis Amarelos (Cartão)",
        "Caderno (Pagamento Funcionários)",
        "Cartão Banco do Brasil",
        "Verificar Taxa Máquina Cartão",
        "Lançar o Valor da Construção da Casa (se houve retirada)",
    ]),
    ("APURAÇÃO DE LUCROS E PERDAS", [
        "Verificar Lucros Prates Eletrônicos",
        "Verificar Lucro em Sobras e Perdas — Prates Eletrônicos",
        "Verificar Lucros Prates Sublimação",
        "Verificar Lucro em Sobras e Perdas — Prates Sublimação",
        "Verificar as Perdas de Produtos com Baixa no C-plus",
        "Verificar Faltas de Produtos no Estoque Eletrônico",
        "Verificar Faltas de Produtos no Estoque Sublimação",
    ]),
    ("LANÇAMENTO DE DÍZIMOS", [
        "Lançar o Dízimo da Prates Eletrônico — Principal",
        "Lançar o Dízimo das Sobras e Faltas — Prates Eletrônico",
        "Lançar o Dízimo da Prates Sublimação — Principal",
        "Lançar o Dízimo das Sobras e Faltas — Prates Sublimação",
    ]),
    ("LANÇAMENTOS NO SISTEMA DE DESPESAS", [
        "Lançar Lucro da Prates Eletrônico no Sistema de Despesas",
        "Lançar Lucro Sobras e Faltas Eletrônico no Sistema de Despesas",
        "Lançar Lucro da Prates Sublimação no Sistema de Despesas",
        "Lançar Lucro Sobras e Faltas Sublimação no Sistema de Despesas",
    ]),
    ("TRANSFERÊNCIAS DE CAIXA", [
        "Transferência do Caixa Eletrônico para Despesa Pessoal",
        "Transferência do Caixa Eletrônico para a Igreja",
        "Transferência Sobras e Faltas Eletrônico para a Igreja",
        "Transferência do Caixa Sublimação para a Igreja",
        "Transferência Sobras e Faltas Sublimação para a Igreja",
    ]),
]
TOTAL_TAREFAS = sum(len(ts) for _, ts in TAREFAS)
STATUS_OPTS = ["☐ Pendente", "⏳ Em Andamento", "✅ Concluído", "⊘ N/A"]

st.markdown("""
<style>
html,body,[class*="css"]{font-family:'Segoe UI',sans-serif;}
[data-testid="stAppViewContainer"]{background:#111318;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"]{background:#16191f;border-right:1px solid #252932;}
[data-testid="stSidebar"] *{color:#c5cad3 !important;}
[data-testid="stSidebar"] .stButton>button,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]{
    background:transparent !important;border:none !important;
    border-left:3px solid transparent !important;border-radius:0 5px 5px 0 !important;
    color:#8892a0 !important;font-size:13px !important;font-weight:400 !important;
    padding:7px 14px !important;text-align:left !important;
    margin:1px 0 !important;box-shadow:none !important;
    width:100% !important;display:block !important;
}
[data-testid="stSidebar"] .stButton>button:hover,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover{
    background:#1a2235 !important;color:#c5cad3 !important;
    border-left:3px solid #2d7a4f44 !important;
}
[data-testid="stSidebar"] .stButton>button div,
[data-testid="stSidebar"] .stButton>button p,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] div,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p{
    text-align:left !important;margin:0 !important;width:100% !important;display:block !important;
}
.stButton>button{background:#1e6b3e;color:#fff;border:none;border-radius:5px;padding:6px 16px;font-size:13px;font-weight:500;}
.stButton>button:hover{background:#248a4e;}
[data-testid="stMetric"]{background:#16191f;border-radius:6px;padding:12px 14px;border:1px solid #252932;}
[data-testid="stMetricLabel"]{color:#6b7280 !important;font-size:11px !important;}
[data-testid="stMetricValue"]{color:#e2e8f0 !important;font-size:20px !important;font-weight:600 !important;}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{
    background:#16191f !important;border:1px solid #252932 !important;
    border-radius:5px !important;color:#e2e8f0 !important;font-size:13px !important;
}
[data-testid="stSelectbox"]>div>div{background:#16191f !important;border:1px solid #252932 !important;border-radius:5px !important;}
[data-testid="stExpander"]{background:#16191f !important;border:1px solid #252932 !important;border-radius:6px !important;margin-bottom:4px !important;}
[data-testid="stTabs"] [role="tablist"]{background:transparent;border-bottom:1px solid #252932;}
[data-testid="stTabs"] [role="tab"]{color:#6b7280 !important;font-size:13px !important;padding:8px 16px !important;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{color:#e2e8f0 !important;border-bottom:2px solid #2d7a4f !important;font-weight:600 !important;}
[data-testid="stInfo"]{background:#0d1e35 !important;border:1px solid #1a3a5c !important;color:#7eb8f7 !important;border-radius:6px !important;}
[data-testid="stSuccess"]{background:#0a1f12 !important;border:1px solid #1a4a2a !important;border-radius:6px !important;}
[data-testid="stWarning"]{background:#1f1a0a !important;border:1px solid #3a2a0a !important;border-radius:6px !important;}
[data-testid="stTextArea"] textarea{background:#16191f !important;border:1px solid #252932 !important;color:#e2e8f0 !important;font-size:13px !important;font-family:monospace !important;}
.page-title{font-size:18px;font-weight:600;color:#e2e8f0;padding-bottom:10px;border-bottom:1px solid #252932;margin-bottom:20px;}
.sec-label{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.8px;margin:16px 0 8px 0;}
.sugestao{background:#0d1e35;border:1px solid #1a3a5c;border-radius:6px;padding:8px 12px;font-size:12px;color:#7eb8f7;margin:4px 0 8px;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:#111318;}
::-webkit-scrollbar-thumb{background:#252932;border-radius:3px;}
</style>
""", unsafe_allow_html=True)

def fmt(v):
    if v is None or v == "": return "—"
    try: return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except: return "—"

def titulo(t): st.markdown(f'<div class="page-title">{t}</div>', unsafe_allow_html=True)
def sec(t):    st.markdown(f'<p class="sec-label">{t}</p>', unsafe_allow_html=True)
def sug(t):    st.markdown(f'<div class="sugestao">💡 {t}</div>', unsafe_allow_html=True)
def nv(v):
    try: return float(v) if v else 0.0
    except: return 0.0

def hash_senha(s): return hashlib.sha256(s.encode()).hexdigest()

def login_valido(u, s):
    r = supabase.table("usuarios").select("*").eq("usuario",u).eq("senha_hash",hash_senha(s)).execute()
    return len(r.data) > 0

def get_checklist(mes):
    r = supabase.table("checklist").select("*").eq("mes",mes).execute()
    return {d["tarefa"]:d for d in r.data}

def salvar_tarefa(mes, tarefa, status, obs):
    ex = supabase.table("checklist").select("id").eq("mes",mes).eq("tarefa",tarefa).execute()
    d = {"mes":mes,"tarefa":tarefa,"status":status,"obs":obs,"atualizado_em":datetime.now().isoformat()}
    if ex.data: supabase.table("checklist").update(d).eq("id",ex.data[0]["id"]).execute()
    else:        supabase.table("checklist").insert(d).execute()

def get_ap(mes):
    r = supabase.table("apuracao").select("*").eq("mes",mes).execute()
    return r.data[0] if r.data else {}

def salvar_ap(mes, d):
    ex = supabase.table("apuracao").select("id").eq("mes",mes).execute()
    d["mes"]=mes; d["atualizado_em"]=datetime.now().isoformat()
    if ex.data: supabase.table("apuracao").update(d).eq("id",ex.data[0]["id"]).execute()
    else:        supabase.table("apuracao").insert(d).execute()

def get_metas(mes):
    r = supabase.table("metas").select("*").eq("mes",mes).execute()
    return r.data[0] if r.data else {}

def salvar_metas(mes, d):
    ex = supabase.table("metas").select("id").eq("mes",mes).execute()
    d["mes"]=mes
    if ex.data: supabase.table("metas").update(d).eq("id",ex.data[0]["id"]).execute()
    else:        supabase.table("metas").insert(d).execute()

def get_ir(mes):
    r = supabase.table("igreja_retiradas").select("*").eq("mes",mes).execute()
    return r.data[0] if r.data else {}

def salvar_ir(mes, d):
    ex = supabase.table("igreja_retiradas").select("id").eq("mes",mes).execute()
    d["mes"]=mes
    if ex.data: supabase.table("igreja_retiradas").update(d).eq("id",ex.data[0]["id"]).execute()
    else:        supabase.table("igreja_retiradas").insert(d).execute()


def get_tarefas_custom():
    r = supabase.table("tarefas_custom").select("*").order("secao").order("id").execute()
    return r.data if r.data else []

def add_tarefa_custom(secao, descricao):
    supabase.table("tarefas_custom").insert({"secao": secao, "descricao": descricao}).execute()

def del_tarefa_custom(id_tarefa):
    supabase.table("tarefas_custom").delete().eq("id", id_tarefa).execute()

def get_meses():
    r = supabase.table("apuracao").select("mes").execute()
    return sorted(set(d["mes"] for d in r.data), reverse=True)

# ── LOGIN ─────────────────────────────────────────────────────────────────────
def tela_login():
    logo = get_logo_b64()
    logo_html = f'<img src="data:image/jpeg;base64,{logo}" width="90" style="border-radius:50%;margin-bottom:8px">' if logo else '<div style="font-size:42px">📋</div>'
    st.markdown(f'<div style="text-align:center;padding-top:60px">{logo_html}<div style="font-size:22px;font-weight:700;color:#e2e8f0;margin:8px 0 4px">Fechamento Mensal</div><div style="font-size:13px;color:#6b7280;margin-bottom:32px">Grupo Prates · Macaé/RJ</div></div>', unsafe_allow_html=True)
    col = st.columns([1,1.2,1])[1]
    with col:
        st.markdown('<div style="background:#16191f;border:1px solid #252932;border-radius:12px;padding:32px">', unsafe_allow_html=True)
        u = st.text_input("👤 Usuário", placeholder="seu usuario")
        s = st.text_input("🔒 Senha", type="password", placeholder="••••••••")
        if st.button("Entrar", use_container_width=True):
            if login_valido(u, s):
                st.session_state.logado = True
                st.session_state.usuario = u
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        st.markdown('</div>', unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        logo = get_logo_b64()
        if logo:
            st.markdown(f'<div style="text-align:center;padding:16px 8px 4px"><img src="data:image/jpeg;base64,{logo}" width="80" style="border-radius:50%"></div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;padding:4px 8px 8px"><div style="font-size:14px;font-weight:700;color:#e2e8f0;margin:4px 0 2px">Fechamento Mensal</div><div style="font-size:11px;color:#6b7280">Grupo Prates</div></div>', unsafe_allow_html=True)
        st.markdown('<hr style="border-color:#252932;margin:10px 0">', unsafe_allow_html=True)
        mes = st.text_input("📅 Mês de referência", value=datetime.today().strftime('%Y-%m'), key="mes_ref")
        st.markdown('<hr style="border-color:#252932;margin:10px 0">', unsafe_allow_html=True)
        if "pagina" not in st.session_state: st.session_state.pagina = "📋 Checklist"
        for item in ["📋 Checklist","💰 Apuração Financeira","🎯 Metas","⛪ Igreja & Retiradas","📊 Histórico","📱 Resumo WhatsApp"]:
            if st.button(item, key=f"nav_{item}", use_container_width=True):
                st.session_state.pagina = item; st.rerun()
        st.markdown('<hr style="border-color:#252932;margin:10px 0">', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#3a4050;font-size:11px;text-align:center">👤 {st.session_state.get("usuario","")}</p>', unsafe_allow_html=True)
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logado = False; st.rerun()
        st.markdown('<p style="text-align:center;color:#3a4050;font-size:10px;margin-top:8px">Grupo Prates · v2.0</p>', unsafe_allow_html=True)
        return mes

# ── CHECKLIST ─────────────────────────────────────────────────────────────────
def pagina_checklist(mes):
    titulo(f"📋 Checklist — Fechamento {mes}")
    dados = get_checklist(mes)
    conc = sum(1 for d in dados.values() if d.get("status")=="✅ Concluído")
    na   = sum(1 for d in dados.values() if d.get("status")=="⊘ N/A")
    pend = TOTAL_TAREFAS - conc - na
    ef   = TOTAL_TAREFAS - na
    pct  = int(conc/ef*100) if ef>0 else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total",TOTAL_TAREFAS); c2.metric("✅ Concluídas",conc)
    c3.metric("☐ Pendentes",pend);    c4.metric("Progresso",f"{pct}%")
    cor = "#22c55e" if pct==100 else "#2d7a4f" if pct>=50 else "#d97706"
    st.markdown(f'<div style="background:#252932;border-radius:6px;height:10px;margin:8px 0 20px"><div style="background:{cor};width:{pct}%;height:10px;border-radius:6px"></div></div>', unsafe_allow_html=True)
    if pct==100: st.success("🎉 Fechamento 100% concluído! Glória a Deus!")
    tarefas_custom = get_tarefas_custom()
    custom_por_secao = {}
    for tc in tarefas_custom:
        custom_por_secao.setdefault(tc["secao"], []).append(tc)

    todas_secoes = list(dict.fromkeys([s for s,_ in TAREFAS] + list(custom_por_secao.keys())))

    for secao in todas_secoes:
        sec(secao)
        tarefas_fixas = dict(TAREFAS).get(secao, [])
        tarefas_desta_secao = list(tarefas_fixas) + [t["descricao"] for t in custom_por_secao.get(secao, [])]
        ids_custom = {t["descricao"]: t["id"] for t in custom_por_secao.get(secao, [])}

        for tarefa in tarefas_desta_secao:
            d = dados.get(tarefa,{})
            st_at = d.get("status","☐ Pendente")
            ob_at = d.get("obs","")
            is_custom = tarefa in ids_custom
            label = f"{st_at[:2]}  {tarefa}" + (" 🔧" if is_custom else "")
            with st.expander(label):
                c1,c2 = st.columns([2,3])
                ns = c1.selectbox("Status",STATUS_OPTS, index=STATUS_OPTS.index(st_at) if st_at in STATUS_OPTS else 0, key=f"st_{mes}_{tarefa}")
                no = c2.text_input("Observação", value=ob_at, key=f"ob_{mes}_{tarefa}")
                col_s, col_d = st.columns([3,1])
                if col_s.button("💾 Salvar", key=f"sv_{mes}_{tarefa}"):
                    salvar_tarefa(mes, tarefa, ns, no); st.success("Salvo!"); st.rerun()
                if is_custom:
                    if col_d.button("🗑️ Excluir", key=f"del_{tarefa}"):
                        del_tarefa_custom(ids_custom[tarefa]); st.success("Tarefa excluída!"); st.rerun()

    st.markdown('<hr style="border-color:#252932;margin:20px 0">', unsafe_allow_html=True)
    sec("➕ Adicionar Nova Tarefa Personalizada")
    secoes_disponiveis = [s for s,_ in TAREFAS] + ["NOVA SEÇÃO PERSONALIZADA"]
    c1,c2,c3 = st.columns([2,3,1])
    secao_nova = c1.selectbox("Seção", secoes_disponiveis, key="nova_secao")
    if secao_nova == "NOVA SEÇÃO PERSONALIZADA":
        secao_nova = c1.text_input("Nome da nova seção", key="nome_nova_secao")
    desc_nova = c2.text_input("Descrição da tarefa", key="nova_tarefa_desc")
    if c3.button("➕ Adicionar", key="btn_add_tarefa"):
        if desc_nova and secao_nova:
            add_tarefa_custom(secao_nova, desc_nova)
            st.success(f"Tarefa adicionada!"); st.rerun()
        else:
            st.warning("Preencha a seção e a descrição.")

# ── APURAÇÃO ──────────────────────────────────────────────────────────────────
def ni(label, key, ap):
    return st.number_input(label, value=float(ap.get(key) or 0), step=0.01, format="%.2f", key=key)

def bloco(ap, px, nome):
    sec(f"Resultado Principal — {nome}")
    c1,c2 = st.columns(2)
    lb = c1.number_input(f"Lucro Bruto (R$)", value=float(ap.get(f"{px}_lb") or 0), step=0.01, format="%.2f", key=f"{px}_lb")
    de = c1.number_input(f"Despesa (R$)",     value=float(ap.get(f"{px}_de") or 0), step=0.01, format="%.2f", key=f"{px}_de")
    res = lb - de
    diz = res*0.10 if res>0 else 0
    c2.metric("Resultado (=)", fmt(res))
    c2.metric("Dízimo 10% automático", fmt(diz))
    if diz>0: sug(f"Distribuição do Dízimo sugerida → 70% direto à Igreja = {fmt(diz*0.7)}  |  30% para Social + Missão = {fmt(diz*0.3)}")
    c3,c4,c5 = st.columns(3)
    of = c3.number_input("Oferta (R$)",  value=float(ap.get(f"{px}_oferta") or 0), step=0.01, format="%.2f", key=f"{px}_oferta")
    so = c4.number_input("Social (R$)",  value=float(ap.get(f"{px}_social") or 0), step=0.01, format="%.2f", key=f"{px}_social")
    if diz>0: sug(f"Sugestão para Social (20% do dízimo) → {fmt(diz*0.2)}")
    mi = c5.number_input("Missão (R$)",  value=float(ap.get(f"{px}_missao") or 0), step=0.01, format="%.2f", key=f"{px}_missao")
    if diz>0: sug(f"Sugestão para Missão (10% do dízimo) → {fmt(diz*0.1)}")
    dp = st.number_input("Despesa Pessoal (R$)", value=float(ap.get(f"{px}_desp_pes") or 0), step=0.01, format="%.2f", key=f"{px}_desp_pes")
    tc = diz+of+so+mi
    ll_p = res - tc - dp

    st.markdown('<hr style="border-color:#252932;margin:10px 0">', unsafe_allow_html=True)
    sec(f"Sobras e Faltas — {nome}")
    c1,c2 = st.columns(2)
    lb2 = c1.number_input("Lucro Bruto S&F (R$)", value=float(ap.get(f"{px}_sf_lb") or 0), step=0.01, format="%.2f", key=f"{px}_sf_lb")
    de2 = c1.number_input("Despesa S&F (R$)",     value=float(ap.get(f"{px}_sf_de") or 0), step=0.01, format="%.2f", key=f"{px}_sf_de")
    res2 = lb2-de2; diz2 = res2*0.10 if res2>0 else 0
    c2.metric("Resultado S&F (=)", fmt(res2))
    c2.metric("Dízimo S&F 10%", fmt(diz2))
    if diz2>0: sug(f"Distribuição do Dízimo S&F sugerida → 70% direto à Igreja = {fmt(diz2*0.7)}  |  30% para Social + Missão = {fmt(diz2*0.3)}")
    c3,c4,c5 = st.columns(3)
    of2 = c3.number_input("Oferta S&F (R$)", value=float(ap.get(f"{px}_sf_oferta") or 0), step=0.01, format="%.2f", key=f"{px}_sf_oferta")
    so2 = c4.number_input("Social S&F (R$)", value=float(ap.get(f"{px}_sf_social") or 0), step=0.01, format="%.2f", key=f"{px}_sf_social")
    mi2 = c5.number_input("Missão S&F (R$)", value=float(ap.get(f"{px}_sf_missao") or 0), step=0.01, format="%.2f", key=f"{px}_sf_missao")
    tc2 = diz2+of2+so2+mi2
    ll_sf = res2-tc2
    total = ll_p+ll_sf
    tc_tot = tc+tc2
    st.markdown('<hr style="border-color:#252932;margin:10px 0">', unsafe_allow_html=True)
    cx1,cx2,cx3 = st.columns(3)
    cx1.metric("Total Contrib. Igreja", fmt(tc_tot))
    cx2.metric("LL Principal", fmt(ll_p))
    cx3.metric(f"💚 LL {nome.upper()} TOTAL", fmt(total))
    return {f"{px}_lb":lb,f"{px}_de":de,f"{px}_dizimo":diz,f"{px}_oferta":of,f"{px}_social":so,f"{px}_missao":mi,
            f"{px}_desp_pes":dp,f"{px}_ll_p":ll_p,f"{px}_sf_lb":lb2,f"{px}_sf_de":de2,
            f"{px}_sf_dizimo":diz2,f"{px}_sf_oferta":of2,f"{px}_sf_social":so2,f"{px}_sf_missao":mi2,
            f"{px}_ll_sf":ll_sf,f"{px}_total":total,f"{px}_contrib_total":tc_tot}

def pagina_apuracao(mes):
    titulo(f"💰 Apuração Financeira — {mes}")
    ap = get_ap(mes)
    t1,t2,t3 = st.tabs(["⚡ Prates Eletrônico","🎨 Prates Sublimação","📊 Consolidado"])
    with t1: de = bloco(ap,"e","Prates Eletrônico")
    with t2: ds = bloco(ap,"s","Prates Sublimação")
    with t3:
        sec("CONSOLIDADO DO GRUPO PRATES")
        ll_e=de.get("e_total",0); ll_s=ds.get("s_total",0)
        tg=ll_e+ll_s; tc=de.get("e_contrib_total",0)+ds.get("s_contrib_total",0)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("LL Eletrônico",fmt(ll_e)); c2.metric("LL Sublimação",fmt(ll_s))
        c3.metric("Total Igreja",fmt(tc));    c4.metric("🏆 LL TOTAL GRUPO",fmt(tg))
    st.markdown('<hr style="border-color:#252932;margin:16px 0">', unsafe_allow_html=True)
    if st.button("💾 Salvar Apuração Completa"):
        salvar_ap(mes, {**de,**ds,"total_grupo":tg,"total_contrib":tc})
        st.success(f"Apuração de {mes} salva!"); st.rerun()

# ── METAS ─────────────────────────────────────────────────────────────────────
def pagina_metas(mes):
    titulo(f"🎯 Metas — {mes}")
    ap=get_ap(mes); mt=get_metas(mes)
    st.info("Defina as metas. O realizado é puxado automaticamente da Apuração.")
    indicadores = [
        ("LL Eletrônico — Principal","e_ll_p","meta_e_ll_p"),
        ("LL Eletrônico — S&F","e_ll_sf","meta_e_ll_sf"),
        ("Total Eletrônico","e_total","meta_e_total"),
        ("LL Sublimação — Principal","s_ll_p","meta_s_ll_p"),
        ("LL Sublimação — S&F","s_ll_sf","meta_s_ll_sf"),
        ("Total Sublimação","s_total","meta_s_total"),
        ("LL Total do Grupo","total_grupo","meta_total"),
        ("Total Contribuições Igreja","total_contrib","meta_contrib"),
    ]
    novos={}
    for label,ak,mk in indicadores:
        real=nv(ap.get(ak)); meta=float(mt.get(mk) or 0); dif=real-meta
        st_ic = "✅" if real>=meta and meta>0 else ("⚠️" if real>=meta*0.9 and meta>0 else ("❌" if meta>0 else "🎯"))
        with st.expander(f"{st_ic}  {label}"):
            c1,c2,c3,c4=st.columns(4)
            nm=c1.number_input("Meta (R$)",value=meta,step=0.01,format="%.2f",key=mk)
            c2.metric("Realizado",fmt(real)); c3.metric("Diferença",fmt(dif))
            c4.metric("Status","✅ Meta Atingida" if real>=meta and meta>0 else ("⚠️ Quase" if real>=meta*0.9 and meta>0 else ("❌ Abaixo" if meta>0 else "—")))
            novos[mk]=nm
    if st.button("💾 Salvar Metas"):
        salvar_metas(mes,novos); st.success("Metas salvas!"); st.rerun()

# ── IGREJA & RETIRADAS ────────────────────────────────────────────────────────
def pagina_igreja(mes):
    titulo(f"⛪ Igreja & Retiradas — {mes}")
    ir=get_ir(mes); ap=get_ap(mes)
    t1,t2=st.tabs(["⛪ Contribuições à Igreja","💼 Retiradas Pessoais"])
    with t1:
        st.info("Registre os valores enviados à Igreja neste mês.")
        c1,c2,c3=st.columns(3)
        diz_e =c1.number_input("Dízimo Eletrônico (R$)",value=float(ir.get("diz_e") or nv(ap.get("e_dizimo"))+nv(ap.get("e_sf_dizimo"))),step=0.01,format="%.2f",key="ir_diz_e")
        diz_s =c2.number_input("Dízimo Sublimação (R$)",value=float(ir.get("diz_s") or nv(ap.get("s_dizimo"))+nv(ap.get("s_sf_dizimo"))),step=0.01,format="%.2f",key="ir_diz_s")
        oferta=c3.number_input("Oferta (R$)",value=float(ir.get("oferta") or 0),step=0.01,format="%.2f",key="ir_oferta")
        c4,c5=st.columns(2)
        social=c4.number_input("Social (R$)",value=float(ir.get("social") or 0),step=0.01,format="%.2f",key="ir_social")
        missao=c5.number_input("Missão (R$)",value=float(ir.get("missao") or 0),step=0.01,format="%.2f",key="ir_missao")
        ti=diz_e+diz_s+oferta+social+missao
        st.metric("Total Enviado à Igreja",fmt(ti))
    with t2:
        st.info("Registre as retiradas pessoais do mês.")
        c1,c2,c3=st.columns(3)
        rs=c1.number_input("Sandro (R$)",value=float(ir.get("ret_sandro") or 0),step=0.01,format="%.2f",key="ret_sandro")
        ro=c2.number_input("Outro Sócio (R$)",value=float(ir.get("ret_outro") or 0),step=0.01,format="%.2f",key="ret_outro")
        rx=c3.number_input("Outros (R$)",value=float(ir.get("ret_outros") or 0),step=0.01,format="%.2f",key="ret_outros")
        tr=rs+ro+rx
        obs=st.text_input("Observações",value=ir.get("obs_ret",""),key="obs_ret")
        st.metric("Total Retiradas",fmt(tr))
    st.markdown('<hr style="border-color:#252932;margin:16px 0">', unsafe_allow_html=True)
    if st.button("💾 Salvar Igreja & Retiradas"):
        salvar_ir(mes,{"diz_e":diz_e,"diz_s":diz_s,"oferta":oferta,"social":social,"missao":missao,
                       "total_igreja":ti,"ret_sandro":rs,"ret_outro":ro,"ret_outros":rx,"total_ret":tr,"obs_ret":obs})
        st.success("Salvo!"); st.rerun()

# ── HISTÓRICO ─────────────────────────────────────────────────────────────────
def pagina_historico():
    titulo("📊 Histórico de Fechamentos")
    meses=get_meses()
    if not meses: st.info("Nenhum fechamento registrado ainda."); return
    rows=[]
    for m in meses:
        ap=get_ap(m); ir=get_ir(m); dados=get_checklist(m)
        conc=sum(1 for d in dados.values() if d.get("status")=="✅ Concluído")
        rows.append({"Mês":m,"LL Eletrônico":nv(ap.get("e_total")),"LL Sublimação":nv(ap.get("s_total")),
                     "LL Total Grupo":nv(ap.get("total_grupo")),"Contrib. Igreja":nv(ir.get("total_igreja")),
                     "Retirada Pessoal":nv(ir.get("total_ret")),"Dízimo Total":nv(ir.get("diz_e"))+nv(ir.get("diz_s")),
                     "Tarefas":f"{conc}/{TOTAL_TAREFAS}"})
    df=pd.DataFrame(rows)
    sec("Resumo Anual")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Total LL Grupo",fmt(df["LL Total Grupo"].sum()))
    c2.metric("Total Igreja",fmt(df["Contrib. Igreja"].sum()))
    c3.metric("Total Retiradas",fmt(df["Retirada Pessoal"].sum()))
    c4.metric("Meses",len(df))
    sec("Detalhamento por Mês")
    df2=df.copy()
    for c in ["LL Eletrônico","LL Sublimação","LL Total Grupo","Contrib. Igreja","Retirada Pessoal","Dízimo Total"]:
        df2[c]=df2[c].apply(fmt)
    st.dataframe(df2,use_container_width=True,hide_index=True)
    mes_sel=st.selectbox("Ver checklist do mês:",meses)
    dados=get_checklist(mes_sel)
    conc=sum(1 for d in dados.values() if d.get("status")=="✅ Concluído")
    na=sum(1 for d in dados.values() if d.get("status")=="⊘ N/A")
    pct=int(conc/(TOTAL_TAREFAS-na)*100) if (TOTAL_TAREFAS-na)>0 else 0
    sec(f"Checklist — {mes_sel} ({pct}% concluído)")
    rows2=[]
    for secao,tarefas in TAREFAS:
        for t in tarefas:
            d=dados.get(t,{})
            rows2.append({"Seção":secao,"Tarefa":t,"Status":d.get("status","☐ Pendente"),"Obs":d.get("obs","")})
    st.dataframe(pd.DataFrame(rows2),use_container_width=True,hide_index=True)

# ── RESUMO WHATSAPP ───────────────────────────────────────────────────────────
def pagina_resumo(mes):
    titulo(f"📱 Resumo para WhatsApp — {mes}")
    ap=get_ap(mes); ir=get_ir(mes); dados=get_checklist(mes)
    conc=sum(1 for d in dados.values() if d.get("status")=="✅ Concluído")
    ll_e=nv(ap.get("e_total")); ll_s=nv(ap.get("s_total"))
    total=nv(ap.get("total_grupo")); igreja=nv(ir.get("total_igreja"))
    texto=f"""📋  FECHAMENTO  —  {mes}
{'─'*44}

⚡  PRATES ELETRÔNICO
    Resultado Principal   →   {fmt(nv(ap.get('e_lb'))-nv(ap.get('e_de')))}   |   Dízimo: {fmt(nv(ap.get('e_dizimo')))}
    Sobras e Faltas          →   {fmt(nv(ap.get('e_sf_lb'))-nv(ap.get('e_sf_de')))}   |   Dízimo: {fmt(nv(ap.get('e_sf_dizimo')))}
    Lucro Líquido Total   →   {fmt(ll_e)}

🎨  PRATES SUBLIMAÇÃO
    Resultado Principal   →   {fmt(nv(ap.get('s_lb'))-nv(ap.get('s_de')))}   |   Dízimo: {fmt(nv(ap.get('s_dizimo')))}
    Sobras e Faltas          →   {fmt(nv(ap.get('s_sf_lb'))-nv(ap.get('s_sf_de')))}   |   Dízimo: {fmt(nv(ap.get('s_sf_dizimo')))}
    Lucro Líquido Total   →   {fmt(ll_s)}

⛪  CONTRIBUIÇÕES À IGREJA
    Dízimo Eletrônico    →   {fmt(nv(ir.get('diz_e')))}
    Dízimo Sublimação   →   {fmt(nv(ir.get('diz_s')))}
    Oferta                        →   {fmt(nv(ir.get('oferta')))}
    Social                        →   {fmt(nv(ir.get('social')))}
    Missão                       →   {fmt(nv(ir.get('missao')))}
    TOTAL ENVIADO À IGREJA  →   {fmt(igreja)}

📊  LUCRO LÍQUIDO TOTAL DO GRUPO  →  {fmt(total)}
      Checklist: {conc} de {TOTAL_TAREFAS} tarefas concluídas
{'─'*44}"""
    st.text_area("Copie o texto abaixo:", texto, height=500)

# ── MAIN ──────────────────────────────────────────────────────────────────────
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    tela_login()
else:
    mes = sidebar()
    pag = st.session_state.get("pagina","📋 Checklist")
    if   pag=="📋 Checklist":            pagina_checklist(mes)
    elif pag=="💰 Apuração Financeira":   pagina_apuracao(mes)
    elif pag=="🎯 Metas":                pagina_metas(mes)
    elif pag=="⛪ Igreja & Retiradas":    pagina_igreja(mes)
    elif pag=="📊 Histórico":            pagina_historico()
    elif pag=="📱 Resumo WhatsApp":      pagina_resumo(mes)
