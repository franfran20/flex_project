from ape import project, accounts, chain


def deploy_mock_usdt():
    acct = accounts.load("test1")

    print("Deploying Mock Usdt....")
    mock_usdt = acct.deploy(project.mockUsdt)

    print("deployed")


def mint_usdt():
    flex_core = chain.contracts.get_deployments(project.flexCore)[-1]

    print("Flex Core", flex_core.address)


def main():
    mint_usdt()
