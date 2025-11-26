import os

def load_materias_primas(path: str = "materias_primas.csv"):
    """
    Lê o arquivo materias_primas.csv e retorna uma lista de nomes.
    Usa sep='\\n' / leitura linha-a-linha para preservar vírgulas e pontos nos nomes.
    """
    # Tenta com pandas se disponível (mais robusto), senão faz leitura simples
    try:
        import pandas as pd
        if not os.path.exists(path):
            return []
        # ler por linha para preservar vírgulas no texto
        df = pd.read_csv(path, header=None, sep="\n", engine="python", encoding="utf-8")
        items = df[0].astype(str).str.strip().tolist()
        return [i for i in items if i]
    except Exception:
        # fallback simples
        try:
            if not os.path.exists(path):
                return []
            with open(path, encoding="utf-8") as f:
                items = [line.rstrip("\n").strip() for line in f if line.strip()]
            return items
        except FileNotFoundError:
            return []