from scripts.helpful_scripts import get_account
from brownie import interface, network, config


def get_weth():
    acc = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    txn = weth.deposit({"from": acc, "value": 0.001*(10**18)})
    txn.wait(1)
    print("deposited 0.1 eth")
    return txn
def main():
    get_weth()