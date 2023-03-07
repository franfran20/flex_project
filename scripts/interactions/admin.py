from ape import accounts, project, chain

fantom_address = "0x0000000000000000000000000000000000000000"
fantom_usd_price_feed = "0xe04676B9A9A2973BCb0D1478b5E1E9098BBB7f3D"

link_token = "0xfaFedb041c0DD4fA2Dc0d87a6B0979Ee6FA7af5F"
link_usd_price_feed = "0x6d5689Ad4C1806D1BA0c70Ab95ebe0Da6B204fC5"

usdt_usd_price_feed = "0x9BB8A6dcD83E36726Cc230a97F1AF8a84ae5F128"


def add_token_support():
    acct = accounts.load("test1")

    flex_core = chain.contracts.get_deployments(project.flexCore)[-1]

    print("Adding Token Support For Token...")
    flex_token = chain.contracts.get_deployments(project.flexToken)[-1]

    usdt_token = chain.contracts.get_deployments(project.mockUsdt)[-1]
    usdt_token_address = usdt_token.address

    flex_core.add_token_support(usdt_token_address, sender=acct)

    print(" Token Support Added")


def add_price_feed():
    acct = accounts.load("test1")

    flex_core = chain.contracts.get_deployments(project.flexCore)[-1]

    flex_token = chain.contracts.get_deployments(project.flexToken)[-1]
    flex_token_price_feed = chain.contracts.get_deployments(project.MockV3Aggregator)[
        -1
    ]

    usdt_token = chain.contracts.get_deployments(project.mockUsdt)[-1]
    usdt_token_address = usdt_token.address

    print("Adding Asset pRiCE fEED...")
    flex_core.add_price_feed_address(
        usdt_token_address, usdt_usd_price_feed, sender=acct
    )

    print("asset Price Feed Added")


def manipulate_flex_token_price():
    flex_token_price_feed = chain.contracts.get_deployments(project.MockV3Aggregator)[
        -1
    ]
    print("Manipulating Flex Usd Price From ")

    # not done intergrating


def main():
    add_price_feed()
