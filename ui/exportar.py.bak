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

def render_exportar():
    st.header("Exportar Planilhas (XLSX) — Padrão Oracle NetSuite")

    # -------------------------
    # Exibe informações do projeto (reutiliza session_state de app/main.py)
    # Nota: A inicialização de project_locked, project_name e project_name_input
    # é feita em app/main.py. Aqui apenas usamos os valores já definidos.
    # -------------------------
    project_locked = st.session_state.get("project_locked", False)
    project_name = st.session_state.get("project_name", "")

    st.subheader("Projeto Atual")

    if project_locked and project_name:
        st.info(f"Projeto ativo: **{project_name}**")
        st.caption("Para alterar o nome do projeto, use a seção 'Informações do Projeto' no topo da página.")
    else:
        st.warning("Projeto não confirmado. Configure o nome do projeto na seção 'Informações do Projeto' no topo da página antes de exportar.")

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
        cols = st.columns([6,1,1])
        cols[0].write(f"{i}. {nome}")
        if cols[1].button("Remover", key=f"remover_{i}"):
            biblioteca.pop(i)
            st.session_state["biblioteca"] = biblioteca
            st.success(f"Removido: {nome}")
            st.rerun()
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
            st.error("Confirme o nome do projeto na seção 'Informações do Projeto' no topo da página antes de exportar.")
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