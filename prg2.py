import subprocess
import json
import time

BITCOIN_CLI = "/home/yash-singh/bitcoin-25.0/bin/bitcoin-cli"

def run_command(args):
    try:
        # Add -rpcwallet parameter before any wallet-related commands
        result = subprocess.run([BITCOIN_CLI, "-regtest", "-rpcwallet=mywallet"] + args,
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None

def get_transaction_details(txid):
    """Get full transaction details including vsize and weight."""
    tx_json = run_command(["getrawtransaction", txid, "true"])
    if tx_json:
        return json.loads(tx_json)
    return None

def mine_blocks(count, address):
    """Mine a specified number of blocks to an address."""
    return run_command(["generatetoaddress", str(count), address])

def log_transaction_data(file_path, a_to_b_tx, b_to_c_tx):
    """Log transaction data to file with vsize and weight information."""
    with open(file_path, "w") as f:
        # Log A to B transaction details
        f.write(f"Transaction from A to B: {a_to_b_tx['txid']}\n")
        f.write(f"Virtual Size: {a_to_b_tx.get('vsize', 'N/A')} vBytes\n")
        f.write(f"Weight: {a_to_b_tx.get('weight', 'N/A')} weight units\n")
        f.write(f"ScriptPubKey (Challenge Script): {a_to_b_tx['vout'][0]['scriptPubKey']['asm'] if 'vout' in a_to_b_tx else 'N/A'}\n\n")
        
        # Log B to C transaction details
        f.write(f"Transaction from B to C: {b_to_c_tx['txid']}\n")
        f.write(f"Virtual Size: {b_to_c_tx.get('vsize', 'N/A')} vBytes\n")
        f.write(f"Weight: {b_to_c_tx.get('weight', 'N/A')} weight units\n")
        f.write(f"ScriptSig (Response Script): {b_to_c_tx['vin'][0]['scriptSig']['asm'] if 'vin' in b_to_c_tx else 'N/A'}\n")
        
        # For P2SH-SegWit, we need to add the witness data
        if 'vin' in b_to_c_tx and 'txinwitness' in b_to_c_tx['vin'][0]:
            f.write(f"Witness Data: {' '.join(b_to_c_tx['vin'][0]['txinwitness'])}\n\n")
        else:
            f.write("No witness data found\n\n")
        
        # Additional information for Bitcoin Script Debugger
        f.write("=== Information for Bitcoin Script Debugger ===\n")
        f.write(f"1. ScriptPubKey (from A to B transaction):\n")
        f.write(f"   {a_to_b_tx['vout'][0]['scriptPubKey']['asm'] if 'vout' in a_to_b_tx else 'N/A'}\n")
        f.write(f"2. ScriptSig (from B to C transaction):\n")
        f.write(f"   {b_to_c_tx['vin'][0]['scriptSig']['asm'] if 'vin' in b_to_c_tx else 'N/A'}\n")
        
        # Add witness data for debugging
        if 'vin' in b_to_c_tx and 'txinwitness' in b_to_c_tx['vin'][0]:
            f.write(f"3. Witness Data (from B to C transaction):\n")
            for i, witness_item in enumerate(b_to_c_tx['vin'][0]['txinwitness']):
                f.write(f"   Witness[{i}]: {witness_item}\n")

# Main execution
def main():
    # Step 1: Generate P2SH-SegWit Addresses
    address_a_p2sh = run_command(["getnewaddress", "", "p2sh-segwit"])
    address_b_p2sh = run_command(["getnewaddress", "", "p2sh-segwit"])
    address_c_p2sh = run_command(["getnewaddress", "", "p2sh-segwit"])

    print(f"P2SH-SegWit Address A: {address_a_p2sh}")
    print(f"P2SH-SegWit Address B: {address_b_p2sh}")
    print(f"P2SH-SegWit Address C: {address_c_p2sh}")

    # Generate mining address and mine some blocks
    mining_address = run_command(["getnewaddress"])
    if mining_address:
        mine_blocks(101, mining_address)  # Mine some blocks for funding

    # Fund P2SH-SegWit Address A
    txid_funding_p2sh = run_command(["sendtoaddress", address_a_p2sh, "10"])
    print(f"Funding transaction ID for P2SH-SegWit: {txid_funding_p2sh}")
    if txid_funding_p2sh:
        mine_blocks(1, mining_address)  # Confirm transaction

    # Step 3: Create Transaction from A to B
    utxos_json = run_command(["listunspent"])
    if not utxos_json:
        print("Failed to get unspent outputs.")
        return

    utxos = json.loads(utxos_json)
    utxo = next((u for u in utxos if u["address"] == address_a_p2sh), None)

    if not utxo:
        print(f"No UTXOs found for address {address_a_p2sh}")
        return

    txid = utxo["txid"]
    vout = utxo["vout"]
    amount = float(utxo["amount"]) - 0.001  # Subtract fee
    amount_str = f"{amount:.8f}"  # Format amount properly

    # Create raw transaction
    inputs = [{"txid": txid, "vout": vout}]
    outputs = {address_b_p2sh: amount_str}
    
    # Convert to JSON strings
    inputs_json = json.dumps(inputs)
    outputs_json = json.dumps(outputs)
    
    raw_tx = run_command(["createrawtransaction", inputs_json, outputs_json])
    if not raw_tx:
        print("Failed to create raw transaction A to B.")
        return
    
    print(f"\nRaw Transaction (A to B) created.")
    
    # Sign the transaction
    signed_tx_json = run_command(["signrawtransactionwithwallet", raw_tx])
    if not signed_tx_json:
        print("Failed to sign transaction A to B.")
        return
    
    signed_tx = json.loads(signed_tx_json)
    signed_tx_hex_a_to_b = signed_tx.get("hex")
    if not signed_tx_hex_a_to_b:
        print("No hex in A→B signed response:", signed_tx); return

    print("Raw hex (A→B):", signed_tx_hex_a_to_b)
    print("Transaction A to B signed successfully.")

    
    # Broadcast the transaction
    if "hex" not in signed_tx:
        print("Signed transaction does not contain hex data.")
        return
    
    txid_a_to_b = run_command(["sendrawtransaction", signed_tx["hex"]])
    if not txid_a_to_b:
        print("Failed to broadcast transaction A to B.")
        return
    
    print(f"Transaction from A to B broadcast: {txid_a_to_b}")
    
    # Generate a block to confirm the transaction
    mine_blocks(1, mining_address)
    
    # Step 4: Create Transaction from B to C
    # Wait a moment to ensure the transaction is fully processed
    time.sleep(2)
    
    # Get the UTXO from the previous transaction (B's address)
    utxos_b_json = run_command(["listunspent", "1", "9999", f"[\"{address_b_p2sh}\"]"])
    if not utxos_b_json:
        print("Failed to get UTXOs for address B.")
        return
    
    utxos_b = json.loads(utxos_b_json)
    if not utxos_b:
        print("No UTXOs found for address B. Make sure the previous transaction is confirmed.")
        return
    
    # Use the UTXO from the previous transaction
    utxo_b = utxos_b[0]
    txid_b = utxo_b["txid"]
    vout_b = utxo_b["vout"]
    amount_b = float(utxo_b["amount"]) - 0.001  # Subtract fee
    amount_b_str = f"{amount_b:.8f}"  # Format amount properly

    # Create raw transaction from B to C
    inputs_b = [{"txid": txid_b, "vout": vout_b}]
    outputs_b = {address_c_p2sh: amount_b_str}
    
    # Convert to JSON strings
    inputs_b_json = json.dumps(inputs_b)
    outputs_b_json = json.dumps(outputs_b)
    
    raw_tx_b = run_command(["createrawtransaction", inputs_b_json, outputs_b_json])
    if not raw_tx_b:
        print("Failed to create raw transaction B to C.")
        return
    
    print(f"\nRaw Transaction (B to C) created.")
    
    # Sign the transaction
    signed_tx_b_json = run_command(["signrawtransactionwithwallet", raw_tx_b])
    if not signed_tx_b_json:
        print("Failed to sign transaction B to C.")
        return
    
    signed_tx_b = json.loads(signed_tx_b_json)
    signed_tx_hex_b_to_c = signed_tx_b.get("hex")
    if not signed_tx_hex_b_to_c:
        print("No hex in B→C signed response:", signed_tx_b); return

    print("Raw hex (B→C):", signed_tx_hex_b_to_c)
    print("Transaction B to C signed successfully.")

    
    # Broadcast the transaction
    if "hex" not in signed_tx_b:
        print("Signed transaction B to C does not contain hex data.")
        return
    
    txid_b_to_c = run_command(["sendrawtransaction", signed_tx_b["hex"]])
    if not txid_b_to_c:
        print("Failed to broadcast transaction B to C.")
        return
    
    print(f"Transaction from B to C broadcast: {txid_b_to_c}")
    
    # Generate a block to confirm the transaction
    mine_blocks(1, mining_address)
    
    # Get full transaction details for analysis and logging
    tx_a_to_b_details = get_transaction_details(txid_a_to_b)
    tx_b_to_c_details = get_transaction_details(txid_b_to_c)
    
    if not tx_a_to_b_details or not tx_b_to_c_details:
        print("Failed to retrieve transaction details.")
        return
    
    # Print transaction details with vsize and weight
    print("\nTransaction from A to B:")
    print(f"Size: {tx_a_to_b_details.get('size', 'N/A')} bytes")
    print(f"Virtual Size: {tx_a_to_b_details.get('vsize', 'N/A')} vBytes")
    print(f"Weight: {tx_a_to_b_details.get('weight', 'N/A')} weight units")
    print(f"ScriptPubKey: {tx_a_to_b_details['vout'][0]['scriptPubKey']['asm'] if 'vout' in tx_a_to_b_details else 'N/A'}")
    
    print("\nTransaction from B to C:")
    print(f"Size: {tx_b_to_c_details.get('size', 'N/A')} bytes")
    print(f"Virtual Size: {tx_b_to_c_details.get('vsize', 'N/A')} vBytes")
    print(f"Weight: {tx_b_to_c_details.get('weight', 'N/A')} weight units")
    print(f"ScriptSig: {tx_b_to_c_details['vin'][0]['scriptSig']['asm'] if 'vin' in tx_b_to_c_details else 'N/A'}")
    
    # Print witness data for SegWit transaction
    if 'vin' in tx_b_to_c_details and 'txinwitness' in tx_b_to_c_details['vin'][0]:
        print("\nWitness Data:")
        for i, witness_item in enumerate(tx_b_to_c_details['vin'][0]['txinwitness']):
            print(f"Witness[{i}]: {witness_item}")
    
    # Log the data to file
    log_transaction_data("p2sh_segwit_transactions_log.txt", tx_a_to_b_details, tx_b_to_c_details)
    print("P2SH-SegWit transactions logged successfully.")

if __name__ == "__main__":
    main()