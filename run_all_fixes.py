from pathlib import Path
import shutil
import sys
import re
import subprocess
import argparse

ROOT = Path.cwd()
TARGET = ROOT / "ui" / "exportar.py"

ROBUST_FN = '''
# --- begin: clear_form_fields_robust added by helper script ---
def clear_form_fields_robust():
    """Remove keys de sessão usados por vários formulários possíveis."""
    try:
        keys_to_explicitly_remove = {
            "form_nome", "form_cor", "form_descricao", "edit_id",
            "nome", "cor", "descricao",
            "conjunto_nome", "conjunto_cor", "conjunto_descricao"
        }
        for k in list(st.session_state.keys()):
            if k in keys_to_explicitly_remove:
                try:
                    del st.session_state[k]
                except Exception:
                    pass
                continue
            if k.startswith("form_") or k.startswith("conjunto_") or k.startswith("cfg_"):
                try:
                    del st.session_state[k]
                except Exception:
                    pass
    except Exception:
        for k in ("form_nome", "form_cor", "form_descricao", "edit_id"):
            if k in st.session_state:
                try:
                    del st.session_state[k]
                except Exception:
                    pass
# --- end: clear_form_fields_robust ---
'''

def make_backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak")
    shutil.copy(path, bak)
    return bak

def replace_clear_calls(path: Path):
    text = path.read_text(encoding="utf-8")
    changed = False
    if "clear_form_fields_robust" in text:
        # Already contains robust function; only replace calls if present
        if "clear_form_fields()" in text:
            text = text.replace("clear_form_fields()", "clear_form_fields_robust()")
            changed = True
    else:
        if "clear_form_fields()" in text:
            text = text.replace("clear_form_fields()", "clear_form_fields_robust()")
            changed = True
        # append robust fn if not present
        if "clear_form_fields_robust" not in text:
            text = text.rstrip() + "\n\n" + ROBUST_FN + "\n"
            changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed

def find_defs(root: Path, names):
    pattern = re.compile(r"def\s+(" + "|".join(re.escape(n) for n in names) + r")\s*\(")
    results = {}
    for p in root.rglob("*.py"):
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in pattern.finditer(txt):
            fn = m.group(1)
            results.setdefault(fn, []).append(str(p.relative_to(root)))
    return results

def git_commit(path: Path, branch_name="fix/exportar-clear"):
    # create branch, add and commit
    cmds = [
        ["git", "checkout", "-b", branch_name],
        ["git", "add", str(path.relative_to(ROOT))],
        ["git", "commit", "-m", "fix: robust clear_form_fields in ui/exportar.py"],
    ]
    for c in cmds:
        res = subprocess.run(c, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            return False, f"git command failed: {' '.join(c)}\nstdout:{res.stdout}\nstderr:{res.stderr}"
    return True, "git commit created on branch " + branch_name

def main(args):
    if not TARGET.exists():
        print("ERRO: ui/exportar.py não encontrado no diretório atual.")
        sys.exit(1)

    print("Criando backup de ui/exportar.py ...")
    bak = make_backup(TARGET)
    print(f"Backup criado em: {bak}")

    print("Substituindo chamadas clear_form_fields() e garantindo função robusta...")
    changed = replace_clear_calls(TARGET)
    print("Arquivo atualizado." if changed else "Nenhuma substituição necessária (já aplicado).")

    print("\nProcurando definições de funções importantes no repositório...")
    defs = find_defs(ROOT, ["insert_conjunto", "update_conjunto", "load_saved_items", "get_all_conjuntos"])
    if defs:
        for fn, files in defs.items():
            print(f"- {fn}:")
            for f in files:
                print(f"    {f}")
    else:
        print("Nenhuma definição encontrada para insert_conjunto/update_conjunto/load_saved_items/get_all_conjuntos")

    if args.commit:
        print("\nTentando criar branch/commit git...")
        ok, msg = git_commit(TARGET)
        if ok:
            print("Commit criado com sucesso:", msg)
            print("Para enviar ao GitHub execute:\n  git push -u origin fix/exportar-clear\nE então abra um Pull Request no GitHub.")
        else:
            print("Falha ao criar commit:", msg)

    print("\nPronto. Verifique ui/exportar.py e reinicie o Streamlit.")
    print("Reinicie com: streamlit run app/main.py")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Aplica correções em ui/exportar.py (backup incluso).")
    parser.add_argument("--commit", action="store_true", help="Criar branch git e commitar a mudança")
    args = parser.parse_args()
    main(args)