# SLSProxy - WebProxy em Python

O SLSProxy é um servidor proxy web desenvolvido como projeto para a disciplina de Sistemas para Internet II da Universidade Federal do Rio Grande (FURG). Ele atua como um intermediário entre o cliente e o servidor, servindo para bloquear, filtrar conteúdo e até mesmo mascarar o IP do cliente dentre outras funcionalidades.

## Funcionalidades

**Suporte a HTTPS (HTTP Connect):** Possui suporte ao HTTP Connect, método utilizado pelo HTTPS. O proxy atua como uma ponte, ele abre uma conexão com o servidor, avisa o cliente que a conexão foi estabelecida (`HTTP/1.1 200 Connection Established`), e eles começam a trocar dados.

**Filtragem de Conteúdo HTML:** Possui implementação para filtragem de conteúdo HTML. O proxy recebe os dados enviados pelo servidor, aplica o filtro de palavras em arquivos HTML apenas e retorna os dados.

**Bloqueio de Domínios (HOSTs):** O proxy verifica se o domínio ou algum subdomínio está presente no arquivo `blocked.json`, arquivo este que gerencia todos os domínios bloqueados pelo proxy. Caso presente, o proxy retorna uma página de erro 403 para o cliente e encerra sua conexão.

## Arquitetura e Tecnologia

O SLSProxy foi desenvolvido utilizando Sockets na linguagem Python. 

### Fluxos de Comunicação

**Arquitetura Cíclica (HTTP Convencional):** Para o restante dos métodos (GET, POST, PUT, DELETE, PATCH), o proxy recebe os dados do cliente e repassa ao servidor. O proxy modifica o header para remover a chave `Content-Length` e altera a chave `Connection` de `Keep-Alive` para `closed` quando possível, para que o cliente não fique carregando infinitamente a página esperando o final da requisição.

**Passthrough Sequencial (HTTP Connect):** O proxy recebe os dados enviados pelo cliente e repassa ao servidor ao mesmo tempo que recebe os dados do servidor e repassa para o cliente. Por conta do conteúdo criptografado, não é possível modificar os dados antes de repassar.

## Estrutura do Repositório

```text
webproxy/
├── blocked.json       # Arquivo que gerencia todos os domínios bloqueados pelo proxy 
├── environment.yml    # Arquivo de configuração de ambiente e dependências para o Conda
├── log.wplog          # Arquivo de log com o registro dos acessos (ALLOWED, BLOCKED, FILTERED)
├── proxy.py           # Código fonte principal com a implementação da classe Proxy e sockets
├── requirements.txt   # Arquivo com as dependências do Python necessárias para a execução
├── words.json         # Dicionário JSON configurado com as palavras para filtragem/substituição no HTML
├── WebProxy.pdf       # Documentação oficial, fluxos de arquitetura e artigo do projeto
└── templates/
    └── blocked.html   # Template da página HTML de erro exibida quando um site é bloqueado
```

## Instalação e Execução

Siga os passos abaixo para configurar e executar o **SLSProxy** no seu ambiente local:

### 1. Clonar o Repositório

```bash
git clone https://github.com/TheoSoares/webproxy
cd webproxy
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

O programa inicia em uma porta definida no .env. Para iniciar o proxy, execute:

```bash
python3 proxy.py
```

## Autores

Theo Corvello Soares
Othavio Christmann Correa