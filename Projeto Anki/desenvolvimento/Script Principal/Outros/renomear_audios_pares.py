import os
import re
import sys

def rename_audio_files_in_pairs(folder_path, start_index):
    """
    Renomeia arquivos de áudio em pares (ES e EN) para uma nova sequência numérica.
    
    Args:
        folder_path (str): O caminho completo para a pasta com os arquivos de áudio.
        start_index (int): O número de onde a nova numeração deve começar.
    """
    if not os.path.isdir(folder_path):
        print(f"❌ Erro: O caminho da pasta '{folder_path}' não foi encontrado.")
        return

    print(f"▶️ Analisando a pasta: {folder_path}")

    # Lista todos os arquivos de áudio .mp3 na pasta
    mp3_files = [f for f in os.listdir(folder_path) if f.endswith('.mp3')]

    # Agrupa os arquivos por seu prefixo numérico (ex: '000', '001', etc.)
    audio_pairs = {}
    pattern = re.compile(r'^(\d{3,4})_')

    for filename in mp3_files:
        match = pattern.match(filename)
        if match:
            prefix = match.group(1)
            if prefix not in audio_pairs:
                audio_pairs[prefix] = []
            audio_pairs[prefix].append(filename)

    # Ordena os grupos de prefixo para garantir a sequência correta
    sorted_prefixes = sorted(audio_pairs.keys(), key=lambda x: int(x))
    
    if not sorted_prefixes:
        print("❌ Nenhum arquivo de áudio com o padrão 'NNN_LANG.mp3' foi encontrado na pasta.")
        print("Certifique-se de que os arquivos estão lá e têm o formato esperado.")
        return

    print(f"✅ Encontrados {len(sorted_prefixes)} pares de arquivos para renomear.")

    current_index = start_index
    for prefix in sorted_prefixes:
        files_to_rename = audio_pairs[prefix]
        
        # Para cada grupo, renomeia ambos os arquivos com o mesmo novo índice
        for old_filename in files_to_rename:
            lang_code = old_filename.split('_')[-1].split('.')[0]
            
            # Cria o novo nome de arquivo com o índice desejado (4 dígitos)
            new_filename = f"{current_index:04d}_{lang_code}.mp3"
            
            old_filepath = os.path.join(folder_path, old_filename)
            new_filepath = os.path.join(folder_path, new_filename)
            
            try:
                os.rename(old_filepath, new_filepath)
                print(f"✅ Renomeado: {old_filename} -> {new_filename}")
            except OSError as e:
                print(f"❌ Erro ao renomear o arquivo {old_filename}: {e}")
                return
        
        # Incrementa o índice apenas após renomear o par
        current_index += 1

    print("\n✅ Processo de renomear concluído com sucesso!")
    print("Agora você pode atualizar o seu CSV com os novos nomes de arquivo.")

# --- Execução do script ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: py renomear_audios_pares.py <caminho_da_pasta_audios> <numero_inicial>")
        print("Exemplo: py renomear_audios_pares.py \"C:\\Users\\guilh\\Desktop\\anki_audio\\Baralho\\audios\" 580")
        sys.exit(1)

    folder = sys.argv[1]
    try:
        start_num = int(sys.argv[2])
    except ValueError:
        print("❌ Erro: O número inicial deve ser um número inteiro.")
        sys.exit(1)

    # AVISO IMPORTANTE: Faça backup da pasta antes de rodar
    print("--- AVISO ---")
    print("Recomenda-se fazer um backup da pasta de áudio antes de rodar este script,")
    print("pois ele irá alterar os nomes dos arquivos permanentemente.")
    proceed = input("Deseja continuar? (S/n): ")
    if proceed.lower() == 's' or proceed.lower() == 'sim':
        rename_audio_files_in_pairs(folder, start_num)
    else:
        print("Processo cancelado pelo usuário.")