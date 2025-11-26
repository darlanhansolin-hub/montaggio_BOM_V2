"""
ui/exportar.py

Module for the "Exportar" (Export) tab in the Montaggio application.
Provides form-based CRUD for saved items (conjuntos) with lightweight persistence.

To adapt to a real database:
- Replace insert_conjunto, update_conjunto, delete_conjunto, and load_saved_items
  functions with actual database calls.
- The fallback uses st.session_state['__saved_items'] for in-memory persistence.
"""

import streamlit as st
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional
from core.export_xlsx import gerar_export_xlsx_unico

# ---------------------------------------------------------------------------
# FORM_KEYS: List of session_state keys used by the conjunto form.
# These are used to control form inputs and reset them after save.
# ---------------------------------------------------------------------------
FORM_KEYS = [
    "form_nome",
    "form_cor",
    "form_descricao",
]


# ---------------------------------------------------------------------------
# Data Layer Helper Functions
# Adapt these to call your real database when available.
# ---------------------------------------------------------------------------

def _get_saved_items_store() -> List[Dict[str, Any]]:
    """
    Returns the list used for lightweight persistence.
    Initializes st.session_state['__saved_items'] if not present.
    """
    if "__saved_items" not in st.session_state:
        st.session_state["__saved_items"] = []
    return st.session_state["__saved_items"]


def insert_conjunto(data: Dict[str, Any]) -> int:
    """
    Insert a new conjunto into the data store.
    Returns the new item's ID.

    To adapt to a real DB:
        # result = db.insert("conjuntos", data)
        # return result.inserted_id
    """
    items = _get_saved_items_store()
    # Generate a simple incremental ID
    new_id = max((item.get("id", 0) for item in items), default=0) + 1
    data["id"] = new_id
    items.append(data)
    return new_id


def update_conjunto(item_id: int, data: Dict[str, Any]) -> bool:
    """
    Update an existing conjunto by ID.
    Returns True if updated, False if not found.

    To adapt to a real DB:
        # result = db.update("conjuntos", {"id": item_id}, data)
        # return result.modified_count > 0
    """
    items = _get_saved_items_store()
    for item in items:
        if item.get("id") == item_id:
            item.update(data)
            item["id"] = item_id  # Ensure ID is preserved
            return True
    return False


def delete_conjunto(item_id: int) -> bool:
    """
    Delete a conjunto by ID.
    Returns True if deleted, False if not found.

    To adapt to a real DB:
        # result = db.delete("conjuntos", {"id": item_id})
        # return result.deleted_count > 0
    """
    items = _get_saved_items_store()
    for i, item in enumerate(items):
        if item.get("id") == item_id:
            items.pop(i)
            return True
    return False


def load_saved_items() -> List[Dict[str, Any]]:
    """
    Load all saved conjuntos from the data store.
    Returns a list of dicts with keys: id, nome, cor, descricao.

    To adapt to a real DB:
        # return list(db.find("conjuntos"))
    """
    return _get_saved_items_store()


# ---------------------------------------------------------------------------
# Form Helper Functions
# ---------------------------------------------------------------------------

def ensure_form_state_defaults() -> None:
    """
    Ensure all form keys have default values in session_state.
    Call this at the start of render to initialize form fields.
    Uses FORM_KEYS constant to ensure consistency.
    """
    for key in FORM_KEYS:
        if key not in st.session_state:
            st.session_state[key] = ""


def clear_form_fields() -> None:
    """
    Clear all form fields by resetting their session_state keys to empty values.
    Also clears the edit_id to switch back to insert mode.
    Uses FORM_KEYS constant to ensure consistency.
    """
    for key in FORM_KEYS:
        st.session_state[key] = ""
    st.session_state["edit_id"] = None


def load_item_into_form(item: Dict[str, Any]) -> None:
    """
    Load an item's values into the form fields and set edit_id.
    """
    st.session_state["form_nome"] = item.get("nome", "")
    st.session_state["form_cor"] = item.get("cor", "")
    st.session_state["form_descricao"] = item.get("descricao", "")
    st.session_state["edit_id"] = item.get("id")


# ---------------------------------------------------------------------------
# Legacy Helper Functions (for biblioteca compatibility)
# ---------------------------------------------------------------------------

def _list_duplicate_names(biblioteca: List) -> List[str]:
    """List duplicate conjunto names in the biblioteca."""
    names = [getattr(c, "nome", None) for c in biblioteca]
    counter = Counter(names)
    duplicates = [name for name, cnt in counter.items() if name and cnt > 1]
    return duplicates


def _indices_by_name(biblioteca: List) -> Dict[str, List[int]]:
    """Map conjunto names to their indices in the biblioteca."""
    idx_map = defaultdict(list)
    for i, c in enumerate(biblioteca):
        idx_map[getattr(c, "nome", "<sem nome>")].append(i)
    return idx_map


# ---------------------------------------------------------------------------
# Main Render Function
# ---------------------------------------------------------------------------

def render_exportar():
    """
    Render the Exportar (Export) tab.
    Includes:
    - Form for creating/editing conjuntos with explicit key values
    - List of saved items with Editar/Remover buttons
    - Export functionality for biblioteca items
    """
    st.header("Exportar Planilhas (XLSX) — Padrão Oracle NetSuite")

    # Initialize form state defaults
    ensure_form_state_defaults()

    # Initialize edit_id if not present
    if "edit_id" not in st.session_state:
        st.session_state["edit_id"] = None

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
            st.experimental_rerun()
        st.info(f"Projeto ativo: {st.session_state.get('project_name', '')}")
    else:
        with st.form("project_form", clear_on_submit=False):
            cols_proj = st.columns([4, 1])
            cols_proj[0].text_input(
                "Nome do Projeto",
                key="project_name_input",
                placeholder="Digite o nome do projeto (ex.: PROJETO VOLVO TESTE EBOM)",
                label_visibility="visible",
            )
            submitted = st.form_submit_button("OK")
        if submitted:
            candidate = (st.session_state.get("project_name_input") or "").strip()
            if not candidate:
                st.error("O nome do projeto não pode ficar vazio. Informe um nome antes de confirmar.")
            else:
                st.session_state["project_name"] = candidate
                st.session_state["project_locked"] = True
                st.success(f"Projeto salvo: {candidate}")
                st.experimental_rerun()

    if not st.session_state["project_locked"]:
        st.warning("Projeto não confirmado. Clique em OK (ou pressione Enter) para salvar o nome antes de exportar.")

    st.write("---")

    # -------------------------
    # Form for creating/editing conjuntos
    # -------------------------
    st.subheader("Salvar Conjunto na Biblioteca")

    # Determine if we're in edit mode
    edit_id = st.session_state.get("edit_id")
    is_editing = edit_id is not None

    if is_editing:
        st.info(f"Editando conjunto (ID: {edit_id}). Altere os campos e clique em 'Salvar'.")

    # Form inputs with explicit keys
    st.text_input(
        "Nome do Conjunto",
        key="form_nome",
        placeholder="Digite o nome do conjunto"
    )
    st.text_input(
        "Cor do Conjunto",
        key="form_cor",
        placeholder="Digite a cor do conjunto"
    )
    st.text_area(
        "Descrição (opcional)",
        key="form_descricao",
        placeholder="Descrição adicional do conjunto"
    )

    # Save button
    col_save, col_cancel = st.columns([1, 1])
    with col_save:
        if st.button("Salvar Conjunto na Biblioteca", key="btn_salvar_conjunto"):
            nome = st.session_state.get("form_nome", "").strip()
            cor = st.session_state.get("form_cor", "").strip()
            descricao = st.session_state.get("form_descricao", "").strip()

            if not nome:
                st.error("O nome do conjunto é obrigatório.")
            elif not cor:
                st.error("A cor do conjunto é obrigatória.")
            else:
                data = {
                    "nome": nome,
                    "cor": cor,
                    "descricao": descricao,
                }

                if is_editing:
                    # Update existing item
                    success = update_conjunto(edit_id, data)
                    if success:
                        st.success(f"Conjunto '{nome}' atualizado com sucesso!")
                    else:
                        st.error("Erro ao atualizar conjunto. Item não encontrado.")
                else:
                    # Insert new item
                    new_id = insert_conjunto(data)
                    st.success(f"Conjunto '{nome}' salvo com sucesso! (ID: {new_id})")

                # Clear form fields and reset edit mode
                clear_form_fields()
                st.experimental_rerun()

    with col_cancel:
        if is_editing:
            if st.button("Cancelar Edição", key="btn_cancelar_edicao"):
                clear_form_fields()
                st.experimental_rerun()

    st.write("---")

    # -------------------------
    # List of saved items with Editar/Remover buttons
    # -------------------------
    st.subheader("Conjuntos Salvos")

    saved_items = load_saved_items()
    if not saved_items:
        st.info("Nenhum conjunto salvo ainda. Use o formulário acima para adicionar.")
    else:
        for item in saved_items:
            item_id = item.get("id")
            nome = item.get("nome", "<sem nome>")
            cor = item.get("cor", "")
            descricao = item.get("descricao", "")

            cols = st.columns([4, 1, 1])
            with cols[0]:
                display_text = f"**{nome}** ({cor})"
                if descricao:
                    display_text += f" — {descricao[:50]}{'...' if len(descricao) > 50 else ''}"
                st.markdown(display_text)

            with cols[1]:
                if st.button("Editar", key=f"btn_editar_{item_id}"):
                    load_item_into_form(item)
                    st.experimental_rerun()

            with cols[2]:
                if st.button("Remover", key=f"btn_remover_{item_id}"):
                    success = delete_conjunto(item_id)
                    if success:
                        st.success(f"Conjunto '{nome}' removido!")
                        # If we were editing this item, clear the form
                        if st.session_state.get("edit_id") == item_id:
                            clear_form_fields()
                        st.experimental_rerun()
                    else:
                        st.error("Erro ao remover conjunto.")

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
        cols = st.columns([6, 1, 1])
        cols[0].write(f"{i}. {nome}")
        if cols[1].button("Remover", key=f"remover_{i}"):
            biblioteca.pop(i)
            st.session_state["biblioteca"] = biblioteca
            st.success(f"Removido: {nome}")
            st.experimental_rerun()
        with cols[2]:
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
                    st.experimental_rerun()

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
            st.experimental_rerun()

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
            st.experimental_rerun()

        st.write("Você também pode renomear manualmente cada item na lista acima ou remover entradas específicas.")
        return

    st.success("Validações OK — sem nomes duplicados. Você pode exportar.")

    if st.button("Gerar arquivo XLSX (3 sheets)"):
        if not st.session_state.get("project_locked") or not st.session_state.get("project_name", "").strip():
            st.error("Confirme o nome do projeto (clique em OK) antes de exportar.")
        else:
            try:
                project_name = st.session_state["project_name"]
                xlsx_bytes = gerar_export_xlsx_unico(biblioteca, project_name)
                st.session_state["_last_export_xlsx"] = xlsx_bytes
                st.success("Arquivo XLSX gerado. Use o botão abaixo para baixar.")
                st.experimental_rerun()
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