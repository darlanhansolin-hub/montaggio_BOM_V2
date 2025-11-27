import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import streamlit as st
from ui import cadastro_conjunto, biblioteca, exportar
from core.models import Projeto
from core.logic import load_materias_primas

st.set_page_config(page_title="Montaggio — Gerador de BOM Oracle", layout="wide")

if "projeto" not in st.session_state:
    st.session_state["projeto"] = Projeto(projeto_nome="PROJETO SEM NOME", conjuntos=[])

if "biblioteca" not in st.session_state:
    st.session_state["biblioteca"] = []

# Carrega lista de MPs no state
load_materias_primas()

st.title("Montaggio — Gerador de BOM Oracle (FASE 2)")

# -----------------------
# Top: nome do projeto (unificado com project_name / project_locked)
# -----------------------
# Nota: este bloco deve ficar AQUI, depois de import streamlit as st e após
# inicializar st.session_state["projeto"], para evitar NameError ("st" não definido).
if "project_locked" not in st.session_state:
    st.session_state["project_locked"] = False

# Garantir que project_name seja inicializado a partir do objeto Projeto existente
projeto_obj = st.session_state.get("projeto")
if "project_name" not in st.session_state:
    initial_name = getattr(projeto_obj, "projeto_nome", "") if projeto_obj else ""
    st.session_state["project_name"] = initial_name

if "project_name_input" not in st.session_state:
    st.session_state["project_name_input"] = st.session_state.get("project_name", "")

with st.expander("Informações do Projeto (clique para editar)", expanded=True):
    cols = st.columns([4, 1])
    # Campo editável / disabled no topo
    with cols[0]:
        if st.session_state["project_locked"]:
            # exibe nome confirmado, disabled (uso de key diferente evita conflito)
            st.text_input("Nome do projeto", value=st.session_state.get("project_name", ""), disabled=True, key="__proj_top_display")
        else:
            # campo editável que escreve em project_name_input
            st.text_input("Nome do projeto", key="project_name_input")

    # Botões OK / Editar no topo (unificados com exportar)
    with cols[1]:
        if st.session_state["project_locked"]:
            if st.button("Editar", key="proj_edit_top"):
                st.session_state["project_locked"] = False
                # carregar valor salvo para edição
                st.session_state["project_name_input"] = st.session_state.get("project_name", "")
                st.rerun()
        else:
            if st.button("OK", key="proj_ok_top"):
                candidate = (st.session_state.get("project_name_input") or "").strip()
                if not candidate:
                    st.error("O nome do projeto não pode ficar vazio.")
                else:
                    # salvar nos dois lugares: state unificado e objeto Projeto usado em outras partes
                    st.session_state["project_name"] = candidate
                    st.session_state["project_locked"] = True
                    if projeto_obj is not None:
                        try:
                            projeto_obj.projeto_nome = candidate
                        except Exception:
                            # fallback: se não for possível setar atributo, mantenha state apenas
                            pass
                    st.success(f"Projeto salvo: {candidate}")
                    st.rerun()

# -----------------------
# Tabs / Conteúdo principal (using st.radio for programmatic tab switching)
# -----------------------
TAB_OPTIONS = ["1) Cadastrar Conjunto", "2) Biblioteca", "3) Exportar Planilhas"]

# Initialize main_tab in session_state if not present
if "main_tab" not in st.session_state:
    st.session_state["main_tab"] = TAB_OPTIONS[0]

# Ensure the value is valid
if st.session_state["main_tab"] not in TAB_OPTIONS:
    st.session_state["main_tab"] = TAB_OPTIONS[0]

# Radio for tab selection (horizontal layout)
# Use index= parameter instead of key= to allow programmatic switching
current_index = TAB_OPTIONS.index(st.session_state["main_tab"])
selected_tab = st.radio(
    "Navegação",
    options=TAB_OPTIONS,
    index=current_index,
    horizontal=True,
    label_visibility="collapsed"
)

# Update main_tab when user clicks a different tab
if selected_tab != st.session_state["main_tab"]:
    st.session_state["main_tab"] = selected_tab
    st.rerun()

st.write("---")

# Render the appropriate tab content based on selection
if st.session_state["main_tab"] == TAB_OPTIONS[0]:
    cadastro_conjunto.render_cadastro()
elif st.session_state["main_tab"] == TAB_OPTIONS[1]:
    biblioteca.render_biblioteca()
else:
    exportar.render_exportar()