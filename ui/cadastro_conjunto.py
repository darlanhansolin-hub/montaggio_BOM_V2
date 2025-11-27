import streamlit as st
import unicodedata
from core.models import Conjunto, Componente, MateriaPrima
from core.logic import load_materias_primas
from typing import List


def _normalize_string(s: str) -> str:
    """Normalize string for comparison: remove accents, lowercase, strip."""
    if not s:
        return ""
    # Remove accents
    normalized = unicodedata.normalize('NFD', s)
    without_accents = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return without_accents.lower().strip()


def clear_cadastro_session_fields_immediate():
    """
    Clear/initialize cadastro form fields at the start of render.
    This ensures the form appears empty after saving.
    """
    # Clear main fields
    st.session_state["cad_nome"] = ""
    st.session_state["cad_cor"] = ""
    st.session_state["cad_num_componentes"] = 1
    
    # Clear edit mode
    if "cad_edit_id" in st.session_state:
        del st.session_state["cad_edit_id"]
    if "cad_edit_bib_index" in st.session_state:
        del st.session_state["cad_edit_bib_index"]
    
    # Clear component and MP fields (iterate through possible keys)
    keys_to_clear = []
    for key in list(st.session_state.keys()):
        if key.startswith(("comp_nome_", "comp_qtd_", "comp_", "mp_select_", "mp_manual_", 
                          "mp_qtd_", "mp_un_", "mp_rend_", "mp_toggle_")):
            keys_to_clear.append(key)
    
    for key in keys_to_clear:
        del st.session_state[key]


def render_cadastro():
    st.header("Cadastrar Conjunto")

    # Check if we need to clear the form (flag-based clear flow)
    if st.session_state.get("cad_should_clear", False):
        clear_cadastro_session_fields_immediate()
        st.session_state["cad_should_clear"] = False

    # Check if we're in edit mode
    edit_id = st.session_state.get("cad_edit_id")
    edit_bib_index = st.session_state.get("cad_edit_bib_index")
    
    if edit_id or edit_bib_index is not None:
        st.info("🖊️ Modo de edição: Você está editando um conjunto existente.")

    # inicializações em session_state (valores iniciais)
    if "cad_num_componentes" not in st.session_state:
        st.session_state["cad_num_componentes"] = 1

    # controle de número de componentes (fora do form)
    num_comp = int(st.number_input(
        "Quantidade de componentes",
        min_value=1, step=1,
        key="cad_num_componentes"
    ))

    # carrega lista de MPs (preservando vírgulas)
    lista_mps = load_materias_primas()
    # Create normalized mapping for matching
    normalized_mps = {_normalize_string(mp): mp for mp in lista_mps}

    # Campos principais - initialize defaults before widget creation
    if "cad_nome" not in st.session_state:
        st.session_state["cad_nome"] = ""
    if "cad_cor" not in st.session_state:
        st.session_state["cad_cor"] = ""
    
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
                # Initialize default before widget creation
                if f"comp_nome_{i}" not in st.session_state:
                    st.session_state[f"comp_nome_{i}"] = ""
                comp_nome = st.text_input(f"Nome do componente #{i+1}", key=f"comp_nome_{i}")
            with col2:
                comp_qtd_key = f"comp_qtd_{i}"
                if comp_qtd_key not in st.session_state:
                    st.session_state[comp_qtd_key] = 1
                comp_qtd = int(st.number_input(
                    f"Qtd #{i+1}", min_value=1,
                    key=comp_qtd_key
                ))

            # número de MPs
            key_num_mp = f"comp_{i}_num_mp"
            if key_num_mp not in st.session_state:
                st.session_state[key_num_mp] = 1
            num_mp = int(st.number_input(
                f"Quantidade de MPs do componente #{i+1}",
                min_value=1,
                key=key_num_mp
            ))

            materias = []
            for j in range(num_mp):
                st.markdown(f"**MP {j+1}**")

                # keys for this MP
                mp_select_key = f"mp_select_{i}_{j}"
                mp_manual_key = f"mp_manual_{i}_{j}"
                qtd_key = f"mp_qtd_{i}_{j}"
                un_key = f"mp_un_{i}_{j}"
                rend_key = f"mp_rend_{i}_{j}"
                mp_toggle_key = f"mp_toggle_{i}_{j}"

                # Initialize defaults only if not present (don't overwrite populated values)
                if qtd_key not in st.session_state:
                    st.session_state[qtd_key] = 1.0
                if un_key not in st.session_state:
                    st.session_state[un_key] = "KG"
                if rend_key not in st.session_state:
                    st.session_state[rend_key] = 100.0
                if mp_toggle_key not in st.session_state:
                    st.session_state[mp_toggle_key] = False

                # checkbox para mostrar/ocultar os detalhes dessa MP
                mp_open = st.checkbox(f"Mostrar detalhes da MP {j+1}", key=mp_toggle_key)

                # se aberto, mostramos os widgets (que atualizarão st.session_state)
                if mp_open:
                    if lista_mps:
                        # Robust handling for matéria-prima selectbox
                        # Prepare options list with proper matching
                        options_list = lista_mps.copy()
                        
                        # Get the current value from session_state
                        current_value = st.session_state.get(mp_select_key, "")
                        manual_value = st.session_state.get(mp_manual_key, "")
                        
                        # Determine the initial selection
                        initial_index = 0
                        if current_value:
                            # Check if current value is in options
                            if current_value in options_list:
                                initial_index = options_list.index(current_value)
                            else:
                                # Try normalized matching
                                normalized_current = _normalize_string(current_value)
                                if normalized_current in normalized_mps:
                                    matched_value = normalized_mps[normalized_current]
                                    if matched_value in options_list:
                                        initial_index = options_list.index(matched_value)
                                        # Update the session state to use the matched value
                                        st.session_state[mp_select_key] = matched_value
                                else:
                                    # Value not found - append it to options
                                    if current_value and current_value not in options_list:
                                        options_list.append(current_value)
                                        initial_index = len(options_list) - 1
                        elif manual_value:
                            # Use manual value if set
                            normalized_manual = _normalize_string(manual_value)
                            if normalized_manual in normalized_mps:
                                matched_value = normalized_mps[normalized_manual]
                                if matched_value in options_list:
                                    initial_index = options_list.index(matched_value)
                                    st.session_state[mp_select_key] = matched_value
                            else:
                                # Append manual value
                                if manual_value and manual_value not in options_list:
                                    options_list.append(manual_value)
                                    initial_index = len(options_list) - 1
                                    st.session_state[mp_select_key] = manual_value
                        
                        # Initialize mp_select_key if not present
                        if mp_select_key not in st.session_state:
                            st.session_state[mp_select_key] = options_list[initial_index] if options_list else ""
                        
                        mp_sel = st.selectbox(
                            "Matéria-prima", 
                            options=options_list, 
                            index=initial_index,
                            key=mp_select_key
                        )
                    else:
                        if mp_manual_key not in st.session_state:
                            st.session_state[mp_manual_key] = ""
                        mp_sel = st.text_input("Matéria-prima (inserir manualmente)", key=mp_manual_key)

                    quantidade = float(st.number_input("Quantidade", min_value=0.0,
                                                      step=0.1, key=qtd_key))

                    unidade = st.selectbox("Unidade", options=["KG", "UN"],
                                           key=un_key)

                    rendimento = float(st.number_input("Rendimento (%)", min_value=1.0, max_value=100.0,
                                                      step=0.1, key=rend_key))
                else:
                    # não aberto: usar valores atuais em session_state (ou defaults)
                    mp_sel = st.session_state.get(mp_select_key, "") or st.session_state.get(mp_manual_key, "")
                    quantidade = float(st.session_state.get(qtd_key, 1.0))
                    unidade = st.session_state.get(un_key, "KG")
                    rendimento = float(st.session_state.get(rend_key, 100.0))

                materias.append(MateriaPrima(mp=mp_sel, quantidade=quantidade, unidade=unidade, rendimento=rendimento))

            componentes.append(Componente(nome=comp_nome, quantidade=int(comp_qtd), materias=materias))

    # Botão de salvar
    button_label = "Atualizar Conjunto" if (edit_id or edit_bib_index is not None) else "Salvar Conjunto na Biblioteca (sessão)"
    if st.button(button_label):
        if not nome or not cor:
            st.error("Nome e cor do conjunto são obrigatórios.")
        else:
            cj = Conjunto(nome=nome, cor=cor, componentes=componentes)
            if "biblioteca" not in st.session_state:
                st.session_state["biblioteca"] = []
            
            # Check if we're updating an existing item or inserting a new one
            if edit_bib_index is not None and 0 <= edit_bib_index < len(st.session_state["biblioteca"]):
                # Update existing item in biblioteca
                st.session_state["biblioteca"][edit_bib_index] = cj
                st.success(f"Conjunto '{nome}' atualizado na biblioteca.")
                
                # Also update in saved items store if applicable
                if edit_id:
                    from ui.exportar import update_conjunto
                    update_conjunto(edit_id, cj.model_dump())
            else:
                # Insert new item
                st.session_state["biblioteca"].append(cj)
                st.success(f"Conjunto '{nome}' salvo na biblioteca (sessão).")
                
                # Also add to saved items store
                from ui.exportar import insert_conjunto
                store_id = insert_conjunto(cj.model_dump())
                # Try to set the store_id on the object
                try:
                    cj.__dict__["__store_id"] = store_id
                except Exception:
                    pass
            
            if st.session_state.get("adicionar_ao_projeto", False):
                if "projeto" not in st.session_state:
                    from core.models import Projeto
                    st.session_state["projeto"] = Projeto(projeto_nome="PROJETO SEM NOME", conjuntos=[])
                st.session_state["projeto"].conjuntos.append(cj)
            
            # Set flag to clear form on next render and rerun
            st.session_state["cad_should_clear"] = True
            st.rerun()