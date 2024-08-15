import socket
import threading
import time

def send_data(connection, data):
    connection.send(data)

def receive_data(connection):
    return connection.recv(1024).decode()

def client_handler(server_address, namefile, duration, target_load, cpu_core, client_id):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(server_address)

        # Enviar nome do arquivo
        send_data(client, namefile.encode())

        # Receber confirmação de recebimento do nome do arquivo
        confirmation = receive_data(client)
        print(f'CLIENTE {client_id} - Recebido: {confirmation}')

        # Enviar duração, carga e núcleo de CPU
        send_data(client, f"{duration}|{target_load}|{cpu_core}".encode())

        confirmation = receive_data(client)
        print(f'CLIENTE {client_id} - Recebido: {confirmation}')

        if confirmation == "Ready":
            with open(namefile, 'rb') as file:
                start_time = time.time()  # Início da contagem do tempo de transferência
                while True:
                    data = file.read(1024)
                    if not data:
                        break
                    client.sendall(data)
                    time.sleep(0.033)  # Atraso de 33 ms entre envios de pacotes

            end_time = time.time()  # Fim da contagem do tempo de transferência
            transfer_time = (end_time - start_time) * 1000  # Tempo em milissegundos

            # Exibir resultados
            print(f'\n---RESULTADOS CLIENTE {client_id}---')
            print(f'Nome do arquivo enviado: {namefile}')
            print(f'Duração, carga e núcleo de CPU: {duration:.1f} segundos, {target_load*100:.1f}%, Núcleo {cpu_core}')
            print(f'Tempo de transferência: {transfer_time:.2f} ms')
            print(f'Arquivo "{namefile}" enviado para o servidor')

        else:
            print(f'\n---RESULTADOS CLIENTE {client_id}---')
            print(f'Erro: {confirmation}')

    except Exception as e:
        print(f'\n---RESULTADOS CLIENTE {client_id}---')
        print(f'Erro ao conectar ao servidor: {e}')
    finally:
        client.close()

def start_clients(server_address, num_clients):
    client_configs = []  # Lista para armazenar as configurações dos clientes

    for i in range(1, num_clients + 1):
        print(f'\n--- Configurações para Cliente {i} ---')
        namefile = input(f'Nome do arquivo a ser enviado: ')
        duration = float(input(f'Duração da carga em segundos: ').replace(',', '.'))
        target_load = float(input(f'Carga desejada (entre 0 e 1): ').replace(',', '.'))
        cpu_core = int(input(f'Núcleo da CPU (número inteiro): '))
        client_configs.append((namefile, duration, target_load, cpu_core, i))

    threads = []
    for config in client_configs:
        thread = threading.Thread(target=client_handler, args=(server_address, *config))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    server_address = ('localhost', 50002)  # Alterado para porta 50002
    num_clients = int(input("Quantos clientes deseja simular? "))

    start_clients(server_address, num_clients)

