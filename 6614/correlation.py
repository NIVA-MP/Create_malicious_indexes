import requests
import json
import csv
import numpy as np
import socket
import time
import timeit


CONFIG = {'ENDPOINT_SEARCH' : 'avantData/search/customSearch',
         'HOST' : '10.20.170.1/',
         'ENDPOINT_INSERT' : '2.0/avantData/index/bulk/upsert',
        }

HEADERS = {'cluster' : 'AvantData'}

# Função para busca customizada na API do AvantData
def customSearch(query):
    payload_request = query
    req = requests.post('http://{0}/{1}'.format(CONFIG['HOST'], CONFIG['ENDPOINT_SEARCH']), json=payload_request, verify=False, headers=HEADERS )
    data = json.loads(req.text)
    return data


# Classe para correlação de índices
class correlation():

    # array_of_searches - array contendo os dicionários [search_1, search_2]
    # index_array - array contendo o nome dos índices cujas pesquisas serão correlacionadas [index_1, index_2]
    def __init__(self, array_of_searches, index_array, type_of_correlation):
        self.array_of_searches = array_of_searches
        self.number_of_searches = len(array_of_searches)
        self.index_array = index_array
        self.type = type_of_correlation
        self.queries = []
        self.correlation_results = []

    # Método que constroí o payload da busca feita no AvantAPI de acordo
    # com o conteúdo em self
    def search_query_construct(self):

        search_iterator = 0
        # Loop para criação de queries de busca a partir dos parâmetros
        # armazenados em dicionários no self.array_of_searches
        for search in self.array_of_searches:

            # Estrutura do payload de busca para correlação do ElasticSearch
            search_struct = {  
                "searchName_placeholder" : {
                    'index': 'indexName_placeholder',
                    'ignore_unavailable':'true',                    # Parâmetro para ignorar índice fechado
                    'body': {"size":6000,   # ver como remover isso
                            "_source":{"includes":[]},
                            'query': {'bool': {'filter': [{'range': {'GenerateTime': {'gte': 'gte_placeholder', 'lte': 'now'}}}]    # now-30s
                                                ,'must': []      # '(ip_addres: 192.168.0.1)'
                                            }
                                    }
                            }
                    }
            }

            # Pega os parâmetros usados como filtro para busca
            search_keys = list(search.keys())
            search_query = search_struct["searchName_placeholder"]
            # Atualiza o índice da pesquisa
            search_query["index"] = self.index_array[search_iterator]
            # Loop para modificação dos parâmetros de pesquisa armazeandos em key
            for key in search_keys:

                if key == "GenerateTime":
                    # Modifica o GenerateTime
                    search_query["body"]["query"]["bool"]["filter"][0]["range"]["GenerateTime"]["gte"] = search[key]

                else:
                    # Insere os campos da pesquisa em _source (campos que serão retornados)
                    search_query["body"]["_source"]["includes"].append(key)

                    # Somente insere os campos de pesquisa para o primeiro índice
                    if search_iterator == 0:
                            
                        # Formato geral da query must
                        formato_must = {'query_string': {'query': '(Computer: vp1*)'}}

                        # Modifica a query do must com os parâmetros de filtros em search
                        formato_must["query_string"]["query"] = '({}: {})'.format(key, search[key])

                        # Insere o format_must modificado no array must da search_query
                        search_query["body"]["query"]["bool"]["must"].append(formato_must)

            print(search_query)
            self.queries.append(search_query)
            search_iterator +=1

    # Método que realiza pesquisa no índice base da correlação
    def search_base(self):

        # Pega os resultados do índice base da correlação
        result_base_search = customSearch(correlate.queries[0])

        # Tenta pegar o resultado da pesquisa em ['hits']['hits']
        try:
            result_array = result_base_search['hits']['hits']
            return result_array
        except KeyError as err:
            return None

    # Método que constroí o campo must da pesquisa no segundo índice baseado no resultados
    # advindos do método search_base() e já os encaminha pra correlation_search()
    def construct_second(self, result_base, replace_array):

        # Resultado na pesquisa do índice base não retornou resultados
        if len(result_base) == 0:
            print("No results for configured search in the base index.")
            exit()


        result_count = 0
        # Loop para cada um dos resultados da pesquisa base
        for result in result_base:
            # Pega os resultados da pesquisa
            result = result["_source"]

            # print("\n")
            # print(result_count)
            # print(result)

            # Query montada para o formato passado em search_2
            second_search = self.queries[1]

            replace_iterator = 0
            # Loop que itera entre os parâmetros de busca no segundo índice em busca
            # da variável que deve ser substituída
            search_structure = self.array_of_searches[1]
            for search_parameter in search_structure:

                # Formato geral da query must
                formato_must = {'query_string': {'query': '(Computer: vp1*)'}}

                # Verifica se é um campo que deve usar o resultado de search_base()
                if search_structure[search_parameter] == None:

                    # Cria um filtro em must com o campo da pesquisa e o valor
                    formato_must["query_string"]["query"] = '({}: {})'.format(search_parameter, 
                                                                                      result[replace_array[replace_iterator]])
                    
                    # Insere o format_must modificado no array must da search_query
                    second_search["body"]["query"]["bool"]["must"].append(formato_must)
                    
                    # Aumenta o iterador que aponta para os parâmetros da primeira pesquisa que devem
                    # servir de filtros na segunda pesquisa
                    replace_iterator += 1

                # Verifica se o campo é diferente de uma wildcard que não fará diferença na filtragem
                elif search_structure[search_parameter] != "*":

                    if search_parameter != "GenerateTime":

                        # Cria um filtro em must com o campo da pesquisa e o valor
                        formato_must["query_string"]["query"] = '({}: {})'.format(search_parameter, 
                                                                                        search_structure[search_parameter])
                        
                        # Insere o format_must modificado no array must da search_query
                        second_search["body"]["query"]["bool"]["must"].append(formato_must)

            
            # print(second_search)

            # Faz as buscas na API do ElasticSearch
            self.correlation_search(second_search)

            # Reinicia os parâmetros de pesquisa
            self.queries[1]["body"]["query"]["bool"]["must"].clear()

            # result_count += 1

    # Método que envia a pesquisa criada na API
    def correlation_search(self, search):

        # Pega o resultado da pesquisa de correlação
        result_search = customSearch(search)
        result = result_search['hits']['hits']

        # Verifica se houveram resultados para a pesquisa
        if len(result) != 0:

            # print("MALICIOUS")

            # Pega os campos do resultado
            result_fields = result['_source']

            # Insere o dicionário dos campos no array correlation_results
            self.correlation_results.append(result_fields)


if __name__ == "__main__":

    search_1 = {
        "ip":"*",
        "type":"*",
        "GenerateTime":"now-5h"
    }

    search_2 = {
        "src_ip":"*",
        "dst_ip":None,
        "log_type":"Firewall",
        "log_subtype":"Allowed",
        "user_name":"*",
        "src_port":"*",
        "dst_port":"*",
        "GenerateTime":"now-1m"
    }

    # Regra para associação de valores do índice 1 com campos do índice 2
    correlate_rule = {
        "dst_ip":"ip"
    }

    correlate = correlation([search_1, search_2], ["malicious_ip_feed", "SOPHOS"], None)
    correlate.search_query_construct()

    # correlate.replace_None_with(["ip"])
    result_base = correlate.search_base()

    # result_base = [{"_source":{"ip":"192.168.0.1","type":"snort_malicious_feed"}}, {"_source":{"ip":"192.168.0.2","type":"daniel_malicious_feed"}}, 
    #                {"_source":{"ip":"192.168.0.3","type":"algum_malicious_feed"}}]
    
    # print("\n")
    start = time.time()
    correlate.construct_second(result_base,["ip"])
    end = time.time()

    print(end-start)


    # if result_base != None:
    #    result_correlation = correlate.search_correlate(result_base, search_2, ["ip","type"])