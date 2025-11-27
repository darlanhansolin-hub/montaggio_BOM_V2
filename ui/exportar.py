import streamlit as st
import unicodedata
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional
from core.export_xlsx import gerar_export_xlsx_unico
from core.logic import load_materias_primas

# -------------------------
# Store functions for saved items (for edit/update workflow)
# -------------------------

def _get_saved_items_store() -> List[Dict[str, Any]]:
    """Get or initialize the saved items store."""
    if "__saved_items" not in st.session_state:
        st.session_state["__saved_items"] = []
    return st.session_state["__saved_items"]


def insert_conjunto(data: Dict[str, Any]) -> str:
    """Insert a new conjunto into the saved items store. Returns the assigned ID."""
    store = _get_saved_items_store()
    # Generate a unique ID
    item_id = f"item_{len(store)}_{id(data)}"
    data["__store_id"] = item_id
    store.append(data)
    return item_id


def update_conjunto(item_id: str, data: Dict[str, Any]) -> bool:
    """Update an existing conjunto in the saved items store by ID. Returns True if updated."""
    store = _get_saved_items_store()
    for i, item in enumerate(store):
        if item.get("__store_id") == item_id:
            data["__store_id"] = item_id
            store[i] = data
            return True
    return False


def delete_conjunto(item_id: str) -> bool:
    """Delete a conjunto from the saved items store by ID. Returns True if deleted."""
    store = _get_saved_items_store()
    for i, item in enumerate(store):
        if item.get("__store_id") == item_id:
            store.pop(i)
            return True
    return False


def load_saved_items() -> List[Dict[str, Any]]:
    """Load all saved items from the store."""
    return _get_saved_items_store()


def _normalize_string(s: str) -> str:
    """Normalize string for comparison: remove accents, lowercase, strip."""
    if not s:
        return ""
    # Remove accents
    normalized = unicodedata.normalize('NFD', s)
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents.lower().strip()


def populate_cadastro_session_for_item(item, item_id: Optional[str] = None):
    """
    Populate st.session_state keys used by the cadastro form for editing an existing item.
    This includes cad_*, comp_*, mp_* keys.
    """
    # Set edit mode
    if item_id:
        st.session_state["cad_edit_id"] = item_id
    
    # Get item attributes (works with both Conjunto objects and dicts)
    if hasattr(item, "__dict__"):
        nome = getattr(item, "nome", "")
        cor = getattr(item, "cor", "")
        componentes = getattr(item, "componentes", []) or []
    else:
        nome = item.get("nome", "")
        cor = item.get("cor", "")
        componentes = item.get("componentes", []) or []
    
    # Set main fields
    st.session_state["cad_nome"] = nome
    st.session_state["cad_cor"] = cor
    st.session_state["cad_num_componentes"] = max(1, len(componentes))
    
    # Load MP options for matching
    lista_mps = load_materias_primas()
    normalized_mps = {_normalize_string(mp): mp for mp in lista_mps}
    
    # Set component fields
    for i, comp in enumerate(componentes):
        if hasattr(comp, "__dict__"):
            comp_nome = getattr(comp, "nome", "")
            comp_qtd = getattr(comp, "quantidade", 1)
            materias = getattr(comp, "materias", []) or []
        else:
            comp_nome = comp.get("nome", "")
            comp_qtd = comp.get("quantidade", 1)
            materias = comp.get("materias", []) or []
        
        st.session_state[f"comp_nome_{i}"] = comp_nome
        st.session_state[f"comp_qtd_{i}"] = int(comp_qtd)
        st.session_state[f"comp_{i}_num_mp"] = max(1, len(materias))
        
        # Set MP fields
        for j, mp in enumerate(materias):
            if hasattr(mp, "__dict__"):
                mp_nome = getattr(mp, "mp", "") or getattr(mp, "nome", "")
                mp_qtd = getattr(mp, "quantidade", 1.0)
                mp_un = getattr(mp, "unidade", "KG")
                mp_rend = getattr(mp, "rendimento", 100.0)
            else:
                mp_nome = mp.get("mp", "") or mp.get("nome", "")
                mp_qtd = mp.get("quantidade", 1.0)
                mp_un = mp.get("unidade", "KG")
                mp_rend = mp.get("rendimento", 100.0)
            
            # Determine the correct selectbox value using normalized matching
            mp_select_value = mp_nome
            if lista_mps:
                normalized_mp_nome = _normalize_string(mp_nome)
                if normalized_mp_nome in normalized_mps:
                    # Use the original (properly accented) version from the list
                    mp_select_value = normalized_mps[normalized_mp_nome]
                else:
                    # If not found, we'll need to append it - store the manual value
                    st.session_state[f"mp_manual_{i}_{j}"] = mp_nome
            
            st.session_state[f"mp_select_{i}_{j}"] = mp_select_value
            st.session_state[f"mp_qtd_{i}_{j}"] = float(mp_qtd)
            st.session_state[f"mp_un_{i}_{j}"] = mp_un if mp_un in ["KG", "UN"] else "KG"
            st.session_state[f"mp_rend_{i}_{j}"] = float(mp_rend)
            # Expand MP details when editing
            st.session_state[f"mp_toggle_{i}_{j}"] = True
    
    # Switch to Cadastrar tab
    st.session_state["main_tab"] = "1) Cadastrar Conjunto"


def _list_duplicate_names(biblioteca: List):
    names = [getattr(c, "nome", None) for c in biblioteca]
    counter = Counter(names)
    duplicates = [name for name, cnt in counter.items() if name and cnt > 1]
    return duplicates

def _indices_by_name(biblioteca: List):
    from collections import defaultdict
    idx_map = defaultdict(list)
    for i, c in enumerate(biblioteca):
        idx_map[getattr(c, "nome", "<sem nome>")].append(i)
    return idx_map

def render_exportar():
    st.header("Exportar Planilhas (XLSX) — Padrão Oracle NetSuite")

    # -------------------------
    # Inicializar state do projeto
    # -------------------------
    if "project_locked" not in st.session_state:
        st.session_state["project_locked"] = False
    if "project_name" not in st.session_state:
        st.session_state["project_name"] = ""
    if "project_name_input" not in st.session_state:
        st.session_state["project_name_input"] = st.session_state["project_name"]

    # -------------------------
    # Bloco de configuração do projeto (OK / Editar)
    # -------------------------
    st.subheader("Configurar Projeto")

    if st.session_state["project_locked"]:
        cols_proj_locked = st.columns([4, 1])
        # mostrar o nome travado (disabled)
        cols_proj_locked[0].text_input(
            "Nome do Projeto",
            value=st.session_state.get("project_name", ""),
            disabled=True,
            key="__proj_display_disabled",
            label_visibility="visible"
        )
        if cols_proj_locked[1].button("Editar", key="proj_edit_btn"):
            st.session_state["project_locked"] = False
            st.session_state["project_name_input"] = st.session_state.get("project_name", "")
            st.rerun()
        st.info(f"Projeto ativo: {st.session_state.get('project_name', '')}")
    else:
        # usar st.form com st.form_submit_button sem key para compatibilidade com várias versões do Streamlit
        with st.form("project_form", clear_on_submit=False):
            cols_proj = st.columns([4, 1])
            cols_proj[0].text_input(
                "Nome do Projeto",
                key="export_project_name_input",
                placeholder="Digite o nome do projeto (ex.: PROJETO VOLVO TESTE EBOM)",
                label_visibility="visible",
            )
            # posiciona o botão de submit (OK) abaixo dos inputs do form
            submitted = st.form_submit_button("OK")
        if submitted:
            candidate = (st.session_state.get("export_project_name_input") or "").strip()
            if not candidate:
                st.error("O nome do projeto não pode ficar vazio. Informe um nome antes de confirmar.")
            else:
                st.session_state["project_name"] = candidate
                st.session_state["project_locked"] = True
                st.success(f"Projeto salvo: {candidate}")
                st.rerun()

    if not st.session_state["project_locked"]:
        st.warning("Projeto não confirmado. Clique em OK (ou pressione Enter) para salvar o nome antes de exportar.")

    st.write("---")

    # -------------------------
    # Conteúdo existente (lista, validações, export)
    # -------------------------
    biblioteca = st.session_state.get("biblioteca", []) or []
    if not biblioteca:
        st.info("A biblioteca está vazia. Cadastre conjuntos antes de exportar.")
        return

    st.subheader("Conjuntos na Biblioteca")
    for i, c in enumerate(biblioteca):
        nome = getattr(c, "nome", "<sem nome>")
        item_id = getattr(c, "id", None) or getattr(c, "__store_id", None) or f"bib_{i}"
        cols = st.columns([5, 1, 1, 1])
        cols[0].write(f"{i}. {nome}")
        
        # Edit button - populates cadastro form and switches tab
        if cols[1].button("Editar", key=f"editar_{i}"):
            populate_cadastro_session_for_item(c, item_id)
            st.session_state["cad_edit_bib_index"] = i  # Track biblioteca index for updates
            st.rerun()
        
        if cols[2].button("Remover", key=f"remover_{i}"):
            biblioteca.pop(i)
            st.session_state["biblioteca"] = biblioteca
            st.success(f"Removido: {nome}")
            st.rerun()
        with cols[3]:
            new_key = f"rename_input_{i}"
            if new_key not in st.session_state:
                st.session_state[new_key] = nome
            st.text_input("", key=new_key, label_visibility="collapsed")
            if st.button("OK", key=f"rename_btn_{i}"):
                new_name = st.session_state.get(new_key, nome).strip()
                if new_name == "":
                    st.error("Nome não pode ser vazio.")
                else:
                    try:
                        setattr(c, "nome", new_name)
                    except Exception:
                        try:
                            c.__dict__["nome"] = new_name
                        except Exception as e:
                            st.error(f"Falha ao renomear: {e}")
                    st.session_state["biblioteca"] = biblioteca
                    st.success(f"Renomeado para: {new_name}")
                    st.rerun()

    st.write("---")
    duplicates = _list_duplicate_names(biblioteca)
    if duplicates:
        st.error("Validações falharam. Corrija antes de exportar:")
        for d in duplicates:
            st.write(f"- Nome de conjunto duplicado: {d}")

        st.write("---")
        st.write("Opções para resolver duplicatas:")
        if st.button("Remover duplicados (manter a primeira ocorrência)"):
            seen = set()
            new_lib = []
            removed = []
            for c in biblioteca:
                name = getattr(c, "nome", None)
                if name in seen:
                    removed.append(name)
                    continue
                seen.add(name)
                new_lib.append(c)
            st.session_state["biblioteca"] = new_lib
            st.success(f"Removidos {len(removed)} duplicatas.")
            st.rerun()

        if st.button("Auto-renomear duplicatas (adiciona sufixo)"):
            idx_map = _indices_by_name(biblioteca)
            changed = 0
            for name, indices in idx_map.items():
                if len(indices) > 1:
                    for k, idx in enumerate(indices[1:], start=2):
                        try:
                            biblioteca[idx].__dict__["nome"] = f"{name}_{k}"
                            changed += 1
                        except Exception:
                            pass
            st.session_state["biblioteca"] = biblioteca
            st.success(f"Auto-renomeadas {changed} entradas.")
            st.rerun()

        st.write("Você também pode renomear manualmente cada item na lista acima ou remover entradas específicas.")
        return

    st.success("Validações OK — sem nomes duplicados. Você pode exportar.")

    if st.button("Gerar arquivo XLSX (3 sheets)"):
        # validar que o projeto foi confirmado antes de gerar
        if not st.session_state.get("project_locked") or not st.session_state.get("project_name", "").strip():
            st.error("Confirme o nome do projeto (clique em OK) antes de exportar.")
        else:
            try:
                project_name = st.session_state["project_name"]
                xlsx_bytes = gerar_export_xlsx_unico(biblioteca, project_name)
                st.session_state["_last_export_xlsx"] = xlsx_bytes
                st.success("Arquivo XLSX gerado. Use o botão abaixo para baixar.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao gerar arquivo XLSX: {e}")
                return

    xlsx_data = st.session_state.get("_last_export_xlsx")
    if xlsx_data:
        proj_for_name = st.session_state.get("project_name") or "export"
        safe_name = proj_for_name.replace(" ", "_")
        st.download_button(
            label="Download XLSX (ItemMontagem, ListaMateriais, Revisao_BOM)",
            data=xlsx_data,
            file_name=f"{safe_name}_export_montaggio.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )