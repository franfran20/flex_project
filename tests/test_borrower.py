import ape
from ape import project, chain
from web3 import Web3

empty_address = "0x0000000000000000000000000000000000000000"

# ///// NOTE: This tests aren't complete and fully robust and would be completed as time goes by ///////

# ////////    BORROWER LOAN  ///////


# TEST CASE 1 - Propose Loan
def test_details_for_lender_loan_gets_updated_as_expected_for_borrower_loan(
    flex_contract_with_proposed_borrower_loan, accounts
):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan

    # loan id
    loan_id = 1
    borrower = accounts[0]

    # asserts
    assert flex_core.loan_details(loan_id)["borrower"] == borrower
    assert flex_core.loan_details(loan_id)["lender"] == accounts[5].address
    assert flex_core.loan_details(loan_id)["margin_cutoff"] == 130
    assert flex_core.loan_details(loan_id)["collateral_ratio"] == 150
    assert flex_core.loan_details(loan_id)["fixed_interest_rate"] == 5
    assert flex_core.loan_details(loan_id)["borrow_amount"] == 0
    assert flex_core.loan_details(loan_id)["time_limit"] == True
    assert flex_core.loan_details(loan_id)["time_amount"] == 3600
    assert flex_core.loan_details(loan_id)["collateral_type"] == flex_token.address
    assert flex_core.loan_details(loan_id)["collateral_deposited"] == 200 * 10**18
    assert flex_core.loan_details(loan_id)["principal_type"] == empty_address
    assert flex_core.loan_details(loan_id)["current_debt"] == 0
    assert flex_core.loan_details(loan_id)["access_control"] == True
    assert flex_core.loan_details(loan_id)["state"] == flex_core.proposed()
    assert flex_core.loan_details(loan_id)["loan_type"] == 1


def test_propose_loan_collects_the_collateral_from_the_borrower_for_borrower_loan(
    flex_contract_with_proposed_borrower_loan,
):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan

    # test params
    loan_id = 1
    expected_borrower_deposit = 200 * 10**18  # amount lender deposits

    # asserts
    assert flex_token.balanceOf(flex_core.address) == expected_borrower_deposit


# TEST CASE 2 - Lender Renegotiations of loans proposed by the borrower
def test_loan_renegotiations_revert_if_renegotiator_isnt_recipient_for_borrower_loan(
    flex_contract_with_proposed_borrower_loan, accounts
):
    # renegotiator
    non_renegotiator = accounts[9]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan

    # test params
    loan_id = 1
    my_custom_id = "franfran"
    renegotiated_margin_cutoff = 120
    renegotiated_collateral_ratio = 140
    renegotiated_fixed_interest_rate = 3
    renegotited_time_limit = 7200

    # expect revert when loan has specific recipient
    with ape.reverts("! Loan Recipient"):
        flex_core.renegotiate(
            loan_id,
            my_custom_id,
            renegotiated_margin_cutoff,
            renegotiated_collateral_ratio,
            renegotiated_fixed_interest_rate,
            renegotited_time_limit,
            sender=non_renegotiator,
        )


def test_renegotiation_terms_updates_the_renegotiation_mapping_as_expected_for_borrower_loan(
    flex_contract_with_proposed_borrower_loan, accounts
):
    # renegotiator
    renegotiator = accounts[5]
    borrower = accounts[0]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan

    # test params
    loan_id = 1
    my_custom_id = "franfran"
    hashed_id = Web3.keccak(text=my_custom_id)
    renegotiated_margin_cutoff = 120
    renegotiated_collateral_ratio = 140
    renegotiated_fixed_interest_rate = 3
    renegotited_time_limit = 7200

    # 1st renegotiation
    flex_core.renegotiate(
        loan_id,
        my_custom_id,
        renegotiated_margin_cutoff,
        renegotiated_collateral_ratio,
        renegotiated_fixed_interest_rate,
        renegotited_time_limit,
        sender=renegotiator,
    )

    # asserts
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["borrower"] == borrower
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["lender"]
        == accounts[5].address
    )
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["margin_cutoff"]
        == renegotiated_margin_cutoff
    )
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["collateral_ratio"]
        == renegotiated_collateral_ratio
    )
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["fixed_interest_rate"]
        == renegotiated_fixed_interest_rate
    )
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["borrow_amount"] == 0
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["time_limit"] == True
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["time_amount"] == 7200
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["collateral_type"]
        == flex_token.address
    )
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["collateral_deposited"]
        == 200 * 10**18
    )
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["principal_type"]
        == empty_address
    )
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["current_debt"] == 0
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["access_control"] == True
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["state"]
        == flex_core.proposed()
    )
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["loan_type"] == 1


# TEST CASE 3 - Change ReNegotiation Terms
def test_change_renegotiation_terms_reverts_when_the_changer_isnt_owner_of_renegotiation_for_borrower_loan(
    flex_contract_with_proposed_borrower_loan, accounts
):
    # renegotiator
    renegotiator = accounts[5]
    non_renegotiator = accounts[7]
    borrower = accounts[0]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan

    # test params
    loan_id = 1
    my_custom_id = "franfran"
    renegotiated_margin_cutoff = 120
    renegotiated_collateral_ratio = 140
    renegotiated_fixed_interest_rate = 3
    renegotited_time_limit = 7200

    # renegotiation terms
    flex_core.renegotiate(
        loan_id,
        my_custom_id,
        renegotiated_margin_cutoff,
        renegotiated_collateral_ratio,
        renegotiated_fixed_interest_rate,
        renegotited_time_limit,
        sender=renegotiator,
    )

    # changed params
    new_renegotiated_margin_cutoff = 110
    new_renegotiated_collateral_ratio = 135
    new_renegotiated_fixed_interest_rate = 7
    new_renegotited_time_limit = 5000

    # new terms
    with ape.reverts("You dont Own This Re-Negotiation"):
        flex_core.change_renegotiation_terms(
            loan_id,
            my_custom_id,
            new_renegotiated_margin_cutoff,
            new_renegotiated_collateral_ratio,
            new_renegotiated_fixed_interest_rate,
            new_renegotited_time_limit,
            sender=non_renegotiator,
        )


# TEST CASE 5 - Accept ReNegotiations
def test_accept_renegotiation_reverts_if_msgsender_is_not_loan_owner_for_borrower_loan(
    flex_contract_with_proposed_borrower_loan, accounts
):
    # renegotiator
    renegotiator = accounts[5]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan

    # test params
    loan_id = 1
    my_custom_id = "franfran"
    hashed_id = Web3.keccak(text=my_custom_id)
    renegotiated_margin_cutoff = 120
    renegotiated_collateral_ratio = 140
    renegotiated_fixed_interest_rate = 3
    renegotited_time_limit = 7200

    # renegotiation terms
    flex_core.renegotiate(
        loan_id,
        my_custom_id,
        renegotiated_margin_cutoff,
        renegotiated_collateral_ratio,
        renegotiated_fixed_interest_rate,
        renegotited_time_limit,
        sender=renegotiator,
    )

    # changed params
    new_renegotiated_margin_cutoff = 110
    new_renegotiated_collateral_ratio = 135
    new_renegotiated_fixed_interest_rate = 7
    new_renegotited_time_limit = 5000

    # new terms - extra fancy step
    flex_core.change_renegotiation_terms(
        loan_id,
        my_custom_id,
        new_renegotiated_margin_cutoff,
        new_renegotiated_collateral_ratio,
        new_renegotiated_fixed_interest_rate,
        new_renegotited_time_limit,
        sender=renegotiator,
    )

    # accept renegotiation
    with ape.reverts("! Loan Owner: Cant Accept"):
        flex_core.accept_renegotiation(loan_id, my_custom_id, sender=renegotiator)


def test_accept_renegotiation_updates_the_loan_details_correctly_for_borrower_loan(
    flex_contract_with_proposed_borrower_loan, accounts
):
    # renegotiator
    renegotiator = accounts[5]
    borrower = accounts[0]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan

    # test params
    loan_id = 1
    my_custom_id = "franfran"
    hashed_id = Web3.keccak(text=my_custom_id)
    renegotiated_margin_cutoff = 120
    renegotiated_collateral_ratio = 140
    renegotiated_fixed_interest_rate = 3
    renegotited_time_limit = 7200

    # renegotiation terms
    flex_core.renegotiate(
        loan_id,
        my_custom_id,
        renegotiated_margin_cutoff,
        renegotiated_collateral_ratio,
        renegotiated_fixed_interest_rate,
        renegotited_time_limit,
        sender=renegotiator,
    )

    # changed params
    new_renegotiated_margin_cutoff = 110
    new_renegotiated_collateral_ratio = 135
    new_renegotiated_fixed_interest_rate = 7
    new_renegotited_time_limit = 5000

    # new terms - extra fancy step
    flex_core.change_renegotiation_terms(
        loan_id,
        my_custom_id,
        new_renegotiated_margin_cutoff,
        new_renegotiated_collateral_ratio,
        new_renegotiated_fixed_interest_rate,
        new_renegotited_time_limit,
        sender=renegotiator,
    )

    flex_core.accept_renegotiation(loan_id, my_custom_id, sender=borrower)

    # asserts
    assert flex_core.loan_details(loan_id)["borrower"] == borrower.address
    assert flex_core.loan_details(loan_id)["lender"] == renegotiator.address
    assert (
        flex_core.loan_details(loan_id)["margin_cutoff"]
        == new_renegotiated_margin_cutoff
    )
    assert (
        flex_core.loan_details(loan_id)["collateral_ratio"]
        == new_renegotiated_collateral_ratio
    )
    assert (
        flex_core.loan_details(loan_id)["fixed_interest_rate"]
        == new_renegotiated_fixed_interest_rate
    )
    assert flex_core.loan_details(loan_id)["borrow_amount"] == 0
    assert flex_core.loan_details(loan_id)["time_limit"] == True
    assert flex_core.loan_details(loan_id)["time_amount"] == new_renegotited_time_limit
    assert flex_core.loan_details(loan_id)["collateral_type"] == flex_token.address
    assert (
        flex_core.loan_details(loan_id)["collateral_deposited"] == 200000000000000000000
    )
    assert flex_core.loan_details(loan_id)["principal_type"] == empty_address
    assert flex_core.loan_details(loan_id)["current_debt"] == 0
    assert flex_core.loan_details(loan_id)["access_control"] == True
    assert flex_core.loan_details(loan_id)["state"] == flex_core.proposed()
    assert flex_core.loan_details(loan_id)["loan_type"] == 1


# TEST CASE 6 - Push Renegotiataion Chat
def test_only_loan_owner_and_renegotiator_can_communicate_for_borrower_loan(
    flex_contract_with_proposed_borrower_loan, accounts
):
    # renegotiator
    renegotiator = accounts[5]
    borrower = accounts[0]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan

    # test params
    loan_id = 1
    my_custom_id = "franfran"
    hashed_id = Web3.keccak(text=my_custom_id)
    test_messsage_uri = "https://fake-message-uri.ipfs-and-stuff.json"
    renegotiated_margin_cutoff = 120
    renegotiated_collateral_ratio = 140
    renegotiated_fixed_interest_rate = 3
    renegotited_time_limit = 7200

    # renegotiation terms
    flex_core.renegotiate(
        loan_id,
        my_custom_id,
        renegotiated_margin_cutoff,
        renegotiated_collateral_ratio,
        renegotiated_fixed_interest_rate,
        renegotited_time_limit,
        sender=renegotiator,
    )

    with ape.reverts("No Chat Permission"):
        flex_core.push_renegotiation_chat(
            loan_id, my_custom_id, test_messsage_uri, sender=accounts[4]
        )


# TEST CASE 7 - Accept Loan
def test_accept_loan_reverts_when_msg_sender_is_loan_owner_for_borrower_loan(
    flex_contract_with_proposed_borrower_loan, accounts
):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan
    borrower = accounts[0]
    lender = accounts[5]

    # test params
    loan_id = 1

    # expect revert: loan owner cant accept his own loan
    with ape.reverts("You Cant Accept Your Loan"):
        flex_core.accept_loan_terms(loan_id, 0, sender=borrower)


def test_accept_loan_terms_transfers_the_principal_to_borrower_and_updates_debt_for_borrower_loan(
    flex_contract_with_proposed_borrower_loan, accounts
):
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan

    # test params
    borrower = accounts[0]
    lender = accounts[5]
    loan_id = 1
    collateralized_amount = 200 * 10**18
    expected_debt = 63333333333333333333
    native_asset_borrower_received = 63333333333333333333

    # prep acceptance
    flex_token.mint(lender.address, expected_debt + 100 * 10**18, sender=lender)
    flex_token.approve(flex_core.address, expected_debt, sender=lender)

    # prev bal
    prev_bal = borrower.balance

    # accept loan
    flex_core.accept_loan_terms(loan_id, 0, sender=lender, value=collateralized_amount)

    # asserts

    assert flex_core.loan_details(loan_id)["current_debt"] == expected_debt
    assert (
        flex_core.loan_details(loan_id)["collateral_deposited"] == collateralized_amount
    )
    assert borrower.balance == native_asset_borrower_received + prev_bal


# TEST CASE 8 - Repay Loan
def test_on_repay_loan_the_principal_is_transferred_back_to_the_lender_for_borrower_loan(
    accepted_borrower_loan, accounts
):
    # anyone can repay loan
    non_borrower_or_lender = accounts[4]
    borrower = accounts[0]
    lender = accounts[5]

    # get contract
    flex_core = accepted_borrower_loan

    # test params
    loan_id = 1
    repay_amount = 63333333333333333333

    # prev lender balance
    prev_lender_bal = lender.balance

    # repay loan principal(flex token)
    flex_core.repay_loan(loan_id, sender=non_borrower_or_lender, value=repay_amount)

    assert lender.balance == prev_lender_bal + repay_amount


def test_on_repay_loan_borrower_receives_his_collateral_back_for_borrower_loan(
    accepted_borrower_loan, accounts
):
    # anyone can repay loan
    non_borrower_or_lender = accounts[4]
    borrower = accounts[0]
    lender = accounts[5]

    # get contract
    flex_core = accepted_borrower_loan

    # test params
    loan_id = 1
    repay_amount = 208 * 10**18

    # approvce contract repay amount
    flex_token = project.flexToken.deployments[-1]

    # prev borrower balance
    prev_borrower_bal = flex_token.balanceOf(borrower.address)

    # repay loan principal(flex token)
    flex_core.repay_loan(loan_id, sender=non_borrower_or_lender, value=repay_amount)

    # collateral deposited
    collateral_deposited = flex_core.loan_details(loan_id)["collateral_deposited"]

    assert (
        flex_token.balanceOf(borrower.address)
        == prev_borrower_bal + collateral_deposited
    )


# TEST CASE 9 - Liquidate Loan
def test_liquidate_loan_gives_liquidator_2_percent_of_collateral_for_borrower_loan(
    accepted_borrower_loan, accounts
):
    # accounts
    borrower = accounts[0]
    liquidator = accounts[9]

    # get contract
    flex_core = accepted_borrower_loan

    # manipulate the price of collateral (Flex) to drop to 1.2 usd
    flex_usd_price_feed = project.MockV3Aggregator.deployments[1]
    flex_usd_price_feed.updateAnswer(int(1.2 * 10**8), sender=borrower)

    # test params
    loan_id = 1
    expected_increase = 4 * 10**18

    # collateral value then drops from 300 usd to 240 usd
    # principal price doesnt change - debt valued at 190 usd - debt
    # borrower had to maintain a 130% difference between debt and collateral
    # the 240 usd is now far lesser than the 247 usd debt. This loan can be liquidated

    flex_token = project.flexToken.deployments[-1]
    prev_liquidator_balance = flex_token.balanceOf(liquidator)

    chain.pending_timestamp += 10000

    flex_core.liquidate_loan(loan_id, sender=liquidator)

    assert (
        flex_token.balanceOf(liquidator) == prev_liquidator_balance + expected_increase
    )


def test_collateral_is_given_to_the_lender_in_a_liquidation_for_borrower_loan(
    accepted_borrower_loan, accounts
):
    # accounts
    borrower = accounts[0]
    lender = accounts[5]
    liquidator = accounts[9]

    # get contract
    flex_core = accepted_borrower_loan

    # manipulate the price of collateral (Flex) to drop to 1.2 usd
    flex_usd_price_feed = project.MockV3Aggregator.deployments[1]
    flex_usd_price_feed.updateAnswer(int(1.2 * 10**8), sender=borrower)

    # test params
    loan_id = 1
    expected_increase = 196 * 10**18

    # collateral value then drops from 300 usd to 240 usd
    # principal price doesnt change - debt valued at 190 usd - debt
    # borrower had to maintain a 130% difference between debt and collateral
    # the 240 usd is now far lesser than the 247 usd debt. This loan can be liquidated

    flex_token = project.flexToken.deployments[-1]
    prev_lender_balance = flex_token.balanceOf(lender)

    chain.pending_timestamp += 10000

    flex_core.liquidate_loan(loan_id, sender=liquidator)

    # assert
    assert flex_token.balanceOf(lender) == prev_lender_balance + expected_increase


#  TEST CASE 10 - Deactivate Loan
def test_deactivate_loan_returns_loan_owner_deposit_and_sets_loan_to_deactivated_state_for_borrower_loan(
    flex_contract_with_proposed_borrower_loan, accounts
):
    # get accounts
    borrower = accounts[0]

    # get contracts
    flex_core, flex_token = flex_contract_with_proposed_borrower_loan

    # test params
    loan_id = 1

    # prev lender balance
    prev_borrower_balance = flex_token.balanceOf(borrower.address)
    collateral_deposited = 200 * 10**18

    # deactivate loan
    flex_core.deactivate_loan(loan_id, sender=borrower)

    # asserts
    assert flex_core.loan_details(loan_id)["state"] == flex_core.deactivated()
    assert (
        flex_token.balanceOf(borrower.address)
        == prev_borrower_balance + collateral_deposited
    )
