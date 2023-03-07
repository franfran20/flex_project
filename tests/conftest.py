import pytest
from ape import project, chain


@pytest.fixture
def acct(accounts):
    return accounts[0]


empty_address = "0x0000000000000000000000000000000000000000"


# ////////// LENDER LOAN ///////
# acct 0 - lender
# acct 1 - borrower

loan_one_details = {
    "margin_cutoff": 130,
    "collateral_ratio": 150,
    "fixed_interest_rate": 4,
    "borrow_amount": 200 * 10**18,
    "time_limit": True,
    "time_amount": 3600,
    "access_control": False,
    "loan_type": 0,
    "collateral_deposit": 0,
}


@pytest.fixture
def flex_contract_with_proposed_lender_loan(accounts):
    acct = accounts[0]
    price_feed_deployer = accounts[5]

    print("Deploying Flex Calc...")
    flex_calc = project.flexCalc.deploy(sender=acct)
    print("Flex Calc Deployed!")

    print("Deploying Flex Core...")
    flex_core = project.flexCore.deploy(flex_calc.address, sender=acct)
    print("Flex Core Deployed!")

    print("Deploying Flex Token...")
    flex_token = project.flexToken.deploy(sender=acct)
    print("Flex Token Deployed")

    print("Adding Support for flex token...")
    flex_core.add_token_support(flex_token.address, sender=acct)
    print("Flex Token Added")

    print("Deploying Mock Price Feed For FTM...")
    ftm_decimals = 8
    ftm_initial_price = 3 * 10**8  # 3 usd
    mock_ftm_usd_price_feed = project.MockV3Aggregator.deploy(
        ftm_decimals, ftm_initial_price, sender=price_feed_deployer
    )
    print("Deployed!")

    print("Deploying Flex Token Price Feed...")
    flex_decimals = 8
    flex_initial_price = int(1.5 * 10**8)  # 1.5 usd
    flex_usd_price_feed = project.MockV3Aggregator.deploy(
        flex_decimals, flex_initial_price, sender=price_feed_deployer
    )
    print("Deployed!")

    print("Adding Price Feed Address For FTM ...")
    flex_core.add_price_feed_address(
        empty_address, mock_ftm_usd_price_feed.address, sender=acct
    )

    print("Adding Price Feed Address For Flex ...")
    flex_core.add_price_feed_address(
        flex_token.address, flex_usd_price_feed.address, sender=acct
    )

    print("Approving Tokens...")
    flex_token.approve(flex_core.address, 200000000000000000000, sender=acct)
    print("Approved")

    print("Contract allowance...")
    allowance = flex_token.allowance(acct.address, flex_core.address)
    print(f"allowance: {allowance}")

    print("Proposing Loan...")

    flex_core.propose_loan(
        loan_one_details["margin_cutoff"],
        loan_one_details["collateral_ratio"],
        loan_one_details["fixed_interest_rate"],
        loan_one_details["borrow_amount"],
        loan_one_details["time_limit"],
        loan_one_details["time_amount"],
        empty_address,
        flex_token.address,
        loan_one_details["access_control"],
        empty_address,
        loan_one_details["loan_type"],
        loan_one_details["collateral_deposit"],
        sender=acct,
    )

    print(f"Loan Proposed With ID {flex_core.loan_counter()}")

    return flex_core, flex_token


@pytest.fixture
def accepted_lender_loan(flex_contract_with_proposed_lender_loan, accounts):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    borrower = accounts[9]
    loan_id = 1

    print("Accepting Loan ID 1...")
    flex_core.accept_loan_terms(loan_id, 0, value=156 * 10**18, sender=borrower)
    print("Loan Accepted!")

    return flex_core


@pytest.fixture
def proposed_loan_with_recipient(accounts):
    acct = accounts[0]
    price_feed_deployer = accounts[4]

    print("Deploying Flex Calc...")
    flex_calc = project.flexCalc.deploy(sender=acct)
    print("Flex Calc Deployed!")

    print("Deploying Flex Core...")
    flex_core = project.flexCore.deploy(flex_calc.address, sender=acct)
    print("Flex Core Deployed!")

    print("Deploying Flex Token...")
    flex_token = project.flexToken.deploy(sender=acct)
    print("Flex Token Deployed")

    print("Adding Support for flex token...")
    flex_core.add_token_support(flex_token.address, sender=acct)
    print("Flex Token Added")

    print("Deploying Mock Price Feed For FTM...")
    ftm_decimals = 8
    ftm_initial_price = 3 * 10**8  # 3 usd
    mock_ftm_usd_price_feed = project.MockV3Aggregator.deploy(
        ftm_decimals, ftm_initial_price, sender=price_feed_deployer
    )
    print("Deployed!")

    print("Deploying Flex Token Price Feed...")
    flex_decimals = 8
    flex_initial_price = int(1.5 * 10**8)  # 1.5 usd
    flex_usd_price_feed = project.MockV3Aggregator.deploy(
        flex_decimals, flex_initial_price, sender=price_feed_deployer
    )
    print("Deployed!")

    print("Adding Price Feed Address For FTM ...")
    flex_core.add_price_feed_address(
        empty_address, mock_ftm_usd_price_feed.address, sender=acct
    )

    print("Adding Price Feed Address For Flex ...")
    flex_core.add_price_feed_address(
        flex_token.address, flex_usd_price_feed.address, sender=acct
    )

    print("Approving Tokens...")
    flex_token.approve(flex_core.address, 200000000000000000000, sender=acct)
    print("Approved")

    print("Contract allowance...")
    allowance = flex_token.allowance(acct.address, flex_core.address)
    print(f"allowance: {allowance}")

    print("Proposing Loan...")

    flex_core.propose_loan(
        loan_one_details["margin_cutoff"],
        loan_one_details["collateral_ratio"],
        loan_one_details["fixed_interest_rate"],
        loan_one_details["borrow_amount"],
        loan_one_details["time_limit"],
        loan_one_details["time_amount"],
        empty_address,
        flex_token.address,
        True,
        accounts[5].address,
        loan_one_details["loan_type"],
        loan_one_details["collateral_deposit"],
        sender=acct,
    )

    print(f"Loan Proposed With ID {flex_core.loan_counter()}")

    return flex_core, flex_token


@pytest.fixture
def loan_without_time_limit(accounts):
    acct = accounts[0]
    price_feed_deployer = accounts[5]

    print("Deploying Flex Calc...")
    flex_calc = project.flexCalc.deploy(sender=acct)
    print("Flex Calc Deployed!")

    print("Deploying Flex Core...")
    flex_core = project.flexCore.deploy(flex_calc.address, sender=acct)
    print("Flex Core Deployed!")

    print("Deploying Flex Token...")
    flex_token = project.flexToken.deploy(sender=acct)
    print("Flex Token Deployed")

    print("Adding Support for flex token...")
    flex_core.add_token_support(flex_token.address, sender=acct)
    print("Flex Token Added")

    print("Deploying Mock Price Feed For FTM...")
    ftm_decimals = 8
    ftm_initial_price = 3 * 10**8  # 3 usd
    mock_ftm_usd_price_feed = project.MockV3Aggregator.deploy(
        ftm_decimals, ftm_initial_price, sender=price_feed_deployer
    )
    print("Deployed!")

    print("Deploying Flex Token Price Feed...")
    flex_decimals = 8
    flex_initial_price = int(1.5 * 10**8)  # 1.5 usd
    flex_usd_price_feed = project.MockV3Aggregator.deploy(
        flex_decimals, flex_initial_price, sender=price_feed_deployer
    )
    print("Deployed!")

    print("Adding Price Feed Address For FTM ...")
    flex_core.add_price_feed_address(
        empty_address, mock_ftm_usd_price_feed.address, sender=acct
    )

    print("Adding Price Feed Address For Flex ...")
    flex_core.add_price_feed_address(
        flex_token.address, flex_usd_price_feed.address, sender=acct
    )

    print("Approving Tokens...")
    flex_token.approve(flex_core.address, 200000000000000000000, sender=acct)
    print("Approved")

    print("Contract allowance...")
    allowance = flex_token.allowance(acct.address, flex_core.address)
    print(f"allowance: {allowance}")

    print("Proposing Loan...")

    flex_core.propose_loan(
        loan_one_details["margin_cutoff"],
        loan_one_details["collateral_ratio"],
        loan_one_details["fixed_interest_rate"],
        loan_one_details["borrow_amount"],
        False,
        0,
        empty_address,
        flex_token.address,
        loan_one_details["access_control"],
        empty_address,
        loan_one_details["loan_type"],
        loan_one_details["collateral_deposit"],
        sender=acct,
    )

    print(f"Loan Proposed With ID {flex_core.loan_counter()}")

    return flex_core, flex_token


@pytest.fixture
def accepted_loan_without_time_limit(loan_without_time_limit, accounts):
    # flex contract and token
    flex_core, flex_token = loan_without_time_limit

    borrower = accounts[9]
    loan_id = 1

    print("Accepting Loan ID 1...")
    flex_core.accept_loan_terms(loan_id, 0, value=156 * 10**18, sender=borrower)
    print("Loan Accepted!")

    return flex_core


@pytest.fixture
def proposed_lender_loan_with_collateral_as_erc20(accounts):
    acct = accounts[0]
    price_feed_deployer = accounts[5]

    print("Deploying Flex Calc...")
    flex_calc = project.flexCalc.deploy(sender=acct)
    print("Flex Calc Deployed!")

    print("Deploying Flex Core...")
    flex_core = project.flexCore.deploy(flex_calc.address, sender=acct)
    print("Flex Core Deployed!")

    print("Deploying Flex Token...")
    flex_token = project.flexToken.deploy(sender=acct)
    print("Flex Token Deployed")

    print("Adding Support for flex token...")
    flex_core.add_token_support(flex_token.address, sender=acct)
    print("Flex Token Added")

    print("Deploying Mock Price Feed For FTM...")
    ftm_decimals = 8
    ftm_initial_price = 3 * 10**8  # 3 usd
    mock_ftm_usd_price_feed = project.MockV3Aggregator.deploy(
        ftm_decimals, ftm_initial_price, sender=price_feed_deployer
    )
    print("Deployed!")

    print("Deploying Flex Token Price Feed...")
    flex_decimals = 8
    flex_initial_price = int(1.5 * 10**8)  # 1.5 usd
    flex_usd_price_feed = project.MockV3Aggregator.deploy(
        flex_decimals, flex_initial_price, sender=price_feed_deployer
    )
    print("Deployed!")

    print("Adding Price Feed Address For FTM ...")
    flex_core.add_price_feed_address(
        empty_address, mock_ftm_usd_price_feed.address, sender=acct
    )

    print("Adding Price Feed Address For Flex ...")
    flex_core.add_price_feed_address(
        flex_token.address, flex_usd_price_feed.address, sender=acct
    )

    print("Proposing Loan...")

    flex_core.propose_loan(
        loan_one_details["margin_cutoff"],
        loan_one_details["collateral_ratio"],
        loan_one_details["fixed_interest_rate"],
        loan_one_details["borrow_amount"],
        loan_one_details["time_limit"],
        loan_one_details["time_amount"],
        flex_token.address,
        empty_address,
        loan_one_details["access_control"],
        empty_address,
        loan_one_details["loan_type"],
        loan_one_details["collateral_deposit"],
        sender=acct,
        value=loan_one_details["borrow_amount"],
    )

    print(f"Loan Proposed With ID {flex_core.loan_counter()}")

    return flex_core, flex_token


@pytest.fixture
def accepted_lender_loan_with_collateral_as_erc20(
    proposed_lender_loan_with_collateral_as_erc20, accounts
):
    # flex contract and token
    flex_core, flex_token = proposed_lender_loan_with_collateral_as_erc20

    # test params
    borrower = accounts[9]
    acct = accounts[0]
    loan_id = 1
    collateralized_amount = 600 * 10**18

    # prepping borrower
    flex_token.mint(borrower.address, collateralized_amount, sender=acct)
    flex_token.approve(flex_core.address, collateralized_amount, sender=borrower)

    print("Accepting Loan ID 1...")
    flex_core.accept_loan_terms(loan_id, collateralized_amount, sender=borrower)
    print("Loan Accepted!")

    return flex_core


# /////// LENDER LOAN FIXTURES END HERE /////


# /////// BORROWER LOAN FIXTURES ////
# acct 0 - borrower
# acct 5 - lender

loan_one_details_borrower = {
    "margin_cutoff": 130,
    "collateral_ratio": 150,
    "fixed_interest_rate": 5,
    "borrow_amount": 0,
    "time_limit": True,
    "time_amount": 3600,
    "access_control": True,
    "loan_type": 1,
    "collateral_deposit": 200 * 10**18,
}


@pytest.fixture
def flex_contract_with_proposed_borrower_loan(accounts):
    acct = accounts[0]
    price_feed_deployer = accounts[5]

    print("Deploying Flex Calc...")
    flex_calc = project.flexCalc.deploy(sender=acct)
    print("Flex Calc Deployed!")

    print("Deploying Flex Core...")
    flex_core = project.flexCore.deploy(flex_calc.address, sender=acct)
    print("Flex Core Deployed!")

    print("Deploying Flex Token...")
    flex_token = project.flexToken.deploy(sender=acct)
    print("Flex Token Deployed")

    print("Adding Support for flex token...")
    flex_core.add_token_support(flex_token.address, sender=acct)
    print("Flex Token Added")

    print("Deploying Mock Price Feed For FTM...")
    ftm_decimals = 8
    ftm_initial_price = 3 * 10**8  # 3 usd
    mock_ftm_usd_price_feed = project.MockV3Aggregator.deploy(
        ftm_decimals, ftm_initial_price, sender=price_feed_deployer
    )
    print("Deployed!")

    print("Deploying Flex Token Price Feed...")
    flex_decimals = 8
    flex_initial_price = int(1.5 * 10**8)  # 1.5 usd
    flex_usd_price_feed = project.MockV3Aggregator.deploy(
        flex_decimals, flex_initial_price, sender=price_feed_deployer
    )
    print("Deployed!")

    print("Adding Price Feed Address For FTM ...")
    flex_core.add_price_feed_address(
        empty_address, mock_ftm_usd_price_feed.address, sender=acct
    )

    print("Adding Price Feed Address For Flex ...")
    flex_core.add_price_feed_address(
        flex_token.address, flex_usd_price_feed.address, sender=acct
    )

    print("Approving Tokens...")
    flex_token.approve(flex_core.address, 200000000000000000000, sender=acct)
    print("Approved")

    print("Contract allowance...")
    allowance = flex_token.allowance(acct.address, flex_core.address)
    print(f"allowance: {allowance}")

    print("Proposing Loan...")

    flex_core.propose_loan(
        loan_one_details_borrower["margin_cutoff"],
        loan_one_details_borrower["collateral_ratio"],
        loan_one_details_borrower["fixed_interest_rate"],
        loan_one_details_borrower["borrow_amount"],
        loan_one_details_borrower["time_limit"],
        loan_one_details_borrower["time_amount"],
        flex_token.address,
        empty_address,
        loan_one_details_borrower["access_control"],
        accounts[5].address,
        loan_one_details_borrower["loan_type"],
        loan_one_details_borrower["collateral_deposit"],
        sender=acct,
    )

    print(f"Borrower Loan Proposed With ID {flex_core.loan_counter()}")

    return flex_core, flex_token


@pytest.fixture
def accepted_borrower_loan(flex_contract_with_proposed_borrower_loan, accounts):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan

    lender = accounts[5]
    loan_id = 1

    print("Accepting Loan ID 1...")
    flex_core.accept_loan_terms(loan_id, 0, value=156 * 10**18, sender=lender)
    print("Loan Accepted!")

    return flex_core
