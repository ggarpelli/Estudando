import os
import requests
import pandas as pd
import json
import sys
import shutil

# === CONFIGURAÇÕES GLOBAIS ===
ANKI_CONNECT_URL = "http://localhost:8765"

# O nome do modelo (tipo de nota) que você já tem no Anki.
MODEL_NAME = "Spanish-English-Portuguese"
MODEL_FIELDS = ["Spanish", "English", "Portuguese", "Audio_ES", "Audio_EN"]

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

# === Funções de comunicação com o AnkiConnect ===
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
    if existing_models and MODEL_NAME in existing_models:
        print(f"✅ Modelo de nota '{MODEL_NAME}' já existe. Prosseguindo...")
        return True
    
    print(f"⚠️ Modelo de nota '{MODEL_NAME}' não encontrado. Tentando criar...")
    result = anki_connect_request(
        "createModel",
        modelName=MODEL_NAME,
        inOrderFields=MODEL_FIELDS,
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
        print(f"✅ Modelo de nota '{MODEL_NAME}' criado com sucesso.")
        return True
    return False

def add_notes_to_deck(deck_name, csv_path):
    """Adiciona notas de um CSV a um baralho específico."""
    
    # 1. Obter os caminhos das pastas de áudio
    audio_source_dir = input("▶️ Digite o CAMINHO COMPLETO da pasta local com os áudios que você quer importar: ")
    anki_media_folder = input("▶️ Agora, digite o CAMINHO COMPLETO da sua pasta de mídia do Anki (collection.media): ")

    if not os.path.exists(audio_source_dir):
        print(f"❌ Erro: O diretório de áudio de origem '{audio_source_dir}' não foi encontrado.")
        return
    if not os.path.exists(anki_media_folder):
        print(f"❌ Erro: O diretório de mídia do Anki '{anki_media_folder}' não foi encontrado.")
        return

    # 2. Copiar os arquivos de áudio
    print(f"\n📦 Copiando arquivos de áudio de '{audio_source_dir}' para '{anki_media_folder}'...")
    try:
        for filename in os.listdir(audio_source_dir):
            source_path = os.path.join(audio_source_dir, filename)
            dest_path = os.path.join(anki_media_folder, filename)
            if os.path.isfile(source_path):
                shutil.copy(source_path, dest_path)
        print("✅ Arquivos de áudio copiados com sucesso.")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível copiar os arquivos de áudio. Erro: {e}")

    # 3. Adicionar as notas ao baralho
    print(f"\nAdicionando notas ao baralho '{deck_name}'...")
    df = pd.read_csv(csv_path)
    notes_to_add = []
    
    for _, row in df.iterrows():
        spanish_text = str(row.get("Spanish", "")).strip()
        english_text = str(row.get("English", "")).strip()
        portuguese_text = str(row.get("Portuguese", "")).strip()
        audio_es_link = str(row.get("Audio_ES", "")).strip()
        audio_en_link = str(row.get("Audio_EN", "")).strip()

        if audio_es_link and spanish_text:
            note = {
                "deckName": deck_name,
                "modelName": MODEL_NAME,
                "fields": {
                    "Spanish": spanish_text,
                    "English": english_text,
                    "Portuguese": portuguese_text,
                    "Audio_ES": audio_es_link,
                    "Audio_EN": audio_en_link
                },
                "options": { "allowDuplicate": False },
                "tags": ["auto-generated", "spanish-vocab"]
            }
            notes_to_add.append(note)

    if notes_to_add:
        print(f"📦 Enviando {len(notes_to_add)} notas para o Anki...")
        result = anki_connect_request("addNotes", notes=notes_to_add)
        if result is not None:
            print("✅ Notas adicionadas com sucesso.")
        else:
            print("❌ Ocorreu um erro ao adicionar as notas.")
    else:
        print("❌ Nenhuma nota válida encontrada para adicionar ao Anki.")

def create_deck(deck_name):
    """Cria um baralho no Anki."""
    result = anki_connect_request('createDeck', deck=deck_name)
    if result is not None:
        print(f"✅ Baralho '{deck_name}' criado com sucesso.")
    else:
        print(f"❌ Não foi possível criar o baralho '{deck_name}' ou ele já existe.")

# === FUNÇÃO PRINCIPAL ===
def main():
    """Função principal que orquestra o processo."""
    
    print("--- Importador de Notas Anki (Áudios Existentes) ---")
    
    if not anki_connect_request("version"):
        print("❌ Script cancelado.")
        return
    
    if not create_note_type():
        print("❌ Não foi possível criar ou encontrar o modelo de nota. Verifique se ele existe no seu Anki ou se a conexão está funcionando. Script cancelado.")
        return
        
    while True:
        file_path = input("▶️ Digite o caminho completo do arquivo CSV para processar: ")
        if os.path.exists(file_path):
            break
        else:
            print(f"❌ Erro: O arquivo ou diretório '{file_path}' não foi encontrado. Por favor, tente novamente.")

    print(f"✅ Arquivo '{file_path}' carregado com sucesso.")

    deck_name = ""
    while True:
        choice = input("\nVocê quer adicionar as frases a um baralho existente ou criar um novo?\n1. Criar um novo baralho\n2. Adicionar a um baralho existente\n▶️ Digite 1 ou 2: ")
        if choice == "1":
            deck_name = input("▶️ Digite o nome do NOVO baralho que você quer criar: ")
            create_deck(deck_name)
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
                    # Tenta converter para um número e encontrar o baralho pelo índice
                    index_choice = int(user_input) - 1
                    if 0 <= index_choice < len(existing_decks):
                        deck_name = existing_decks[index_choice]
                        break
                except ValueError:
                    # Se não for um número, tenta encontrar pelo nome
                    if user_input in existing_decks:
                        deck_name = user_input
                        break
                
                print(f"❌ Erro: O baralho '{user_input}' não foi encontrado. Por favor, tente novamente.")
            else:
                print("❌ Não foi possível obter a lista de baralhos existentes. Verifique a conexão com o AnkiConnect.")
                sys.exit(1)
        else:
            print("❌ Opção inválida. Por favor, digite 1 ou 2.")
    
    add_notes_to_deck(deck_name, file_path)

if __name__ == "__main__":
    main()