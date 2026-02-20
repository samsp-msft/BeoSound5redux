import httpx
import json
import asyncio
import os

async def test():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    key = config.get('tmdb_api_key').strip()
    # Let's test with Inception (ID: 27205)
    movie_id = 27205
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={key}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    asyncio.run(test())
