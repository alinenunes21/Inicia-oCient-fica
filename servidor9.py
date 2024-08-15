import socket
import threading
import os
import psutil
from cpu_load_generator import load_single_core
import time

# Variável global para monitorar a quantidade de memória alocada
allocated_memory_mb = 0
max_memory_mb = 16000  # Limite máximo de memória 

def allocate_memory(size_in_mb):
    """Aloca uma carga de memória especificada em megabytes."""
    global allocated_memory_mb
    if allocated_memory_mb + size_in_mb > max_memory_mb:
        print("Memória máxima alocada atingida.")
        return False

    allocated_memory_mb += size_in_mb
    print(f"Memória alocada: {allocated_memory_mb} MB")

    try:
        # Calcular o número de elementos que a lista deve ter para alcançar o tamanho especificado
        element_size = 24  # Tamanho aproximado de um objeto inteiro em bytes no Python
        num_elements = (size_in_mb * 1024 * 1024) // element_size

        # Criar uma lista com o número de elementos especificado
        large_list = [0] * int(num_elements)

        # Realizar alguma operação na lista para simular uso de memória
        sum_large_list = sum(large_list)
        return True
    except MemoryError:
        print("Erro de memória ao alocar.")
        return False

def handle_client(connection, address):
    global allocated_memory_mb
    print(f'Conexão estabelecida com {address}')
    try:
        # Receber nome do arquivo
        namefile = connection.recv(1024).decode()
        print(f'Solicitado arquivo: {namefile}')

        # Enviar confirmação de recebimento do nome do arquivo
        connection.send("File name received".encode())

        # Receber duração, carga e núcleo de CPU
        data = connection.recv(1024).decode()
        duration, target_load, cpu_core = data.split('|')
        duration = float(duration)
        target_load = float(target_load)
        cpu_core = int(cpu_core)
        print(f'Duração: {duration} segundos, Carga: {target_load * 100}%, Núcleo: {cpu_core}')

        # Simular tempo de processamento
        time.sleep(0.033)  # Atraso de 33 ms

        # Alocar memória para o cliente
        if not allocate_memory(2400):  # Aloca 2.4 GB de memória para o cliente
            connection.send("Memory allocation failed".encode())
            return

        if os.path.exists(namefile):
            file_size_before = os.path.getsize(namefile)
            print(f'Tamanho do arquivo antes da transferência: {file_size_before} bytes')

            if file_size_before > 0:
                connection.send("Ready".encode())

                # Definir a afinidade de CPU para a thread atual
                p = psutil.Process()
                p.cpu_affinity([cpu_core])

                # Gerar a carga de CPU em cada núcleo single
                threading.Thread(target=load_single_core, args=(cpu_core, duration, target_load)).start()

                with open(namefile, 'rb') as file:
                    while True:
                        data = file.read(1024)
                        if not data:
                            break
                        try:
                            connection.sendall(data)
                        except BrokenPipeError:
                            print(f"Erro: Cliente desconectado durante a transferência para {address}")
                            break

                print(f'Arquivo "{namefile}" enviado para {address}')
                print("Transferência concluída com sucesso.")

                # Após enviar, agora enviar de volta para o cliente
                try:
                    connection.send("Servidor enviou o arquivo de volta para o cliente".encode())
                except BrokenPipeError:
                    print(f"Erro: Cliente desconectado ao enviar confirmação para {address}")

                print(f'Servidor enviou o arquivo de volta para {address}')

            else:
                connection.send("Empty file".encode())
                print(f'Erro: O arquivo "{namefile}" está vazio')
        else:
            connection.send("File not found".encode())
            print(f'Erro: Arquivo "{namefile}" não encontrado')
    except Exception as e:
        print(f'Erro durante o manuseio da conexão com {address}: {e}')
    finally:
        allocated_memory_mb -= 2400  # Liberar memória alocada após o fechamento da conexão
        connection.close()

# Alocar memória ao iniciar o script
if not allocate_memory(1300):  # Aloca 1.3 GB de memória ao iniciar o script
    print("Falha ao alocar memória inicial")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 50002))  # Usar uma porta disponível
    server.listen()  # Permitir um número indefinido de clientes simultâneos

    print('Aguardando conexões...')

    try:
        while True:
            connection, address = server.accept()
            threading.Thread(target=handle_client, args=(connection, address)).start()  # Iniciar uma nova thread para cada cliente
    except KeyboardInterrupt:
        print("Servidor encerrado.")
    finally:
        server.close()

if __name__ == "__main__":
    main()

