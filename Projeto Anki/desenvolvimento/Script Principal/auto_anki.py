import os
import requests
import pandas as pd
import json
import sys
import shutil
import re
import unicodedata

# === CONFIGURAÇÕES GLOBAIS ===
ANKI_CONNECT_URL = "http://localhost:8765"

# Sua chave da ElevenLabs (definida no terminal ou aqui)
API_KEY = os.getenv("ELEVEN_API_KEY") 
if not API_KEY:
    print("❌ Erro: A variável de ambiente ELEVEN_API_KEY não está definida.")
    print("Por favor, defina-a no seu terminal com 'export ELEVEN_API_KEY=sua_chave' (macOS/Linux) ou 'set ELEVEN_API_KEY=sua_chave' (Windows).")
    sys.exit(1)

# IDs das vozes que você escolheu
VOICE_ES = "kulszILr6ees0ArU8miO"
VOICE_EN = "UgBBYS2sOqTuMpoF3BR0"
MODEL = "eleven_multilingual_v2"
URL_TTS = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
URL_QUOTA = "https://api.elevenlabs.io/v1/user/subscription"

# Nomes dos campos
FIELDS = ["Spanish", "English", "Portuguese", "Audio_ES", "Audio_EN"]

# Templates da carta (Front e Back)
FRONT_TEMPLATE = """
<div style="font-family: Arial; font-size: 24px; text-align: center; color: #007acc;">
    {{Spanish}}
</div>
<br>
<div style="font-family: Arial; font-size: 18px; text-align: center;">
    {{Audio_ES}}
</div>
"""

BACK_TEMPLATE = """
{{FrontSide}}
<hr>
<div style="font-family: Arial; font-size: 20px; text-align: center;">
    <b>{{English}}</b>
</div>
<div style="font-family: Arial; font-size: 18px; text-align: center;">
    {{Audio_EN}}
</div>
<br>
<div style="font-family: Arial; font-size: 20px; text-align: center;">
    <b>{{Portuguese}}</b>
</div>
"""

# === FUNÇÕES DE VERIFICAÇÃO DE TOKENS ===
def get_user_quota():
    """Obtém o saldo de caracteres do usuário na ElevenLabs."""
    headers = {"xi-api-key": API_KEY}
    try:
        response = requests.get(URL_QUOTA, headers=headers)
        response.raise_for_status()
        data = response.json()
        character_limit = data.get("character_limit")
        character_used = data.get("character_used")
        return character_limit, character_used
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao obter dados de uso da API. Verifique sua chave. Erro: {e}")
        return None, None

def calculate_characters_needed(input_csv_path):
    """Calcula o total de caracteres a serem consumidos."""
    if not os.path.isfile(input_csv_path):
        return None
    try:
        df = pd.read_csv(input_csv_path).dropna(subset=['Spanish', 'English'], how='any')
        chars_spanish = df["Spanish"].astype(str).str.len().sum()
        chars_english = df["English"].astype(str).str.len().sum()
        return chars_spanish + chars_english
    except Exception as e:
        print(f"❌ Erro ao calcular caracteres do arquivo: {e}")
        return None

# === FUNÇÕES DO ELEVENLABS ===
def generate_filename(text, lang_code):
    """Cria um nome de arquivo seguro a partir do texto e idioma."""
    # Normaliza a string para remover acentos
    text = str(text).strip().lower()
    text = ''.join(c for c in text if c.isalnum() or c.isspace())
    text = text.replace(' ', '-')
    text = text.replace('"', '').replace("'", "")
    text = re.sub(r'[^a-z0-9-]', '', text)
    # Limita o tamanho do nome do arquivo para evitar problemas
    text = text[:50]
    return f"{text}_{lang_code}.mp3"

def generate_audio(text, voice_id, lang_code, output_dir):
    """Gera áudio usando a API do ElevenLabs."""
    text = str(text).strip()
    if not text:
        return ""
    
    filename = generate_filename(text, lang_code)
    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath):
        print(f"✅ Áudio para '{text}' já existe: {filename}")
        return f"[sound:{filename}]"

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
    try:
        response = requests.post(URL_TTS.format(voice_id=voice_id), headers=headers, json=data)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"✅ Áudio salvo: {filepath}")
        return f"[sound:{filename}]"
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erro HTTP {response.status_code}: {e}")
        return ""
    except Exception as e:
        print(f"❌ Erro ao gerar áudio: {e}")
        return ""

def process_csv_and_generate_audios(input_csv_path):
    """Lê o CSV, gera os áudios e salva em um novo CSV."""
    if not os.path.isfile(input_csv_path):
        print(f"❌ Erro: Arquivo '{input_csv_path}' não encontrado.")
        return None, None

    input_dir = os.path.dirname(input_csv_path)
    base_name = os.path.splitext(os.path.basename(input_csv_path))[0]
    output_audio_csv = os.path.join(input_dir, f"{base_name}_with_audio.csv")
    audio_dir = os.path.join(input_dir, "audios")

    os.makedirs(audio_dir, exist_ok=True)
    
    try:
        df = pd.read_csv(input_csv_path).dropna(subset=['Spanish', 'English'], how='any')
        
        print(f"⏳ Processando {len(df)} frases...")
        
        if "Audio_ES" not in df.columns:
            df["Audio_ES"] = ""
        if "Audio_EN" not in df.columns:
            df["Audio_EN"] = ""
        
        for idx, row in df.iterrows():
            if pd.isna(row["Audio_ES"]) or not row["Audio_ES"]:
                es_audio = generate_audio(row["Spanish"], VOICE_ES, "ES", audio_dir)
                df.at[idx, "Audio_ES"] = es_audio
            else:
                print(f"✅ Áudio espanhol para '{row['Spanish']}' já existe no CSV. Pulando...")
            
            if pd.isna(row["Audio_EN"]) or not row["Audio_EN"]:
                en_audio = generate_audio(row["English"], VOICE_EN, "EN", audio_dir)
                df.at[idx, "Audio_EN"] = en_audio
            else:
                print(f"✅ Áudio inglês para '{row['English']}' já existe no CSV. Pulando...")

        df.to_csv(output_audio_csv, index=False)
        print(f"✅ Arquivo '{output_audio_csv}' atualizado com sucesso!")
        return output_audio_csv, audio_dir
        
    except FileNotFoundError as e:
        print(f"❌ Erro: Arquivo '{e.filename}' não encontrado.")
        return None, None
    except Exception as e:
        print(f"❌ Ocorreu um erro: {e}")
        return None, None

# === FUNÇÕES DO ANKICONNECT ===
def anki_connect_request(action, **params):
    """Função genérica para fazer requisições à API do AnkiConnect."""
    payload = json.dumps({"action": action, "version": 6, "params": params})
    try:
        response = requests.post(ANKI_CONNECT_URL, data=payload)
        response.raise_for_status()
        result = response.json()
        if result.get("error"):
            if "Model name already exists" not in str(result.get("error")):
                print(f"❌ Erro na requisição ao AnkiConnect: {result['error']}")
                return None
        return result.get("result")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar com o AnkiConnect. Verifique se o Anki está aberto e o AnkiConnect está instalado. Erro: {e}")
        return None

def create_note_type():
    """Cria um novo modelo de nota no Anki se ele não existir."""
    existing_models = anki_connect_request('modelNames')
    if existing_models and "Spanish-English-Portuguese" in existing_models:
        print(f"✅ Modelo de nota 'Spanish-English-Portuguese' já existe. Prosseguindo...")
        return True
    
    print(f"⚠️ Modelo de nota 'Spanish-English-Portuguese' não encontrado. Tentando criar...")
    result = anki_connect_request(
        "createModel",
        modelName="Spanish-English-Portuguese",
        inOrderFields=FIELDS,
        isCloze=False,
        cardTemplates=[
            {
                "Name": "Card 1",
                "Front": FRONT_TEMPLATE,
                "Back": BACK_TEMPLATE
            }
        ]
    )
    if result is not None:
        print(f"✅ Modelo de nota 'Spanish-English-Portuguese' criado com sucesso.")
        return True
    return False

def find_anki_media_folder():
    """Tenta encontrar o diretório de mídia do Anki automaticamente."""
    home_dir = os.path.expanduser("~")
    
    if os.name == 'nt':  # Windows
        anki_dir = os.path.join(os.getenv('APPDATA'), 'Anki2')
    else:  # macOS / Linux
        anki_dir = os.path.join(home_dir, '.local', 'share', 'Anki2')
        
    if os.path.exists(anki_dir):
        for profile in os.listdir(anki_dir):
            profile_path = os.path.join(anki_dir, profile)
            media_path = os.path.join(profile_path, "collection.media")
            if os.path.exists(media_path) and os.path.isdir(media_path):
                print(f"✅ Diretório de mídia do Anki encontrado: {media_path}")
                return media_path
                
    print("⚠️ Não foi possível encontrar o diretório de mídia do Anki automaticamente.")
    return None

def add_notes_to_deck(deck_name, csv_path, audio_dir):
    """Adiciona notas de um CSV a um baralho específico."""
    print(f"\n--- Adicionando notas ao baralho '{deck_name}' ---")
    
    anki_connect_request("createDeck", deck=deck_name)

    anki_media_folder = find_anki_media_folder()
    if not anki_media_folder:
        anki_media_folder = input("▶️ Por favor, digite o CAMINHO COMPLETO da sua pasta de mídia do Anki ('collection.media'): ")
        while not os.path.isdir(anki_media_folder):
            print("❌ Caminho inválido. A pasta de mídia não foi encontrada.")
            anki_media_folder = input("▶️ Por favor, digite o CAMINHO COMPLETO da sua pasta de mídia do Anki ('collection.media'): ")
    
    if os.path.exists(audio_dir):
        print(f"✅ Copiando arquivos de áudio de '{audio_dir}' para '{anki_media_folder}'...")
        try:
            for filename in os.listdir(audio_dir):
                source_path = os.path.join(audio_dir, filename)
                dest_path = os.path.join(anki_media_folder, filename)
                shutil.copy(source_path, dest_path)
            print("✅ Arquivos de áudio copiados com sucesso.")
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível copiar os arquivos de áudio. Por favor, copie a pasta '{audio_dir}' manualmente para '{anki_media_folder}'. Erro: {e}")
    else:
        print("⚠️ Aviso: A pasta de áudios gerada não existe. Verifique se a geração foi bem-sucedida.")

    df = pd.read_csv(csv_path)
    notes = []
    
    for _, row in df.iterrows():
        spanish_text = str(row.get("Spanish", "")).strip() if not pd.isna(row.get("Spanish", "")) else ""
        english_text = str(row.get("English", "")).strip() if not pd.isna(row.get("English", "")) else ""
        portuguese_text = str(row.get("Portuguese", "")).strip() if not pd.isna(row.get("Portuguese", "")) else ""
        
        if row.get("Audio_ES") and not pd.isna(row.get("Audio_ES")):
            note = {
                "deckName": deck_name,
                "modelName": "Spanish-English-Portuguese",
                "fields": {
                    "Spanish": spanish_text,
                    "English": english_text,
                    "Portuguese": portuguese_text,
                    "Audio_ES": row["Audio_ES"],
                    "Audio_EN": row["Audio_EN"]
                },
                "options": { "allowDuplicate": False },
                "tags": ["auto-generated", "spanish-vocab"]
            }
            notes.append(note)

    if notes:
        print(f"📦 Enviando {len(notes)} notas para o Anki...")
        result = anki_connect_request("addNotes", notes=notes)
        if result:
            print(f"✅ Notas adicionadas com sucesso.")
    else:
        print("❌ Nenhuma nota válida encontrada para adicionar ao Anki. Verifique se o seu CSV possui dados e se os áudios foram gerados.")

# === FUNÇÃO PRINCIPAL ===
def main():
    """Função principal que orquestra o processo."""
    
    print("--- Gerador de Baralho Anki Automático ---")
    
    if not anki_connect_request("version"):
        print("❌ Script cancelado.")
        return
        
    while True:
        input_file_path = input("▶️ Por favor, digite o CAMINHO COMPLETO do arquivo CSV com as frases: ")
        if os.path.isfile(input_file_path):
            break
        else:
            print(f"❌ Erro: O arquivo '{input_file_path}' não foi encontrado. Por favor, tente novamente.")

    # Verificação de tokens antes de processar
    char_limit, char_used = get_user_quota()
    chars_needed = calculate_characters_needed(input_file_path)

    if char_limit is None or chars_needed is None:
        print("❌ Não foi possível verificar o consumo de caracteres. Prosseguindo...")
        proceed = input("▶️ Deseja continuar com a geração? (S/n): ")
        if proceed.lower() != 's' and proceed.lower() != '':
            print("Processo cancelado pelo usuário.")
            sys.exit(0)
    else:
        chars_available = char_limit - char_used
        print("\n--- RESUMO DE CARACTERES DO ELEVENLABS ---")
        print(f"✅ Saldo de caracteres disponível: {chars_available:,.0f} caracteres")
        print(f"✍️ Total de caracteres a serem consumidos: {chars_needed:,.0f} caracteres")

        if chars_needed > chars_available:
            print("\n⚠️ AVISO: O consumo estimado é maior que o seu saldo disponível.")
            print("O processo será cancelado para evitar cobranças indesejadas.")
            sys.exit(0)
        
        print("\n✅ Seu saldo é suficiente para gerar todos os áudios.")
        proceed = input("▶️ Deseja continuar com a geração? (S/n): ")
        if proceed.lower() != 's' and proceed.lower() != '':
            print("Processo cancelado pelo usuário.")
            sys.exit(0)

    output_audio_csv, audio_dir = process_csv_and_generate_audios(input_file_path)
    if not output_audio_csv:
        print("❌ Processo encerrado devido a erros na geração dos áudios.")
        return
        
    print("\n--- Configuração do Baralho Anki ---")
    
    deck_name = ""
    while True:
        choice = input("Você quer adicionar as frases a um baralho existente ou criar um novo?\n1. Criar um novo baralho\n2. Adicionar a um baralho existente\n▶️ Digite 1 ou 2: ")
        if choice == "1":
            deck_name = input("▶️ Digite o nome do NOVO baralho que você quer criar: ")
            create_note_type()
            break
        elif choice == "2":
            existing_decks_response = anki_connect_request('deckNames')
            if existing_decks_response and isinstance(existing_decks_response, list):
                existing_decks = existing_decks_response
                print("\nBaralhos existentes:")
                for i, deck in enumerate(existing_decks):
                    print(f"  {i+1}. {deck}")
                
                user_input = input("▶️ Digite o NOME ou NÚMERO do baralho EXISTENTE que você quer usar: ")
                
                try:
                    index_choice = int(user_input) - 1
                    if 0 <= index_choice < len(existing_decks):
                        deck_name = existing_decks[index_choice]
                        break
                except ValueError:
                    if user_input in existing_decks:
                        deck_name = user_input
                        break
                
                print(f"❌ Erro: O baralho '{user_input}' não foi encontrado. Por favor, tente novamente.")
            else:
                print("❌ Não foi possível obter a lista de baralhos existentes. Verifique a conexão com o AnkiConnect.")
                sys.exit(1)
        else:
            print("❌ Opção inválida. Por favor, digite 1 ou 2.")
    
    add_notes_to_deck(deck_name, output_audio_csv, audio_dir)

if __name__ == "__main__":
    main()