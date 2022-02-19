import imp
from scripts.get_weth import get_weth
from brownie import config, network
from scripts.helpful_scripts import get_account
from brownie import interface
from web3 import Web3

amount = 0.001*(10**18)
def main():
    acc = get_account()
    erc20_add = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    lending_pool_add = get_lnd_pool_add()
    #Approve sending erc20 token
    approve_erc20(amount , lending_pool_add, erc20_add, get_account())
    tx = lending_pool_add.deposit(erc20_add, amount, acc.address, 0, {"from": acc})
    print("Depositing")
    tx.wait(1)
    print("Deposited")
    borrowable_eth, total_debt = get_borrwable_data(lending_pool_add, acc)
    #converting borrowable eth to dai
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    # borrowable_eth -> borrowable_dai * 95%\
    print(f"We are going to borrow {amount_dai_to_borrow} DAI")

    # Now we will borrow!
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool_add.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        acc.address,
        {"from": acc}
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI!")
    get_borrwable_data(lending_pool_add, acc)

    #now we will repay
    repay_all(Web3.toWei(amount_dai_to_borrow, "ether"), lending_pool_add, acc)

    get_borrwable_data(lending_pool_add, acc)
    print(
        "You just deposited, borrowed, and repayed with Aave, Brownie, and Chainlink!"
    )
def get_lnd_pool_add():
    prov = interface.ILendingPoolAddressesProvider(config["networks"][network.show_active()]["lending_pool_addresses_provider"])
    add = prov.getLendingPool()
    
    lnd_pool = interface.ILendingPool(add)
    return lnd_pool

def approve_erc20(amt, spender, add, account):
    tok = interface.IERC20(add)
    tx = tok.approve(spender, amt, {"from": account})
    tx.wait(1)
    return tx
def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_latest_price}")
    return float(converted_latest_price)

def get_borrwable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")
    return (float(available_borrow_eth), float(total_debt_eth))

def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)

    