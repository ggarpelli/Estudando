import os
import requests
import pandas as pd
import re
import glob

# === CONFIGURAÇÕES ===
API_KEY = os.getenv("ELEVEN_API_KEY")  # sua chave da ElevenLabs (definida no terminal)
OUTPUT_DIR = "audios"
INPUT_CSV = "anki_vocab_ES_EN_PT.csv"
OUTPUT_CSV = "anki_vocab_ES_EN_PT_with_audio.csv"

# IDs das vozes que você escolheu
VOICE_ES = "kulszILr6ees0ArU8miO"  # Espanhol (Franco - Argentino)
VOICE_EN = "UgBBYS2sOqTuMpoF3BR0"  # Inglês (Mark - Natural Conversations)

MODEL = "eleven_multilingual_v2"
URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

def find_last_index(directory):
    """Encontra o último índice numérico de arquivos de áudio em um diretório."""
    max_index = -1
    if os.path.exists(directory):
        # Escaneia arquivos .mp3 e extrai o número
        files = glob.glob(os.path.join(directory, '*.mp3'))
        for filepath in files:
            filename = os.path.basename(filepath)
            match = re.match(r'(\d+)_', filename)
            if match:
                max_index = max(max_index, int(match.group(1)))
    return max_index

def generate_audio(text, voice_id, lang_code, idx):
    if not API_KEY:
        print("❌ A chave da API não foi encontrada. Por favor, defina a variável de ambiente ELEVEN_API_KEY.")
        return ""
        
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": MODEL,
        "voice_settings": {
            "stability": 0.7,
            "similarity_boost": 0.7,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }

    response = requests.post(URL.format(voice_id=voice_id), headers=headers, json=data)
    if response.status_code == 200:
        filename = f"{idx:03d}_{lang_code}.mp3"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"✅ Saved: {filepath}")
        return f"[sound:{filename}]"
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return ""

def main():
    print("--- Gerador de Áudios ---")

    # 1. Obter o caminho da pasta de mídia do Anki
    while True:
        anki_media_path = input("▶️ Digite o CAMINHO COMPLETO da sua pasta de mídia do Anki (collection.media) para verificar o último áudio: ")
        if os.path.exists(anki_media_path):
            break
        else:
            print(f"❌ Erro: O diretório '{anki_media_path}' não foi encontrado. Por favor, tente novamente.")

    # 2. Encontrar o último índice para começar a numeração
    last_index = find_last_index(anki_media_path)
    start_index = last_index + 1
    print(f"✅ Encontrado o último índice de áudio: {last_index}. A nova numeração começará em {start_index}.")

    # 3. Carregar e processar o CSV
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Erro: O arquivo de entrada '{INPUT_CSV}' não foi encontrado. Certifique-se de que ele está na mesma pasta que o script.")
        return

    df = pd.read_csv(INPUT_CSV)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Criar novas colunas (se não existirem)
    if "Audio_ES" not in df.columns:
        df["Audio_ES"] = ""
    if "Audio_EN" not in df.columns:
        df["Audio_EN"] = ""
    
    current_index = start_index
    for idx, row in df.iterrows():
        spanish_text = row.get("Spanish", "")
        english_text = row.get("English", "")
        
        if pd.isna(spanish_text) or spanish_text.strip() == "":
            continue
        
        # Gerar áudio para o Espanhol
        df.loc[idx, "Audio_ES"] = generate_audio(spanish_text, VOICE_ES, "ES", current_index)
        
        # Gerar áudio para o Inglês
        df.loc[idx, "Audio_EN"] = generate_audio(english_text, VOICE_EN, "EN", current_index)
        
        current_index += 1

    # 4. Salvar o novo CSV
    df.to_csv(OUTPUT_CSV, index=False)

    print("\n--- Processo Concluído ---")
    print(f"✅ Arquivo '{OUTPUT_CSV}' gerado com sucesso.")
    print("Agora você pode usar o script de importação para adicionar as notas ao Anki.")

if __name__ == "__main__":
    main()