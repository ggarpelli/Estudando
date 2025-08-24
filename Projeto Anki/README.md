# 🚀 Gerador Dinâmico de Baralhos para Anki

### ✨ Visão Geral

Este script em Python automatiza a criação de baralhos do Anki. Ele lê frases de um arquivo CSV, converte-as em áudio de alta qualidade usando a API da **ElevenLabs** e importa automaticamente as notas para o seu aplicativo Anki. É a ferramenta perfeita para quem estuda idiomas e quer agilizar a criação de flashcards com áudio.

---

### 🌟 Funcionalidades

* Geração de áudio para múltiplos idiomas a partir de um único arquivo CSV.
* Criação automática de baralhos e notas no Anki via AnkiConnect.
* Reutilização de IDs de voz para evitar configurações repetitivas.
* Mensagens de erro detalhadas para ajudar na solução de problemas.

---

### 🛠️ Pré-requisitos

Para usar o script, você precisa ter o seguinte instalado e configurado:

-   **Python 3.6 ou superior.**
-   **Anki Desktop** (versão mais recente).
-   **Add-on AnkiConnect:** Instale este add-on no Anki usando o código `2054694901`.
-   **Chave da API ElevenLabs:** Obtenha sua chave na [página de perfil da ElevenLabs](https://elevenlabs.io/app/profile).

---

### ⚙️ Instruções de Uso

#### 1. Configuração Inicial

1.  **Instale as dependências:** Abra o terminal na pasta do projeto e execute o comando:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure a chave da API:** O script lê sua chave de uma variável de ambiente por segurança.
    -   **Windows:** `set ELEVEN_API_KEY=sua_chave_aqui`
    -   **macOS / Linux:** `export ELEVEN_API_KEY=sua_chave_aqui`

#### 2. Preparação do Arquivo CSV

Crie um arquivo CSV para suas frases. **A primeira linha deve conter os nomes exatos dos idiomas**.

**💡 Dica:** Você pode usar uma ferramenta de IA para gerar o conteúdo no formato correto. Basta copiar e colar este prompt:

Crie uma tabela em formato CSV. A estrutura do arquivo deve ter EXATAMENTE as colunas: Spanish, English, Portuguese. Gere X entradas. O conteúdo deve ser uma mistura de frases e palavras comuns. As entradas devem ser traduzidas nas três colunas. O resultado deve ser APENAS o texto do CSV, sem qualquer outra informação ou bloco de código.

Após a geração, copie o texto puro e salve-o como `seu_arquivo.csv`.

#### 3. Execução do Script

1.  Certifique-se de que o **Anki esteja aberto**.
2.  Abra o terminal na pasta do projeto e execute o script:
    ```bash
    py anki_dynamic_generator.py
    ```
3.  Siga as instruções na tela:
    -   Digite o caminho completo para o seu arquivo CSV.
    -   Confirme ou insira os IDs de voz para cada idioma.
    -   Escolha se deseja criar um novo baralho ou adicionar as notas a um baralho existente.

---

### ⚠️ Solução de Problemas Comuns

-   **`❌ Erro HTTP 400`:** Este erro geralmente significa que o ID da voz não foi adicionado à sua lista **"My Voices"** na ElevenLabs. Verifique e adicione o ID correto.
-   **`❌ Caminho inválido`:** Se o script não encontrar a pasta `collection.media` do Anki, ele pedirá o caminho. Para encontrá-lo, vá em **Anki > Ferramentas > Add-ons > AnkiConnect > Ver Arquivos**.