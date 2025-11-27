import streamlit as st
from core.models import Conjunto, Componente, MateriaPrima
from core.logic import load_materias_primas
from typing import List


def clear_cadastro_session_fields_immediate():
    """
    Immediately clears all cadastro session fields (cad_*, comp_*, mp_*).
    This is used before populating new values when editing or after saving.
    """
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith("cad_") or key.startswith("comp_") or key.startswith("mp_"):
            keys_to_remove.append(key)
    for key in keys_to_remove:
        del st.session_state[key]


def update_conjunto(idx: int, cj: Conjunto):
    """
    Updates an existing conjunto in the biblioteca at the specified index.
    """
    if "biblioteca" in st.session_state and 0 <= idx < len(st.session_state["biblioteca"]):
        st.session_state["biblioteca"][idx] = cj


def render_cadastro():
    st.header("Cadastrar Conjunto")

    # Check if we should clear fields before rendering
    if st.session_state.get("cad_should_clear", False):
        clear_cadastro_session_fields_immediate()
        st.session_state["cad_should_clear"] = False

    # Check if we're editing an existing item
    edit_id = st.session_state.get("cad_edit_id", None)
    if edit_id is not None:
        st.info(f"Editando conjunto existente (índice {edit_id}). Clique em 'Salvar' para atualizar ou 'Cancelar Edição' para voltar.")
        if st.button("Cancelar Edição"):
            st.session_state["cad_edit_id"] = None
            st.session_state["cad_should_clear"] = True
            st.experimental_rerun()

    # inicializações em session_state (valores iniciais)
    if "cad_num_componentes" not in st.session_state:
        st.session_state["cad_num_componentes"] = 1

    # controle de número de componentes (fora do form)
    num_comp_default = int(st.session_state.get("cad_num_componentes", 1))
    num_comp = int(st.number_input(
        "Quantidade de componentes",
        min_value=1, step=1, value=num_comp_default,
        key="cad_num_componentes"
    ))

    # carrega lista de MPs (preservando vírgulas)
    lista_mps = load_materias_primas()

    # Ensure default values are set before widgets
    if "cad_nome" not in st.session_state:
        st.session_state["cad_nome"] = ""
    if "cad_cor" not in st.session_state:
        st.session_state["cad_cor"] = ""

    # Campos principais
    nome = st.text_input("Nome do conjunto", key="cad_nome")
    cor = st.text_input("Cor do conjunto", key="cad_cor")

    componentes: List[Componente] = []
    qtd_componentes = max(1, num_comp)

    for i in range(qtd_componentes):
        exp_label = f"Componente {i+1}"
        with st.expander(exp_label, expanded=(i == 0)):
            # nome e quantidade do componente em colunas
            col1, col2 = st.columns([3,1])
            with col1:
                # Ensure default for component name
                if f"comp_nome_{i}" not in st.session_state:
                    st.session_state[f"comp_nome_{i}"] = ""
                comp_nome = st.text_input(f"Nome do componente #{i+1}", key=f"comp_nome_{i}")
            with col2:
                comp_qtd_key = f"comp_qtd_{i}"
                if comp_qtd_key not in st.session_state:
                    st.session_state[comp_qtd_key] = 1
                comp_qtd = int(st.number_input(
                    f"Qtd #{i+1}", min_value=1, value=int(st.session_state.get(comp_qtd_key, 1)),
                    key=comp_qtd_key
                ))

            # número de MPs
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

                # keys e defaults (inicializar antes de criar widgets)
                mp_key = f"mp_select_{i}_{j}"
                mp_manual_key = f"mp_manual_{i}_{j}"

                qtd_key = f"mp_qtd_{i}_{j}"
                if qtd_key not in st.session_state:
                    st.session_state[qtd_key] = 1.0

                un_key = f"mp_un_{i}_{j}"
                if un_key not in st.session_state:
                    st.session_state[un_key] = "KG"

                rend_key = f"mp_rend_{i}_{j}"
                if rend_key not in st.session_state:
                    st.session_state[rend_key] = 100.0

                # checkbox para mostrar/ocultar os detalhes dessa MP
                mp_toggle_key = f"mp_toggle_{i}_{j}"
                if mp_toggle_key not in st.session_state:
                    st.session_state[mp_toggle_key] = False
                mp_open = st.checkbox(f"Mostrar detalhes da MP {j+1}", key=mp_toggle_key)

                # se aberto, mostramos os widgets (que atualizarão st.session_state)
                if mp_open:
                    if lista_mps:
                        # Normalize selectbox: ensure current value is in options
                        current_mp_val = st.session_state.get(mp_key, "")
                        if current_mp_val and current_mp_val in lista_mps:
                            default_index = lista_mps.index(current_mp_val)
                        else:
                            default_index = 0
                            if mp_key not in st.session_state:
                                st.session_state[mp_key] = lista_mps[0] if lista_mps else ""
                        mp_sel = st.selectbox("Matéria-prima", options=lista_mps, index=default_index, key=mp_key)
                    else:
                        if mp_manual_key not in st.session_state:
                            st.session_state[mp_manual_key] = ""
                        mp_sel = st.text_input("Matéria-prima (inserir manualmente)", key=mp_manual_key)

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
                    # não aberto: usar valores atuais em session_state (ou defaults)
                    if lista_mps:
                        mp_sel = st.session_state.get(mp_key, lista_mps[0] if lista_mps else "")
                    else:
                        mp_sel = st.session_state.get(mp_manual_key, "")
                    quantidade = float(st.session_state.get(qtd_key, 1.0))
                    unidade = st.session_state.get(un_key, "KG")
                    rendimento = float(st.session_state.get(rend_key, 100.0))

                materias.append(MateriaPrima(mp=mp_sel, quantidade=quantidade, unidade=unidade, rendimento=rendimento))

            componentes.append(Componente(nome=comp_nome, quantidade=int(comp_qtd), materias=materias))

    # Botão de salvar
    if st.button("Salvar Conjunto na Biblioteca (sessão)"):
        if not nome or not cor:
            st.error("Nome e cor do conjunto são obrigatórios.")
        else:
            cj = Conjunto(nome=nome, cor=cor, componentes=componentes)
            if "biblioteca" not in st.session_state:
                st.session_state["biblioteca"] = []

            # Check if we're updating an existing item or adding a new one
            if edit_id is not None:
                update_conjunto(edit_id, cj)
                st.success(f"Conjunto '{nome}' atualizado na biblioteca (sessão).")
                # Clear edit mode
                st.session_state["cad_edit_id"] = None
            else:
                st.session_state["biblioteca"].append(cj)
                st.success(f"Conjunto '{nome}' salvo na biblioteca (sessão).")

            # Clear form after saving
            st.session_state["cad_should_clear"] = True

            if st.session_state.get("adicionar_ao_projeto", False):
                if "projeto" not in st.session_state:
                    from core.models import Projeto
                    st.session_state["projeto"] = Projeto(projeto_nome="PROJETO SEM NOME", conjuntos=[])
                st.session_state["projeto"].conjuntos.append(cj)

            st.experimental_rerun()