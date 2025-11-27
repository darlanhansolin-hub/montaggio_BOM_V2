from pathlib import Path
import shutil
import sys

SRC = Path("ui") / "cadastro_conjunto.py"
BAK = SRC.with_suffix(SRC.suffix + ".bak")

if not SRC.exists():
    print("ERRO: ui/cadastro_conjunto.py não encontrado. Rode este script na raiz do projeto.")
    sys.exit(1)

txt = SRC.read_text(encoding="utf-8")

if "clear_cadastro_session_fields" in txt and "_clear_cadastro_keys()" in txt:
    print("Parece que a correção já foi aplicada. Nada a fazer.")
    sys.exit(0)

# backup
shutil.copy(SRC, BAK)
print(f"Backup criado em: {BAK}")

# Insert a small clearing helper at end if not present
helper_fn = '''

# --- begin: clear_cadastro_session_fields added by helper script ---
def clear_cadastro_session_fields():
    """
    Remove keys de sessão criadas pelo formulário de cadastro de conjuntos
    para evitar que valores persistam entre abas.
    """
    try:
        for k in list(st.session_state.keys()):
            if k.startswith("cad_") or k.startswith("comp_") or k.startswith("mp_"):
                try:
                    del st.session_state[k]
                except Exception:
                    pass
    except Exception:
        # degrade graciosamente
        for k in ("cad_nome", "cad_cor", "cad_num_componentes"):
            if k in st.session_state:
                try:
                    del st.session_state[k]
                except Exception:
                    pass
# --- end: clear_cadastro_session_fields ---
'''

if "clear_cadastro_session_fields" not in txt:
    txt = txt.rstrip() + "\n\n" + helper_fn + "\n"
    print("Função helper adicionada ao final do arquivo.")

# Now, insert a call to clear and rerun right after the success message when saving
old_snippet = "st.success(f\"Conjunto '{nome}' salvo na biblioteca (sessÃ£o).\")"
if old_snippet in txt:
    new_snippet = old_snippet + """\n            # limpar chaves do formulário de cadastro para evitar poluição entre abas\n            try:\n                clear_cadastro_session_fields()\n            except Exception:\n                pass\n            st.experimental_rerun()"""
    txt = txt.replace(old_snippet, new_snippet)
    print("Inserida chamada para limpar as chaves de sessão e reiniciar a UI após salvar.")
else:
    # fallback: try to find a simpler marker 'st.session_state[\"biblioteca\"].append(cj)' and inject after it
    marker = 'st.session_state["biblioteca"].append(cj)'
    if marker in txt and "clear_cadastro_session_fields()" not in txt:
        txt = txt.replace(marker, marker + """\n            try:\n                clear_cadastro_session_fields()\n            except Exception:\n                pass\n            st.experimental_rerun()""")
        print("Marcador alternativo encontrado; chamada de limpeza inserida após append.")
    else:
        print("Não encontrei o trecho esperado para inserir a limpeza automaticamente. Abra o arquivo ui/cadastro_conjunto.py e, logo após a mensagem de sucesso, adicione:\n\n    try:\n        clear_cadastro_session_fields()\n    except Exception:\n        pass\n    st.experimental_rerun()\n\nOu me diga e eu gero um patch manual.")

# write back
SRC.write_text(txt, encoding="utf-8")
print("Arquivo atualizado. Reinicie o Streamlit e teste.")