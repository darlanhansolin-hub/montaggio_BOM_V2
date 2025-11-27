import streamlit as st
from core.models import Conjunto, Componente, MateriaPrima
from core.logic import load_materias_primas
from typing import List
import unicodedata


def _serialize_conjunto(cj: Conjunto) -> dict:
    comps = []
    for comp in getattr(cj, "componentes", []) or []:
        mps = []
        for mp in getattr(comp, "materias", []) or []:
            mps.append({
                "mp": getattr(mp, "mp", "") or getattr(mp, "nome", ""),
                "quantidade": getattr(mp, "quantidade", 0),
                "unidade": getattr(mp, "unidade", "") or getattr(mp, "un", ""),
                "rendimento": getattr(mp, "rendimento", 100),
            })
        comps.append({
            "nome": getattr(comp, "nome", "") or "",
            "quantidade": getattr(comp, "quantidade", 1),
            "materias": mps
        })
    return {
        "nome": getattr(cj, "nome", ""),
        "cor": getattr(cj, "cor", ""),
        "descricao": getattr(cj, "descricao", ""),
        "componentes": comps
    }


def _normalize(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


def clear_cadastro_session_fields_immediate():
    """
    Clear/reset cadastro keys *before widgets are created*.
    This function sets defaults (empty strings / 1s) so widgets read cleared values.
    """
    # basic fields
    st.session_state["cad_nome"] = ""
    st.session_state["cad_cor"] = ""
    st.session_state["cad_num_componentes"] = 1
    # remove component/mp keys (safe to delete at start of render)
    for k in list(st.session_state.keys()):
        if k.startswith("comp_") or k.startswith("mp_") or k.startswith("comp_qtd_"):
            try:
                del st.session_state[k]
            except Exception:
                pass
    # remove edit flag
    if "cad_edit_id" in st.session_state:
        try:
            del st.session_state["cad_edit_id"]
        except Exception:
            st.session_state["cad_edit_id"] = None
    # remove the clear request flag
    if "cad_should_clear" in st.session_state:
        try:
            del st.session_state["cad_should_clear"]
        except Exception:
            pass


def render_cadastro():
    st.header("Cadastrar Conjunto")

    # If a previous save requested a clear, perform it now (before creating widgets)
    if st.session_state.get("cad_should_clear"):
        clear_cadastro_session_fields_immediate()

    if "cad_num_componentes" not in st.session_state:
        st.session_state["cad_num_componentes"] = 1

    num_comp_default = int(st.session_state.get("cad_num_componentes", 1))
    num_comp = int(st.number_input(
        "Quantidade de componentes",
        min_value=1, step=1, value=num_comp_default,
        key="cad_num_componentes"
    ))

    lista_mps = load_materias_primas() or []

    nome = st.text_input("Nome do conjunto", key="cad_nome")
    cor = st.text_input("Cor do conjunto", key="cad_cor")

    componentes: List[Componente] = []
    qtd_componentes = max(1, num_comp)

    for i in range(qtd_componentes):
        exp_label = f"Componente {i+1}"
        with st.expander(exp_label, expanded=(i == 0)):
            col1, col2 = st.columns([3, 1])
            with col1:
                # Garantir default explícito para o nome do componente antes de instanciar o widget
                comp_nome_key = f"comp_nome_{i}"
                if comp_nome_key not in st.session_state:
                    st.session_state[comp_nome_key] = ""
                comp_nome = st.text_input(f"Nome do componente #{i+1}", key=comp_nome_key)
            with col2:
                comp_qtd_key = f"comp_qtd_{i}"
                if comp_qtd_key not in st.session_state:
                    st.session_state[comp_qtd_key] = 1
                comp_qtd = int(st.number_input(
                    f"Qtd #{i+1}", min_value=1, value=int(st.session_state.get(comp_qtd_key, 1)),
                    key=comp_qtd_key
                ))

            key_num_mp = f"comp_{i}_num_mp"
            if key_num_mp not in st.session_state:
                st.session_state[key_num_mp] = 1
            num_mp = int(st.number_input(
                f"Quantidade de MPs do componente #{i+1}",
                min_value=1, value=int(st.session_state.get(key_num_mp, 1)),
                key=key_num_mp
            ))

            materias = []
            for j in range(num_mp):
                st.markdown(f"**MP {j+1}**")

                # keys
                mp_key = f"mp_select_{i}_{j}"
                manual_key = f"mp_manual_{i}_{j}"
                qtd_key = f"mp_qtd_{i}_{j}"
                un_key = f"mp_un_{i}_{j}"
                rend_key = f"mp_rend_{i}_{j}"
                mp_toggle_key = f"mp_toggle_{i}_{j}"

                # defaults for numeric and toggles (safe to set anytime)
                if qtd_key not in st.session_state:
                    st.session_state[qtd_key] = 1.0
                if un_key not in st.session_state:
                    st.session_state[un_key] = "KG"
                if rend_key not in st.session_state:
                    st.session_state[rend_key] = 100.0
                if mp_toggle_key not in st.session_state:
                    st.session_state[mp_toggle_key] = False
                if manual_key not in st.session_state:
                    st.session_state[manual_key] = ""

                # Prepare options and initial value BEFORE creating the selectbox widget.
                if lista_mps:
                    # ensure options are strings
                    options = [str(o) for o in lista_mps]
                    # Determine candidate current value (could come from populate action)
                    current_candidate = st.session_state.get(mp_key, "") or st.session_state.get(manual_key, "") or ""
                    current_candidate = str(current_candidate) if current_candidate is not None else ""
                    # Try normalized match to pick the canonical option if present
                    selected_value = None
                    if current_candidate:
                        norm_cur = _normalize(current_candidate)
                        for opt in options:
                            if _normalize(opt) == norm_cur:
                                selected_value = opt
                                break
                        if selected_value is None:
                            # not found: append candidate as extra option so selectbox can show it
                            if current_candidate not in options:
                                options = options + [current_candidate]
                            selected_value = current_candidate
                    # Set session key BEFORE widget instantiation. Overwrite is OK here.
                    st.session_state[mp_key] = selected_value if selected_value is not None else (options[0] if options else "")

                else:
                    # no lista_mps: fall back to manual text
                    if mp_key not in st.session_state:
                        st.session_state[mp_key] = st.session_state.get(manual_key, "")

                # checkbox to show/hide details
                mp_open = st.checkbox(f"Mostrar detalhes da MP {j+1}", key=mp_toggle_key)

                # create widgets for details (selectbox/text_input, quantidade, unidade, rendimento)
                if mp_open:
                    if lista_mps:
                        try:
                            mp_sel = st.selectbox("Matéria-prima", options=options, key=mp_key)
                        except Exception:
                            # fallback to manual input but keep user informed
                            st.warning("Problema com selectbox; insira a matéria-prima manualmente abaixo.")
                            # ensure manual key exists and show manual input
                            if manual_key not in st.session_state:
                                st.session_state[manual_key] = st.session_state.get(mp_key, "")
                            mp_sel = st.text_input("Matéria-prima (manual)", key=manual_key)
                            # keep mp_key in sync for downstream code
                            st.session_state[mp_key] = st.session_state.get(manual_key, "")
                    else:
                        mp_sel = st.text_input("Matéria-prima (inserir manualmente)", key=mp_key)

                    quantidade = float(st.number_input("Quantidade", min_value=0.0,
                                                      value=float(st.session_state.get(qtd_key, 1.0)),
                                                      step=0.1, key=qtd_key))

                    unidade = st.selectbox("Unidade", options=["KG", "UN"],
                                           index=0 if st.session_state.get(un_key, "KG") == "KG" else 1,
                                           key=un_key)

                    rendimento = float(st.number_input("Rendimento (%)", min_value=1.0, max_value=100.0,
                                                      value=float(st.session_state.get(rend_key, 100.0)),
                                                      step=0.1, key=rend_key))
                else:
                    mp_sel = st.session_state.get(mp_key, "")
                    quantidade = float(st.session_state.get(qtd_key, 1.0))
                    unidade = st.session_state.get(un_key, "KG")
                    rendimento = float(st.session_state.get(rend_key, 100.0))

                materias.append(MateriaPrima(mp=mp_sel, quantidade=quantidade, unidade=unidade, rendimento=rendimento))

            componentes.append(Componente(nome=comp_nome, quantidade=int(comp_qtd), materias=materias))

    # Botão de salvar (respeita cad_edit_id para update)
    if st.button("Salvar Conjunto na Biblioteca (sessão)"):
        if not nome or not cor:
            st.error("Nome e cor do conjunto são obrigatórios.")
        else:
            cj = Conjunto(nome=nome, cor=cor, componentes=componentes)

            cad_edit_id = st.session_state.get("cad_edit_id")

            try:
                from ui.exportar import insert_conjunto, update_conjunto
            except Exception:
                insert_conjunto = None
                update_conjunto = None

            data_for_store = {"nome": nome, "cor": cor, "descricao": ""}

            if cad_edit_id:
                updated = False
                try:
                    if update_conjunto is not None:
                        updated = update_conjunto(cad_edit_id, data_for_store)
                    else:
                        items = st.session_state.get("__saved_items", [])
                        for it in items:
                            if it.get("id") == cad_edit_id:
                                it.update(data_for_store)
                                updated = True
                        st.session_state["__saved_items"] = items
                except Exception:
                    updated = False

                # update object in biblioteca if matches id
                try:
                    if "biblioteca" in st.session_state:
                        for idx, existing in enumerate(st.session_state["biblioteca"]):
                            if getattr(existing, "id", None) == cad_edit_id:
                                try:
                                    st.session_state["biblioteca"][idx] = cj
                                    setattr(st.session_state["biblioteca"][idx], "id", cad_edit_id)
                                except Exception:
                                    pass
                                break
                except Exception:
                    pass

                if updated:
                    st.success(f"Conjunto '{nome}' atualizado com sucesso!")
                else:
                    if insert_conjunto is not None:
                        new_id = insert_conjunto(data_for_store)
                        try:
                            setattr(cj, "id", new_id)
                        except Exception:
                            pass
                        if "biblioteca" not in st.session_state:
                            st.session_state["biblioteca"] = []
                        st.session_state["biblioteca"].append(cj)
                        st.success(f"Conjunto '{nome}' salvo na biblioteca (sessão). (novo id: {new_id})")
                    else:
                        st.error("Falha ao atualizar o item existente; tente salvar novamente.")
            else:
                # insert new
                if "biblioteca" not in st.session_state:
                    st.session_state["biblioteca"] = []
                st.session_state["biblioteca"].append(cj)

                try:
                    if insert_conjunto is not None:
                        new_id = insert_conjunto(data_for_store)
                        try:
                            setattr(cj, "id", new_id)
                        except Exception:
                            pass
                    else:
                        items = st.session_state.get("__saved_items", [])
                        new_id = max((it.get("id", 0) for it in items), default=0) + 1
                        data_for_store["id"] = new_id
                        items.append(data_for_store)
                        st.session_state["__saved_items"] = items
                        try:
                            setattr(cj, "id", new_id)
                        except Exception:
                            pass
                except Exception:
                    pass

                st.success(f"Conjunto '{nome}' salvo na biblioteca (sessão).")

            # request a clear on next run (so clearing happens before widgets are created)
            st.session_state["cad_should_clear"] = True

            # remove edit flag now that we've processed it (optional, kept for safety)
            if "cad_edit_id" in st.session_state:
                try:
                    del st.session_state["cad_edit_id"]
                except Exception:
                    st.session_state["cad_edit_id"] = None

            # adicionar ao projeto se solicitado
            if st.session_state.get("adicionar_ao_projeto", False):
                if "projeto" not in st.session_state:
                    from core.models import Projeto
                    st.session_state["projeto"] = Projeto(projeto_nome="PROJETO SEM NOME", conjuntos=[])
                st.session_state["projeto"].conjuntos.append(cj)

            st.experimental_rerun()