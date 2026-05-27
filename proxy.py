import socket
import threading
from dotenv import load_dotenv
import os
import re
import json
from datetime import datetime

load_dotenv()

# -- GET IP
def ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip_local = s.getsockname()[0]
    except Exception:
        ip_local = '127.0.0.1'  # Retorna localhost caso esteja sem rede
    finally:
        s.close()
    return ip_local

# -- LOG PRINT
def log(info: str) -> None:
    print(f'[{datetime.now().strftime("%d/%M/%Y %H:%M:%S")}] {info}')
    return None

class Proxy:
    def __init__(self) -> None:
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", 8080))

        with open(os.getenv("BLOCKED", "blocked.json"), "r") as blocked:
            self.BLOCKED_SITES: dict[str, list[str]] = json.load(blocked)["bloqueados"]

        with open(os.getenv("WORDS", "words.json"), "r") as words:
            self.WORDS_FILTER: dict[str, str] = json.load(words)

        self._logfile_lock = threading.Lock()

        with self._logfile_lock:
            with open(os.getenv("LOGFILE", "log.wplog"), "a") as log:
                if log.tell() == 0: # Caso não contenha nada ou não exista
                    log.write('TIME HOST ACCESS METHOD IP')

    def _add_log(self, site: str, access: str, method: str, ip: str) -> None:
        with self._logfile_lock:
            with open(os.getenv("LOGFILE", "log.wplog"), "a") as log:
                log.write(f'\n[{datetime.now().strftime("%d-%M-%Y %H:%M:%S")}] {site} {access} {method} {ip}')

    @staticmethod
    def _bridge(sender: socket.socket, receiver: socket.socket) -> None:
        try:
            while True:
                data = sender.recv(4096)
                receiver.sendall(data)
                if not data:
                    break
        except BrokenPipeError:
            return None

        return None

    def connect(self, host: str, port: int, raw_request: bytes, client_conn: socket.socket, **kwargs) -> None:
        """Handle method CONNECT"""
        protocol = kwargs['protocol']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.connect((host, port))
            client_conn.sendall(f'{protocol} 200 Connection Established\r\n\r\n'.encode())
            log(f'Connected! Client <-> {host}')

            client_thread = threading.Thread(target=self._bridge, args=(client_conn, server), daemon=True)
            server_thread = threading.Thread(target=self._bridge, args=(server, client_conn), daemon=True)

            client_thread.start()
            server_thread.start()

            client_thread.join()
            server_thread.join()

        return None
    
    def _manipulate_html(self, first_slice: bytes, second_slice: bytes, client: socket.socket, infos: list[bool], final: bool=False) -> bytes:
        """Receive 2 parts of an HTML. Filters both together and slice in half again, to fix broken words at final
        If first part ends with 'motherfu' and second part starts with 'cker', it will be filtered, sent the first part filtered and return the second one"""

        content = first_slice + second_slice

        if not content: # Caso tenha enviado tudo e receba um 'falso' positivo de arquivo faltando
            return b''

        if not infos[0]: # Caso ainda não tenha enviado o Header
            try:
                header, body = content.split(b"\r\n\r\n", 1) # Separa header e body
                header = re.sub(rb'Content-Length: \d+\r\n', b'', header, flags=re.IGNORECASE) # Remove Content-Length do header, para evitar erros
                header = re.sub(rb'Keep-Alive', b'close', header, flags=re.IGNORECASE) # Remove Keep-Alive do header, para fechar servidor após enviar todos dados

                if re.search(rb'Content-Type:.*text/html', header, re.IGNORECASE):
                    infos[1] = True

                content = header + b'\r\n\r\n' + body # Após arrumar Header, junta com body e segue procedimento padrão
            except ValueError: # Caso header não tenha sido enviado e não esteja completo
                return content

        if not infos[1]: # Caso não seja um HTML envia normalmente
            client.sendall(content)
            return b''

        cut_index = content.rfind(b">") # Encontra última tag fechada

        if cut_index == -1: # Falhou em encontrar um fechamento de TAG. Retorna HTML completo como first slice e remanipula após recebimento de second slice
            return content
        
        first_slice = content[:cut_index + 1] # Aplica o corte correto de TAGS
        second_slice = content[cut_index + 1:]
            
        # Manipulate HTML
        for old, new in self.WORDS_FILTER.items(): # Replace de palavras
            first_slice, count = re.subn(old.encode(), new.encode(), first_slice, flags=re.IGNORECASE)
            if count > 0:
                infos[2] = True

        client.sendall(first_slice) # Send first part
        infos[0] = True
        return second_slice # Return second part as first part now

    def response(self, host: str, port: int, raw_request: bytes, client_conn: socket.socket, **kwargs) -> None:
        """Handle methods GET | POST | PUT | DELETE | PATCH"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            log(f'Connected in {host}:{port}\nRaw Request: {raw_request.decode()}')
            server.connect((host, port))
            server.sendall(raw_request)

            first_data = b''
            infos = [False, False, False] # Header Sended | Is TEXT/HTML | Was Filtered
            while True:
                second_data = server.recv(4096)
                if not second_data:
                    self._manipulate_html(first_data, b'', client_conn, infos, True)
                    break
                first_data = self._manipulate_html(first_data, second_data, client_conn, infos) 

            self._add_log(f'{host}{":" + str(port) if port != 443 or port != 80 else ""}{kwargs['page']}', 'FILTERED' if infos[2] else 'ALLOWED', kwargs['method'], str(kwargs['addr'][0]))
            return None
        
    @staticmethod
    def _manage_request_line(data: bytes) -> tuple[bytes, str, str, int, str, str]:
        """Manage Request Line to return Modified and important infos as such as host and port"""
        data = data.split(b'\r\n', 1)
        method, url, protocol = data[0].decode().split(" ") # Coleta Método, URL e Protocolo usado no Request Line

        if '://' in url:
            url = url.split("://")[1] # Remove o protocolo indicado na URL

        url = url.split(":") # Separa porta do HOST

        if len(url) == 1: # Se a porta não é especificada
            try:
                hostname, page = url[0].split("/", 1)
                page = "/" + page
            except ValueError: # Se não há / no link
                hostname = url[0]
                page = "/"
            port = 80 # 80 pois HTTP não é obrigado a declarar porta, diferentemente do método HTTPS

        else: # A porta é especificada
            hostname = url[0] # Hostname será o primeiro índice
            try:
                port, page = url[1].split("/", 1) # Separa porta da página
                page = "/" + page
            except ValueError: # Caso não haja página, default=/
                port = url[1]
                page = "/"

        port = int(port)

        new_request_line = f'{method} {page} {protocol}'.encode() # Cria nova Request Line com URL modificada

        data[0] = new_request_line
        data = b'\r\n'.join(data) # Modifica Requisição do Cliente

        return (data, method, hostname, port, page, protocol)
    
    def _verify_block(self, hostname: str, conn: socket.socket, url: str, ip: str) -> bool:
        """If site in blocked.json sends Blocked Page to client and returns True"""
        t_hostname = hostname.split(".")
        for i in range(len(t_hostname)):
            if '.'.join(t_hostname[i:]) in self.BLOCKED_SITES:
                with open("templates/blocked.html", "r") as f:
                    html = f.read().encode() # Se estiver bloqueado irá ler o HTML e enviar

                    # Trocar variáveis do HTML
                    html = re.sub(b'{{ url }}', hostname.encode(), html)
                    html = re.sub(b'{{ ip }}', ip.encode(), html)
                    html = re.sub(b'{{ timestamp }}', datetime.now().strftime("%d/%m/%Y, %H:%M:%S").encode(), html)
                    
                    resp = b'HTTP/1.1 403 Forbidden\r\nContent-Type: text/html; charset=utf-8\r\nConnection: close\r\n\r\n'
                    conn.sendall(resp + html)
                    return True
        return False

    def handle_connection(self, conn: socket.socket, addr: socket._RetAddress) -> None:
        with conn:
            try:
                while True:
                    data: list[bytes] = conn.recv(2048)
                    if not data:
                        return None

                    data, method, hostname, port, page, protocol = self._manage_request_line(data)

                    if self._verify_block(hostname, conn, f'{hostname}{":" + str(port) if port != 443 or port != 80 else ""}{page}', str(addr[0])):
                        self._add_log(f'{hostname}{":" + str(port) if port != 443 or port != 80 else ""}{page}', 'BLOCKED', method, str(addr[0]))
                        return None

                    # Caso não haja bloqueios
                    method_f = getattr(self, method.lower(), self.response) # Reconhece método pedido
                    method_f(host=hostname, port=port, raw_request=data, client_conn=conn, protocol=protocol, method=method, page=page, addr=addr) # Chamada do método CONNECT, GET, POST etc...

                    if method != 'CONNECT':
                        return None

            except Exception as e:
                log(f'Erro {e}')
                return None

if __name__ == '__main__':
    try:
        proxy = Proxy()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((proxy.HOST, proxy.PORT))
            s.listen()

            log(f'Proxy incializado em {ip()}:{proxy.PORT}\n')
            while True:
                conn, addr = s.accept()
                t = threading.Thread(target=proxy.handle_connection, args=(conn, addr), daemon=True)
                t.start()

    except KeyboardInterrupt:
        log("O proxy foi desligado com sucesso. Remova ou desligue-o dos navegadores.")
        exit(0)

    except Exception as e:
        log(f'Erro: {e}')
        exit(1)
