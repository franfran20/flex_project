from ape import project, chain
import ape
from web3 import Web3


empty_address = "0x0000000000000000000000000000000000000000"

# ///// NOTE: This tests aren't complete and fully robust and would be completed as time goes by ///////


# /////// LENDER LOAN /////


# TEST CASE 1 - PROPOSED LENDER LOAN WITH COLLATERAL ACCEPTED AS NATIVE ASSET AND BORROW ASSET AS ERC20 (FLEX TOKEN)
def test_propose_loan_increments_loan_id(flex_contract_with_proposed_lender_loan):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    assert flex_core.loan_counter() == 1


def test_propose_loan_sets_time_limit_when_selected(
    flex_contract_with_proposed_lender_loan,
):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 1
    set_time = 3600

    # asserts
    assert flex_core.loan_details(1)["time_limit"] == True
    assert flex_core.loan_details(1)["time_amount"] == set_time


def test_propose_loan_reverts_when_unaccepted_loan_type_is_used(
    flex_contract_with_proposed_lender_loan, acct
):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_details_with_unaccepted_loan_type = {
        "margin_cutoff": 130,
        "collateral_ratio": 150,
        "fixed_interest_rate": 2,
        "borrow_amount": 200**18,
        "time_limit": True,
        "time_amount": 3600,
        "access_control": False,
        "loan_type": 4,
        "collateral_deposit": 0,
    }

    # expected revert
    with ape.reverts("Loan Type Does Not Exist"):
        flex_core.propose_loan(
            loan_details_with_unaccepted_loan_type["margin_cutoff"],
            loan_details_with_unaccepted_loan_type["collateral_ratio"],
            loan_details_with_unaccepted_loan_type["fixed_interest_rate"],
            loan_details_with_unaccepted_loan_type["borrow_amount"],
            loan_details_with_unaccepted_loan_type["time_limit"],
            loan_details_with_unaccepted_loan_type["time_amount"],
            empty_address,
            flex_token.address,
            loan_details_with_unaccepted_loan_type["access_control"],
            empty_address,
            loan_details_with_unaccepted_loan_type["loan_type"],
            loan_details_with_unaccepted_loan_type["collateral_deposit"],
            sender=acct,
        )


def test_propose_loan_reverts_when_the_asset_isnt_supported(accounts):
    # acct
    acct = accounts[0]

    # setup
    print("Deploying Flex Calc...")
    flex_calc = project.flexCalc.deploy(sender=acct)
    print("Flex Calc Deployed!")

    print("Deploying Flex Core...")
    flex_core = project.flexCore.deploy(flex_calc.address, sender=acct)
    print("Flex Core Deployed!")

    print("Deploying Flex Token...")
    flex_token = project.flexToken.deploy(sender=acct)
    print("Flex Token Deployed")

    print("Proposing Loan...")

    # loan one - willing to lend 200 test tokens and receive eth as collateral
    loan_one_details = {
        "margin_cutoff": 130,
        "collateral_ratio": 150,
        "fixed_interest_rate": 4,
        "borrow_amount": 200000000000000000000,
        "time_limit": True,
        "time_amount": 3600,
        "access_control": False,
        "loan_type": 0,
        "collateral_deposit": 0,
    }

    # expect revert
    with ape.reverts("An Asset Is Not Supported"):
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


def test_details_for_lender_loan_gets_updated_As_expected(
    flex_contract_with_proposed_lender_loan, acct
):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # loan id
    loan_id = 1

    # asserts
    assert flex_core.loan_details(loan_id)["borrower"] == empty_address
    assert flex_core.loan_details(loan_id)["lender"] == acct.address
    assert flex_core.loan_details(loan_id)["margin_cutoff"] == 130
    assert flex_core.loan_details(loan_id)["collateral_ratio"] == 150
    assert flex_core.loan_details(loan_id)["fixed_interest_rate"] == 4
    assert flex_core.loan_details(loan_id)["borrow_amount"] == 200000000000000000000
    assert flex_core.loan_details(loan_id)["time_limit"] == True
    assert flex_core.loan_details(loan_id)["time_amount"] == 3600
    assert flex_core.loan_details(loan_id)["collateral_type"] == empty_address
    assert flex_core.loan_details(loan_id)["collateral_deposited"] == 0
    assert flex_core.loan_details(loan_id)["principal_type"] == flex_token.address
    assert flex_core.loan_details(loan_id)["current_debt"] == 0
    assert flex_core.loan_details(loan_id)["access_control"] == False
    assert flex_core.loan_details(loan_id)["state"] == flex_core.proposed()
    assert flex_core.loan_details(loan_id)["loan_type"] == 0


def test_propose_loan_collects_the_principal_from_the_lender(
    flex_contract_with_proposed_lender_loan,
):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 1
    expected_borrrow_amount = 200 * 10**18  # amount lender deposits

    # asserts
    assert flex_token.balanceOf(flex_core.address) == expected_borrrow_amount


def test_after_propose_loan_loan_existence_tracker_is_true(
    flex_contract_with_proposed_lender_loan, acct
):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 1

    # assert
    assert flex_core.loan_existence_tracker(loan_id) == True


# TEST CASE 2 - Borower Renegotiations of loans proposed by the lender
def test_only_existing_loans_can_be_renegotiated(
    flex_contract_with_proposed_lender_loan, accounts
):
    # renegotiator
    renegotiator = accounts[9]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 3
    my_custom_id = "franfran"
    renegotiated_margin_cutoff = 120
    renegotiated_collateral_ratio = 140
    renegotiated_fixed_interest_rate = 3
    renegotited_time_limit = 7200

    # expect revert for non existent loan id
    with ape.reverts("Loan Does Not Exist"):
        flex_core.renegotiate(
            loan_id,
            my_custom_id,
            renegotiated_margin_cutoff,
            renegotiated_collateral_ratio,
            renegotiated_fixed_interest_rate,
            renegotited_time_limit,
            sender=renegotiator,
        )


def test_loan_state_is_proposed_before_being_able_to_renogotiate(
    accepted_lender_loan, accounts
):
    # renegotiator
    renegotiator = accounts[9]

    # flex contract and token
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    my_custom_id = "franfran"
    renegotiated_margin_cutoff = 120
    renegotiated_collateral_ratio = 140
    renegotiated_fixed_interest_rate = 3
    renegotited_time_limit = 7200

    # expect revert when loan is accpected
    with ape.reverts("Loan ! In Proposed State"):
        flex_core.renegotiate(
            loan_id,
            my_custom_id,
            renegotiated_margin_cutoff,
            renegotiated_collateral_ratio,
            renegotiated_fixed_interest_rate,
            renegotited_time_limit,
            sender=renegotiator,
        )


def test_loan_renegotiations_revert_if_renegotiator_isnt_recipient(
    proposed_loan_with_recipient, accounts
):
    # renegotiator
    renegotiator = accounts[9]

    # flex contract and token
    flex_core, flex_token = proposed_loan_with_recipient

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
            sender=renegotiator,
        )


def test_there_can_only_be_a_single_renegotiation_id_for_each_user(
    flex_contract_with_proposed_lender_loan, accounts
):
    # renegotiator
    renegotiator = accounts[9]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 1
    my_custom_id = "franfran"
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

    # expect revert for already existing re-nego id
    with ape.reverts("Custom ID Taken"):
        flex_core.renegotiate(
            loan_id,
            my_custom_id,
            renegotiated_margin_cutoff,
            renegotiated_collateral_ratio,
            renegotiated_fixed_interest_rate,
            renegotited_time_limit,
            sender=renegotiator,
        )


def test_renegotiation_terms_updates_the_renegotiation_mapping_as_expected(
    flex_contract_with_proposed_lender_loan, accounts
):
    # renegotiator
    renegotiator = accounts[9]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

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
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["borrower"] == renegotiator
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["lender"]
        == accounts[0].address
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
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["borrow_amount"]
        == 200000000000000000000
    )
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["time_limit"] == True
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["time_amount"] == 7200
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["collateral_type"]
        == empty_address
    )
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["collateral_deposited"] == 0
    )
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["principal_type"]
        == flex_token.address
    )
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["current_debt"] == 0
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["access_control"] == False
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["state"]
        == flex_core.proposed()
    )
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["loan_type"] == 0


# TEST CASE 3 - Change renegotiation terms
def test_change_renegotiation_terms(flex_contract_with_proposed_lender_loan, accounts):
    # renegotiator
    renegotiator = accounts[9]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

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

    # new terms
    flex_core.change_renegotiation_terms(
        loan_id,
        my_custom_id,
        new_renegotiated_margin_cutoff,
        new_renegotiated_collateral_ratio,
        new_renegotiated_fixed_interest_rate,
        new_renegotited_time_limit,
        sender=renegotiator,
    )

    # asserts
    assert flex_core.loan_renegotiations(loan_id, hashed_id)["borrower"] == renegotiator
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["margin_cutoff"]
        == new_renegotiated_margin_cutoff
    )
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["collateral_ratio"]
        == new_renegotiated_collateral_ratio
    )
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["fixed_interest_rate"]
        == new_renegotiated_fixed_interest_rate
    )
    assert (
        flex_core.loan_renegotiations(loan_id, hashed_id)["time_amount"]
        == new_renegotited_time_limit
    )


def test_change_renegotiation_terms_reverts_when_renegotiation_does_not_exist(
    flex_contract_with_proposed_lender_loan, accounts
):
    # renegotiator
    renegotiator = accounts[9]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 1
    my_custom_id = "franfran"
    hashed_id = Web3.keccak(text=my_custom_id)
    renegotiated_margin_cutoff = 120
    renegotiated_collateral_ratio = 140
    renegotiated_fixed_interest_rate = 3
    renegotited_time_limit = 7200

    # renegotiation terms
    with ape.reverts("Re-Negotiation Does Not Exist"):
        flex_core.change_renegotiation_terms(
            loan_id,
            my_custom_id,
            renegotiated_margin_cutoff,
            renegotiated_collateral_ratio,
            renegotiated_fixed_interest_rate,
            renegotited_time_limit,
            sender=renegotiator,
        )


def test_change_renegotiation_terms_reverts_when_the_changer_isnt_owner_of_renegotiation(
    flex_contract_with_proposed_lender_loan, accounts
):
    # renegotiator
    renegotiator = accounts[9]
    non_renegotiator = accounts[5]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

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


#  TEST CASE 4 - Change Original Loan Terms
def test_change_original_loan_terms(flex_contract_with_proposed_lender_loan, accounts):
    lender = accounts[0]
    renegotiator = accounts[9]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 1

    # changed params
    new_margin_cutoff = 110
    new_collateral_ratio = 135
    new_fixed_interest_rate = 7
    new_time_limit = 5000

    # new terms
    flex_core.change_original_loan_terms(
        loan_id,
        new_margin_cutoff,
        new_collateral_ratio,
        new_fixed_interest_rate,
        new_time_limit,
        sender=lender,
    )

    # asserts
    assert flex_core.loan_details(loan_id)["margin_cutoff"] == new_margin_cutoff
    assert flex_core.loan_details(loan_id)["collateral_ratio"] == new_collateral_ratio
    assert (
        flex_core.loan_details(loan_id)["fixed_interest_rate"]
        == new_fixed_interest_rate
    )
    assert flex_core.loan_details(loan_id)["time_amount"] == new_time_limit


def test_change_loan_terms_reverts_if_msg_sender_is_not_lender(
    flex_contract_with_proposed_lender_loan, accounts
):
    lender = accounts[0]
    non_lender = accounts[9]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 1
    my_custom_id = "franfran"

    # changed params
    new_margin_cutoff = 110
    new_collateral_ratio = 135
    new_fixed_interest_rate = 7
    new_time_limit = 5000

    # new terms
    with ape.reverts("!Loan Owner"):
        flex_core.change_original_loan_terms(
            loan_id,
            new_margin_cutoff,
            new_collateral_ratio,
            new_fixed_interest_rate,
            new_time_limit,
            sender=non_lender,
        )


# TEST CASE 5 - Accepting Renegotiations
def test_accept_renegotiation_reverts_if_msgsender_is_not_loan_owner(
    flex_contract_with_proposed_lender_loan, accounts
):
    # renegotiator
    renegotiator = accounts[9]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

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


def test_accept_renegotiation_updates_the_loan_details_correctly(
    flex_contract_with_proposed_lender_loan, accounts
):
    # renegotiator
    renegotiator = accounts[9]

    lender = accounts[0]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

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

    flex_core.accept_renegotiation(loan_id, my_custom_id, sender=lender)

    # asserts
    assert flex_core.loan_details(loan_id)["borrower"] == renegotiator.address
    assert flex_core.loan_details(loan_id)["lender"] == accounts[0].address
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
    assert flex_core.loan_details(loan_id)["borrow_amount"] == 200000000000000000000
    assert flex_core.loan_details(loan_id)["time_limit"] == True
    assert flex_core.loan_details(loan_id)["time_amount"] == new_renegotited_time_limit
    assert flex_core.loan_details(loan_id)["collateral_type"] == empty_address
    assert flex_core.loan_details(loan_id)["collateral_deposited"] == 0
    assert flex_core.loan_details(loan_id)["principal_type"] == flex_token.address
    assert flex_core.loan_details(loan_id)["current_debt"] == 0
    assert flex_core.loan_details(loan_id)["access_control"] == False
    assert flex_core.loan_details(loan_id)["state"] == flex_core.proposed()
    assert flex_core.loan_details(loan_id)["loan_type"] == 0


# TEST CASE 6 - Push renegotiation chat
def test_push_renegotiation_chat_reverts_if_renegotitaion_does_not_exist(
    flex_contract_with_proposed_lender_loan, accounts
):
    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 1
    my_custom_id = "franfran"
    hashed_id = Web3.keccak(text=my_custom_id)
    test_messsage_uri = "https://fake-message-uri.ipfs-and-stuff.json"

    with ape.reverts("Re-Negotiation Does Not Exist"):
        flex_core.push_renegotiation_chat(
            loan_id, my_custom_id, test_messsage_uri, sender=accounts[0]
        )


def test_only_loan_owner_and_renegotiator_can_communicate(
    flex_contract_with_proposed_lender_loan, accounts
):
    # renegotiator
    renegotiator = accounts[9]
    lender = accounts[0]

    # flex contract and token
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

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


#  TEST CASE 7 - Accept Loan Terms
def test_accept_loan_reverts_when_msg_sender_is_loan_owner(
    proposed_loan_with_recipient, accounts
):
    # flex contract and token
    flex_core, flex_token = proposed_loan_with_recipient
    lender = accounts[0]
    borrower = accounts[5]

    # test params
    loan_id = 1

    # expect revert: loan owner cant accept his own loan
    with ape.reverts("You Cant Accept Your Loan"):
        flex_core.accept_loan_terms(loan_id, 0, sender=lender)


def test_state_of_loan_is_changed_to_accepted(proposed_loan_with_recipient, accounts):
    # flex contract and token
    flex_core, flex_token = proposed_loan_with_recipient
    borrower = accounts[5]

    # test params
    loan_id = 1
    collateralized_amount = 150 * 10**18

    # accept loan terms
    flex_core.accept_loan_terms(
        loan_id, 0, sender=borrower, value=collateralized_amount
    )

    assert flex_core.loan_details(loan_id)["state"] == flex_core.accepted()


def test_accept_loan_reverts_if_collateral_deposited_is_less_than_required(
    flex_contract_with_proposed_lender_loan, accounts
):
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    borrower = accounts[8]
    loan_id = 1
    under_collateralized_amount = 149 * 10**18

    with ape.reverts("Insufficient Collateral Deposit"):
        flex_core.accept_loan_terms(
            loan_id, 0, sender=borrower, value=under_collateralized_amount
        )


def test_accept_loan_terms_transfers_the_principal_to_borrower_and_updates_debt(
    flex_contract_with_proposed_lender_loan, accounts
):
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    borrower = accounts[8]
    loan_id = 1
    collateralized_amount = 150 * 10**18
    expected_debt = 208 * 10**18
    tokens_borrower_received = 200 * 10**18

    # accept loan
    flex_core.accept_loan_terms(
        loan_id, 0, sender=borrower, value=collateralized_amount
    )

    # asserts
    assert flex_core.loan_details(loan_id)["current_debt"] == expected_debt
    assert (
        flex_core.loan_details(loan_id)["collateral_deposited"] == collateralized_amount
    )
    assert flex_token.balanceOf(borrower.address) == tokens_borrower_received


def test_accept_loan_updates_the_time_limit_mapping_if_time_set(
    flex_contract_with_proposed_lender_loan, accounts
):
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    borrower = accounts[8]
    loan_id = 1
    collateralized_amount = 150 * 10**18
    expected_debt = 208 * 10**18
    loan_end_date = (
        chain.pending_timestamp + flex_core.loan_details(loan_id)["time_amount"]
    )

    # accept loan
    flex_core.accept_loan_terms(
        loan_id, 0, sender=borrower, value=collateralized_amount
    )

    # asserts
    assert flex_core.loan_timers(loan_id) == loan_end_date


#  TEST CASE 8 - Propose New Terms After Acceptance
def test_propose_new_terms_reverts_when_specified_loan_isnt_in_accepted_state(
    flex_contract_with_proposed_lender_loan, accounts
):
    # get account
    lender = accounts[0]

    # get contracts
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 1
    new_margin_cutoff = 120
    new_fixed_interest_rate = 6
    new_time_amount = 10000

    # propose new terms
    with ape.reverts("Loan ! Accepted State"):
        flex_core.propose_new_terms_after_acceptance(
            loan_id,
            new_margin_cutoff,
            new_fixed_interest_rate,
            new_time_amount,
            sender=lender,
        )


def test_propose_new_terms_reverts_When_proposer_is_not_lender_or_borrower(
    accepted_lender_loan, accounts
):
    # get account
    lender = accounts[0]
    non_borrower_or_lender = accounts[5]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    new_margin_cutoff = 120
    new_fixed_interest_rate = 6
    new_time_amount = 10000

    # propose new terms
    with ape.reverts("! Permission To Propose"):
        flex_core.propose_new_terms_after_acceptance(
            loan_id,
            new_margin_cutoff,
            new_fixed_interest_rate,
            new_time_amount,
            sender=non_borrower_or_lender,
        )


def test_loan_proposal_was_updated_for_proposer_and_is_active(
    accepted_lender_loan, accounts
):
    # get account
    lender = accounts[0]
    borrower = accounts[9]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    new_margin_cutoff = 120
    new_fixed_interest_rate = 6
    new_time_amount = 10000

    prev_coll_ratio = 150
    prev_borr_amount = 200 * 10**18
    collateral_deposited = 150 * 10**18
    debt = 208 * 10**18
    lender_loan_type = 0

    # propose new terms
    flex_core.propose_new_terms_after_acceptance(
        loan_id,
        new_margin_cutoff,
        new_fixed_interest_rate,
        new_time_amount,
        sender=lender,
    )

    lender_proposal = flex_core.lender_proposal()

    # assert
    assert flex_core.loan_proposals(loan_id, lender_proposal)["borrower"] == borrower
    assert flex_core.loan_proposals(loan_id, lender_proposal)["lender"] == lender
    assert (
        flex_core.loan_proposals(loan_id, lender_proposal)["margin_cutoff"]
        == new_margin_cutoff
    )
    assert (
        flex_core.loan_proposals(loan_id, lender_proposal)["collateral_ratio"]
        == prev_coll_ratio
    )
    assert (
        flex_core.loan_proposals(loan_id, lender_proposal)["fixed_interest_rate"]
        == new_fixed_interest_rate
    )
    assert (
        flex_core.loan_proposals(loan_id, lender_proposal)["borrow_amount"]
        == prev_borr_amount
    )
    assert flex_core.loan_proposals(loan_id, lender_proposal)["time_limit"] == True
    assert (
        flex_core.loan_proposals(loan_id, lender_proposal)["time_amount"]
        == new_time_amount
    )
    assert (
        flex_core.loan_proposals(loan_id, lender_proposal)["collateral_type"]
        == empty_address
    )
    assert (
        flex_core.loan_proposals(loan_id, lender_proposal)["collateral_deposited"]
        == collateral_deposited
    )
    assert (
        flex_core.loan_proposals(loan_id, lender_proposal)["principal_type"]
        == project.flexToken.deployments[-1]
    )
    assert flex_core.loan_proposals(loan_id, lender_proposal)["current_debt"] == debt
    assert flex_core.loan_proposals(loan_id, lender_proposal)["access_control"] == False
    assert (
        flex_core.loan_proposals(loan_id, lender_proposal)["state"]
        == flex_core.accepted()
    )
    assert (
        flex_core.loan_proposals(loan_id, lender_proposal)["loan_type"]
        == lender_loan_type
    )

    # assert loan proposal tracker
    assert flex_core.loan_proposal_tracker(loan_id, lender_proposal) == True


# Test Case 9 - Accept New Proposal For Loan After Acceptance
def test_accept_new_proposal_reverts_when_acceptor_isnt_lender_or_borrower(
    accepted_lender_loan, accounts
):
    # get accounts
    lender = accounts[0]
    borrower = accounts[9]
    non_lender_or_borrower = accounts[5]

    # get contracts
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    new_margin_cutoff = 120
    new_fixed_interest_rate = 6
    new_time_amount = 10000

    # propose new terms
    flex_core.propose_new_terms_after_acceptance(
        loan_id,
        new_margin_cutoff,
        new_fixed_interest_rate,
        new_time_amount,
        sender=lender,
    )

    # expect revert
    with ape.reverts("! Access"):
        flex_core.accept_new_proposal(loan_id, sender=non_lender_or_borrower)


def test_accept_new_proposal_reverts_if_the_proposal_does_not_exist(
    accepted_lender_loan, accounts
):
    # get accounts
    borrower = accounts[9]

    # get contracts
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1

    # expect revert
    with ape.reverts("No Proposal To Accept"):
        flex_core.accept_new_proposal(loan_id, sender=borrower)


def test_accept_new_proposal_modifies_original_loan_details(
    accepted_lender_loan, accounts
):
    # get accounts
    lender = accounts[0]
    borrower = accounts[9]

    # get contracts
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    new_margin_cutoff = 120
    new_fixed_interest_rate = 6
    new_time_amount = 10000

    prev_coll_ratio = 150
    prev_borr_amount = 200 * 10**18
    collateral_deposited = 150 * 10**18
    debt = 208 * 10**18
    lender_loan_type = 0

    # propose new terms
    flex_core.propose_new_terms_after_acceptance(
        loan_id,
        new_margin_cutoff,
        new_fixed_interest_rate,
        new_time_amount,
        sender=lender,
    )

    # borrower accepts the new terms
    flex_core.accept_new_proposal(loan_id, sender=borrower)

    # asserts
    # asserts
    assert flex_core.loan_details(loan_id)["borrower"] == borrower.address
    assert flex_core.loan_details(loan_id)["lender"] == lender.address
    assert flex_core.loan_details(loan_id)["margin_cutoff"] == new_margin_cutoff
    assert flex_core.loan_details(loan_id)["collateral_ratio"] == prev_coll_ratio
    assert (
        flex_core.loan_details(loan_id)["fixed_interest_rate"]
        == new_fixed_interest_rate
    )
    assert flex_core.loan_details(loan_id)["borrow_amount"] == prev_borr_amount
    assert flex_core.loan_details(loan_id)["time_limit"] == True
    assert flex_core.loan_details(loan_id)["time_amount"] == new_time_amount
    assert flex_core.loan_details(loan_id)["collateral_type"] == empty_address
    assert (
        flex_core.loan_details(loan_id)["collateral_deposited"] == collateral_deposited
    )
    assert (
        flex_core.loan_details(loan_id)["principal_type"]
        == project.flexToken.deployments[-1]
    )
    assert flex_core.loan_details(loan_id)["current_debt"] == debt
    assert flex_core.loan_details(loan_id)["access_control"] == False
    assert flex_core.loan_details(loan_id)["state"] == flex_core.accepted()
    assert flex_core.loan_details(loan_id)["loan_type"] == lender_loan_type


# TEST CASE 10 - Repay Loan
def test_on_repay_loan_the_principal_is_transferred_back_to_the_lender(
    accepted_lender_loan, accounts
):
    # anyone can repay loan
    non_borrower_or_lender = accounts[4]
    borrower = accounts[9]
    lender = accounts[0]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    repay_amount = 208 * 10**18

    # approvce contract repay amount
    flex_token = project.flexToken.deployments[-1]

    flex_token.mint(
        non_borrower_or_lender.address, repay_amount, sender=non_borrower_or_lender
    )
    flex_token.approve(flex_core.address, repay_amount, sender=non_borrower_or_lender)

    # prev lender balance
    prev_lender_bal = flex_token.balanceOf(lender.address)

    # repay loan principal(flex token)
    flex_core.repay_loan(loan_id, sender=non_borrower_or_lender)

    assert flex_token.balanceOf(lender.address) == prev_lender_bal + repay_amount


def test_on_repay_loan_state_changes_to_fulfilled_and_debt_zeros(
    accepted_lender_loan, accounts
):
    # anyone can repay loan
    non_borrower_or_lender = accounts[4]
    borrower = accounts[9]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    repay_amount = 208 * 10**18

    # approvce contract repay amount
    flex_token = project.flexToken.deployments[-1]

    flex_token.mint(
        non_borrower_or_lender.address, repay_amount, sender=non_borrower_or_lender
    )
    flex_token.approve(flex_core.address, repay_amount, sender=non_borrower_or_lender)

    # repay loan principal(flex token)
    flex_core.repay_loan(loan_id, sender=non_borrower_or_lender)

    assert flex_core.loan_details(loan_id)["state"] == flex_core.fulfilled()
    assert flex_core.loan_details(loan_id)["current_debt"] == 0


# TEST CASE 11 - Liquidate Loan
def test_liquidate_loan_reverts_if_loan_state_is_not_accepted(
    flex_contract_with_proposed_lender_loan, accounts
):
    # get account
    liquidator = accounts[7]

    # get the contract
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 1

    # expect revert
    with ape.reverts("Loan State ! Liquidatable"):
        flex_core.liquidate_loan(loan_id, sender=liquidator)


def test_liquidate_loan_reverts_when_time_hasnt_been_exceeded(
    accepted_lender_loan, accounts
):
    # get account
    liquidator = accounts[7]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1

    # liquidate loan reverts
    with ape.reverts("Time ! Exceeded"):
        flex_core.liquidate_loan(loan_id, sender=liquidator)


def test_liquidation_reverts_when_there_is_no_time_limit_and_loan_is_still_over_collateralized(
    accepted_loan_without_time_limit, accounts
):
    # get account
    liquidator = accounts[7]

    # get contract
    flex_core = accepted_loan_without_time_limit

    # test params
    loan_id = 1

    # liquidate loan reverts
    with ape.reverts("Loan ! Liquidatable"):
        flex_core.liquidate_loan(loan_id, sender=liquidator)


def test_liquidate_loan_gives_liquidator_2_percent_of_collateral(
    accepted_lender_loan, accounts
):
    # accounts
    acct = accounts[0]
    liquidator = accounts[0]

    # get contract
    flex_core = accepted_lender_loan

    # manipulate the price of collateral to drop(FTM) to drop to 2 usd
    ftm_usd_price_feed = project.MockV3Aggregator.deployments[0]
    ftm_usd_price_feed.updateAnswer(2 * 10**8, sender=acct)

    # test params
    loan_id = 1

    # collateral value then drops from 450usd to 300 usd
    # principal price doesnt change - debt valued at 312 usd - debt
    # borrower had to maintain a 130% difference between debt and collateral
    # the 300 usd is now far lesser than the 312 usd debt. This loan can be liquidated

    prev_liquidator_balance = liquidator.balance

    chain.pending_timestamp += 10000

    flex_core.liquidate_loan(loan_id, sender=liquidator)

    assert liquidator.balance > prev_liquidator_balance


def test_collateral_is_given_to_the_lender_in_a_liquidation(
    accepted_lender_loan, accounts
):
    # accounts
    lender = accounts[0]
    liquidator = accounts[7]

    # get contract
    flex_core = accepted_lender_loan

    # manipulate the pric of collateral to drop(FTM) to drop to 2 usd
    ftm_usd_price_feed = project.MockV3Aggregator.deployments[0]
    ftm_usd_price_feed.updateAnswer(2 * 10**8, sender=lender)

    # test params
    loan_id = 1

    prev_lender_balance = lender.balance
    expected_increase = 147 * 10**18

    chain.pending_timestamp += 10000

    flex_core.liquidate_loan(loan_id, sender=liquidator)

    # assert
    assert lender.balance == prev_lender_balance + expected_increase


def test_liquidation_occurs_when_time_limit_is_up(accepted_lender_loan, accounts):
    # accounts
    lender = accounts[0]
    liquidator = accounts[7]

    # get contract
    flex_core = accepted_lender_loan

    # move time

    # test params
    loan_id = 1
    chain.pending_timestamp += 100000

    prev_lender_balance = lender.balance
    expected_increase = 147 * 10**18

    flex_core.liquidate_loan(loan_id, sender=liquidator)

    # assert
    assert lender.balance == prev_lender_balance + expected_increase


#  TEST CASE 12 - Buyout Loan
def test_propose_loan_buyout_reverts_if_loan_isnt_in_accepted_state(
    flex_contract_with_proposed_lender_loan, accounts
):
    # get account
    buyout_proposer = accounts[6]

    # get contract
    flex_core, flex_token = flex_contract_with_proposed_lender_loan

    # test params
    loan_id = 1
    buyout_amount = 205 * 10**18

    # expect revert
    with ape.reverts("Loan ! Accepted State"):
        flex_core.propose_loan_buyout(loan_id, buyout_amount, sender=buyout_proposer)


def test_propose_loan_buyout_reverts_when_sender_is_lender(
    accepted_lender_loan, accounts
):
    # get account
    buyout_proposer = accounts[6]
    lender = accounts[0]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    buyout_amount = 205 * 10**18

    # expect revert
    with ape.reverts("You Cant Buy Your Own Loan"):
        flex_core.propose_loan_buyout(loan_id, buyout_amount, sender=lender)


def test_propose_loan_buyout_reverts_when_there_is_an_initial_proposal_taht_Wasnt_canceled(
    accepted_lender_loan, accounts
):
    # get account
    buyout_proposer = accounts[6]
    lender = accounts[0]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    buyout_amount = 205 * 10**18

    # mint and approve tokens to contract
    flex_token = project.flexToken.deployments[-1]
    flex_token.mint(buyout_proposer.address, buyout_amount, sender=buyout_proposer)
    flex_token.approve(flex_core.address, buyout_amount, sender=buyout_proposer)

    # propose
    flex_core.propose_loan_buyout(loan_id, buyout_amount, sender=buyout_proposer)

    # propose again
    # expect revert
    with ape.reverts("Cancel Initial Buyout"):
        flex_core.propose_loan_buyout(loan_id, buyout_amount, sender=buyout_proposer)


def test_loan_buyout_mapping_gets_updated_accordingly(accepted_lender_loan, accounts):
    # get account
    buyout_proposer = accounts[6]
    lender = accounts[0]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    buyout_amount = 205 * 10**18

    # mint and approve tokens to contract
    flex_token = project.flexToken.deployments[-1]
    flex_token.mint(buyout_proposer.address, buyout_amount, sender=buyout_proposer)
    flex_token.approve(flex_core.address, buyout_amount, sender=buyout_proposer)

    # propose
    flex_core.propose_loan_buyout(loan_id, buyout_amount, sender=buyout_proposer)

    # asserts
    assert flex_core.loan_buyouts(loan_id, buyout_proposer.address) == buyout_amount


# TEST CASE 13 - Cancel Loan Buyout
def test_cancel_loan_buyout_must_exist_to_be_canceled(accepted_lender_loan, accounts):
    # get account
    buyout_proposer = accounts[6]
    lender = accounts[0]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    buyout_amount = 205 * 10**18

    # expect revert
    with ape.reverts("No Initial Buyout Or Accepted"):
        flex_core.cancel_loan_buyout(loan_id, sender=buyout_proposer)


def test_cancel_loan_buyout_returns_proposers_initial_Depositand_resets_buyout_mapping_to_zero(
    accepted_lender_loan, accounts
):
    # get account
    buyout_proposer = accounts[6]
    lender = accounts[0]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    buyout_amount = 205 * 10**18

    # mint and approve tokens to contract
    flex_token = project.flexToken.deployments[-1]
    flex_token.mint(buyout_proposer.address, buyout_amount, sender=buyout_proposer)
    flex_token.approve(flex_core.address, buyout_amount, sender=buyout_proposer)

    # propose
    flex_core.propose_loan_buyout(loan_id, buyout_amount, sender=buyout_proposer)

    # cancel loan buyout
    flex_core.cancel_loan_buyout(loan_id, sender=buyout_proposer)

    # asserts
    assert flex_token.balanceOf(buyout_proposer.address) == buyout_amount
    assert flex_core.loan_buyouts(loan_id, buyout_proposer.address) == 0


# TEST CASE 13 - Accept Loan Buyout
def test_accept_loan_buyout_reverts_if_msgsender_is_not_loan_lender(
    accepted_lender_loan, accounts
):
    # get account
    buyout_proposer = accounts[6]
    lender = accounts[0]
    non_lender = accounts[7]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    buyout_amount = 205 * 10**18

    # mint and approve tokens to contract
    flex_token = project.flexToken.deployments[-1]
    flex_token.mint(buyout_proposer.address, buyout_amount, sender=buyout_proposer)
    flex_token.approve(flex_core.address, buyout_amount, sender=buyout_proposer)

    # propose
    flex_core.propose_loan_buyout(loan_id, buyout_amount, sender=buyout_proposer)

    # expect revert
    with ape.reverts("!Permission To Accept Buyout"):
        flex_core.accept_loan_buyout(
            loan_id, buyout_proposer.address, sender=non_lender
        )


def test_accept_loan_buyout_transfer_buyout_amount_to_lender(
    accepted_lender_loan, accounts
):
    # get account
    buyout_proposer = accounts[6]
    lender = accounts[0]
    non_lender = accounts[7]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    buyout_amount = 205 * 10**18

    # mint and approve tokens to contract
    flex_token = project.flexToken.deployments[-1]
    flex_token.mint(buyout_proposer.address, buyout_amount, sender=buyout_proposer)
    flex_token.approve(flex_core.address, buyout_amount, sender=buyout_proposer)

    # propose
    flex_core.propose_loan_buyout(loan_id, buyout_amount, sender=buyout_proposer)

    prev_lender_balance = flex_token.balanceOf(lender.address)

    # accept loan buyout
    flex_core.accept_loan_buyout(loan_id, buyout_proposer.address, sender=lender)

    assert flex_token.balanceOf(lender.address) == prev_lender_balance + buyout_amount


def test_accept_loan_buyout_changes_the_loan_lender_to_the_buyout_proposer(
    accepted_lender_loan, accounts
):
    # get account
    buyout_proposer = accounts[6]
    lender = accounts[0]
    non_lender = accounts[7]

    # get contract
    flex_core = accepted_lender_loan

    # test params
    loan_id = 1
    buyout_amount = 205 * 10**18

    # mint and approve tokens to contract
    flex_token = project.flexToken.deployments[-1]
    flex_token.mint(buyout_proposer.address, buyout_amount, sender=buyout_proposer)
    flex_token.approve(flex_core.address, buyout_amount, sender=buyout_proposer)

    # propose
    flex_core.propose_loan_buyout(loan_id, buyout_amount, sender=buyout_proposer)

    # accept loan buyout
    flex_core.accept_loan_buyout(loan_id, buyout_proposer.address, sender=lender)

    assert flex_core.loan_details(loan_id)["lender"] == buyout_proposer.address


# /////////// LENDER LOAN WITH COLLATERAL AS ERC20 AND PRINCIPAL AS NATIVE ASSET /////
# MAIN FUNCTION TO TEST FOR
# 1. Accept Loan [DONE]
# 2. Liquidate Loan [DONE]
# 3. Repay Loan [DONE]


# TEST CASE 15 - Accept Loan Terms (Collateral as erc20)
def test_accept_loan_reverts_if_collateral_deposited_is_less_than_required_with_collateral_as_erc20(
    proposed_lender_loan_with_collateral_as_erc20, accounts
):
    flex_core, flex_token = proposed_lender_loan_with_collateral_as_erc20

    acct = accounts[0]

    # test params
    borrower = accounts[8]
    loan_id = 1
    under_collateralized_amount = 598 * 10**18

    # prepping borrower
    flex_token.mint(borrower.address, under_collateralized_amount, sender=acct)
    flex_token.approve(flex_core.address, under_collateralized_amount, sender=borrower)

    with ape.reverts("Insufficient Collateral Deposit"):
        flex_core.accept_loan_terms(
            loan_id, under_collateralized_amount, sender=borrower
        )


def test_accept_loan_terms_transfers_the_principal_to_borrower_and_updates_debt_with_erc20_collateral(
    proposed_lender_loan_with_collateral_as_erc20, accounts
):
    flex_core, flex_token = proposed_lender_loan_with_collateral_as_erc20

    # test params
    acct = accounts[0]
    borrower = accounts[8]
    loan_id = 1
    collateralized_amount = 600 * 10**18
    expected_debt = 208 * 10**18
    native_asset_borrower_received = 200 * 10**18

    # prepping borrower
    flex_token.mint(borrower.address, collateralized_amount, sender=acct)
    flex_token.approve(flex_core.address, collateralized_amount, sender=borrower)

    # prev bal
    prev_borrower_bal = borrower.balance

    # accept loan
    tx = flex_core.accept_loan_terms(loan_id, collateralized_amount, sender=borrower)

    # asserts
    assert flex_core.loan_details(loan_id)["current_debt"] == expected_debt
    assert (
        flex_core.loan_details(loan_id)["collateral_deposited"] == collateralized_amount
    )
    assert (
        borrower.balance + tx.total_fees_paid
        == native_asset_borrower_received + prev_borrower_bal
    )


# TEST CASE 16 - Liquidate Loan (Collateral as erc20)
def test_liquidate_loan_gives_liquidator_2_percent_of_collateral_with_collateral_as_erc20(
    accepted_lender_loan_with_collateral_as_erc20, accounts
):
    # accounts
    acct = accounts[0]
    liquidator = accounts[7]

    # get contract
    flex_core = accepted_lender_loan_with_collateral_as_erc20

    # manipulate the pric of collateral (Flex) to drop to 1.35 usd
    flex_usd_price_feed = project.MockV3Aggregator.deployments[1]
    flex_usd_price_feed.updateAnswer(int(1.35 * 10**8), sender=acct)

    # test params
    loan_id = 1

    # collateral value then drops from 900usd to 810 usd usd (price dropped to 1.35 usd)
    # principal price doesnt change - debt valued at 624 usd - debt
    # borrower had to maintain a 130% difference between debt and collateral
    # the 810 usd is now far lesser than the 811.2 usd debt. This loan can be liquidated

    flex_token = project.flexToken.deployments[-1]
    prev_liquidator_balance = flex_token.balanceOf(liquidator.address)

    chain.pending_timestamp += 10000

    flex_core.liquidate_loan(loan_id, sender=liquidator)

    assert (
        flex_token.balanceOf(liquidator.address)
        == 12 * 10**18 + prev_liquidator_balance
    )


def test_collateral_is_given_to_the_lender_in_a_liquidation_with_collateral_as_erc20(
    accepted_lender_loan_with_collateral_as_erc20, accounts
):
    # accounts
    lender = accounts[0]
    liquidator = accounts[7]

    # get contract
    flex_core = accepted_lender_loan_with_collateral_as_erc20

    # collateral value then drops from 900usd to 810 usd usd (price dropped to 1.35 usd)
    # principal price doesnt change - debt valued at 624 usd - debt
    # borrower had to maintain a 130% difference between debt and collateral
    # the 810 usd is now far lesser than the 811.2 usd debt. This loan can be liquidated

    flex_usd_price_feed = project.MockV3Aggregator.deployments[1]
    flex_usd_price_feed.updateAnswer(int(1.35 * 10**8), sender=lender)

    # test params
    loan_id = 1
    flex_token = project.flexToken.deployments[-1]

    prev_lender_balance = flex_token.balanceOf(lender.address)
    expected_increase = 588 * 10**18

    chain.pending_timestamp += 10000

    flex_core.liquidate_loan(loan_id, sender=liquidator)

    # assert
    assert (
        flex_token.balanceOf(lender.address) == prev_lender_balance + expected_increase
    )


# TEST CASE 17 - Repay Loan (Collateral as erc20)
def test_on_repay_loan_the_principal_is_transferred_back_to_the_lender_with_collateral_as_erc20(
    accepted_lender_loan_with_collateral_as_erc20, accounts
):
    # anyone can repay loan
    non_borrower_or_lender = accounts[4]
    borrower = accounts[9]
    lender = accounts[0]

    # get contract
    flex_core = accepted_lender_loan_with_collateral_as_erc20

    # test params
    loan_id = 1
    repay_amount = 208 * 10**18

    # prev bal
    prev_lender_bal = lender.balance

    # repay loan principal(flex token)
    flex_core.repay_loan(loan_id, sender=non_borrower_or_lender, value=repay_amount)

    assert lender.balance == prev_lender_bal + repay_amount


def test_on_repay_loan_satte_changes_to_fulfilled_and_debt_zeros_with_collateral_as_erc20(
    accepted_lender_loan_with_collateral_as_erc20, accounts
):
    # anyone can repay loan
    non_borrower_or_lender = accounts[4]
    borrower = accounts[9]

    # get contract
    flex_core = accepted_lender_loan_with_collateral_as_erc20

    # test params
    loan_id = 1
    repay_amount = 208 * 10**18

    # flex token
    flex_token = project.flexToken.deployments[-1]

    # prev bal
    prev_borrower_bal = flex_token.balanceOf(borrower.address)

    # repay loan principal(ftm)
    flex_core.repay_loan(loan_id, sender=non_borrower_or_lender, value=repay_amount)

    assert flex_core.loan_details(loan_id)["state"] == flex_core.fulfilled()
    assert flex_core.loan_details(loan_id)["current_debt"] == 0
