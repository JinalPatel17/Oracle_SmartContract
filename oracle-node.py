# Setup
import json
import time

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from solcx import compile_source, install_solc
from web3 import Web3

# Update me: set up my Alchemy API endpoint, CoinMarketCap API key, and test account info from Metamask wallet.
alchemy_url = "alchmy_url"
CMC_API = "api_id"
my_account = "metamask_id"
private_key = bytes.fromhex("privatekey")
contract_id = "contract_id"

# Update me: write a MyOracle contract.
MyOracleSource = "./contracts/MyOracle.sol"


def get_eth_price():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {
        'symbol': 'ETH',
        'convert': 'USD'
    }
    headers = {
        'X-CMC_PRO_API_KEY': CMC_API
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        # print(data)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)

    eth_in_usd = data['data']['ETH']['quote']['USD']['price']
    return eth_in_usd

def compile_contract(w3):
    # This function is complete (no updates needed) and will compile your MyOracle.sol contract.

    with open(MyOracleSource, 'r') as file:
        oracle_code = file.read()

    compiled_sol = compile_source(
        oracle_code,
        output_values=['abi', 'bin'],
        solc_version="v0.8.17"
    )

    # Retrieve the contract interface
    contract_id, contract_interface = compiled_sol.popitem()

    # get bytecode binary and abi
    bytecode = contract_interface['bin']
    abi = contract_interface['abi']
 
    # print(w3.isAddress(w3.eth.default_account))
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    print("Compile completed!")
    return Contract 

def deploy_oracle(w3, contract):
    deploy_txn = contract.constructor().build_transaction({
        'nonce': w3.eth.get_transaction_count(my_account),
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei')
    })

    signed_txn = w3.eth.account.sign_transaction(deploy_txn, private_key=private_key)
    print("Deploying Contract...")
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    txn_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    oracle_address = txn_receipt.contractAddress
    return oracle_address

def update_oracle(w3, contract, ethprice):
    set_txn = contract.functions.setETHUSD(ethprice).build_transaction({
        'nonce': w3.eth.get_transaction_count(my_account),
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'to': contract.address,
    })

    signed_txn = w3.eth.account.sign_transaction(set_txn, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    txn_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return txn_receipt

def main():
    install_solc('v0.8.17')
    w3 = Web3(Web3.HTTPProvider(alchemy_url))
    w3.eth.default_account = my_account

    if not w3.is_connected():
        print('Not connected to Alchemy endpoint')
        exit(-1)

    MyOracle = compile_contract(w3)
    MyOracle.address = deploy_oracle(w3, MyOracle)
    print("My oracle address:")
    print(MyOracle.address)

    event_filter = MyOracle.events.UpdateRequested.create_filter(fromBlock='latest')

    while True:
        print("Waiting for an oracle update request...")
        for event in event_filter.get_new_entries():
            if event.event == "UpdateRequested":
                print("------------------------------------------")
                print("Callback found:")
                for _ in range(10):
                    try:
                        ETH_price = get_eth_price()
                        ETH_price = int(ETH_price)
                    except:
                        continue
                    else:
                        break
                print("Pulled Current ETH price in USD: $", ETH_price)
                print("Writing to blockchain...")
                txn = update_oracle(w3, MyOracle, ETH_price)
                print("Transaction complete!")
                print("blockNumber:", txn.blockNumber, "gasUsed:", txn.gasUsed)
                print("------------------------------------------")
        time.sleep(2)

if __name__ == "__main__":
    main()
