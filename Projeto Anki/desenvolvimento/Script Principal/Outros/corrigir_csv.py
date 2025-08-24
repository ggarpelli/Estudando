import pandas as pd
import os
import re

def update_csv_audio_links():
    """
    Script interativo para atualizar os links de áudio em um arquivo CSV.
    """
    print("--- Corretor de Links de Áudio para CSV ---")

    # 1. Pede o caminho do arquivo CSV
    csv_path = input("▶️ Por favor, digite o NOME do arquivo CSV que você quer corrigir (ex: parte_3_with_audio.csv): ")
    if not os.path.isfile(csv_path):
        print(f"❌ Erro: Arquivo '{csv_path}' não encontrado. Certifique-se de que o script e o arquivo estão na mesma pasta.")
        input("Pressione Enter para sair.")
        return

    # 2. Pede o número de início
    while True:
        try:
            start_num_str = input("▶️ Por favor, digite o NÚMERO INICIAL para os novos áudios (ex: 580): ")
            start_index = int(start_num_str)
            break
        except ValueError:
            print("❌ Entrada inválida. Por favor, digite um número inteiro.")

    print(f"\n▶️ Carregando o arquivo: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo CSV. Verifique se o formato está correto. Erro: {e}")
        input("Pressione Enter para sair.")
        return

    if "Audio_ES" not in df.columns or "Audio_EN" not in df.columns:
        print("❌ O arquivo CSV não contém as colunas 'Audio_ES' ou 'Audio_EN'.")
        input("Pressione Enter para sair.")
        return

    print(f"✅ Arquivo carregado. Total de {len(df)} linhas para processar.")

    pattern = re.compile(r'\[sound:(\d{3,4})_')

    for index, row in df.iterrows():
        if pd.notna(row["Audio_ES"]) and pd.notna(row["Audio_EN"]):
            old_es_link = str(row["Audio_ES"])
            
            match = pattern.search(old_es_link)
            if match:
                old_index_num = int(match.group(1))
                new_index_num = start_index + old_index_num
                
                new_es_link = f"[sound:{new_index_num:04d}_ES.mp3]"
                new_en_link = f"[sound:{new_index_num:04d}_EN.mp3]"

                df.at[index, "Audio_ES"] = new_es_link
                df.at[index, "Audio_EN"] = new_en_link
                
                print(f"✅ Linha {index+1}: Links atualizados de {old_index_num:03d} para {new_index_num:04d}.")

    updated_csv_path = csv_path.replace(".csv", "_updated.csv")
    df.to_csv(updated_csv_path, index=False)
    
    print("\n--- Processo Concluído ---")
    print(f"✅ O seu arquivo corrigido foi salvo como: {updated_csv_path}")
    print("Agora você pode importar este novo arquivo no Anki.")
    input("Pressione Enter para sair.")

if __name__ == "__main__":
    update_csv_audio_links()