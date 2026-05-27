# SLSProxy - WebProxy em Python

O **SLSProxy** é um servidor proxy web desenvolvido como projeto para a disciplina de Sistemas para Internet II da Universidade Federal do Rio Grande (FURG). Ele atua como um intermediário entre o cliente e o servidor, servindo para bloquear, filtrar conteúdo e mascarar o IP do cliente, dentre outras funcionalidades.

## Funcionalidades

- **Suporte a HTTPS (HTTP Connect):** O proxy atua como uma ponte entre cliente e servidor, abrindo a conexão e confirmando ao cliente com `HTTP/1.1 200 Connection Established`. Por conta do conteúdo criptografado, os dados são repassados sem modificação.

- **Filtragem de Conteúdo HTML:** O proxy aplica um filtro de palavras no conteúdo HTML retornado pelo servidor, substituindo termos conforme configurado. Funciona apenas para requisições HTTP (GET, POST, etc.) — conteúdo HTTPS não pode ser modificado sem MITM.

- **Bloqueio de Domínios (HOSTs):** O proxy verifica se o domínio ou algum subdomínio está presente no arquivo `blocked.json`. Caso presente, retorna uma página de erro **403** ao cliente e encerra a conexão.

## Arquitetura e Tecnologia

O SLSProxy foi desenvolvido utilizando Sockets TCP/IP na linguagem Python, o que permite manipular livremente os dados enviados e recebidos, conectar-se manualmente aos servidores e implementar o método CONNECT de forma direta — algo mais difícil com frameworks como Flask.

### Fluxos de Comunicação

**Arquitetura Cíclica (HTTP Convencional — GET, POST, PUT, DELETE, PATCH):** O proxy recebe a requisição do cliente, analisa os cabeçalhos, repassa ao servidor e aplica o filtro de palavras no HTML antes de retornar ao cliente. O header `Content-Length` é removido (para não cortar o conteúdo modificado) e `Connection` é alterado de `Keep-Alive` para `closed`.

**Passthrough Sequencial (HTTP Connect — HTTPS):** O proxy abre uma conexão com o servidor e passa a repassar os dados em ambas as direções sem modificá-los, atuando apenas como ponte.

## Estrutura do Repositório

```text
webproxy/
├── blocked.json       # Domínios bloqueados pelo proxy
├── words.json         # Palavras para filtragem/substituição no HTML
├── proxy.py           # Código fonte principal
├── environment.yml    # Configuração de ambiente para Conda
├── requirements.txt   # Dependências Python
├── log.wplog          # Log de acessos (ALLOWED, BLOCKED, FILTERED)
├── WebProxy.pdf       # Documentação e artigo do projeto
└── templates/
    └── blocked.html   # Página de erro exibida ao bloquear um site
```

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/TheoSoares/webproxy.git
cd webproxy
```

### 2. Gerenciar ambiente

#### 2.1 Conda

Para criar um ambiente conda com as dependências, utilize o `environment.yml`:

```bash
conda env create -f environment.yml
conda activate <nome-do-ambiente>
```

#### 2.2 Outros ambientes (venv, poetry, etc.)

O arquivo `requirements.txt` está disponível. Basta ativar seu ambiente e executar:

```bash
pip install -r requirements.txt
```

### 3. Executar o proxy

O proxy inicia na porta definida no arquivo `.env`. Para executá-lo:

```bash
python3 proxy.py
```

## Configuração

### `blocked.json` — Domínios bloqueados

Adicione, altere ou remova domínios da lista para controlar o bloqueio:

```json
{
    "bloqueados": [
        "dominio.com",
        "dominio2.com"
    ]
}
```

### `words.json` — Filtro de palavras

Insira como chave a palavra a ser substituída e como valor a palavra substituta:

```json
{
    "palavra antiga": "palavra nova",
    "segundapalavra": "novapalavra"
}
```

## Uso

O cliente deve configurar o proxy no sistema operacional ou no navegador apontando para `IP_LOCAL:PORTA`. Ambos os valores são definidos no arquivo `.env`.

### Ubuntu

![Proxy configurado no Ubuntu](https://i.imgur.com/2iEzx4B.png)

### Firefox

![Proxy configurado no Firefox](https://i.imgur.com/KBmkigh.png)

## Autores

| Nome | GitHub |
|------|--------|
| Théo Corvello Soares | [@TheoSoares](https://github.com/TheoSoares) |
| Othávio Christmann Correa | [@othaviocc](https://github.com/othaviocc) |

---

*Desenvolvido na Universidade Federal do Rio Grande – FURG | Sistemas para Internet II | Graduação em Engenharia de Computação*
