from ape import accounts, project


def deploy():
    acct = accounts.load("test1")

    print("Deploying Flex Calc...")
    flex_calc = acct.deploy(project.flexCalc)
    print("Flex Calc Deployed!")

    print("Deploying Flex Core...")
    flex_core = acct.deploy(project.flexCore, flex_calc.address)
    print("Flex Core Deployed!")

    print("Deploying Flex Token...")
    flex_token = acct.deploy(project.flexToken)
    print("Flex Token Deployed")

    print("Deploying Flex Token Price Feed...")
    flex_decimals = 8
    flex_initial_price = int(1.5 * 10**8)  # 1.5 usd
    flex_usd_price_feed = acct.deploy(
        project.MockV3Aggregator, flex_decimals, flex_initial_price
    )
    print("Deployed!")


def main():
    deploy()


# flex-calc: 0x9F192326C0C17b9F4E5F9A428cC958b887397f08
# flex-core: 0x507BEBE72854E2d886Bdd3Cc59e31d255d2AB400
# flex-token: 0x476cFd8523e767eA40Eb094AAc07D9A2e5F17Ef1
# flex-price-feed: 0x8F85Fae0e7d9efB00c27aD1BBEFf396F753b74ed
# mock usdt: 0xE14B4e52d15a3704502096b5aF28D4e2cd83Fb70
