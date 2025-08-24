import pandas as pd
import requests
import json
import os

# === CONFIGURAÇÕES ===
# Verifique se o Anki está aberto e o AnkiConnect está instalado e rodando.
ANKI_CONNECT_URL = "http://localhost:8765"

# Nomes para o seu baralho, modelo e campos
DECK_NAME = "Spanish-English-Portuguese"
NOTE_TYPE_NAME = "Spanish-English-Portuguese"
FIELDS = ["Spanish", "English", "Portuguese", "Audio_ES", "Audio_EN"]

# Arquivo CSV de entrada
INPUT_CSV = "anki_vocab_ES_EN_PT_with_audio.csv"
AUDIO_DIR = "audios"

# Templates da carta (Front e Back) baseados na sua imagem
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

def anki_connect_request(action, **params):
    """Função genérica para fazer requisições à API do AnkiConnect."""
    payload = json.dumps({"action": action, "version": 6, "params": params})
    try:
        response = requests.post(ANKI_CONNECT_URL, data=payload)
        response.raise_for_status()
        result = response.json()
        if result.get("error"):
            raise Exception(result.get("error"))
        return result.get("result")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar com o AnkiConnect. Verifique se o Anki está aberto e o AnkiConnect está instalado. Erro: {e}")
        return None
    except Exception as e:
        print(f"Erro na requisição ao AnkiConnect: {e}")
        return None

def create_note_type():
    """Cria um novo modelo de nota no Anki."""
    anki_connect_request(
        "createModel",
        modelName=NOTE_TYPE_NAME,
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

def create_deck():
    """Cria um novo baralho no Anki."""
    anki_connect_request("createDeck", deck=DECK_NAME)

def add_notes_from_csv():
    """Lê o CSV e adiciona as notas ao baralho."""
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Erro: Arquivo CSV '{INPUT_CSV}' não encontrado.")
        return

    df = pd.read_csv(INPUT_CSV, encoding='utf-8')
    notes = []

    for index, row in df.iterrows():
        note = {
            "deckName": DECK_NAME,
            "modelName": NOTE_TYPE_NAME,
            "fields": {
                "Spanish": row["Spanish"],
                "English": row["English"],
                "Portuguese": row["Portuguese"],
                "Audio_ES": row["Audio_ES"],
                "Audio_EN": row["Audio_EN"]
            },
            "options": {
                "allowDuplicate": False  # Evita duplicatas com a mesma frase em espanhol
            },
            "tags": ["auto-generated", "spanish-vocab"]
        }
        notes.append(note)

    if notes:
        print(f"📦 Enviando {len(notes)} notas para o Anki...")
        result = anki_connect_request("addNotes", notes=notes)
        if result:
            print(f"✅ Notas adicionadas com sucesso.")
            # Para carregar os áudios no Anki, você deve movê-los para o media folder.
            # O AnkiConnect pode fazer isso automaticamente com a ação storeMediaFile
            # mas é mais simples fazer isso manualmente ou com um script de copia
            # O Anki espera que os arquivos estejam em AppData/Roaming/Anki2/User 1/collection.media
            # Para simplificar, o script assume que o seu diretório de áudios já está nesse local,
            # ou que você vai copiar/mover os arquivos manualmente para lá.

def find_anki_media_folder():
    """Tenta encontrar o diretório de mídia do Anki."""
    home_dir = os.path.expanduser("~")
    media_dir = None

    if os.name == 'nt':  # Windows
        anki_dir = os.path.join(os.getenv('APPDATA'), 'Anki2')
    else:  # macOS / Linux
        anki_dir = os.path.join(home_dir, '.local', 'share', 'Anki2')

    # Tenta encontrar o perfil do usuário
    if os.path.exists(anki_dir):
        for profile in os.listdir(anki_dir):
            profile_path = os.path.join(anki_dir, profile)
            if os.path.isdir(profile_path) and profile != "addons21":
                media_dir = os.path.join(profile_path, "collection.media")
                if os.path.exists(media_dir):
                    print(f"✅ Diretório de mídia do Anki encontrado: {media_dir}")
                    return media_dir

    print("⚠️ Não foi possível encontrar o diretório de mídia do Anki. Os áudios precisam ser movidos manualmente para a pasta 'collection.media' para funcionar.")
    return None

def main():
    """Função principal."""
    # Passo 1: Verifica a conexão com o AnkiConnect
    if not anki_connect_request("version"):
        print("❌ Script cancelado. Por favor, abra o Anki e verifique a instalação do AnkiConnect.")
        return

    # Passo 2: O AnkiConnect precisa que o modelo exista antes de adicionar as notas.
    # Esta parte é um pouco mais complexa porque não podemos 'listar' modelos facilmente
    # com uma ação simples, então vamos apenas tentar criar o modelo e lidar com o erro
    # caso ele já exista.
    print("Criando o modelo de nota...")
    create_note_type()
    
    # Passo 3: Criar o baralho
    print("Criando o baralho...")
    create_deck()

    # Passo 4: Adicionar as notas e carregar os áudios
    print("Adicionando notas e carregando áudios...")
    add_notes_from_csv()
    
    # Passo 5: Mover os arquivos de áudio para a pasta do Anki
    # Esta parte é um passo manual ou pode ser automatizada com a ação "storeMediaFile"
    # do AnkiConnect. O script assume que você fará isso ou que o seu script anterior já fez.
    # Para automação, o código abaixo seria uma opção, mas o AnkiConnect exige que os arquivos
    # sejam movidos de forma síncrona, o que pode ser lento para muitos arquivos. A abordagem
    # mais segura é copiar a pasta 'audios' inteira.
    
    anki_media_folder = find_anki_media_folder()
    if anki_media_folder and os.path.exists(AUDIO_DIR):
        print(f"✅ Copiando arquivos de áudio de '{AUDIO_DIR}' para '{anki_media_folder}'...")
        for filename in os.listdir(AUDIO_DIR):
            source_path = os.path.join(AUDIO_DIR, filename)
            if os.path.isfile(source_path):
                dest_path = os.path.join(anki_media_folder, filename)
                import shutil
                shutil.copy(source_path, dest_path)
        print("✅ Arquivos de áudio copiados. Você pode sincronizar seu Anki agora.")

if __name__ == "__main__":
    main()