```markdown
# Montaggio — Gerador de BOM Oracle (FASE 2)

Aplicação Streamlit para cadastro de conjuntos, manutenção de biblioteca em sessão e exportação de 3 planilhas XLSX no padrão Oracle NetSuite.

Como rodar
1. Crie um virtualenv (Python 3.10+ recomendado)
2. pip install -r requirements.txt
3. Coloque um arquivo materias_primas.csv na mesma pasta (ex. o arquivo de exemplo já incluso)
4. streamlit run app/main.py

Estrutura
- app/main.py — entrada Streamlit
- ui/ — telas: cadastro_conjunto.py, biblioteca.py, exportar.py
- core/ — models.py, logic.py, export_xlsx.py
- materias_primas.csv — lista de MPs (exemplo)

Observações
- Validações bloqueiam exportação se regras essenciais não forem atendidas.
- MPs com unidade "UN" não somam peso (kg) automaticamente — se for necessário, adicionar campo peso por unidade.
- IDs auto gerados (CJ_0001, CP_0001).
```