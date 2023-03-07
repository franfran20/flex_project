from ape import project, chain, accounts


def mint_flex():
    acct = accounts.load("test1")
    flex_token = chain.contracts.get_deployments(project.flexToken)[-1]

    print("Minting Flex Tokens")
    amount = 100 * 10**18

    flex_token.mint(
        acct.address,
        amount,
        sender=acct,
    )

    print("Minted!")


def main():
    mint_flex()
