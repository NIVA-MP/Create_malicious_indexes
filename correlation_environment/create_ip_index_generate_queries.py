from create_malicious_indexes import maliciousIP, read_csv, customSearch, indexData, check_deduplication, HEADERS, CONFIG

# Função que deleta os documentos presentes no índice diariamente
def delete_malicious_ip_index():


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
    ips_list = list(resultado_ips.keys())
    print(len(ips_list))
    #print(resultado_ips)

    # ips_list = {"192.168.0.1":"oi", "192.168.0.2":"ola"}
    
    index_iterator = 0
    for ip in ips_list:
         print(index_iterator)
         # Indexa no índice malicious_ip_feed
         indexData([{'ip':ip, 'type':resultado_ips[ip]}])

         index_iterator += 1