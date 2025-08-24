import os
import requests
import pandas as pd
import json
import sys
import shutil
import re
import unicodedata
import subprocess

# === FUNÇÃO PARA INSTALAR DEPENDÊNCIAS ===
def install_dependencies():
    """Instala as dependências necessárias para o script."""
    required_libraries = ['requests', 'pandas']
    
    print("--- Verificando e instalando dependências ---")
    
    for lib in required_libraries:
        try:
            __import__(lib)
            print(f"✅ A biblioteca '{lib}' já está instalada.")
        except ImportError:
            print(f"⚠️ A biblioteca '{lib}' não foi encontrada. Tentando instalá-la...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                print(f"✅ '{lib}' instalada com sucesso.")
            except subprocess.CalledProcessError:
                print(f"❌ Erro ao instalar '{lib}'. Por favor, tente instalar manualmente com: 'pip install {lib}'")
                sys.exit(1)

# Chamar a função de instalação no início do script
install_dependencies()

# === CONFIGURAÇÕES GLOBAIS ===
ANKI_CONNECT_URL = "http://localhost:8765"
VOICE_IDS_FILE = "voice_ids.json"

# Sua chave da ElevenLabs (definida no terminal ou aqui)
# É altamente recomendável usar uma variável de ambiente por segurança.
API_KEY = os.getenv("ELEVEN_API_KEY") 
if not API_KEY:
    print("❌ Erro: A variável de ambiente ELEVEN_API_KEY não está definida.")
    print("Por favor, defina-a no seu terminal com 'export ELEVEN_API_KEY=sua_chave' (macOS/Linux) ou 'set ELEVEN_API_KEY=sua_chave' (Windows).")
    sys.exit(1)

MODEL = "eleven_multilingual_v2"
URL_TTS = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
URL_QUOTA = "https://api.elevenlabs.io/v1/user/subscription"


# === FUNÇÕES DE MANIPULAÇÃO DO BANCO DE DADOS DE VOZES ===
def load_or_create_voice_ids():
    """Carrega os IDs de voz de um arquivo JSON ou cria um com IDs padrão."""
    if os.path.exists(VOICE_IDS_FILE):
        with open(VOICE_IDS_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ Aviso: O arquivo '{VOICE_IDS_FILE}' está corrompido. Um novo será criado.")
                return {}
    
    print(f"✅ Arquivo '{VOICE_IDS_FILE}' não encontrado. Criando um novo com IDs de voz padrão.")
    default_ids = {
        "Danish": "ygiXC2Oa1BiHksD3WkJZ",
        "English": "UgBBYS2sOqTuMpoF3BR0",
        "Spanish": "kulszILr6ees0ArU8miO",
        "Portuguese": "33B4UnXyTNbgLmdEDh5P",
        "German": "IWm8DnJ4NGjFI7QAM5lM"
    }
    save_voice_ids(default_ids)
    return default_ids

def save_voice_ids(ids_dict):
    """Salva os IDs de voz em um arquivo JSON."""
    with open(VOICE_IDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ids_dict, f, indent=4)
    print(f"✅ IDs de voz salvos em '{VOICE_IDS_FILE}'.")

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

def calculate_characters_needed(df, audio_languages):
    """Calcula o total de caracteres a serem consumidos."""
    chars_needed = 0
    for lang in audio_languages:
        if lang in df.columns:
            if not df[lang].empty:
                chars_needed += df[lang].astype(str).str.len().sum()
    return chars_needed

# === FUNÇÕES DO ELEVENLABS ===
def generate_filename(text, lang_code):
    """Cria um nome de arquivo seguro a partir do texto e idioma."""
    text = str(text).strip().lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = text.replace(' ', '-').replace('--', '-')
    text = text.strip('-')
    return f"{text}_{lang_code}.mp3"

def generate_audio(text, voice_id, lang_code, output_dir):
    """Gera áudio usando a API do ElevenLabs."""
    text = str(text).strip()
    if not text:
        return ""
    
    filename = generate_filename(text, lang_code)
    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath):
        print(f"✅ Áudio para '{text}' ({lang_code}) já existe. Pulando...")
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
    
    while True:
        try:
            response = requests.post(URL_TTS.format(voice_id=voice_id), headers=headers, json=data)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"✅ Áudio salvo: {filepath}")
            return f"[sound:{filename}]"
        except requests.exceptions.HTTPError as e:
            print(f"❌ Erro HTTP {response.status_code}: {e}")
            print("⚠️ **Atenção:** Esta falha pode ser porque a voz não está em sua lista 'My Voices'.")
            
            retry_choice = input(f"▶️ Você já adicionou o ID '{voice_id}' da voz para o idioma '{lang_code}' na sua lista 'My Voices' (https://elevenlabs.io/app/voice-lab)? (S/n) ou digite o NOVO ID: ")
            
            if retry_choice.lower() == 's' or retry_choice.strip() == '':
                # Tenta novamente com o mesmo ID
                continue
            elif retry_choice.lower() == 'n':
                print("Por favor, adicione o ID da voz à sua lista 'My Voices' na ElevenLabs.")
                while True:
                    final_choice = input("▶️ Você já adicionou o ID no 'My Voices' do https://elevenlabs.io/app/voice-lab? (S/n/cancelar): ")
                    if final_choice.lower() == 's' or final_choice.strip() == '':
                        print("Ok, tentando novamente...")
                        break  # Sai do loop interno e tenta novamente a geração de áudio
                    elif final_choice.lower() == 'n':
                        print("Por favor, adicione o ID da voz para continuar.")
                    elif final_choice.lower() == 'cancelar' or final_choice.lower() == 'c':
                        print(f"❌ Pulando geração de áudio para '{lang_code}' nesta frase.")
                        return None
                    else:
                        print("Opção inválida.")
                continue # Volta para o loop externo para tentar a geração
            else:
                voice_id = retry_choice
                print(f"✅ Usando o novo ID de voz: '{voice_id}'")
                # O loop continua com o novo ID
                continue
        except Exception as e:
            print(f"❌ Erro ao gerar áudio: {e}")
            return None


def create_anki_model(model_name, fields, front_template, back_template):
    """Cria um novo modelo de nota no Anki se ele não existir."""
    existing_models = anki_connect_request('modelNames')
    if existing_models and model_name in existing_models:
        print(f"✅ Modelo de nota '{model_name}' já existe. Prosseguindo...")
        return True
    
    print(f"⚠️ Modelo de nota '{model_name}' não encontrado. Tentando criar...")
    result = anki_connect_request(
        "createModel",
        modelName=model_name,
        inOrderFields=fields,
        isCloze=False,
        cardTemplates=[
            {
                "Name": "Card 1",
                "Front": front_template,
                "Back": back_template
            }
        ]
    )
    if result is not None:
        print(f"✅ Modelo de nota '{model_name}' criado com sucesso.")
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

def anki_connect_request(action, **params):
    """Função genérica para fazer requisições à API do AnkiConnect."""
    payload = json.dumps({"action": action, "version": 6, "params": params})
    try:
        response = requests.post(ANKI_CONNECT_URL, data=payload)
        response.raise_for_status()
        result = response.json()
        if result.get("error"):
            error_message = result['error']
            if isinstance(error_message, list) and 'cannot create note because it is a duplicate' in str(error_message):
                print("❌ Erro: As notas não foram adicionadas porque já existem no Anki.")
                print("O Anki impede a criação de notas duplicadas. O processo de adição foi cancelado.")
            else:
                print(f"❌ Erro na requisição ao AnkiConnect: {error_message}")
            return None
        return result.get("result")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar com o AnkiConnect. Verifique se o Anki está aberto e o AnkiConnect está instalado. Erro: {e}")
        return None

def add_notes_to_deck(deck_name, df, audio_dir, model_name, fields):
    """Adiciona notas de um DataFrame a um baralho específico."""
    print(f"\n--- Adicionando notas ao baralho '{deck_name}' ---")
    
    anki_connect_request("createDeck", deck=deck_name)

    anki_media_folder = find_anki_media_folder()
    if not anki_media_folder:
        print("\nPara encontrar a pasta 'collection.media':")
        print("1. Abra o Anki.")
        print("2. Vá em 'Ferramentas' -> 'Add-ons' -> 'AnkiConnect'.")
        print("3. Clique em 'Ver Arquivos'. A pasta do Anki será aberta.")
        print("4. Dentro dela, localize a pasta do seu perfil (ex: 'Usuário 1') e, depois, 'collection.media'.")
        print("Exemplo de caminho: C:\\Users\\Cabrito\\AppData\\Roaming\\Anki2\\Usuário 1\\collection.media")
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

    notes = []
    
    for _, row in df.iterrows():
        note_fields = {}
        has_audio = False
        for field in fields:
            if field in row:
                value = str(row[field]).strip() if pd.notna(row[field]) else ""
                note_fields[field] = value
                if value.startswith("[sound:") and value.endswith("]"):
                    has_audio = True
            else:
                note_fields[field] = ""

        if has_audio:
            note = {
                "deckName": deck_name,
                "modelName": model_name,
                "fields": note_fields,
                "options": { "allowDuplicate": False },
                "tags": ["auto-generated", "vocab"]
            }
            notes.append(note)

    if notes:
        print(f"📦 Enviando {len(notes)} notas para o Anki...")
        result = anki_connect_request("addNotes", notes=notes)
        if result:
            print(f"✅ Notas adicionadas com sucesso.")
            return True
        else:
            return False
    else:
        print("❌ Nenhuma nota válida encontrada para adicionar ao Anki. Verifique se o seu CSV possui dados e se os áudios foram gerados.")
        return False

def main():
    """Função principal que orquestra o processo."""
    
    print("--- Gerador de Baralho Anki Dinâmico ---")
    
    if not anki_connect_request("version"):
        print("❌ Script cancelado.")
        return

    while True:
        input_file_path = input("▶️ Por favor, digite o CAMINHO COMPLETO do arquivo CSV com as frases: ")
        if os.path.isfile(input_file_path):
            break
        else:
            print(f"❌ Erro: O arquivo '{input_file_path}' não foi encontrado. Por favor, tente novamente.")

    try:
        df = pd.read_csv(input_file_path).dropna(how='all')
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo CSV: {e}")
        return

    text_columns = [col for col in df.columns if len(col) >= 2 and not col.startswith("Audio_")]
    
    saved_voice_ids = load_or_create_voice_ids()
    audio_languages = {}
    print("\n▶️ O script detectou os seguintes idiomas no seu CSV:")
    for lang in text_columns:
        print(f"- {lang}")
    
    print("\n--- Configuração de Vozes ---")
    
    for lang in text_columns:
        if lang in saved_voice_ids:
            choice = input(f"▶️ ID de voz para '{lang}' já salvo: '{saved_voice_ids[lang]}'. Quer usar este ID? (S/n): ")
            if choice.lower() == 's' or choice.strip() == '':
                audio_languages[lang] = saved_voice_ids[lang]
                print(f"✅ Usando ID salvo para '{lang}'.")
                print(f"⚠️ Lembre-se de que a voz precisa estar em sua lista 'My Voices' do https://elevenlabs.io/app/voice-lab para funcionar.")
            else:
                new_voice_id = input(f"▶️ Digite o NOVO ID da voz para '{lang}' (ou deixe em branco para sem áudio): ")
                if new_voice_id:
                    audio_languages[lang] = new_voice_id
                else:
                    print(f"❌ Áudio desabilitado para '{lang}'.")
        else:
            voice_id_input = input(f"▶️ Digite o ID da voz para '{lang}' (ou deixe em branco se não quiser áudio): ")
            if voice_id_input:
                audio_languages[lang] = voice_id_input

    updated_voice_ids = saved_voice_ids.copy()
    updated_voice_ids.update(audio_languages)
    save_voice_ids(updated_voice_ids)
    
    model_name = "Dynamic-" + "-".join(text_columns)
    # A linha abaixo foi alterada para forçar o campo de áudio a ser maiúsculo
    fields = text_columns + [f"Audio_{lang[:2].upper()}" for lang in audio_languages]

    front_template_parts = []
    back_template_parts = ["{{FrontSide}}<hr>"]
    for i, lang in enumerate(text_columns):
        template_html = f"""
<div style="font-family: Arial; font-size: 24px; text-align: center; color: #007acc;">
    {{{{{lang}}}}}
</div>
"""
        if lang in audio_languages:
            # Esta linha também foi alterada para corresponder ao novo campo
            audio_field = f"Audio_{lang[:2].upper()}"
            template_html += f"""
<br>
<div style="font-family: Arial; font-size: 18px; text-align: center;">
    {{{{{audio_field}}}}}
</div>
"""
        if i == 0:
            front_template_parts.append(template_html)
        else:
            back_template_parts.append(template_html)
    
    FRONT_TEMPLATE = "".join(front_template_parts)
    BACK_TEMPLATE = "".join(back_template_parts)
    
    input_dir = os.path.dirname(input_file_path)
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    output_audio_csv = os.path.join(input_dir, f"{base_name}_with_audio.csv")
    audio_dir = os.path.join(input_dir, "audios")
    os.makedirs(audio_dir, exist_ok=True)
    
    for lang in text_columns:
        if lang in audio_languages:
            audio_col_name = f"Audio_{lang[:2].upper()}"
            if audio_col_name not in df.columns:
                df[audio_col_name] = ""
    
    char_limit, char_used = get_user_quota()
    if char_limit is not None and char_used is not None:
        chars_needed = calculate_characters_needed(df, audio_languages.keys())
        print(f"\n--- Saldo de Caracteres ---")
        print(f"▶️ Consumo estimado para este processo: {chars_needed} caracteres.")
        print(f"▶️ Saldo disponível na sua conta: {char_limit - char_used} caracteres.")
        print(f"▶️ Limite da sua conta: {char_limit} caracteres. Usado: {char_used}")
        if chars_needed > (char_limit - char_used):
            print("\n❌ AVISO: O consumo estimado é maior que o seu saldo disponível.")
            print("O processo será cancelado para evitar cobranças indesejadas.")
            sys.exit(0)
    else:
        print("\n⚠️ AVISO: Não foi possível verificar o saldo de caracteres na ElevenLabs.")
        print("O processo continuará. Verifique sua chave da API e sua conexão.")

    for idx, row in df.iterrows():
        for lang, voice_id in list(audio_languages.items()):
            audio_col_name = f"Audio_{lang[:2].upper()}"
            text_to_generate = row[lang]

            if pd.isna(row[audio_col_name]) or not row[audio_col_name]:
                if pd.notna(text_to_generate) and text_to_generate:
                    audio_link = generate_audio(text_to_generate, voice_id, lang, audio_dir)
                    if audio_link:
                        df.at[idx, audio_col_name] = audio_link
    
    df.to_csv(output_audio_csv, index=False)
    print(f"✅ Arquivo '{output_audio_csv}' atualizado com sucesso!")

    print("\n--- Configuração do Baralho Anki ---")
    deck_name = ""
    success = False
    while True:
        choice = input("Você quer adicionar as notas a um baralho existente ou criar um novo?\n1. Criar um novo baralho\n2. Adicionar a um baralho existente\n3. Cancelar e Sair\n▶️ Digite 1, 2 ou 3: ")
        if choice == "1":
            deck_name = input("▶️ Digite o nome do NOVO baralho que você quer criar: ")
            create_anki_model(model_name, fields, FRONT_TEMPLATE, BACK_TEMPLATE)
            success = add_notes_to_deck(deck_name, df, audio_dir, model_name, fields)
            break
        elif choice == "2":
            existing_decks = anki_connect_request('deckNames')
            if existing_decks and isinstance(existing_decks, list):
                print("\nBaralhos existentes:")
                for i, deck in enumerate(existing_decks):
                    print(f"  {i+1}. {deck}")
                user_input = input("▶️ Digite o NOME ou NÚMERO do baralho EXISTENTE que você quer usar: ")
                try:
                    index_choice = int(user_input) - 1
                    if 0 <= index_choice < len(existing_decks):
                        deck_name = existing_decks[index_choice]
                        create_anki_model(model_name, fields, FRONT_TEMPLATE, BACK_TEMPLATE)
                        success = add_notes_to_deck(deck_name, df, audio_dir, model_name, fields)
                        break
                except ValueError:
                    if user_input in existing_decks:
                        deck_name = user_input
                        create_anki_model(model_name, fields, FRONT_TEMPLATE, BACK_TEMPLATE)
                        success = add_notes_to_deck(deck_name, df, audio_dir, model_name, fields)
                        break
                print(f"❌ Erro: O baralho '{user_input}' não foi encontrado. Por favor, tente novamente.")
            else:
                print("❌ Não foi possível obter a lista de baralhos existentes. Verifique a conexão com o AnkiConnect.")
                sys.exit(1)
        elif choice == "3":
            print("✅ Processo cancelado.")
            sys.exit(0)
        else:
            print("❌ Opção inválida. Por favor, digite 1, 2 ou 3.")
    
    if success:
        print("\n✅ Processo concluído com sucesso!")
    else:
        print("\n❌ O processo foi concluído, mas houve erros na adição de notas ao Anki.")

if __name__ == "__main__":
    main()