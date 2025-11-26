import io
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import date

def _parse_number(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s == "":
        return 0.0
    # interpreta formatos pt-BR e en-US
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        if "," in s and "." not in s:
            s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        try:
            return float(s.replace(".", "").replace(",", "."))
        except Exception:
            return 0.0

def _component_weight_kg(comp) -> float:
    total = 0.0
    mps = getattr(comp, "materias", []) or []
    for mp in mps:
        mp_qtd = _parse_number(getattr(mp, "quantidade", 0))
        mp_un = (getattr(mp, "unidade", "") or "").upper()
        mp_rend = _parse_number(getattr(mp, "rendimento", 100)) or 100.0
        qtd_ajustada = mp_qtd if mp_rend == 0 else mp_qtd * (100.0 / mp_rend)
        # somar apenas MPs em kg
        if mp_un in ["KG", "K", "KG."]:
            total += qtd_ajustada
    return total

def _compute_total_weight_kg(conjunto) -> float:
    total = 0.0
    componentes = getattr(conjunto, "componentes", []) or []
    for comp in componentes:
        comp_qty = _parse_number(getattr(comp, "quantidade", 1))
        comp_weight_per_unit = _component_weight_kg(comp)
        total += comp_weight_per_unit * comp_qty
    return total

def gerar_export_xlsx_unico(biblioteca: List, project_name: Optional[str]) -> bytes:
    """
    Gera um XLSX (em bytes) com 3 sheets:
      - Item_Montagem: inclui o item do projeto (project_name), 1 linha por conjunto e 1 linha por componente.
      - Lista_de_Materiais: contém:
           * 1 linha do projeto (project_name),
           * 1 linha por conjunto,
           * 1 linha por componente,
           * linhas de associação project->conjunto representadas utilizando a coluna "Usado em Item Montado"
             mantendo "Nome" == "Restringir a Itens Montados Específicos" em todas as linhas.
      - Revisao_BOM: árvore da BOM sem linhas com "Item" vazio e sem totais compostos.
    Observações:
      - project_name deve ser passado pela UI; se vazio, será usado "BOM GLOBAL" como fallback.
      - Valores binários usam "Sim"/"Não" em português.
    """
    if not project_name:
        project_name = "BOM GLOBAL"  # fallback, ideal é sempre passar o nome vindo da UI

    today = date.today().isoformat()

    rows_item_montagem: List[Dict[str, Any]] = []
    rows_lista_materiais: List[Dict[str, Any]] = []
    rows_revisao: List[Dict[str, Any]] = []

    # evitar duplicatas por nome nas listas de itens
    seen_items_item_montagem = set()
    seen_lista_rows = set()  # set of tuples to dedupe identical rows

    # --- Item_Montagem ---
    def add_item_montagem(name: str, peso: Optional[float] = ""):
        key = name.strip()
        if not key:
            return
        if key in seen_items_item_montagem:
            return
        seen_items_item_montagem.add(key)
        rows_item_montagem.append({
            "ID Externo": "",
            "Nome/Número do Item": key,
            "Nome de Exibição/Código": key,
            "Tipo de Unidade Principal": "UN",
            "Unidade de Estoque Principal": "UN",
            "Unidade de Compra Principal": "UN",
            "Unidade de Venda Principal": "UN",
            "Unidade de Consumo Principal": "UN",
            "Subsidiária": 1,
            "Código do item do suitetax latam engine": "",
            "Origem": "00",
            "CEST": "",
            "Código de enquadramento do IPI": "",
            "Tipo de sped EFD": "",
            "Categoria de Custo": "",
            "Método de Custeio": "Custo Médio",
            "Conta de CMV": "",
            "Conta de Ativo": "",
            "Conta de Receita": "",
            "Conta de Variação de Quantidade Produzida": "",
            "Conta de Variação de Desmontagem": "",
            "Conta de Variação de Custo em Produção (WIP)": "",
            "Conta de Refugo": "",
            "Conta de Produção em Andamento (WIP)": "",
            "Rastrear Custo de Aquisição": "",
            "Peso do Item": peso if peso != "" else ""
        })

    # adicionar item do projeto
    add_item_montagem(project_name, "")

    for cj in biblioteca:
        cj_nome = getattr(cj, "nome", "") or ""
        cj_cor = getattr(cj, "cor", "") or ""
        cj_fullname = f"{cj_nome} {cj_cor}".strip()
        comps = getattr(cj, "componentes", []) or []

        # Peso total do conjunto (somente MPs em kg)
        peso_total_kg = _compute_total_weight_kg(cj)

        # adicionar conjunto como item
        add_item_montagem(cj_fullname, peso_total_kg)

        # adicionar componentes como itens
        for comp in comps:
            comp_nome = getattr(comp, "nome", "") or ""
            comp_weight = _component_weight_kg(comp)
            add_item_montagem(comp_nome, comp_weight)

    # --- Lista_de_Materiais ---
    # colunas principais: "Campo","ID Externo","Nome","Considerar Rendimento do Componente",
    # "Disponível para Todos os Itens Montados","Restringir a Itens Montados Específicos",
    # "Disponível para Todas as Localizações","Restringir a Localizações Específicas",
    # "Subsidiária","Usado em Item Montado"

    # 1) linha do projeto/global (apenas uma linha base)
    base_proj_row = (
        "", "", project_name, "Sim",
        "Sim", project_name,
        "Sim", "", 1, ""
    )
    if base_proj_row not in seen_lista_rows:
        seen_lista_rows.add(base_proj_row)
        rows_lista_materiais.append({
            "Campo": "",
            "ID Externo": "",
            "Nome": project_name,
            "Considerar Rendimento do Componente": "Sim",
            "Disponível para Todos os Itens Montados": "Sim",
            "Restringir a Itens Montados Específicos": project_name,
            "Disponível para Todas as Localizações": "Sim",
            "Restringir a Localizações Específicas": "",
            "Subsidiária": 1,
            "Usado em Item Montado": ""
        })

    for cj in biblioteca:
        cj_nome = getattr(cj, "nome", "") or ""
        cj_cor = getattr(cj, "cor", "") or ""
        cj_fullname = f"{cj_nome} {cj_cor}".strip()
        comps = getattr(cj, "componentes", []) or []

        # linha que associa project -> conjunto:
        # mantemos "Nome" == "Restringir a Itens Montados Específicos" conforme solicitado,
        # e colocamos o conjunto alvo na coluna "Usado em Item Montado" para representar a associação.
        assoc_row = (
            "", "", project_name, "Sim",
            "Sim", project_name,
            "Sim", "", 1, cj_fullname
        )
        if assoc_row not in seen_lista_rows:
            seen_lista_rows.add(assoc_row)
            rows_lista_materiais.append({
                "Campo": "",
                "ID Externo": "",
                "Nome": project_name,
                "Considerar Rendimento do Componente": "Sim",
                "Disponível para Todos os Itens Montados": "Sim",
                "Restringir a Itens Montados Específicos": project_name,
                "Disponível para Todas as Localizações": "Sim",
                "Restringir a Localizações Específicas": "",
                "Subsidiária": 1,
                "Usado em Item Montado": cj_fullname
            })

        # linha do próprio conjunto (uma por conjunto)
        cj_row = (
            "", "", cj_fullname, "Sim",
            "Não", cj_fullname,
            "Sim", "", 1, ""
        )
        if cj_row not in seen_lista_rows:
            seen_lista_rows.add(cj_row)
            rows_lista_materiais.append({
                "Campo": "",
                "ID Externo": "",
                "Nome": cj_fullname,
                "Considerar Rendimento do Componente": "Sim",
                "Disponível para Todos os Itens Montados": "Não",
                "Restringir a Itens Montados Específicos": cj_fullname,
                "Disponível para Todas as Localizações": "Sim",
                "Restringir a Localizações Específicas": "",
                "Subsidiária": 1,
                "Usado em Item Montado": ""
            })

        # linhas de componentes (cada componente uma linha, Nome == Restringir)
        for comp in comps:
            comp_nome = getattr(comp, "nome", "") or ""
            comp_row = (
                "", "", comp_nome, "Sim",
                "Não", comp_nome,
                "Sim", "", 1, ""
            )
            if comp_row not in seen_lista_rows:
                seen_lista_rows.add(comp_row)
                rows_lista_materiais.append({
                    "Campo": "",
                    "ID Externo": "",
                    "Nome": comp_nome,
                    "Considerar Rendimento do Componente": "Sim",
                    "Disponível para Todos os Itens Montados": "Não",
                    "Restringir a Itens Montados Específicos": comp_nome,
                    "Disponível para Todas as Localizações": "Sim",
                    "Restringir a Localizações Específicas": "",
                    "Subsidiária": 1,
                    "Usado em Item Montado": ""
                })

    # --- Revisao_BOM ---
    # Para cada conjunto: 1 linha associando project -> conjunto (Item = nome do conjunto)
    # Para cada componente: 1 linha vinculando conjunto -> componente (Item = componente)
    # Para cada MP do componente: 1 linha com Nome/Estrutura = componente e Item = mp
    # Não gerar linhas com Item vazio e não gerar totais compostos.

    for cj in biblioteca:
        cj_nome = getattr(cj, "nome", "") or ""
        cj_cor = getattr(cj, "cor", "") or ""
        cj_fullname = f"{cj_nome} {cj_cor}".strip()
        comps = getattr(cj, "componentes", []) or []

        # associação project -> conjunto
        rows_revisao.append({
            "ID Externo": "",
            "Nome": project_name,
            "Estrutura de Produto": project_name,
            "Data de Início": today,
            "Data de Fim": "",
            "Item": cj_fullname,
            "Rendimento (%)": 100,
            "Quantidade da BOM": 1,
            "Quantidade do Componente": "",
            "Unidade": "UN",
            "Origem": "OS",
            "Etapa de Liberação": "",
            "Emissão Automática": "",
            "Outros": ""
        })

        for comp in comps:
            comp_nome = getattr(comp, "nome", "") or ""
            comp_qtd = _parse_number(getattr(comp, "quantidade", 1))

            # vínculo conjunto -> componente (Item preenchido)
            rows_revisao.append({
                "ID Externo": "",
                "Nome": cj_fullname,
                "Estrutura de Produto": cj_fullname,
                "Data de Início": today,
                "Data de Fim": "",
                "Item": comp_nome,
                "Rendimento (%)": 100,
                "Quantidade da BOM": comp_qtd,
                "Quantidade do Componente": "",
                "Unidade": "UN",
                "Origem": "OS",
                "Etapa de Liberação": "",
                "Emissão Automática": "",
                "Outros": ""
            })

            # linhas das MPs do componente (Nome/Estrutura = componente; Item = mp)
            mps = getattr(comp, "materias", []) or []
            for mp in mps:
                mp_nome = getattr(mp, "mp", "") or getattr(mp, "nome", "") or ""
                mp_qtd = _parse_number(getattr(mp, "quantidade", 0))
                mp_un = (getattr(mp, "unidade", "") or "").upper()
                mp_rend = _parse_number(getattr(mp, "rendimento", 100))
                mp_rend_use = mp_rend if mp_un != "UN" else 100.0

                # garantir que só adicionamos linhas com item preenchido
                if not mp_nome:
                    continue

                rows_revisao.append({
                    "ID Externo": "",
                    "Nome": comp_nome,
                    "Estrutura de Produto": comp_nome,
                    "Data de Início": today,
                    "Data de Fim": "",
                    "Item": mp_nome,
                    "Rendimento (%)": mp_rend_use,
                    "Quantidade da BOM": mp_qtd,
                    "Quantidade do Componente": "",
                    "Unidade": mp_un if mp_un else "KG",
                    "Origem": "Estoque",
                    "Etapa de Liberação": "",
                    "Emissão Automática": "",
                    "Outros": ""
                })

    # Construir DataFrames e garantir colunas consistentes
    df_item = pd.DataFrame(rows_item_montagem)
    df_lista = pd.DataFrame(rows_lista_materiais)
    df_rev = pd.DataFrame(rows_revisao)

    # garantir colunas (se algum df estiver vazio)
    if df_item.empty:
        df_item = pd.DataFrame(columns=[
            "ID Externo","Nome/Número do Item","Nome de Exibição/Código","Tipo de Unidade Principal",
            "Unidade de Estoque Principal","Unidade de Compra Principal","Unidade de Venda Principal",
            "Unidade de Consumo Principal","Subsidiária","Código do item do suitetax latam engine",
            "Origem","CEST","Código de enquadramento do IPI","Tipo de sped EFD","Categoria de Custo",
            "Método de Custeio","Conta de CMV","Conta de Ativo","Conta de Receita",
            "Conta de Variação de Quantidade Produzida","Conta de Variação de Desmontagem",
            "Conta de Variação de Custo em Produção (WIP)","Conta de Refugo",
            "Conta de Produção em Andamento (WIP)","Rastrear Custo de Aquisição","Peso do Item"
        ])
    if df_lista.empty:
        df_lista = pd.DataFrame(columns=[
            "Campo","ID Externo","Nome","Considerar Rendimento do Componente",
            "Disponível para Todos os Itens Montados","Restringir a Itens Montados Específicos",
            "Disponível para Todas as Localizações","Restringir a Localizações Específicas",
            "Subsidiária","Usado em Item Montado"
        ])
    if df_rev.empty:
        df_rev = pd.DataFrame(columns=[
            "ID Externo","Nome","Estrutura de Produto","Data de Início","Data de Fim",
            "Item","Rendimento (%)","Quantidade da BOM","Quantidade do Componente",
            "Unidade","Origem","Etapa de Liberação","Emissão Automática","Outros"
        ])

    # Gerar XLSX em memória com 3 sheets
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_item.to_excel(writer, sheet_name="Item_Montagem", index=False)
        df_lista.to_excel(writer, sheet_name="Lista_de_Materiais", index=False)
        df_rev.to_excel(writer, sheet_name="Revisao_BOM", index=False)
    output.seek(0)
    return output.getvalue()