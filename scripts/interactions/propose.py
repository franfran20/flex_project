from ape import accounts, project, chain
from web3 import Web3


def propose():
    acct = accounts.load("test1")
    empty_address = "0x0000000000000000000000000000000000000000"

    flex_core = chain.contracts.get_deployments(project.flexCore)[-1]
    flex_token = chain.contracts.get_deployments(project.flexToken)[-1]

    print("Minting And Approving Flex Tokens...")
    print("Minting...")
    mint_amount = Web3.to_wei(3, "ether")
    flex_token.mint(acct.address, mint_amount, sender=acct)

    print("Approving...")
    flex_token.approve(flex_core.address, mint_amount, sender=acct)

    print(f"Proposing Loan {flex_core.loan_counter() + 1}")

    loan_details = {
        "margin_cutoff": 130,
        "collateral_ratio": 165,
        "fixed_interest_rate": 5,
        "borrow_amount": Web3.to_wei(3, "ether"),
        "time_limit": False,
        "time_amount": 0,
        "collateral_type": empty_address,
        "principal_type": flex_token.address,
        "access_control": False,
        "recipient": empty_address,
        "loan_type": 0,
        "collateral_deposit": 0,
    }

    flex_core.propose_loan(
        loan_details["margin_cutoff"],
        loan_details["collateral_ratio"],
        loan_details["fixed_interest_rate"],
        loan_details["borrow_amount"],
        loan_details["time_limit"],
        loan_details["time_amount"],
        loan_details["collateral_type"],
        loan_details["principal_type"],
        loan_details["access_control"],
        loan_details["recipient"],
        loan_details["loan_type"],
        loan_details["collateral_deposit"],
        sender=acct,
    )

    print("Loan proposed!")


def check_address():
    flex_core = chain.contracts.get_deployments(project.flexCore)[-1]
    flex_token = chain.contracts.get_deployments(project.flexToken)[-1]

    print(flex_core.address, flex_token.address)


def main():
    propose()
