# @version 0.3.7


struct Loan:
    borrower: address 
    lender: address 
    margin_cutoff: uint256 
    collateral_ratio: uint256 
    fixed_interest_rate: uint256 
    borrow_amount: uint256 
    time_limit: bool
    time_amount: uint256 
    collateral_type: address 
    collateral_deposited: uint256 
    principal_type: address
    current_debt: uint256  
    access_control: bool 
    state: bytes32 
    loan_type: uint256

@external
@view
def loan_acceptance_calculations(collateral_price: uint256, principal_price: uint256, selected_loan: Loan) -> (uint256, uint256):
    
    over_collateralized_amount: uint256 = 0
    estimated_principle: uint256 = 0

    # ////////  FOR LENDER LOAN   ////////
    if selected_loan.loan_type == 0:
        principal_amount: uint256 = selected_loan.borrow_amount

        principal_amount_in_usd: uint256 = ((principal_amount * principal_price) / 10**18) 

        over_collateralized_principal_usd_amount: uint256 = (principal_amount_in_usd * selected_loan.collateral_ratio) / 100

        over_collateralized_amount = (over_collateralized_principal_usd_amount * 10**18) / collateral_price


    # /////////  FOR BORROWER LOAN   //////////
    if selected_loan.loan_type == 1:
        collateral_deposited: uint256 = selected_loan.collateral_deposited
        interest_to_be_paid: uint256 = (selected_loan.fixed_interest_rate * collateral_deposited) / 100

        
        total_collateral_deposited: uint256 = collateral_deposited - interest_to_be_paid
        total_collateral_deposited_in_usd: uint256 = (total_collateral_deposited * collateral_price) / 10**18

        estimated_principle_in_usd: uint256 = (total_collateral_deposited_in_usd / selected_loan.collateral_ratio) * 100

        estimated_principle = (estimated_principle_in_usd * 10**18) / principal_price

    return over_collateralized_amount, estimated_principle