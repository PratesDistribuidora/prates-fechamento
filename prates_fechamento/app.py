"""
app.py — Sistema Fechamento Mensal · Grupo Prates v3.1
Checklist + Apuração + Metas + Igreja & Retiradas + Resumo WhatsApp
+ Cadastro de Usuários + Níveis de Acesso + Recuperação de Senha
"""
import streamlit as st
from datetime import datetime
import pandas as pd
import os, base64

_favicon = "📋"
try:
    from PIL import Image as _PIL_Image
    for _p in ["prates_fechamento/logo.jpeg","prates_fechamento/logo.jpg",
               "prates_fechamento/logo.png","logo.jpeg","logo.jpg","logo.png"]:
        if os.path.exists(_p):
            _favicon = _PIL_Image.open(_p)
            break
except Exception:
    pass

st.set_page_config(
    page_title="Fechamento Mensal · Grupo Prates",
    page_icon=_favicon,
    layout="wide",
    initial_sidebar_state="auto",
)

@st.cache_resource
def get_supabase():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

@st.cache_data(show_spinner=False)
def get_logo_b64():
    for nome in ["logo.jpeg","logo.jpg","logo.png"]:
        if os.path.exists(nome):
            with open(nome,"rb") as f:
                return base64.b64encode(f.read()).decode()
    return None



NIVEIS = {
    "admin":  {"label": "Administrador", "cor": "#22c55e", "icone": "👑"},
    "editor": {"label": "Editor",        "cor": "#3b82f6", "icone": "✏️"},
    "viewer": {"label": "Visualizador",  "cor": "#94a3b8", "icone": "👁️"},
}
PERMISSOES = {
    "admin":  ["ver", "editar", "gerenciar_usuarios"],
    "editor": ["ver", "editar"],
    "viewer": ["ver"],
}

def pode(permissao):
    nivel = st.session_state.get("nivel_acesso", "viewer")
    return permissao in PERMISSOES.get(nivel, [])



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

TAREFAS = [
    ("RELATÓRIOS E LANÇAMENTOS", [
        "Relatório — Conferir e Lançar Prates Eletrônico",
        "Relatório — Lançar Sobras e Faltas Caixa Prates Eletrônico",
        "Relatório — Conferir e Lançar Prates Sublimação",
        "Relatório — Lançar Sobras e Faltas Caixa Prates Sublimação",
    ]),
    ("DOCUMENTOS E VERIFICAÇÕES FINANCEIRAS", [
        "Boletos","Papéis Amarelos (Cartão)","Caderno (Pagamento Funcionários)",
        "Cartão Banco do Brasil","Verificar Taxa Máquina Cartão",
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

# ── BANCO ─────────────────────────────────────────────────
def get_checklist(mes):
    r = supabase.table("checklist").select("*").eq("mes",mes).execute()
    return {d["tarefa"]:d for d in r.data}

def salvar_tarefa(mes, tarefa, status, obs):
    ex = supabase.table("checklist").select("id").eq("mes",mes).eq("tarefa",tarefa).execute()
    d = {"mes":mes,"tarefa":tarefa,"status":status,"obs":obs,"atualizado_em":datetime.now().isoformat()}
    if ex.data: supabase.table("checklist").update(d).eq("id",ex.data[0]["id"]).execute()
    else: supabase.table("checklist").insert(d).execute()

def get_ap(mes):
    r = supabase.table("apuracao").select("*").eq("mes",mes).execute()
    return r.data[0] if r.data else {}

def salvar_ap(mes, d):
    ex = supabase.table("apuracao").select("id").eq("mes",mes).execute()
    d["mes"]=mes; d["atualizado_em"]=datetime.now().isoformat()
    if ex.data: supabase.table("apuracao").update(d).eq("id",ex.data[0]["id"]).execute()
    else: supabase.table("apuracao").insert(d).execute()

def get_metas(mes):
    r = supabase.table("metas").select("*").eq("mes",mes).execute()
    return r.data[0] if r.data else {}

def salvar_metas(mes, d):
    ex = supabase.table("metas").select("id").eq("mes",mes).execute()
    d["mes"]=mes
    if ex.data: supabase.table("metas").update(d).eq("id",ex.data[0]["id"]).execute()
    else: supabase.table("metas").insert(d).execute()

def get_ir(mes):
    r = supabase.table("igreja_retiradas").select("*").eq("mes",mes).execute()
    return r.data[0] if r.data else {}

def salvar_ir(mes, d):
    ex = supabase.table("igreja_retiradas").select("id").eq("mes",mes).execute()
    d["mes"]=mes
    if ex.data: supabase.table("igreja_retiradas").update(d).eq("id",ex.data[0]["id"]).execute()
    else: supabase.table("igreja_retiradas").insert(d).execute()

def get_tarefas_custom():
    r = supabase.table("tarefas_custom").select("*").order("secao").order("id").execute()
    return r.data if r.data else []

def add_tarefa_custom(secao, descricao):
    supabase.table("tarefas_custom").insert({"secao":secao,"descricao":descricao}).execute()

def del_tarefa_custom(id_tarefa):
    supabase.table("tarefas_custom").delete().eq("id",id_tarefa).execute()

def get_meses():
    r = supabase.table("apuracao").select("mes").execute()
    return sorted(set(d["mes"] for d in r.data), reverse=True)

# ── AUTH ──────────────────────────────────────────────────
def fazer_login(login_val, senha):
    import bcrypt, hashlib
    val = login_val.strip()
    # Busca todos e filtra em Python — evita erro quando email é NULL
    r = supabase.table("usuarios").select("id,usuario,email,senha_hash,nivel,ativo").execute()
    if not r.data: return None
    u = None
    for row in r.data:
        if row.get("usuario","").lower() == val.lower():
            u = row; break
        if row.get("email") and row["email"].lower() == val.lower():
            u = row; break
    if not u: return None
    if not u.get("ativo", True): return None
    h = u["senha_hash"]
    try:
        if h.startswith("$2b$") or h.startswith("$2a$"):
            ok = bcrypt.checkpw(senha.encode(), h.encode())
        else:
            ok = (hashlib.sha256(senha.encode()).hexdigest() == h)
            if ok:
                nh = bcrypt.hashpw(senha.encode(), bcrypt.gensalt(12)).decode()
                supabase.table("usuarios").update({"senha_hash": nh}).eq("id", u["id"]).execute()
    except Exception:
        return None
    if not ok: return None
    try:
        supabase.table("usuarios").update({"ultimo_acesso": datetime.utcnow().isoformat()}).eq("id", u["id"]).execute()
    except Exception:
        pass
    return u

def solicitar_recuperacao(email):
    import secrets, smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from datetime import timedelta
    r = supabase.table("usuarios").select("id,email").eq("email", email.lower().strip()).eq("ativo", True).execute()
    if not r.data: return
    u = r.data[0]
    token = secrets.token_urlsafe(32)
    expira = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    supabase.table("recuperacao_senha").insert({"usuario_id": u["id"], "token": token, "expira_em": expira}).execute()
    link = f"https://fechamento-prates.streamlit.app?token={token}"
    html = f'<html><body style="font-family:Arial;background:#111318;color:#e2e8f0;padding:2rem"><div style="max-width:480px;margin:auto;background:#16191f;border-radius:12px;padding:2rem;border:1px solid #22c55e"><h2 style="color:#22c55e">Recuperação de Senha</h2><p>Clique para redefinir sua senha no <strong>Fechamento Mensal — Grupo Prates</strong>. Válido por 1 hora.</p><a href="{link}" style="display:inline-block;background:#22c55e;color:#111318;padding:.8rem 2rem;border-radius:8px;text-decoration:none;font-weight:bold">Redefinir Senha</a></div></body></html>'
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Recuperação de Senha — Grupo Prates"
        msg["From"] = st.secrets["EMAIL_REMETENTE"]
        msg["To"] = u["email"]
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(st.secrets["EMAIL_REMETENTE"], st.secrets["EMAIL_SENHA_APP"])
            srv.send_message(msg)
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")

def validar_token(token):
    r = supabase.table("recuperacao_senha").select("usuario_id,expira_em,usado").eq("token", token).execute()
    if not r.data: return None
    rec = r.data[0]
    if rec["usado"]: return None
    if datetime.fromisoformat(rec["expira_em"]) < datetime.utcnow(): return None
    return rec["usuario_id"]

def redefinir_senha(token, nova):
    import bcrypt
    uid = validar_token(token)
    if not uid: return False
    h = bcrypt.hashpw(nova.encode(), bcrypt.gensalt(12)).decode()
    supabase.table("usuarios").update({"senha_hash": h}).eq("id", uid).execute()
    supabase.table("recuperacao_senha").update({"usado": True}).eq("token", token).execute()
    return True

# ── TELAS AUTH ────────────────────────────────────────────
def tela_login():
    logo = get_logo_b64()

    # CSS da tela de login
    st.markdown("""
    <style>
    html,body,[class*="css"]{font-family:'Segoe UI',sans-serif;}
    [data-testid="stAppViewContainer"]{background:#111318;}
    [data-testid="stHeader"]{background:transparent;}
    [data-testid="stAppViewContainer"] > .main { padding-top: 0 !important; }
    div[data-testid="stForm"] {
        background: #16191f;
        border: 1px solid #252932;
        border-radius: 16px;
        padding: 2rem;
    }
    [data-testid="stTextInput"] input {
        background:#16191f !important;
        border:1px solid #252932 !important;
        border-radius:5px !important;
        color:#e2e8f0 !important;
        font-size:13px !important;
    }
    .stButton>button {
        background:#1e6b3e;color:#fff;border:none;
        border-radius:5px;padding:6px 16px;
        font-size:13px;font-weight:500;width:100%;
    }
    .stButton>button:hover{background:#248a4e;}
    [data-testid="stFormSubmitButton"] button {
        background:#1e6b3e !important;color:#fff !important;
        border:none !important;border-radius:5px !important;
        font-size:13px !important;font-weight:500 !important;
    }

    footer{visibility:hidden;} #MainMenu{visibility:hidden;}
    </style>
    """, unsafe_allow_html=True)

    col = st.columns([1.5, 1, 1.5])[1]
    with col:
        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

        # Logo + título
        if logo:
            st.markdown(f"""
            <div style='text-align:center;margin-bottom:1.5rem'>
                <img src='data:image/jpeg;base64,{logo}'
                     style='width:90px;height:90px;border-radius:50%;
                            object-fit:cover;border:3px solid #22c55e;
                            margin-bottom:12px'>
                <div style='font-size:20px;font-weight:700;color:#e2e8f0'>
                    Fechamento Mensal
                </div>
                <div style='font-size:12px;color:#6b7280;margin-top:4px'>
                    Faça login para continuar
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='text-align:center;margin-bottom:1.5rem'>
                <div style='font-size:48px;margin-bottom:8px'>📋</div>
                <div style='font-size:20px;font-weight:700;color:#e2e8f0'>
                    Fechamento Mensal
                </div>
                <div style='font-size:12px;color:#6b7280;margin-top:4px'>
                    Faça login para continuar
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Formulário — st.form garante que os valores são capturados corretamente
        with st.form("form_login", clear_on_submit=False):
            u = st.text_input("Usuário ou E-mail", placeholder="usuario ou email@...")
            s = st.text_input("Senha", type="password", placeholder="••••••••")
            entrar = st.form_submit_button("Entrar", use_container_width=True)

        if entrar:
            if not u or not s:
                st.warning("Preencha usuário e senha.")
            else:
                with st.spinner("Verificando..."):
                    usuario = fazer_login(u, s)
                if usuario:
                    st.session_state.logado        = True
                    st.session_state.usuario_id    = usuario["id"]
                    st.session_state.usuario       = usuario["usuario"]
                    st.session_state.usuario_email = usuario.get("email", "")
                    st.session_state.nivel_acesso  = usuario.get("nivel", "viewer")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            if st.button("🔑 Esqueci minha senha", key="btn_esqueci_unico", use_container_width=True):
                st.session_state.tela_auth = "recuperar"
                st.rerun()

        st.markdown("""
        <div style='text-align:center;margin-top:12px'>
            <span style='color:#6b7280;font-size:12px;cursor:pointer'
                  onclick='window.parent.postMessage({type:"streamlit:setComponentValue"}, "*")'>
            </span>
        </div>
        """, unsafe_allow_html=True)


        st.markdown("""
        <div style='text-align:center;color:#3a4050;font-size:11px;margin-top:1.5rem'>
            Grupo Prates · Macaé/RJ · v3.1
        </div>
        """, unsafe_allow_html=True)

def tela_recuperar_senha():
    col = st.columns([1,1.2,1])[1]
    with col:
        st.markdown("## 🔑 Recuperar Senha")
        st.caption("Digite seu e-mail. Você receberá um link em até 1 minuto.")
        with st.form("form_rec"):
            email = st.text_input("📧 E-mail")
            enviar = st.form_submit_button("Enviar link", use_container_width=True)
        if enviar:
            with st.spinner("Enviando..."):
                solicitar_recuperacao(email)
            st.success("✅ Se este e-mail estiver cadastrado, o link foi enviado!")
        if st.button("← Voltar ao Login"):
            st.session_state.tela_auth = None
            st.rerun()

def tela_redefinir_senha(token):
    col = st.columns([1,1.2,1])[1]
    with col:
        uid = validar_token(token)
        if not uid:
            st.error("❌ Link inválido ou expirado. Solicite um novo.")
            if st.button("← Voltar"):
                st.query_params.clear(); st.rerun()
            return
        st.markdown("## 🔒 Nova Senha")
        with st.form("form_nova"):
            nova     = st.text_input("Nova senha", type="password")
            confirma = st.text_input("Confirmar senha", type="password")
            salvar   = st.form_submit_button("Salvar", use_container_width=True)
        if salvar:
            if len(nova) < 8: st.warning("Mínimo 8 caracteres.")
            elif nova != confirma: st.error("As senhas não coincidem.")
            elif redefinir_senha(token, nova):
                st.success("✅ Senha redefinida! Faça login.")
                st.query_params.clear()
                st.session_state.tela_auth = None
                st.rerun()

# ── SIDEBAR ───────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        logo  = st.session_state.get("_logo_cache") or get_logo_b64()
        if logo: st.session_state["_logo_cache"] = logo
        nivel = st.session_state.get("nivel_acesso","viewer")
        info  = NIVEIS[nivel]
        nome  = st.session_state.get("usuario","")

        # Cabeçalho
        if logo:
            st.markdown(f"""
            <div style='padding:16px 12px 8px;display:flex;align-items:center;gap:12px'>
                <img src='data:image/jpeg;base64,{logo}'
                     style='width:52px;height:52px;border-radius:10px;object-fit:cover;flex-shrink:0'>
                <div>
                    <div style='font-size:13px;font-weight:700;color:#e2e8f0'>Fechamento Mensal</div>
                    <div style='font-size:11px;color:{info["cor"]}'>{info["icone"]} {nome} ({info["label"]})</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='padding:16px 12px 8px'>
                <div style='font-size:14px;font-weight:700;color:#e2e8f0'>Fechamento Mensal</div>
                <div style='font-size:11px;color:{info["cor"]};margin-top:2px'>{info["icone"]} {nome} ({info["label"]})</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<hr style="border-color:#252932;margin:6px 0 10px">', unsafe_allow_html=True)
        mes = st.text_input("📅 Mês", value=datetime.today().strftime('%Y-%m'), key="mes_ref")
        st.markdown('<hr style="border-color:#252932;margin:10px 0">', unsafe_allow_html=True)

        if "pagina" not in st.session_state:
            st.session_state.pagina = "📋 Checklist"

        # Itens do menu com cores por categoria (estilo Sublimação)
        MENU = [
            ("📋", "Checklist",          "#22c55e"),
            ("💰", "Apuração Financeira","#3b82f6"),
            ("🎯", "Metas",              "#a855f7"),
            ("⛪", "Igreja & Retiradas", "#f59e0b"),
            ("📊", "Histórico",          "#06b6d4"),
            ("📱", "Resumo WhatsApp",    "#22c55e"),
        ]
        if pode("gerenciar_usuarios"):
            MENU.append(("👥", "Usuários", "#94a3b8"))

        paginas_menu = [f"{icone} {label}" for icone, label, cor in MENU]

        if st.session_state.get("pagina") not in paginas_menu:
            st.session_state.pagina = paginas_menu[0]

        idx_atual = paginas_menu.index(st.session_state.pagina)
        pagina_sel = st.radio("", paginas_menu, index=idx_atual,
                              key="nav_radio", label_visibility="collapsed")
        st.session_state.pagina = pagina_sel

        st.markdown('<hr style="border-color:#252932;margin:10px 0">', unsafe_allow_html=True)
        if st.button("🚪  Sair", key="btn_sair", use_container_width=True):
            for k in ["logado","usuario_id","usuario","usuario_email","nivel_acesso","pagina"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown(f'<p style="text-align:center;color:#3a4050;font-size:10px;margin-top:12px">Grupo Prates · Macaé/RJ · v3.1</p>', unsafe_allow_html=True)
        return mes, pagina_sel

# ── PÁGINA USUÁRIOS ───────────────────────────────────────
def pagina_usuarios():
    import bcrypt
    titulo("👥 Gerenciar Usuários")
    tab_lista, tab_novo, tab_senha = st.tabs(["👥 Usuários", "➕ Novo Usuário", "🔒 Minha Senha"])
    with tab_lista:
        res = supabase.table("usuarios").select("id,usuario,email,nivel,ativo,ultimo_acesso,criado_em").order("criado_em").execute()
        for u in (res.data or []):
            info = NIVEIS.get(u.get("nivel","viewer"), NIVEIS["viewer"])
            ultimo = (u.get("ultimo_acesso") or "")[:10] or "nunca"
            status = "🟢" if u.get("ativo",True) else "🔴"
            with st.container(border=True):
                c1,c2,c3,c4 = st.columns([3,2,2,1])
                c1.markdown(f"**{status} {u['usuario']}**")
                c1.caption(u.get("email","—"))
                c2.markdown(f"<span style='color:{info['cor']}'>{info['icone']} {info['label']}</span>", unsafe_allow_html=True)
                c3.caption(f"Último acesso: {ultimo}")
                if u["id"] != st.session_state.get("usuario_id"):
                    with c4.popover("⚙️"):
                        nn = st.selectbox("Nível", list(NIVEIS.keys()), index=list(NIVEIS.keys()).index(u.get("nivel","viewer")), key=f"nivel_{u['id']}", format_func=lambda x: NIVEIS[x]["label"])
                        if st.button("Salvar nível", key=f"salvar_{u['id']}"):
                            supabase.table("usuarios").update({"nivel":nn}).eq("id",u["id"]).execute()
                            st.success("Salvo!"); st.rerun()
                        acao = "Desativar" if u.get("ativo",True) else "Ativar"
                        if st.button(f"{'🔴' if u.get('ativo',True) else '🟢'} {acao}", key=f"tog_{u['id']}"):
                            supabase.table("usuarios").update({"ativo": not u.get("ativo",True)}).eq("id",u["id"]).execute()
                            st.rerun()
    with tab_novo:
        with st.form("form_novo", clear_on_submit=True):
            nome    = st.text_input("Nome / usuário")
            email   = st.text_input("E-mail")
            nivel   = st.selectbox("Nível", list(NIVEIS.keys()), format_func=lambda x: f"{NIVEIS[x]['icone']} {NIVEIS[x]['label']}")
            senha   = st.text_input("Senha temporária", type="password")
            confirma= st.text_input("Confirmar senha", type="password")
            ok      = st.form_submit_button("Cadastrar", use_container_width=True)
        if ok:
            erros = []
            if not nome: erros.append("Nome obrigatório")
            if not email or "@" not in email: erros.append("E-mail inválido")
            if len(senha) < 8: erros.append("Senha mínima: 8 caracteres")
            if senha != confirma: erros.append("Senhas não coincidem")
            if erros:
                for e in erros: st.error(e)
            else:
                try:
                    h = bcrypt.hashpw(senha.encode(), bcrypt.gensalt(12)).decode()
                    supabase.table("usuarios").insert({"usuario":nome.strip(),"email":email.lower().strip(),"senha_hash":h,"nivel":nivel,"ativo":True}).execute()
                    st.success(f"✅ Usuário {nome} cadastrado!")
                except Exception as ex:
                    st.error("❌ E-mail já cadastrado." if "duplicate" in str(ex).lower() else f"Erro: {ex}")
    with tab_senha:
        st.caption(f"Usuário: {st.session_state.get('usuario_email','—')}")
        with st.form("form_senha", clear_on_submit=True):
            atual    = st.text_input("Senha atual", type="password")
            nova     = st.text_input("Nova senha", type="password")
            confirma2= st.text_input("Confirmar nova senha", type="password")
            alterar  = st.form_submit_button("Alterar senha", use_container_width=True)
        if alterar:
            import hashlib
            res2 = supabase.table("usuarios").select("senha_hash").eq("id", st.session_state.usuario_id).execute()
            hbd = res2.data[0]["senha_hash"]
            ok2 = bcrypt.checkpw(atual.encode(), hbd.encode()) if hbd.startswith("$2b$") else (hashlib.sha256(atual.encode()).hexdigest() == hbd)
            if not ok2: st.error("❌ Senha atual incorreta.")
            elif len(nova) < 8: st.warning("Mínimo 8 caracteres.")
            elif nova != confirma2: st.error("As senhas não coincidem.")
            else:
                nh = bcrypt.hashpw(nova.encode(), bcrypt.gensalt(12)).decode()
                supabase.table("usuarios").update({"senha_hash":nh}).eq("id", st.session_state.usuario_id).execute()
                st.success("✅ Senha alterada!")

# ── CHECKLIST ─────────────────────────────────────────────
def pagina_checklist(mes):
    titulo(f"📋 Checklist — Fechamento {mes}")
    dados = get_checklist(mes)
    conc = sum(1 for d in dados.values() if d.get("status")=="✅ Concluído")
    na   = sum(1 for d in dados.values() if d.get("status")=="⊘ N/A")
    pend = TOTAL_TAREFAS - conc - na
    ef   = TOTAL_TAREFAS - na
    pct  = int(conc/ef*100) if ef > 0 else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total",TOTAL_TAREFAS); c2.metric("✅ Concluídas",conc)
    c3.metric("☐ Pendentes",pend);    c4.metric("Progresso",f"{pct}%")
    cor = "#22c55e" if pct==100 else "#2d7a4f" if pct>=50 else "#d97706"
    st.markdown(f'<div style="background:#252932;border-radius:6px;height:10px;margin:8px 0 20px"><div style="background:{cor};width:{pct}%;height:10px;border-radius:6px"></div></div>', unsafe_allow_html=True)
    if pct==100: st.success("🎉 Fechamento 100% concluído! Glória a Deus!")
    ed = pode("editar")
    tarefas_custom = get_tarefas_custom()
    custom_por_secao = {}
    for tc in tarefas_custom: custom_por_secao.setdefault(tc["secao"],[]).append(tc)
    todas_secoes = list(dict.fromkeys([s for s,_ in TAREFAS] + list(custom_por_secao.keys())))
    for secao in todas_secoes:
        sec(secao)
        tarefas_fixas = dict(TAREFAS).get(secao,[])
        tarefas_desta = list(tarefas_fixas) + [t["descricao"] for t in custom_por_secao.get(secao,[])]
        ids_custom = {t["descricao"]:t["id"] for t in custom_por_secao.get(secao,[])}
        for tarefa in tarefas_desta:
            d=dados.get(tarefa,{}); st_at=d.get("status","☐ Pendente"); ob_at=d.get("obs",""); is_c=tarefa in ids_custom
            with st.expander(f"{st_at[:2]}  {tarefa}" + (" 🔧" if is_c else "")):
                if ed:
                    c1,c2=st.columns([2,3])
                    ns=c1.selectbox("Status",STATUS_OPTS,index=STATUS_OPTS.index(st_at) if st_at in STATUS_OPTS else 0,key=f"st_{mes}_{tarefa}")
                    no=c2.text_input("Observação",value=ob_at,key=f"ob_{mes}_{tarefa}")
                    cs,cd=st.columns([3,1])
                    if cs.button("💾 Salvar",key=f"sv_{mes}_{tarefa}"): salvar_tarefa(mes,tarefa,ns,no); st.success("Salvo!"); st.rerun()
                    if is_c and cd.button("🗑️",key=f"del_{tarefa}"): del_tarefa_custom(ids_custom[tarefa]); st.rerun()
                else:
                    st.caption(f"Status: {st_at}"); st.caption(f"Obs: {ob_at}" if ob_at else "")
                    st.info("🔒 Acesso somente leitura.")
    if ed:
        st.markdown('<hr style="border-color:#252932;margin:20px 0">', unsafe_allow_html=True)
        sec("➕ Adicionar Nova Tarefa")
        secoes_d=[s for s,_ in TAREFAS]+["NOVA SEÇÃO"]
        c1,c2,c3=st.columns([2,3,1])
        sn=c1.selectbox("Seção",secoes_d,key="nova_secao")
        if sn=="NOVA SEÇÃO": sn=c1.text_input("Nome da seção",key="nome_nova_secao")
        dn=c2.text_input("Descrição",key="nova_tarefa_desc")
        if c3.button("➕"):
            if dn and sn: add_tarefa_custom(sn,dn); st.rerun()
            else: st.warning("Preencha seção e descrição.")

# ── APURAÇÃO ──────────────────────────────────────────────
def bloco(ap, px, nome):
    ed = pode("editar")
    sec(f"Resultado Principal — {nome}")
    c1,c2=st.columns(2)
    lb=c1.number_input("Lucro Bruto (R$)",  value=float(ap.get(f"{px}_lb") or 0),step=0.01,format="%.2f",key=f"{px}_lb",disabled=not ed)
    de=c1.number_input("Despesa (R$)",       value=float(ap.get(f"{px}_de") or 0),step=0.01,format="%.2f",key=f"{px}_de",disabled=not ed)
    res=lb-de; diz_s=res*0.10 if res>0 else 0
    c2.metric("Resultado (=)",fmt(res))
    if diz_s>0: sug(f"Dízimo sugerido (10%) → {fmt(diz_s)}  |  70% Igreja={fmt(diz_s*0.7)}  |  20% Social={fmt(diz_s*0.2)}  |  10% Missão={fmt(diz_s*0.1)}")
    c3,c4,c5=st.columns(3)
    diz=c3.number_input("Dízimo (R$)",        value=float(ap.get(f"{px}_dizimo") or diz_s),step=0.01,format="%.2f",key=f"{px}_dizimo",disabled=not ed)
    of =c4.number_input("Oferta (R$)",         value=float(ap.get(f"{px}_oferta") or 0),   step=0.01,format="%.2f",key=f"{px}_oferta", disabled=not ed)
    dp =c5.number_input("Despesa Pessoal (R$)",value=float(ap.get(f"{px}_desp_pes") or 0), step=0.01,format="%.2f",key=f"{px}_desp_pes",disabled=not ed)
    c6,c7=st.columns(2)
    so=c6.number_input("Social (R$)",value=float(ap.get(f"{px}_social") or 0),step=0.01,format="%.2f",key=f"{px}_social",disabled=not ed)
    mi=c7.number_input("Missão (R$)",value=float(ap.get(f"{px}_missao") or 0),step=0.01,format="%.2f",key=f"{px}_missao",disabled=not ed)
    tc=diz+of+so+mi; ll_p=res-tc-dp
    st.markdown('<hr style="border-color:#252932;margin:10px 0">', unsafe_allow_html=True)
    sec(f"Sobras e Faltas — {nome}")
    c1,c2=st.columns(2)
    lb2=c1.number_input("Lucro Bruto S&F (R$)",value=float(ap.get(f"{px}_sf_lb") or 0),step=0.01,format="%.2f",key=f"{px}_sf_lb",disabled=not ed)
    de2=c1.number_input("Despesa S&F (R$)",     value=float(ap.get(f"{px}_sf_de") or 0),step=0.01,format="%.2f",key=f"{px}_sf_de",disabled=not ed)
    res2=lb2-de2; diz2_s=res2*0.10 if res2>0 else 0
    c2.metric("Resultado S&F (=)",fmt(res2))
    if diz2_s>0: sug(f"Dízimo S&F sugerido → {fmt(diz2_s)}")
    c3,c4=st.columns(2)
    diz2=c3.number_input("Dízimo S&F (R$)",value=float(ap.get(f"{px}_sf_dizimo") or diz2_s),step=0.01,format="%.2f",key=f"{px}_sf_dizimo",disabled=not ed)
    of2 =c4.number_input("Oferta S&F (R$)", value=float(ap.get(f"{px}_sf_oferta") or 0),   step=0.01,format="%.2f",key=f"{px}_sf_oferta", disabled=not ed)
    c6,c7=st.columns(2)
    so2=c6.number_input("Social S&F (R$)",value=float(ap.get(f"{px}_sf_social") or 0),step=0.01,format="%.2f",key=f"{px}_sf_social",disabled=not ed)
    mi2=c7.number_input("Missão S&F (R$)",value=float(ap.get(f"{px}_sf_missao") or 0),step=0.01,format="%.2f",key=f"{px}_sf_missao",disabled=not ed)
    tc2=diz2+of2+so2+mi2; ll_sf=res2-tc2; total=ll_p+ll_sf; tc_tot=tc+tc2
    st.markdown('<hr style="border-color:#252932;margin:10px 0">', unsafe_allow_html=True)
    cx1,cx2,cx3=st.columns(3)
    cx1.metric("Total Contrib. Igreja",fmt(tc_tot)); cx2.metric("LL Principal",fmt(ll_p)); cx3.metric(f"💚 LL {nome.upper()} TOTAL",fmt(total))
    return {f"{px}_lb":lb,f"{px}_de":de,f"{px}_dizimo":diz,f"{px}_oferta":of,f"{px}_social":so,f"{px}_missao":mi,
            f"{px}_desp_pes":dp,f"{px}_ll_p":ll_p,f"{px}_sf_lb":lb2,f"{px}_sf_de":de2,f"{px}_sf_dizimo":diz2,
            f"{px}_sf_oferta":of2,f"{px}_sf_social":so2,f"{px}_sf_missao":mi2,f"{px}_ll_sf":ll_sf,
            f"{px}_total":total,f"{px}_contrib_total":tc_tot}

def pagina_apuracao(mes):
    titulo(f"💰 Apuração Financeira — {mes}")
    ap=get_ap(mes)
    t1,t2,t3=st.tabs(["⚡ Prates Eletrônico","🎨 Prates Sublimação","📊 Consolidado"])
    with t1: de=bloco(ap,"e","Prates Eletrônico")
    with t2: ds=bloco(ap,"s","Prates Sublimação")
    with t3:
        sec("CONSOLIDADO DO GRUPO PRATES")
        ll_e=de.get("e_total",0); ll_s=ds.get("s_total",0)
        tg=ll_e+ll_s; tc=de.get("e_contrib_total",0)+ds.get("s_contrib_total",0)
        c1,c2,c3,c4=st.columns(4)
        c1.metric("LL Eletrônico",fmt(ll_e)); c2.metric("LL Sublimação",fmt(ll_s))
        c3.metric("Total Igreja",fmt(tc));    c4.metric("🏆 LL TOTAL GRUPO",fmt(tg))
    st.markdown('<hr style="border-color:#252932;margin:16px 0">', unsafe_allow_html=True)
    if pode("editar") and st.button("💾 Salvar Apuração Completa"):
        salvar_ap(mes,{**de,**ds,"total_grupo":tg,"total_contrib":tc}); st.success(f"Apuração {mes} salva!"); st.rerun()

# ── METAS ─────────────────────────────────────────────────
def pagina_metas(mes):
    titulo(f"🎯 Metas — {mes}")
    ap=get_ap(mes); mt=get_metas(mes); ed=pode("editar")
    indicadores=[("LL Eletrônico — Principal","e_ll_p","meta_e_ll_p"),("LL Eletrônico — S&F","e_ll_sf","meta_e_ll_sf"),
                 ("Total Eletrônico","e_total","meta_e_total"),("LL Sublimação — Principal","s_ll_p","meta_s_ll_p"),
                 ("LL Sublimação — S&F","s_ll_sf","meta_s_ll_sf"),("Total Sublimação","s_total","meta_s_total"),
                 ("LL Total do Grupo","total_grupo","meta_total"),("Total Contribuições Igreja","total_contrib","meta_contrib")]
    novos={}
    for label,ak,mk in indicadores:
        real=nv(ap.get(ak)); meta=float(mt.get(mk) or 0); dif=real-meta
        ic="✅" if real>=meta and meta>0 else ("⚠️" if real>=meta*0.9 and meta>0 else ("❌" if meta>0 else "🎯"))
        with st.expander(f"{ic}  {label}"):
            c1,c2,c3,c4=st.columns(4)
            nm=c1.number_input("Meta (R$)",value=meta,step=0.01,format="%.2f",key=mk,disabled=not ed)
            c2.metric("Realizado",fmt(real)); c3.metric("Diferença",fmt(dif))
            c4.metric("Status","✅ Meta Atingida" if real>=meta and meta>0 else ("⚠️ Quase" if real>=meta*0.9 and meta>0 else ("❌ Abaixo" if meta>0 else "—")))
            novos[mk]=nm
    if ed and st.button("💾 Salvar Metas"): salvar_metas(mes,novos); st.success("Metas salvas!"); st.rerun()

# ── IGREJA & RETIRADAS ────────────────────────────────────
def pagina_igreja(mes):
    titulo(f"⛪ Igreja & Retiradas — {mes}")
    ir=get_ir(mes); ap=get_ap(mes); ed=pode("editar")
    t1,t2=st.tabs(["⛪ Contribuições à Igreja","💼 Retiradas Pessoais"])
    with t1:
        c1,c2,c3=st.columns(3)
        diz_e =c1.number_input("Dízimo Eletrônico (R$)",value=float(ir.get("diz_e") or nv(ap.get("e_dizimo"))+nv(ap.get("e_sf_dizimo"))),step=0.01,format="%.2f",key="ir_diz_e",disabled=not ed)
        diz_s =c2.number_input("Dízimo Sublimação (R$)",value=float(ir.get("diz_s") or nv(ap.get("s_dizimo"))+nv(ap.get("s_sf_dizimo"))),step=0.01,format="%.2f",key="ir_diz_s",disabled=not ed)
        oferta=c3.number_input("Oferta (R$)",value=float(ir.get("oferta") or 0),step=0.01,format="%.2f",key="ir_oferta",disabled=not ed)
        c4,c5=st.columns(2)
        social=c4.number_input("Social (R$)",value=float(ir.get("social") or 0),step=0.01,format="%.2f",key="ir_social",disabled=not ed)
        missao=c5.number_input("Missão (R$)",value=float(ir.get("missao") or 0),step=0.01,format="%.2f",key="ir_missao",disabled=not ed)
        ti=diz_e+diz_s+oferta+social+missao; st.metric("Total Enviado à Igreja",fmt(ti))
    with t2:
        c1,c2,c3=st.columns(3)
        rs=c1.number_input("Sandro (R$)",    value=float(ir.get("ret_sandro") or 0),step=0.01,format="%.2f",key="ret_sandro",disabled=not ed)
        ro=c2.number_input("Outro Sócio (R$)",value=float(ir.get("ret_outro") or 0), step=0.01,format="%.2f",key="ret_outro", disabled=not ed)
        rx=c3.number_input("Outros (R$)",    value=float(ir.get("ret_outros") or 0),step=0.01,format="%.2f",key="ret_outros",disabled=not ed)
        tr=rs+ro+rx
        obs=st.text_input("Observações",value=ir.get("obs_ret",""),key="obs_ret",disabled=not ed)
        st.metric("Total Retiradas",fmt(tr))
    st.markdown('<hr style="border-color:#252932;margin:16px 0">', unsafe_allow_html=True)
    if ed and st.button("💾 Salvar Igreja & Retiradas"):
        salvar_ir(mes,{"diz_e":diz_e,"diz_s":diz_s,"oferta":oferta,"social":social,"missao":missao,"total_igreja":ti,"ret_sandro":rs,"ret_outro":ro,"ret_outros":rx,"total_ret":tr,"obs_ret":obs})
        st.success("Salvo!"); st.rerun()

# ── HISTÓRICO ─────────────────────────────────────────────
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
                     "Retirada Pessoal":nv(ir.get("total_ret")),"Tarefas":f"{conc}/{TOTAL_TAREFAS}"})
    df=pd.DataFrame(rows)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Total LL Grupo",fmt(df["LL Total Grupo"].sum()))
    c2.metric("Total Igreja",fmt(df["Contrib. Igreja"].sum()))
    c3.metric("Total Retiradas",fmt(df["Retirada Pessoal"].sum()))
    c4.metric("Meses",len(df))
    df2=df.copy()
    for c in ["LL Eletrônico","LL Sublimação","LL Total Grupo","Contrib. Igreja","Retirada Pessoal"]:
        df2[c]=df2[c].apply(fmt)
    st.dataframe(df2,use_container_width=True,hide_index=True)
    mes_sel=st.selectbox("Ver checklist do mês:",meses)
    dados=get_checklist(mes_sel); conc=sum(1 for d in dados.values() if d.get("status")=="✅ Concluído")
    na=sum(1 for d in dados.values() if d.get("status")=="⊘ N/A")
    pct=int(conc/(TOTAL_TAREFAS-na)*100) if (TOTAL_TAREFAS-na)>0 else 0
    sec(f"Checklist — {mes_sel} ({pct}% concluído)")
    rows2=[]
    for secao,tarefas in TAREFAS:
        for t in tarefas:
            d=dados.get(t,{}); rows2.append({"Seção":secao,"Tarefa":t,"Status":d.get("status","☐ Pendente"),"Obs":d.get("obs","")})
    st.dataframe(pd.DataFrame(rows2),use_container_width=True,hide_index=True)

# ── RESUMO WHATSAPP ───────────────────────────────────────
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

# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
token_url = st.query_params.get("token")
if token_url and not st.session_state.get("logado"):
    tela_redefinir_senha(token_url)
    st.stop()

if st.session_state.get("tela_auth") == "recuperar":
    tela_recuperar_senha()
    st.stop()

if not st.session_state.get("logado"):
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display: none !important; }
    [data-testid="stAppViewContainer"] > section.main > div { padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)
    placeholder = st.empty()
    with placeholder.container():
        tela_login()
    st.stop()

st.markdown("""
<style>
html,body,[class*="css"]{font-family:'Segoe UI',sans-serif;}
[data-testid="stAppViewContainer"]{background:#111318;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"]{background:#16191f;border-right:1px solid #252932;}
[data-testid="stSidebar"] *{color:#c5cad3 !important;}
[data-testid="stSidebar"] .stButton>button{
    background:transparent !important;border:none !important;
    border-radius:6px !important;
    color:#94a3b8 !important;font-size:13px !important;font-weight:400 !important;
    padding:9px 14px !important;
    margin:1px 0 !important;box-shadow:none !important;
    width:100% !important;transition:all .15s !important;
    display:flex !important;flex-direction:row !important;
    justify-content:flex-start !important;align-items:center !important;
    text-align:left !important;
}
[data-testid="stSidebar"] .stButton>button:hover{
    background:#1e293b !important;color:#e2e8f0 !important;
}
[data-testid="stSidebar"] .stButton>button *{
    text-align:left !important;width:auto !important;
    margin:0 !important;padding:0 !important;
    flex:unset !important;
}
.stButton>button{background:#1e6b3e;color:#fff;border:none;border-radius:5px;padding:6px 16px;font-size:13px;font-weight:500;}
.stButton>button:hover{background:#248a4e;}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    display:flex !important;align-items:center !important;
    padding:8px 14px !important;border-radius:6px !important;
    color:#8892a0 !important;font-size:13px !important;
    cursor:pointer !important;transition:all .15s !important;
    border-left:3px solid transparent !important;
    margin:1px 0 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background:#1a2235 !important;color:#c5cad3 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"] + label,
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {
    background:#1a2235 !important;color:#e2e8f0 !important;
    border-left:3px solid #22c55e !important;font-weight:600 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    font-size:13px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
    gap:0 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
    display:none !important;
}
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
footer{visibility:hidden;} #MainMenu{visibility:hidden;}
</style>

""", unsafe_allow_html=True)

# PWA leve — só roda uma vez por sessão
if not st.session_state.get("_pwa_injetado"):
    _logo = get_logo_b64()
    if _logo:
        import json
        _ext = "png" if os.path.exists("logo.png") or os.path.exists("prates_fechamento/logo.png") else "jpeg"
        _mime = "image/png" if _ext == "png" else "image/jpeg"
        _ico = f"data:{_mime};base64,{_logo}"
        _manifest = json.dumps({
            "name": "Prates Fechamento",
            "short_name": "Prates",
            "start_url": "https://fechamento-prates.streamlit.app",
            "display": "standalone",
            "background_color": "#111318",
            "theme_color": "#22c55e",
            "icons": [{"src": _ico, "sizes": "192x192", "type": _mime, "purpose": "any maskable"}]
        })
        _mb64 = __import__('base64').b64encode(_manifest.encode()).decode()
        st.markdown(f"""
<link rel="apple-touch-icon" href="{_ico}">
<link rel="manifest" href="data:application/json;base64,{_mb64}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Prates Fechamento">
<meta name="theme-color" content="#22c55e">
""", unsafe_allow_html=True)
    st.session_state["_pwa_injetado"] = True

mes, pag = sidebar()

if   "Checklist"  in pag: pagina_checklist(mes)
elif "Apuração"   in pag: pagina_apuracao(mes)
elif "Metas"      in pag: pagina_metas(mes)
elif "Igreja"     in pag: pagina_igreja(mes)
elif "Histórico"  in pag: pagina_historico()
elif "WhatsApp"   in pag: pagina_resumo(mes)
elif "Usuários"   in pag: pagina_usuarios()
