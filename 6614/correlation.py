import requests
import json
import csv
import numpy as np
import socket
import time

CONFIG = {'ENDPOINT_SEARCH' : 'avantData/search/customSearch',
         'HOST' : '10.20.170.1/',
         'ENDPOINT_INSERT' : '2.0/avantData/index/bulk/upsert',
        }

HEADERS = {'cluster' : 'AvantData'}


# QUERYS_SEARCH = {  
#     "searchFirewall" : {'index': 'SOPHOS', 'body': {'size': 6000,'query': {'bool': {'filter': [{'range': {'GenerateTime': {'gte': 'now-30s', 'lte': 'now'}}}], 'must': [{'query_string': {'query': '(log_subtype: Allowed) && NOT (dst_ip: \"10.34.0.0/15\")'}}]}}}}
#     }

QUERYS_SEARCH = {  
    "searchFirewall" : {
        'index': 'AvantAgent_security', 
        'body': {"size":1000,
                'query': {'bool': {'filter': [{'range': {'GenerateTime': {'gte': 'now-30s', 'lte': 'now'}}}]
                            # ,'must': [{'query_string': {'query': '(Computer: vp1*)'}}]
                            }
                        }
                }
    }
}


def customSearch(query):
    payload_request = query
    req = requests.post('http://{0}/{1}'.format(CONFIG['HOST'], CONFIG['ENDPOINT_SEARCH']), json=payload_request, verify=False, headers=HEADERS )
    data = json.loads(req.text)
    return data


# Classe para correlação de índices
class correlation():

    # array_of_searches - array contendo os dicionários [search_1, search_2]
    def __init__(self, array_of_searches, index_array, type_of_correlation):
        self.array_of_searches = array_of_searches
        self.number_of_searches = len(array_of_searches)
        self.index_array = index_array
        self.type = type_of_correlation
        self.queries = []

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
                    'body': {"size":6000,   # ver como remover isso
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
                    # Formato geral da query must
                    formato_must = {'query_string': {'query': '(Computer: vp1*)'}}
                    # Modifica a query do must com os parâmetros de filtros em search
                    formato_must["query_string"]["query"] = '(\"{}\": \"{}\")'.format(key, search[key])

                    # Insere o format_must modificado no array must da search_query
                    search_query["body"]["query"]["bool"]["must"].append(formato_must)

                    
                    
            self.queries.append(search_query)
            search_iterator +=1


    

    def search(self):
        pass
    

if __name__ == "__main__":

    # dictionary[new_key] = dictionary[old_key]
    # del dictionary[old_key]

    # for query in QUERYS_SEARCH.keys():
    #     print("Query: {}".format(query))
    #     query_payload = QUERYS_SEARCH[query]
    #     print("Query payload: {}".format(query_payload))
    #     api_response = customSearch(query_payload)

    search_1 = {
        "ip":"*",
        "type":"*",
        "GenerateTime":"now-30s"
    }

    search_2 = {
        "src_ip":"*",
        "dst_ip":None,
        "log_type":"Firewall",
        "log_subtype":"Allowed",
        "user_name":"*",
        "src_port":"*",
        "dst_port":"*",
        "GenerateTime":"now-30s"
    }


    correlate = correlation([search_1, search_2], ["index_1", "index_2"], None)
    correlate.search_query_construct()
