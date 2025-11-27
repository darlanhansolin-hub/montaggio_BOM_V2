import streamlit as st
from collections import Counter, defaultdict
from typing import List
from core.export_xlsx import gerar_export_xlsx_unico

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


def populate_cadastro_session_for_item(item, idx: int):
    """
    Populates all cadastro session keys (cad_*, comp_*, mp_*) from the given item.
    Sets cad_edit_id to the library index so the cadastro form knows to update instead of append.
    """
    # Clear any existing fields first
    from ui.cadastro_conjunto import clear_cadastro_session_fields_immediate
    clear_cadastro_session_fields_immediate()

    # Set main fields
    st.session_state["cad_nome"] = getattr(item, "nome", "")
    st.session_state["cad_cor"] = getattr(item, "cor", "")

    componentes = getattr(item, "componentes", []) or []
    st.session_state["cad_num_componentes"] = max(1, len(componentes))

    # Populate each component and its matérias-primas
    for i, comp in enumerate(componentes):
        st.session_state[f"comp_nome_{i}"] = getattr(comp, "nome", "")
        st.session_state[f"comp_qtd_{i}"] = getattr(comp, "quantidade", 1)

        materias = getattr(comp, "materias", []) or []
        st.session_state[f"comp_{i}_num_mp"] = max(1, len(materias))

        for j, mp in enumerate(materias):
            mp_nome = getattr(mp, "mp", "")
            # Store both select and manual keys to handle either case
            st.session_state[f"mp_select_{i}_{j}"] = mp_nome
            st.session_state[f"mp_manual_{i}_{j}"] = mp_nome
            st.session_state[f"mp_qtd_{i}_{j}"] = getattr(mp, "quantidade", 1.0)
            st.session_state[f"mp_un_{i}_{j}"] = getattr(mp, "unidade", "KG")
            st.session_state[f"mp_rend_{i}_{j}"] = getattr(mp, "rendimento", 100.0)
            st.session_state[f"mp_toggle_{i}_{j}"] = True  # Open the details

    # Mark that we are editing an existing item (library index)
    st.session_state["cad_edit_id"] = idx
    # Switch to the cadastro tab
    st.session_state["main_tab"] = "1) Cadastrar Conjunto"

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
            st.experimental_rerun()
        st.info(f"Projeto ativo: {st.session_state.get('project_name', '')}")
    else:
        # usar st.form com st.form_submit_button sem key para compatibilidade com várias versões do Streamlit
        with st.form("project_form", clear_on_submit=False):
            cols_proj = st.columns([4, 1])
            cols_proj[0].text_input(
                "Nome do Projeto",
                key="project_name_input",
                placeholder="Digite o nome do projeto (ex.: PROJETO VOLVO TESTE EBOM)",
                label_visibility="visible",
            )
            # posiciona o botão de submit (OK) abaixo dos inputs do form
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
    # Conteúdo existente (lista, validações, export)
    # -------------------------
    biblioteca = st.session_state.get("biblioteca", []) or []
    if not biblioteca:
        st.info("A biblioteca está vazia. Cadastre conjuntos antes de exportar.")
        return

    st.subheader("Conjuntos na Biblioteca")
    for i, c in enumerate(biblioteca):
        nome = getattr(c, "nome", "<sem nome>")
        cols = st.columns([5,1,1,1])
        cols[0].write(f"{i}. {nome}")
        if cols[1].button("Editar", key=f"editar_{i}"):
            populate_cadastro_session_for_item(c, i)
            st.experimental_rerun()
        if cols[2].button("Remover", key=f"remover_{i}"):
            biblioteca.pop(i)
            st.session_state["biblioteca"] = biblioteca
            st.success(f"Removido: {nome}")
            st.experimental_rerun()
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
        # validar que o projeto foi confirmado antes de gerar
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