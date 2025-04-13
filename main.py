import datetime, hashlib, json
import random
import time
import ecdsa
import requests
from flask import Flask, jsonify, request
from ecdsa import SigningKey, VerifyingKey, NIST384p


class Blockchain:
    def __init__(self, difficulty, privateKey=None):
        """The Main Blockchain class that serves as everything from server hosting to mining"""
        self.chain = []
        self.currentBlockData = []
        self.blockReward = 100
        self.createBlock(proof=1, winner=-1)
        self.difficulty = difficulty
        if privateKey == 'server':
            self.privateKey = None
            self.walletId = None
        elif privateKey:
            self.privateKey = SigningKey.from_string(bytes.fromhex(privateKey), curve=NIST384p)
            self.walletId = self.privateKey.get_verifying_key()
            self.walletIdStr = self.walletId.to_string().hex()
        else:
            self.privateKey = self.getNewPrivateKey()
            self.walletId = self.privateKey.get_verifying_key()
            self.walletIdStr = self.walletId.to_string().hex()

    @staticmethod
    def hexToKey(string: str):
        """Converts a hex value to a key w/ NIST384p"""
        return VerifyingKey.from_string(bytes.fromhex(string), curve=NIST384p)

    def createBlock(self, proof, winner):
        """Creates a block and appends it to the main network"""
        block = {
            'blockReward': self.blockReward,
            'data': self.currentBlockData,
            'index': len(self.chain) + 1,
            'nonce': proof,
            'previousBlock': self.getHash(proof),
            'winner': winner,
        }
        self.currentBlockData = []
        self.chain.append(block)
        return block

    def previousBlock(self):
        """Gets the previous block returns '0' if it is the genesis block"""
        try:
            return self.chain[-1]
        except IndexError:
            return '0'

    def getHash(self, nonce):
        """Hashes the nonce"""
        return str(hashlib.sha256(str(str(self.previousBlock()) + str(nonce)).encode()).hexdigest())

    def POW(self, startNonce):
        """Starts hashing until it finds a valid code"""
        check = False
        nonceMult = 0
        tries = 0
        while check is False:
            tries += 1
            nonceMult = random.randint(0, 9 * 1111111111111111111111111111111)
            testing = self.getHash(str(hashlib.sha256(str(startNonce * nonceMult).encode()).hexdigest()))
            if testing[:self.difficulty] == '0' * self.difficulty:
                print("found block!")
                check = True
            if not tries % 1000000 == 0:
                continue
            else:
                if not len(self.chain) == len(requests.get('http://127.0.0.1:5000/chain').json()['chain']):
                    self.loadBlockChain(requests.get('http://127.0.0.1:5000/chain').json()['chain'])
                    return False
                else:
                    continue
        return str(hashlib.sha256(str(startNonce * nonceMult).encode()).hexdigest())

    def checkValid(self, testNonce, sender):
        """Checks to see if a transaction is valid or not"""
        if str(self.getHash(testNonce)[:self.difficulty]) == '0' * self.difficulty:
            print('Valid', testNonce)
            self.createBlock(testNonce, sender)
            return True
        else:
            print('Invalid', testNonce)
            return False

    def checkFullChain(self):
        """Checks the full chain for errors in the chains integrity"""
        isValid = True
        it = 0
        for block in self.chain[1:]:
            if str(hashlib.sha256(str(str(self.chain[it]) + str(block['nonce'])).encode()).hexdigest())[
               :self.difficulty] == '0' * self.difficulty:
                print("Block:", str(block), "Is valid")
            else:
                isValid = False
                break
            it += 1
        return isValid

    def loadBlockChain(self, chain_json):
        """Loads a chain from json value"""
        self.chain = chain_json
        return chain_json

    @staticmethod
    def getNewPrivateKey():
        """Generates a new key pair"""
        return SigningKey.generate(curve=NIST384p)

    def createTransaction(self, to, amount):
        """Creates a transaction between two accounts and attempts to send it"""
        transaction = {
            'amount': str(amount),
            'from': self.walletIdStr,
            'to': to,
        }
        print('hashGenerated:', hashlib.sha256(str(transaction).encode()).hexdigest())
        signature: bytes = self.privateKey.sign(bytes.fromhex(hashlib.sha256(str(transaction).encode()).hexdigest()))

        fullTransaction = {
            'transaction': str(transaction),
            'digitalSignature': signature.hex(),
        }
        return fullTransaction

    def verifyTransaction(self, walletId: str, fullTransaction):
        """Verification of the transaction is checked to see if it was an authorized transaction"""
        signature = fullTransaction['digitalSignature']
        amt = fullTransaction['transaction']['amount']
        sendBal = self.countBalance(walletId)
        data = hashlib.sha256(fullTransaction['transaction'].encode()).hexdigest()
        walletId = Blockchain.hexToKey(walletId)
        if walletId.verify(bytes.fromhex(signature), data=bytes.fromhex(data)) and amt <= sendBal:
            return True
        else:
            return False

    def countBalance(self, walletId):
        """Counts how many tokens the person has on the latest part of the chain"""
        counted = 0
        for block in self.chain:
            if block['winner'] == walletId:
                counted += block['blockReward']
            for transaction in block['data']:
                transaction = json.loads(transaction.replace("'", '"'))
                if transaction["to"] == walletId:
                    counted += float(transaction['amount'])
                if transaction["from"] == walletId:
                    counted -= float(transaction['amount'])
        return counted


if __name__ == "__main__":
    # This is the main server part of it
    chain = Blockchain(difficulty=6, privateKey='server')
    app = Flask(__name__)


    @app.route('/sendIn', methods=['POST'])
    def handle():
        """Handles someone sending in a valid nonce"""
        toCheck = request.form["checkIn"]
        sender = request.form['sender']
        x = chain.checkValid(toCheck, sender)
        print(x)
        if x:
            return jsonify({'valid': True})
        else:
            return jsonify({'valid': False})


    @app.route('/balance', methods=['POST'])
    def check():
        """Checks wallet balance"""
        id = request.form['walletId']
        return jsonify({'walletId': id, 'balance': chain.countBalance(id)})


    @app.route('/makeTransaction', methods=['POST'])
    def handleTransaction():
        """Handles a transaction and appends it to the blockchain if valid"""
        transaction = json.loads(request.form['transaction'].replace("'", '"'))  # Loads request
        digitalSignature = request.form['digitalSignature']
        valid = chain.verifyTransaction(transaction['from'], {
            'transaction': request.form(['transaction']),
            'digitalSignature': str(digitalSignature)
        })
        print(valid)  # Valid check
        if valid:
            # Adds to main network if valid
            chain.currentBlockData.append({'transaction': str(transaction), 'digitalSignature': str(digitalSignature)})
            return jsonify({'valid': True})
        else:
            return jsonify({'valid': False})


    @app.route('/chain')
    def display():
        """Displays the chain"""
        return jsonify({'chain': chain.chain, 'difficulty': chain.difficulty})


    app.config["JSON_SORT_KEYS"] = False
    app.run(host='127.0.0.1', port=5000)
