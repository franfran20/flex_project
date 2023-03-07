from ape import project, chain, accounts, Contract

link_usd_price_feed = "0x6d5689Ad4C1806D1BA0c70Ab95ebe0Da6B204fC5"
fantom_usd_price_feed = "0xe04676B9A9A2973BCb0D1478b5E1E9098BBB7f3D"
usdt_usd_price_feed = "0x9BB8A6dcD83E36726Cc230a97F1AF8a84ae5F128"


def get_price():
    link_price = Contract(link_usd_price_feed).latestRoundData()
    ftm_price = Contract(fantom_usd_price_feed).latestRoundData()
    usdt_price = Contract(usdt_usd_price_feed).latestRoundData()

    flex_token_price_feed = chain.contracts.get_deployments(project.MockV3Aggregator)[
        -1
    ]
    flex_price = flex_token_price_feed.latestRoundData()

    print("Link Price: ", link_price["answer"] / 10**8)
    print("Ftm Price: ", ftm_price["answer"] / 10**8)
    print("Usdt Price: ", usdt_price["answer"] / 10**8)
    print("Flex Price: ", flex_price[1] / 10**8)


def main():
    get_price()
