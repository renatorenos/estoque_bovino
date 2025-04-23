import pandas as pd

# Leitura dos arquivos
df_in = pd.read_csv('entradas.csv', sep=';', decimal=',', quotechar='"')
df_out = pd.read_csv('vendas.csv', sep=';', decimal=',', quotechar='"')

# Converter colunas numéricas
df_in['QUANTIDADE'] = pd.to_numeric(df_in['QUANTIDADE'], errors='coerce')
df_out['QUANTIDADE'] = pd.to_numeric(df_out['QUANTIDADE'], errors='coerce')

# Converter datas
df_in['DATA'] = pd.to_datetime(df_in['DATA'], format='%d/%m/%y')
df_out['DATA'] = pd.to_datetime(df_out['DATA'], format='%d/%m/%y')

# Padronizar formato da hora
df_in['HORA'] = df_in['HORA'].astype(str).str.zfill(8)
df_out['HORA'] = df_out['HORA'].astype(str).str.zfill(8)

# Criar datetime completo
df_in['DATETIME'] = pd.to_datetime(df_in['DATA'].dt.strftime('%Y-%m-%d') + ' ' + df_in['HORA'])
df_out['DATETIME'] = pd.to_datetime(df_out['DATA'].dt.strftime('%Y-%m-%d') + ' ' + df_out['HORA'])

# Ordenar cronologicamente
in_sorted = df_in.sort_values('DATETIME').reset_index(drop=True)
out_sorted = df_out.sort_values('DATETIME').reset_index(drop=True)

# Alocação FIFO
alloc = []
entry_idx = 0
remain = in_sorted.loc[entry_idx, 'QUANTIDADE']

for _, out_row in out_sorted.iterrows():
    need = out_row['QUANTIDADE']
    while need > 1e-9 and entry_idx < len(in_sorted):
        take = min(need, remain)
        alloc.append({
            'ENTRY_IDX': entry_idx,
            'ENTRY_DATE': in_sorted.loc[entry_idx, 'DATA'],
            'ENTRY_QTY': in_sorted.loc[entry_idx, 'QUANTIDADE'],
            'OUT_DATE': out_row['DATA'],
            'CUT_CODE': out_row['SEQPRODUTO'],
            'CUT_DESC': out_row['DESCCOMPLETA'],
            'ALLOC_KG': take
        })
        need -= take
        remain -= take
        if remain <= 1e-9:
            entry_idx += 1
            if entry_idx < len(in_sorted):
                remain = in_sorted.loc[entry_idx, 'QUANTIDADE']

# Criar DataFrame de alocação
alloc_df = pd.DataFrame(alloc)

# Calcular sumário por entrada
summary = alloc_df.groupby(['ENTRY_IDX', 'ENTRY_DATE', 'CUT_DESC'])['ALLOC_KG'].sum().reset_index()
summary = summary.merge(alloc_df[['ENTRY_IDX', 'ENTRY_QTY']].drop_duplicates(), on='ENTRY_IDX')
summary['PERCENT'] = summary['ALLOC_KG'] / summary['ENTRY_QTY'] * 100

print("\nCortes por entrada (em percentual do peso total):\n")
for entry_idx in summary['ENTRY_IDX'].unique():
    entry_data = summary[summary['ENTRY_IDX'] == entry_idx].sort_values('PERCENT', ascending=False)
    entry_date = entry_data['ENTRY_DATE'].iloc[0].strftime('%d/%m/%Y')
    total_allocated = entry_data['ALLOC_KG'].sum()
    total_qty = entry_data['ENTRY_QTY'].iloc[0]

    print(f"\nEntrada {entry_idx} - Data: {entry_date}")
    print(f"Peso total: {total_qty:.2f} kg")
    print(f"Peso alocado: {total_allocated:.2f} kg ({(total_allocated/total_qty*100):.2f}%)")
    print("\nTodos os cortes:")

    for _, row in entry_data.iterrows():
        print(f"{row['CUT_DESC']}: {row['PERCENT']:.2f}%")

def obter_maior_porcentagem_por_produto():
    """
    Retorna a maior porcentagem utilizada para cada produto.
    
    Returns:
        pandas.Series: Série com as maiores porcentagens por produto
    """
    return summary.groupby('CUT_DESC')['PERCENT'].max().sort_values(ascending=False)

# Salvar resultados em CSV
summary.to_csv('analise_cortes.csv', index=False, sep=';', decimal=',', encoding='utf-8-sig')

print("\n Maior porcentagem por produto: ")
maiores_porcentagens = obter_maior_porcentagem_por_produto()
for produto, porcentagem in maiores_porcentagens.items():
    print(f"{produto}: {porcentagem:.2f}%")
print(maiores_porcentagens.sum())