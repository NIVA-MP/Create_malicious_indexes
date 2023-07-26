import aiohttp
import asyncio
import time
import requests


# async def main():

#     async with aiohttp.ClientSession() as session:

#         pokemon_url = 'https://pokeapi.co/api/v2/pokemon/151'
#         async with session.get(pokemon_url) as resp:
#             pokemon = await resp.json()
#             print(pokemon['name'])

# asyncio.run(main())


# async def request_async(id):
        
#         pokemon_url = 'https://pokeapi.co/api/v2/pokemon/{}'.format(str(id))
#         async with requests.get(pokemon_url) as response:
#             pokemon = await response.json()
#             print(pokemon["name"])

ids = list(range(1,100))
results = []

def get_tasks(session):
    tasks = []
    for id in ids:
        pokemon_url = 'https://pokeapi.co/api/v2/pokemon/{}'.format(str(id))
        tasks.append(asyncio.create_task(session.get(pokemon_url)))
    return tasks

async def get_pokemon():

    async with aiohttp.ClientSession() as session:
        tasks = get_tasks(session)
        responses = await asyncio.gather(*tasks)
        for response in responses:
            results.append(await response.json())

def get_pokemon_sync():

    for id in ids:
        pokemon_url = 'https://pokeapi.co/api/v2/pokemon/{}'.format(str(id))
        response = requests.get(pokemon_url)
        results.append(response.json())


if __name__ == "__main__":
    

    # print(async_iter())

    # start = time.time()
    # asyncio.run(request_async(100))
    # end = time.time()

    print("Async")
    start = time.time()
    asyncio.run(get_pokemon())
    end = time.time()

    print(end-start)

    print("sync")
    start_sync = time.time()
    get_pokemon_sync()
    end_sync = time.time()

    print(end_sync-start_sync)

    # print("Elapsed time: {}".format(end-start))

    # start = time.time()
    # request_normal()
    # end = time.time()

    # print("Elapsed time: {}".format(end-start))
