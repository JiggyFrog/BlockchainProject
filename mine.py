import hashlib
from ecdsa import SigningKey, VerifyingKey, NIST384p
from main import Blockchain
import requests


# This script isn't noteworthy because it is just a loop to try to find a valid nonce for the block,
# This is basically just the mining software. However, you could use any hashing script and just post the nonce to the
# SendIn part of the server


def initialize():
    try:
        if open('secrets.txt', 'r').readline():
            keyHex = open('secrets.txt', 'r').readline()
        else:
            keyHex = None
    except FileNotFoundError:
        keyHex = None
    return keyHex


chain = Blockchain(requests.get('http://127.0.0.1:5000/chain').json()['difficulty'], privateKey=initialize())
print(chain.privateKey.to_string().hex())
print(chain.difficulty)


def getChain():
    return requests.get('http://127.0.0.1:5000/chain').json()['chain']


print(chain.loadBlockChain(getChain()))
for key in chain.chain[0]:
    print(chain.chain[0][key], type(chain.chain[0][key]))
terminated = False

while not terminated:
    b = chain.POW(3)
    print(type(b), b)
    q = requests.post('http://127.0.0.1:5000/sendIn', {'checkIn': b, 'sender': chain.walletIdStr})
    print("block found, validating")
    if q.json()['valid']:
        print("We Found The Block!")
        chain.loadBlockChain(getChain())
        print("currentBalance:", chain.countBalance(walletId=chain.walletIdStr))
    else:
        print('rejected')
        chain.loadBlockChain(getChain())
