import requests
import json
import csv
import numpy as np
import socket
import time

# Função que retorna todos os dados de umd dataset armazenado em CSV
def read_csv(name):

    file = open(name)
    csvreader = csv.reader(file)

    rows = []
    for row in csvreader:
        rows.append(row)

    return rows


# Classe que visa coletar diariamente as informações dos feeds em tipos plaintext, csv e json
# para em seguida remover duplicatas e inserer em um índice de IPs maliciosos
class maliciousIP():

    def __init__(self):
        # dicionário formato: {"url":"txt/json/csv"}
        self.malicious_feeds = {}
        # dicionário formato: {"url":"comentário do feed"}
        self.feeds_comments = {}
        # arrays contendo IPs e comentários que serão usados para deduplicação
        self.feeds_ip = []
        self.ip_comments = []
        # array de dicionário com resultados no formato {"ip":"url-fonte.com"}
        self.result = {}

    # Método que lê o arquivo com os feeds e os instância em um dict na memória
    def get_feeds(self, filename):

        feeds = read_csv(str(filename))
        for feeds in feeds:

            # Instancia um dicionário no formarto exemplo:{"malicious.com/block.txt":"txt"}
            self.malicious_feeds[feeds[0]] = feeds[1]

            # Instancia um dicionário no formato exemplo:{"malicious.com":"malicious_blocklist"}
            self.feeds_comments[feeds[0]] = feeds[2]

        # Cria um array com a URL de todos os feeds cadastrados no arquivo
        self.feeds = list(self.malicious_feeds.keys())


    # Método que identifica o tipo do feed (csv, txt ou json) e usa a função apropriada para
    # coleta dos IPs
    def init_scrapping(self):

        # Itera em todos os feeds cadastrados em maliciousfeed.csv
        for feed in self.feeds:
            print(feed)
            if self.malicious_feeds[feed] == "csv":
                self.request_csv(feed)
                print(len(self.feeds_ip))

            elif self.malicious_feeds[feed] == "txt":
                self.request_txt(feed)
                print(len(self.feeds_ip))

            elif self.malicious_feeds[feed] == "json":
                self.request_json(feed)
                print(len(self.feeds_ip))


    # Método que carrega e processa feeds de IPs maliciosos em formato CSV
    def request_csv(self,feed_url):

        # Inicia conexão com a URL que contém o arquivo CSV
        with requests.Session() as s:
            download = s.get(feed_url)
            # Decodifica para UTF-8
            decoded_content = download.content.decode('utf-8')

            # Lê o CSV baixado com delimitador ','
            csv_rows = csv.reader(decoded_content.splitlines(), delimiter=',')

            # Transforma o resultado em um array
            csv_values = list(csv_rows)

            for value in csv_values:
                result_dict = {}
                # Pega o IP no primeiro valor do CSV
                ip = str(value[0])
                # Coloca os IPs e respecitvos comentários nos arrays atributos da classe
                self.feeds_ip.append(ip)
                self.ip_comments.append(self.feeds_comments[feed_url])

    # Método que carrega e processa feeds de IPs maliciosos em formato TXT
    def request_txt(self,feed_url):

        # Inicia conexão com a URL que retorna no formato TXT
        with requests.Session() as s:
            download = s.get(feed_url)
            # Decodifica para UTF-8
            decoded_content = download.content.decode('utf-8')
            data = decoded_content.split('\n')

            # Transforma em um array
            data = list(data)

            # Caso o resultado seja um erro não faça nada
            if len(data) == 1:
                pass

            else:
                # Loop que itera no resultado e cria os dicionários
                for ip in data:
                  
                    if ip == data[-1]:
                        pass

                    else:
                        # Coloca os IPs e respecitvos comentários nos arrays atributos da classe
                        self.feeds_ip.append(ip)
                        self.ip_comments.append(self.feeds_comments[feed_url])

    # Método que carrega e processa feeds de IPs maliciosos em formato JSON
    def request_json(self,feed_url):

        response = requests.get(feed_url)

        response = response.json()
        
        # Verifica se a resposta é um dicionário
        if isinstance(response, dict):

            ips = response["data"]["ip"]
            for ip in ips:
                # Coloca os IPs e respecitvos comentários nos arrays atributos da classe
                self.feeds_ip.append(ip)
                self.ip_comments.append(self.feeds_comments[feed_url])
                

        # Verifica se a resposta é uma lista
        elif isinstance(response, list):
    
            for dicto in response:
                dicto = dict(dicto)

                # tenta pegar o valor ip_address no dicionário
                try:
                    addr = dicto['ip_address']
                    # Coloca os IPs e respecitvos comentários nos arrays atributos da classe
                    self.feeds_ip.append(addr)
                    self.ip_comments.append(self.feeds_comments[feed_url])

                # caso ip_addres não exista, tenta pegar o valor ip no dicionário
                except KeyError:
                    try:
                        addr = dicto['ip']
                        # Coloca os IPs e respecitvos comentários nos arrays atributos da classe
                        self.feeds_ip.append(addr)
                        self.ip_comments.append(self.feeds_comments[feed_url])
                    except KeyError:
                        pass
        else:
            pass

    # Tira as duplicatas e combina os feed_comments para algo como: {"ip":"block_list e block_list"}
    def deduplicate(self):

        self.duplicate_counter = 0
        loop_iterator = 0
        while loop_iterator <= len(self.feeds_ip)-1:

            # Verifica se é um IP válido
            try:
                socket.inet_aton(self.feeds_ip[loop_iterator])
            except socket.error:
                self.feeds_ip = np.delete(np.array(self.feeds_ip), loop_iterator)
                self.ip_comments = np.delete(np.array(self.ip_comments), loop_iterator)
                loop_iterator += 1
                continue

            # Retorna um array com True em posições em que self.feeds_ip == ip
            equal = np.equal(np.array(self.feeds_ip), np.array(self.feeds_ip[loop_iterator]))
            # Retorna o índice dos elementos que são iguais a ip
            where_equal = np.where(equal == True)[0]
            # Pega a primeira aparência de ip em self.feeds_ip
            first_equal = where_equal[0]

            # Verifica se tem mais de um elemento do mesmo (existência de repetidos)
            if len(where_equal) != 1:

                ip_belongs_to = []
                where_iterator = 0
                # Itera por todas as posições em que existe o valor em ip
                for where in where_equal:
                    
                    # Se estamos na primeira aparição de um IP pegue o comment para ser 
                    # usado como comment final
                    if where_iterator == 0:
                        ip_belongs_to.append(self.ip_comments[where])
                        
                    else:
                        self.duplicate_counter += 1
                        # Caso contrário remova o elemento na posição where do array geral de IPs
                        self.feeds_ip = np.array(self.feeds_ip)

                        # Ajusta a posição de where após a remoção em iterações de where_iterator > 1
                        if where_iterator > 1:
                            # Remove os IPs duplicados da posição where-(where_iterator-1)
                            self.feeds_ip = np.delete(np.array(np.ndarray.tolist(self.feeds_ip)), where-(where_iterator-1))
                            # Remove os comentários duplicados da posição where-(where_iterator-1)
                            self.ip_comments = np.delete(np.array(self.ip_comments), where-(where_iterator-1))

                        else:
                            # Remove os IPs duplicados da posição where
                            self.feeds_ip = np.delete(np.array(self.feeds_ip), where)
                            # Remove os comentários duplicados da posição where
                            self.ip_comments = np.delete(np.array(self.ip_comments), where)


                    where_iterator += 1

                # Coloca o nome do feed da primeira aparição do IP como nome final
                self.ip_comments[first_equal] = ip_belongs_to[0]

            
            else:
                pass

            loop_iterator += 1

    # Combina os resultados em self.feeds_ip e self.ip_comments no dicionário
    # self.result no formato {"ip":"alguma_blocklist"}
    def return_result_dict(self):

        if len(self.feeds_ip) == len(self.ip_comments):
            ip_iterator = 0
            for ip in self.feeds_ip:
                self.result[ip] = self.ip_comments[ip_iterator]
                ip_iterator += 1

            return self.result

        else:
            print("Error")
            return None
    
    # Método que verifica se índice já existe, caso contrário cria o template
    # no AvantData e insere os dados no índice novo
    def create_malicious_ip_index():
        pass

CONFIG = {'ENDPOINT_SEARCH' : 'avantData/search/customSearch',
         'HOST' : '10.20.170.1/',
         'ENDPOINT_INSERT' : '2.0/avantData/index/bulk/upsert',
        }

# Verifica se a deduplicação foi feita corretamente
def check_deduplication(resultado):
    array_ip = list(resultado.keys())

    for ip in array_ip:
        # Retorna um array com True em posições em que self.feeds_ip == ip
        equal = np.equal(np.array(array_ip), np.array(ip))
        # Retorna o índice dos elementos que são iguais a ip
        where_equal = np.where(equal == True)[0]

        if len(where_equal) > 1:
            print("ainda tem duplicata")
            print(ip)
            print(where_equal)

if __name__ == "__main__":

    ips = maliciousIP()
    # Carrega os feeds no objeto
    ips.get_feeds("./maliciousfeed.csv")
    # Realiza a coleta de todos os feeds
    ips.init_scrapping()
    # Remove as duplicatas dos IPs extraídos das fontes
    ips.deduplicate()
    # Transform o resultado em um dicionário
    resultado_ips = ips.return_result_dict()
    # print(resultado_ips)