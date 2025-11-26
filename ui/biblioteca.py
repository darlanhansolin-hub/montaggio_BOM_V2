import streamlit as st
from typing import List, Dict, Any
import pandas as pd

# Import models defensivamente (se não existir, usamos atributos via getattr)
try:
    from core.models import Projeto
except Exception:
    Projeto = None

def _parse_number(value):
    """
    Interpreta números vindos de diferentes fontes (float/int/str) tentando
    reconhecer formatos com vírgula decimal e separador de milhares.
    Exemplos:
      "1.000,5" -> 1000.5
      "1,5" -> 1.5
      "1.000" -> 1000.0
      1, 1.0 -> 1.0
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s == "":
        return 0.0
    # se contém ambos '.' e ',' assumimos formato pt-BR: '.' milhares, ',' decimal
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        # se só tem ',', assume vírgula decimal
        if "," in s and "." not in s:
            s = s.replace(",", ".")
        # se só tem '.', assume ponto decimal (ou milhares sem decimal) -> float() trata
    try:
        return float(s)
    except Exception:
        # fallback seguro
        try:
            return float(s.replace(".", "").replace(",", "."))
        except Exception:
            return 0.0

def _fmt_num(n, dec=3, use_comma_decimal=True):
    """
    Formata número de forma amigável:
    - se inteiro, mostra sem casas decimais (10.0 -> "10")
    - senão mostra até 'dec' casas removendo zeros finais (10.500 -> "10.5")
    - por padrão troca '.' por ',' para decimal em pt-BR
    """
    try:
        n = float(n)
    except Exception:
        return str(n)
    if n.is_integer():
        s = str(int(n))
    else:
        s = f"{n:.{dec}f}".rstrip("0").rstrip(".")
    if use_comma_decimal:
        s = s.replace(".", ",")
    return s

def _compute_conjunto_weight(conjunto) -> (float, List[Dict[str, Any]]):
    """
    Calcula o peso (em KG) estimado do conjunto.
    Retorna (peso_total_kg, breakdown) onde breakdown é lista de dicts com detalhe por componente/MP.
    Regras usadas:
    - Apenas MPs com unidade 'KG' contribuem para peso.
    - qtd_ajustada = mp_qtd / (rendimento/100)   <==> mp_qtd * (100/rendimento)
    - peso do componente = sum(qtd_ajustada de suas MPs) * componente.quantidade
    - UN (unidade 'UN') é ignorado no cálculo de peso (não convertido para KG).
    """
    total_conjunto = 0.0
    breakdown = []

    componentes = getattr(conjunto, "componentes", []) or []
    for comp in componentes:
        comp_nome = getattr(comp, "nome", "<sem nome componente>")
        comp_qtd = _parse_number(getattr(comp, "quantidade", 1))
        mps = getattr(comp, "materias", []) or []

        soma_mps_comp = 0.0
        for mp in mps:
            mp_nome = getattr(mp, "mp", "") or getattr(mp, "nome", "")
            mp_qtd_raw = getattr(mp, "quantidade", 0)
            mp_un = (getattr(mp, "unidade", "") or "").upper()
            mp_rend_raw = getattr(mp, "rendimento", 100)

            mp_qtd = _parse_number(mp_qtd_raw)
            mp_rend = _parse_number(mp_rend_raw) or 100.0
            # evita divisão por zero
            if mp_rend == 0:
                qtd_ajustada = mp_qtd
            else:
                qtd_ajustada = mp_qtd * (100.0 / mp_rend)

            # só somamos se unidade for KG (ou campo vazio que assumimos KG)
            contrib_kg = 0.0
            if mp_un in ["KG", "K", "KG."]:
                contrib_kg = qtd_ajustada
            else:
                # se UN ou outro, não somamos ao peso; deixamos registro para debug
                contrib_kg = 0.0

            soma_mps_comp += contrib_kg

            breakdown.append({
                "componente": comp_nome,
                "componente_qtd": comp_qtd,
                "mp_nome": mp_nome,
                "mp_qtd_raw": mp_qtd_raw,
                "mp_qtd_parsed": mp_qtd,
                "mp_unidade": mp_un,
                "mp_rendimento_pct": mp_rend,
                "mp_qtd_ajustada": qtd_ajustada,
                "mp_contrib_kg": contrib_kg
            })

        # multiplicar pela quantidade de componentes no conjunto
        peso_comp_total = soma_mps_comp * comp_qtd
        # registrar total por componente também no breakdown (linha agregada)
        breakdown.append({
            "componente": comp_nome,
            "componente_qtd": comp_qtd,
            "mp_nome": "<TOTAL_COMPOSITO>",
            "mp_qtd_raw": "",
            "mp_qtd_parsed": "",
            "mp_unidade": "KG",
            "mp_rendimento_pct": "",
            "mp_qtd_ajustada": "",
            "mp_contrib_kg": peso_comp_total
        })

        total_conjunto += peso_comp_total

    return total_conjunto, breakdown

def render_biblioteca():
    st.header("Biblioteca de Conjuntos (sessão)")

    biblioteca = st.session_state.get("biblioteca", []) or []
    if not biblioteca:
        st.info("A biblioteca está vazia. Cadastre conjuntos na aba 'Cadastrar Conjunto'.")
    else:
        st.subheader("Conjuntos salvos (biblioteca)")
        for idx, cj in enumerate(biblioteca):
            nome = getattr(cj, "nome", "<sem nome>")
            cor = getattr(cj, "cor", "")
            cols = st.columns([6,1])
            cols[0].write(f"{idx+1}. {nome} — {cor}")
            # botão para inserir no projeto
            if cols[1].button("Inserir no projeto", key=f"inserir_{idx}"):
                # garante que exista um projeto em session_state
                if "projeto" not in st.session_state or st.session_state.get("projeto") is None:
                    if Projeto is not None:
                        st.session_state["projeto"] = Projeto(projeto_nome="PROJETO SEM NOME", conjuntos=[])
                    else:
                        # estrutura mínima se modelo Projeto não existir
                        st.session_state["projeto"] = type("P", (), {"projeto_nome": "PROJETO SEM NOME", "conjuntos": []})()
                st.session_state["projeto"].conjuntos.append(cj)
                st.success(f"{nome} inserido no projeto.")
                st.experimental_rerun()

    st.write("---")
    st.subheader("Conjuntos atualmente no Projeto")
    projeto = st.session_state.get("projeto")
    if not projeto or not getattr(projeto, "conjuntos", []):
        st.info("Nenhum conjunto inserido no projeto ainda.")
        return

    # exibir cada conjunto no projeto com peso estimado e botão de remover
    for idx, cj in enumerate(getattr(projeto, "conjuntos", [])):
        nome = getattr(cj, "nome", "<sem nome>")
        cor = getattr(cj, "cor", "")
        num_comps = len(getattr(cj, "componentes", []) or [])
        peso_total, breakdown = _compute_conjunto_weight(cj)

        cols = st.columns([6,1])
        display_text = f"{nome} ({cor}) — {num_comps} componentes — Peso estimado: {_fmt_num(peso_total, dec=3)} kg"
        cols[0].write(display_text)
        if cols[1].button("Remover", key=f"remover_proj_{idx}"):
            projeto.conjuntos.pop(idx)
            st.success(f"{nome} removido do projeto.")
            st.experimental_rerun()

        # Expander de debug/validação: mostra tabela com breakdown dos cálculos
        with st.expander("Mostrar detalhes do cálculo (debug)", expanded=False):
            if breakdown:
                try:
                    df = pd.DataFrame(breakdown)
                    # organizar colunas para leitura
                    cols_order = [
                        "componente", "componente_qtd", "mp_nome",
                        "mp_qtd_raw", "mp_qtd_parsed", "mp_unidade",
                        "mp_rendimento_pct", "mp_qtd_ajustada", "mp_contrib_kg"
                    ]
                    df = df[[c for c in cols_order if c in df.columns]]
                    # formatar algumas colunas para exibição
                    df["mp_qtd_parsed"] = df["mp_qtd_parsed"].apply(lambda x: _fmt_num(x))
                    df["mp_qtd_ajustada"] = df["mp_qtd_ajustada"].apply(lambda x: _fmt_num(x) if x != "" else "")
                    df["mp_contrib_kg"] = df["mp_contrib_kg"].apply(lambda x: _fmt_num(x))
                    st.dataframe(df)
                except Exception as e:
                    st.write("Não foi possível montar tabela de debug:", e)
            st.write(f"Peso total calculado (raw): {_fmt_num(peso_total, dec=6)} kg")
            st.write("Observações:")
            st.write("- Apenas MPs com unidade 'KG' são consideradas no peso.")
            st.write("- Se suas MPs estiverem em 'UN' e precisarem ser convertidas para KG, informe a regra de conversão que eu implemento.")
            st.write("- Se números aparecem com formatação estranha (ex.: '1.000'), o parser tenta interpretar separador de milhares e vírgula decimal automaticamente.")