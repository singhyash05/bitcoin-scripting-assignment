# Bitcoin Scripting Assignment

This project demonstrates how to interact with Bitcoin Core using RPC to create, analyze, and broadcast transactions between legacy (P2PKH) addresses. The scripts cover the complete workflow of creating transactions, examining their structure, and understanding Bitcoin's locking and unlocking mechanisms.  

## Prerequisites  

- Bitcoin Core installed and configured  
- Python 3.6+  
- `python-bitcoinrpc` library  

## Setup  

### 1. Start Bitcoin Core in Regtest Mode  

Regtest mode allows you to create a local Bitcoin blockchain for testing:  

```bash
bitcoind -regtest -daemon
```  

### 2. Create a Wallet  

Create a new wallet or use an existing one:  

```bash
bitcoin-cli -regtest createwallet "mywallet"
```  

### 3. Configure RPC Credentials  

Ensure your RPC credentials are set in the `~/.bitcoin/bitcoin.conf` file.  

## Usage  

Run the Python scripts to interact with Bitcoin Core:  

```bash
python prg1.py
python prg2.py
```
## Team Members
1. Shorya Kshettry - Roll No. - 230003070
2. Yash Singh - Roll No. - 230051019
3. Hardik Bansal - Roll No. - 230001031


---
