import streamlit as st
from core.models import Conjunto, Componente, MateriaPrima
from core.logic import load_materias_primas
from typing import List

def render_cadastro():
    st.header("Cadastrar Conjunto")

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
                if lista_mps:
                    mp_key = f"mp_select_{i}_{j}"
                    if mp_key not in st.session_state:
                        st.session_state[mp_key] = lista_mps[0] if lista_mps else ""
                else:
                    mp_key = f"mp_manual_{i}_{j}"
                    if mp_key not in st.session_state:
                        st.session_state[mp_key] = ""

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
                        mp_sel = st.selectbox("Matéria-prima", options=lista_mps, key=mp_key)
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
                    # não aberto: usar valores atuais em session_state (ou defaults)
                    mp_sel = st.session_state.get(mp_key, "")
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
            st.session_state["biblioteca"].append(cj)
            st.success(f"Conjunto '{nome}' salvo na biblioteca (sessão).")
            if st.session_state.get("adicionar_ao_projeto", False):
                if "projeto" not in st.session_state:
                    from core.models import Projeto
                    st.session_state["projeto"] = Projeto(projeto_nome="PROJETO SEM NOME", conjuntos=[])
                st.session_state["projeto"].conjuntos.append(cj)