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


def get_loan_states():
    flex_core = chain.contracts.get_deployments(project.flexCore)[-1]

    print("Proposed State", flex_core.proposed().hex())
    print("Accepted State", flex_core.accepted().hex())
    print("Fulfilled State", flex_core.fulfilled().hex())
    print("Deactivated State", flex_core.deactivated().hex())


def get_proposals():
    flex_core = chain.contracts.get_deployments(project.flexCore)[-1]

    print("lender proposal: ", flex_core.lender_proposal().hex())
    print("borrower proposal: ", flex_core.borrower_proposal().hex())


def get_loan_details_by_id():
    flex_core = chain.contracts.get_deployments(project.flexCore)[-1]

    print("Loan Details: ", flex_core.get_loan_Details_by_id(9))


def get_renegotiated_loan_by_its_id():
    flex_core = chain.contracts.get_deployments(project.flexCore)[-1]

    print("Loan Details: ", flex_core.get_renegotiated_loan_by_its_id(8, "Chris"))


def calulate_require_loan_principal_or_collateral_for_renegotiation_acceptance():
    flex_core = chain.contracts.get_deployments(project.flexCore)[-1]

    print(
        "Loan Details: ",
        flex_core.calulate_require_loan_principal_or_collateral_for_renegotiation_acceptance(
            8, "Chris"
        ),
    )


def main():
    get_loan_details_by_id()
