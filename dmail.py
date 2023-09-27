import asyncio
import random
import string
from abi import dmail_abi
from loguru import logger
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))


delay = (1,10)

NODE = "https://starknet-mainnet.public.blastapi.io"

scan = 'https://starkscan.co/tx/'

def generate_random_email():
    domain = random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])
    name = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return f'{name}@{domain}'

def generate_random_theme():
    return ''.join(random.choices(string.ascii_letters, k=random.randint(5, 8)))

async def dmail(key,address):
    to = generate_random_email()
    theme = generate_random_theme()
    try:

        account = Account(address=address,
                            client=FullNodeClient(node_url=NODE),
                            key_pair=KeyPair.from_private_key(int(key[2:], 16)),
                            chain=StarknetChainId.MAINNET)
        current_nonce = await account.get_nonce()

        contract = Contract(0x0454f0bd015e730e5adbb4f080b075fdbf55654ff41ee336203aa2e1ac4d4309, dmail_abi, account)
        call = contract.functions['transaction'].prepare(
            to, theme)

        tx = await account.execute(calls=call, auto_estimate=True,cairo_version=1, nonce=current_nonce)
        status = await account.client.wait_for_tx(tx.transaction_hash)
        if status.finality_status.ACCEPTED_ON_L2:
            logger.success(
                f'{address} - транзакция подтвердилась, аккаунт успешно отправил письмо {scan}{hex(tx.transaction_hash)}')
            return 'updated'
    except Exception as e:
        error = str(e)
        if 'StarknetErrorCode.INSUFFICIENT_ACCOUNT_BALANCE' in error:
            logger.error(f'{address} - Не хватает баланса на деплой аккаунта...')
            return 'not balance'
        else:
            logger.error(f'{address} - ошибка {e}')
        return e
async def main():
    with open("keys.txt", "r") as f:
        keys = [row.strip() for row in f]
    with open("addresses.txt", "r") as f:
        addresses = [row.strip() for row in f]
    logger.info('Начало скрипта')
    for address, key in zip(addresses, keys):
        gas_price_in_wei = w3.eth.gas_price
        gas_price_in_gwei = w3.from_wei(gas_price_in_wei, 'gwei')
        if gas_price_in_gwei < 19:
            await dmail(key, address)
            await asyncio.sleep(*delay)
        else:
            logger.info(f'Газовая цена слишком высока ({gas_price_in_gwei}). Ожидание...')
            t = 2  # Ожидание 60 секунд
            logger.info(f'Сплю {t} секунд')
            await asyncio.sleep(t)
if __name__ == '__main__':
    asyncio.run(main())