import os
import random
import hashlib
import signal

from main import Blockchain
from tkinter import *
import requests
import customtkinter
import pyperclip
import subprocess

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("green")

def initialize():
    """Initializes the secret private keys"""
    try:
        if open('secrets.txt', 'r').readline():
            keyHex = open('secrets.txt', 'r').readline()
        else:
            keyHex = None
    except FileNotFoundError:
        keyHex = None
    return keyHex

def copyWallet():
    """Copies the wallet addr"""
    pyperclip.copy(chain.walletIdStr)

def getChain():
    """Gets the Chain status"""
    return requests.get('http://127.0.0.1:5000/chain').json()['chain']


mining_status = False

pid = -1


def sendCurrency():
    """Signs and authenticates a currency transaction"""
    recipient = inputBox.get(0.0)
    try:
        amount = int(amountBox.get(0.0))
    except ValueError:
        print("invalid input")
    if len(recipient) == 192:
        x = requests.post('http://127.0.0.1:5000/makeTransaction', chain.createTransaction(
            to=recipient,
            amount=amount))
        if x.json()['valid']:
            sentLabel.configure(text=f"Sent {amount} to {recipient[:5]}...{recipient[-5:]}")


def refresh():
    """Refreshes the UI"""
    x = chain.loadBlockChain(requests.get('http://127.0.0.1:5000/chain').json()['chain'])
    print(chain.chain)
    print(chain.countBalance(chain.walletIdStr))
    balanceText.configure(text=f"Balance: {chain.countBalance(chain.walletIdStr)} blockcoin")


root = customtkinter.CTk()
root.title("Blockain Test Rig")
root.geometry('400x600')

chain = Blockchain(requests.get('http://127.0.0.1:5000/chain').json()['difficulty'], initialize())
chain.loadBlockChain(requests.get('http://127.0.0.1:5000/chain').json()['chain'])
open('secrets.txt', 'w').write(chain.privateKey.to_string().hex())
walletText = customtkinter.CTkButton(root, text=f"Wallet: {chain.walletIdStr[:10]}...",
                                     font=("Helvetica", 24), command=copyWallet)
balanceText = customtkinter.CTkLabel(root, text=f"Balance: {chain.countBalance(chain.walletIdStr)} blockcoin", font=("Helvetica", 24))
recipientLabel = customtkinter.CTkLabel(root, text="Recipient", font=("Helvetica", 24))
inputBox = customtkinter.CTkTextbox(root, width=300, height=48)
amountLabel = customtkinter.CTkLabel(root, text="Recipient", font=("Helvetica", 24))
amountBox = customtkinter.CTkTextbox(root, width=300, height=12)
sendButton = customtkinter.CTkButton(root, text="Send!",
                                     font=("Helvetica", 24), command=sendCurrency)
sentLabel = customtkinter.CTkLabel(root, text="", font=("Helvetica", 24))
refreshButton = customtkinter.CTkButton(root, text="Refresh", font=("Helvetica", 24), command=refresh)
walletText.pack()
balanceText.pack()
recipientLabel.pack()
inputBox.pack()
amountLabel.pack()
amountBox.pack()
sendButton.pack()
sentLabel.pack()
refreshButton.pack()
root.mainloop()