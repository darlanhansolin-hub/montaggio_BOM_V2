from pathlib import Path
import shutil
import sys

path = Path("ui") / "exportar.py"
bak = Path("ui") / "exportar.py.bak"

if not path.exists():
    print("ERRO: arquivo ui/exportar.py não encontrado. Rode este script na raiz do projeto.")
    sys.exit(1)

text = path.read_text(encoding="utf-8")

if "clear_form_fields_robust" in text:
    print("Parece que o ajuste já foi aplicado (clear_form_fields_robust encontrado). Nada a fazer.")
    sys.exit(0)

# backup
shutil.copy(path, bak)

# substitui chamadas antigas por chamada robusta
new_text = text.replace("clear_form_fields()", "clear_form_fields_robust()")

# função robusta a ser adicionada no final do arquivo
robust_fn = """

# --- begin: clear_form_fields_robust added by helper script ---
def clear_form_fields_robust():
    \"\"\"Remove keys de sessão usados por vários formulários possíveis.
    Mantém lista de chaves comuns e também remove prefixes comuns.
    \"\"\"
    try:
        keys_to_explicitly_remove = {
            \"form_nome\", \"form_cor\", \"form_descricao\", \"edit_id\",
            \"nome\", \"cor\", \"descricao\",
            \"conjunto_nome\", \"conjunto_cor\", \"conjunto_descricao\"
        }
        # iterate over a list copy because we'll delete while iterating
        for k in list(st.session_state.keys()):
            if k in keys_to_explicitly_remove:
                del st.session_state[k]
                continue
            # remove common prefixes
            if k.startswith(\"form_\") or k.startswith(\"conjunto_\") or k.startswith(\"cfg_\"):
                try:
                    del st.session_state[k]
                except Exception:
                    pass
    except Exception:
        # se algo falhar, não quebrar a app (só tenta remover as chaves usuais)
        for k in (\"form_nome\", \"form_cor\", \"form_descricao\", \"edit_id\"):
            if k in st.session_state:
                try:
                    del st.session_state[k]
                except Exception:
                    pass
# --- end: clear_form_fields_robust ---
"""

# append the function to the file
new_text = new_text.rstrip() + "\n\n" + robust_fn + "\n"

path.write_text(new_text, encoding="utf-8")
print("done — backup salvo em ui/exportar.py.bak e clear_form_fields substituído por clear_form_fields_robust().")