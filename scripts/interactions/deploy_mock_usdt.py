from ape import project, accounts


def deploy_mock_usdt():
    acct = accounts.load("test1")

    print("Deploying Mock Usdt....")
    mock_usdt = acct.deploy(project.mockUsdt)

    print("deployed")


def main():
    deploy_mock_usdt()
