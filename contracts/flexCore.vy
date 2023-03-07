# @version 0.3.7 

# INTERFACES

from vyper.interfaces import ERC20

interface AggregatorV3Interface:
    def latestRoundData() -> (uint80, int256, uint256,  uint256, uint80): view

interface flexCalc:
    def loan_acceptance_calculations(collateral_price: uint256, principal_price: uint256, selected_loan: Loan) -> (uint256, uint256): view


# FLEX CORE

# Loan Details
struct Loan:
    borrower: address 
    lender: address 
    margin_cutoff: uint256 # the liquidation threshold percentage
    collateral_ratio: uint256 # the percentage amount of money the borrower can take based on his collateral to always keep him afloat
    fixed_interest_rate: uint256 # interest on loan repay
    borrow_amount: uint256 # max amount lender is willing to pay
    time_limit: bool # activate time limit liquidation
    time_amount: uint256 # set amount of time
    collateral_type: address # accepted collateral for loan
    collateral_deposited: uint256 # collateral deposited by borrower
    principal_type: address
    current_debt: uint256  # amount currently owed by the borrower
    access_control: bool # public or private loan
    state: bytes32 # state of the loan
    loan_type: uint256


# STATE VARIABLES 

# deployer
owner: public(address)
# flex calc
flex_calc: public(address)

# loan id counter
loan_counter: public(uint256)
# Loan types
lender_loan: public(uint256)
borrower_loan: public(uint256)
# liquidation fee
LIQUIDATION_FEE: constant(uint256) = 2

# Loan States
proposed: public(bytes32)
accepted: public(bytes32)
fulfilled: public(bytes32)
deactivated: public(bytes32)
# loan proposal types
borrower_proposal: public(bytes32)
lender_proposal: public(bytes32)


# loan id to details
loan_details:  public(HashMap[uint256, Loan])
# time tracker
loan_timers: public(HashMap[uint256, uint256])
# loan existence tracker
loan_existence_tracker: public(HashMap[uint256, bool])
# loan renegotiations
loan_renegotiations: public(HashMap[uint256, HashMap[bytes32, Loan]])
# renegotiation ID tracker
loan_renegotiation_id_tracker: public(HashMap[uint256, HashMap[bytes32, address]])
# loan proposals
loan_proposals: public(HashMap[uint256, HashMap[bytes32, Loan]])
# loan proposal tracker
loan_proposal_tracker: public(HashMap[uint256, HashMap[bytes32, bool]])
# supported assets
supported_assets: public(HashMap[address, bool])
# supported assets to price feed
supported_assets_pricefeed: public(HashMap[address, address])
# asset to price feeds
price_feeds: public(HashMap[address, address])
# loan buyout
loan_buyouts: public(HashMap[uint256, HashMap[address, uint256]])



# EVENTS
event LoanProposed:
    loan_id: uint256
    loan_info: Loan

event LoanRenegotiated:
    loan_id: uint256
    user_custom_id: String[30]
    renegotiaited_loan_id: bytes32
    renegotiaited_loan_info: Loan

event LoanTermsChanged:
    loan_id: uint256
    loan_info: Loan

event RenegotiationTermsChanged:
    loan_id: uint256
    user_custom_id: String[30]
    renegotiaited_loan_id: bytes32
    renegotiaited_loan_info: Loan

event LoanAccepted :
    loan_id: uint256
    loan: Loan

event ChatPushed:
    loan_id: uint256
    user_custom_id: String[30]
    renegotiaited_loan_id: bytes32
    messageURI: String[500]
    lender_or_borrower: uint256 # 0 -lender and 1 for borrower

event LoanReNegotiationAccepted:
    loan_id: uint256
    user_custom_id: String[30]
    renegotiaited_loan_id: bytes32
    renegotiaited_loan_info: Loan

event ProposalPushed:
    loan_id: uint256
    proposer_type: bytes32
    proposal_details: Loan

event ProposalAccepted:
    loan_id: uint256
    proposal_accepted: bytes32
    proposal_details: Loan

event LoanRepaid:
    loan_id: uint256
    loan_details: Loan

event LoanLiquidated:
    loan_id: uint256
    loan_details: Loan

event BuyoutProposed:
    loan_id: uint256
    buyer: address
    buyout_amount: uint256

event BuyOutCanceled:
    loan_id: uint256
    buyer: address
    buyout_amount: uint256

event LoanDeactivated:
    loan_id: uint256
    loan_Details: Loan

event LoanBought:
    loan_id: uint256
    buyer: address
    buyout_amount: uint256

event CollateralTopUp:
    loan_id: uint256
    amount: uint256
    
# constructor
@external
def __init__(_flex_calc: address): 
    # LOAN STATES
    self.proposed = keccak256("PROPOSED")
    self.accepted =  keccak256("ACCEPTED")
    self.fulfilled = keccak256("FULFILLED")
    self.deactivated = keccak256("DEACTIVATED")

    # LOAN TYPES
    self.lender_loan = 0
    self.borrower_loan =  1

    # LOAN PROPOSAL TYPES
    self.borrower_proposal = keccak256("BORROWER_PROPOSAL")
    self.lender_proposal = keccak256("LENDER_PROPOSAL")

    # INITIALIZE THE FLEX CALC
    self.flex_calc = _flex_calc

    self.owner = msg.sender
    self.supported_assets[empty(address)] = True
   


@external 
@payable
def propose_loan(_margin_cutoff: uint256, _collateral_ratio: uint256, _fixed_intererst_rate: uint256, _borrow_amount: uint256, _time_limit: bool, _time_amount: uint256, _collateral_type: address, _principal_type: address, _access_control: bool, _recipient: address, _loan_type: uint256, _collateral_deposit: uint256):
    # increment Loan ID
    loan_id: uint256 =  self.loan_counter
    loan_id += 1
    self.loan_counter = loan_id

    # Set Time If True
    _time_amount_set: uint256 = 0
    if _time_limit:
        _time_amount_set = _time_amount

    # deciding parameters
    actual_lender: address = empty(address)
    actual_borrower: address = empty(address)
    deposited_collateral: uint256 = 0
    borrow_amount: uint256 = 0

    # validate loan type
    if _loan_type not in [self.lender_loan, self.borrower_loan]:
        raise "Loan Type Does Not Exist"

    # check asset support
    if not self.supported_assets[_collateral_type] or not self.supported_assets[_principal_type]:
            raise "An Asset Is Not Supported"

    # Set borrower and lender accordingly
    if _loan_type == self.lender_loan:
        actual_lender = msg.sender
        borrow_amount = _borrow_amount
        # collect the asset from the lender and keep in contract
        self._collectDeposit(_principal_type, borrow_amount, msg.value, msg.sender)
        if _access_control:
            actual_borrower = _recipient
        else :
            actual_borrower = empty(address)

    if _loan_type == self.borrower_loan:
        actual_borrower = msg.sender
        # collect collateral deposit from borrower
        self._collectDeposit(_collateral_type, _collateral_deposit, msg.value, msg.sender)
        deposited_collateral = _collateral_deposit
        if _access_control:
            actual_lender = _recipient
        else :
            actual_lender = empty(address)
    
    # update loan details
    loan_info: Loan = Loan({
        borrower: actual_borrower,
        lender: actual_lender,
        margin_cutoff: _margin_cutoff,
        collateral_ratio: _collateral_ratio,
        fixed_interest_rate: _fixed_intererst_rate,
        borrow_amount: borrow_amount,
        time_limit: _time_limit,
        time_amount: _time_amount_set,
        collateral_type: _collateral_type,
        collateral_deposited: deposited_collateral,
        principal_type: _principal_type,
        current_debt: 0,
        access_control: _access_control,
        state: self.proposed,
        loan_type: _loan_type
    })

    self.loan_details[loan_id] = loan_info
    self.loan_existence_tracker[loan_id] = True

    log LoanProposed(loan_id, loan_info)



@external 
def renegotiate(_loan_id: uint256, _user_custom_id: String[30], _margin_cutoff: uint256, _collateral_ratio: uint256, _fixed_intererst_rate: uint256, _time_amount: uint256):
    selected_loan: Loan = self.loan_details[_loan_id]

    self.check_loan_exist(_loan_id)
    self.check_loan_state_is_proposed(selected_loan.state)
    self.check_loan_access(selected_loan, msg.sender)
    
   
    _renegotiaited_loan_id: bytes32 = self.generate_id(_user_custom_id)

    if self.loan_renegotiation_id_tracker[_loan_id][_renegotiaited_loan_id] != empty(address): 
        raise "Custom ID Taken"
    self.loan_renegotiation_id_tracker[_loan_id][_renegotiaited_loan_id] = msg.sender

    
    _new_time_amount: uint256 = 0
    if selected_loan.time_limit:
        _new_time_amount = _time_amount

    actual_lender: address = empty(address)
    actual_borrower: address = empty(address)

    if selected_loan.loan_type == self.lender_loan:
        actual_lender = selected_loan.lender
        actual_borrower = msg.sender
    if selected_loan.loan_type == self.borrower_loan:
        actual_lender = msg.sender
        actual_borrower = selected_loan.borrower

    renegotiaited_loan: Loan = Loan({
        borrower: actual_borrower, 
        lender: actual_lender, 
        margin_cutoff: _margin_cutoff,
        collateral_ratio: _collateral_ratio,
        fixed_interest_rate: _fixed_intererst_rate,
        borrow_amount: selected_loan.borrow_amount,
        time_limit: selected_loan.time_limit,
        time_amount: _new_time_amount,
        collateral_type: selected_loan.collateral_type,
        collateral_deposited: selected_loan.collateral_deposited,
        principal_type: selected_loan.principal_type,
        current_debt: selected_loan.current_debt,
        access_control: selected_loan.access_control,
        state: selected_loan.state,
        loan_type: selected_loan.loan_type
    })

    self.loan_renegotiations[_loan_id][_renegotiaited_loan_id] = renegotiaited_loan 

    log LoanRenegotiated(_loan_id, _user_custom_id, _renegotiaited_loan_id, renegotiaited_loan)



@external 
def change_renegotiation_terms(_loan_id: uint256, _user_custom_id: String[30],  _margin_cutoff: uint256, _collateral_ratio: uint256, _fixed_intererst_rate: uint256, _time_amount: uint256):

    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]
    self.check_loan_state_is_proposed(selected_loan.state)

   
    renegotiaited_loan_id: bytes32 = keccak256(_user_custom_id)
    prev_renegotiation: Loan = self.loan_renegotiations[_loan_id][renegotiaited_loan_id]
    renegotiation_owner: address = self.loan_renegotiation_id_tracker[_loan_id][renegotiaited_loan_id]
    
    
    if renegotiation_owner == empty(address) :
        raise "Re-Negotiation Does Not Exist"
    if renegotiation_owner != msg.sender :
        raise "You dont Own This Re-Negotiation"

    _new_time_amount: uint256 = 0
    if selected_loan.time_limit:
        _new_time_amount = _time_amount

    new_renegotiaited_terms: Loan = Loan({
        borrower: prev_renegotiation.borrower, 
        lender: prev_renegotiation.lender, 
        margin_cutoff: _margin_cutoff,
        collateral_ratio: _collateral_ratio,
        fixed_interest_rate: _fixed_intererst_rate,
        borrow_amount: prev_renegotiation.borrow_amount,
        time_limit: prev_renegotiation.time_limit,
        time_amount: _new_time_amount,
        collateral_type: prev_renegotiation.collateral_type,
        collateral_deposited: prev_renegotiation.collateral_deposited,
        principal_type: prev_renegotiation.principal_type,
        current_debt: prev_renegotiation.current_debt,
        access_control: prev_renegotiation.access_control,
        state: prev_renegotiation.state,
        loan_type: prev_renegotiation.loan_type
    })

    self.loan_renegotiations[_loan_id][renegotiaited_loan_id] = new_renegotiaited_terms

    log RenegotiationTermsChanged(_loan_id, _user_custom_id, renegotiaited_loan_id, new_renegotiaited_terms)



@external 
def change_original_loan_terms(_loan_id: uint256, _margin_cutoff: uint256, _collateral_ratio: uint256, _fixed_intererst_rate: uint256, _time_amount: uint256):


    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]
    self.check_loan_state_is_proposed(selected_loan.state)

    
    loan_owner: address = empty(address)
    if selected_loan.loan_type == self.lender_loan:
        loan_owner = selected_loan.lender
    if selected_loan.loan_type == self.borrower_loan:
        loan_owner = selected_loan.borrower
    
    if msg.sender != loan_owner :
        raise "!Loan Owner"


    actual_lender: address = empty(address)
    actual_borrower: address = empty(address)

    if selected_loan.loan_type == self.lender_loan:
        actual_lender = selected_loan.lender
    if selected_loan.loan_type == self.borrower_loan:
        actual_borrower = selected_loan.borrower


    _new_time_amount: uint256 = 0
    if selected_loan.time_limit:
        _new_time_amount = _time_amount

    new_loan_details: Loan = Loan({
        borrower: actual_borrower,
        lender: actual_lender,
        margin_cutoff: _margin_cutoff,
        collateral_ratio: _collateral_ratio,
        fixed_interest_rate: _fixed_intererst_rate,
        borrow_amount: selected_loan.borrow_amount,
        time_limit: selected_loan.time_limit,
        time_amount: _new_time_amount,
        collateral_type: selected_loan.collateral_type,
        collateral_deposited: selected_loan.collateral_deposited,
        principal_type: selected_loan.principal_type,
        current_debt: selected_loan.current_debt,
        access_control: selected_loan.access_control,
        state: selected_loan.state,
        loan_type: selected_loan.loan_type
    })

    self.loan_details[_loan_id] = new_loan_details

    log LoanTermsChanged(_loan_id, new_loan_details)


@external
@payable 
def accept_renegotiation(_loan_id: uint256, _user_custom_id: String[30]):

    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]
    self.check_loan_state_is_proposed(selected_loan.state)

    _renegotiaited_loan_id: bytes32 = keccak256(_user_custom_id)
    renegotiaited_loan: Loan = self.loan_renegotiations[_loan_id][_renegotiaited_loan_id]


    if renegotiaited_loan.loan_type == self.lender_loan:
        if msg.sender != renegotiaited_loan.lender:
            raise "! Loan Owner: Cant Accept"
        
        
    if renegotiaited_loan.loan_type == self.borrower_loan:
        if msg.sender != renegotiaited_loan.borrower:
            raise "! Loan Owner: Cant Accept"

    self.loan_details[_loan_id] = renegotiaited_loan
    
    log LoanReNegotiationAccepted(_loan_id, _user_custom_id, _renegotiaited_loan_id, renegotiaited_loan)

 
@external 
def push_renegotiation_chat(_loan_id: uint256, _user_custom_id: String[30], message: String[500]):
   
    selected_loan: Loan = self.loan_details[_loan_id]
    self.check_loan_exist(_loan_id)
    self.check_loan_state_is_proposed(selected_loan.state)

   
    _renegotiaited_loan_id: bytes32 = keccak256(_user_custom_id)
    if self.loan_renegotiation_id_tracker[_loan_id][_renegotiaited_loan_id] == empty(address): 
        raise "Re-Negotiation Does Not Exist"

    renegotiaited_loan: Loan = self.loan_renegotiations[_loan_id][_renegotiaited_loan_id]

    borrower: address = renegotiaited_loan.borrower
    lender: address = renegotiaited_loan.lender
    
    if msg.sender not in [borrower, lender]:
        raise "No Chat Permission"
    
    if msg.sender == lender:
        log ChatPushed(_loan_id, _user_custom_id, _renegotiaited_loan_id, message, 0)

    if msg.sender == borrower:
        log ChatPushed(_loan_id, _user_custom_id, _renegotiaited_loan_id, message, 1)
  

@external 
@payable 
def accept_loan_terms(_loan_id: uint256, _erc20Amount: uint256):
    
    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]
    self.check_loan_state_is_proposed(selected_loan.state)

  
    if selected_loan.loan_type == self.lender_loan:
        if msg.sender == selected_loan.lender:
            raise "You Cant Accept Your Loan"
        
        if selected_loan.borrower != empty(address):
            if msg.sender != selected_loan.borrower:
                raise "Loan ! For You"

        self.loan_details[_loan_id].borrower = msg.sender

    if selected_loan.loan_type == self.borrower_loan:
        if msg.sender == selected_loan.borrower:
            raise "You Cant Accept Your Loan"

        if selected_loan.lender != empty(address):
            if msg.sender != selected_loan.lender:
                raise "Loan ! For You"
        self.loan_details[_loan_id].lender = msg.sender

    self.loan_details[_loan_id].state = self.accepted
    
    collateral_price: uint256 = 0
    principal_price: uint256 = 0

    collateral_price, principal_price = self.get_asset_prices(selected_loan.collateral_type, selected_loan.principal_type)

   
    over_collateralized_amount: uint256 = 0
    estimated_principle: uint256 = 0

    (over_collateralized_amount, estimated_principle) = flexCalc(self.flex_calc).loan_acceptance_calculations(collateral_price, principal_price, selected_loan)

   
    if selected_loan.collateral_type == empty(address): 
        if selected_loan.loan_type == self.lender_loan: 
            assert msg.value >= over_collateralized_amount, "Insufficient Collateral Deposit"
            ERC20(selected_loan.principal_type).transfer(msg.sender, selected_loan.borrow_amount)
            
            interest: uint256 = (selected_loan.fixed_interest_rate * selected_loan.borrow_amount) / 100
            self.loan_details[_loan_id].current_debt = selected_loan.borrow_amount + interest
            self.loan_details[_loan_id].collateral_deposited = over_collateralized_amount

        if selected_loan.loan_type == self.borrower_loan :
            ERC20(selected_loan.principal_type).transferFrom(msg.sender, selected_loan.borrower, estimated_principle)

            self.loan_details[_loan_id].borrow_amount = estimated_principle
            self.loan_details[_loan_id].current_debt = estimated_principle

    
    if selected_loan.collateral_type != empty(address):
        if selected_loan.loan_type == self.lender_loan:

            if over_collateralized_amount > _erc20Amount:
                raise "Insufficient Collateral Deposit"
            ERC20(selected_loan.collateral_type).transferFrom(msg.sender, self, over_collateralized_amount)

            if selected_loan.principal_type == empty(address):
                raw_call(msg.sender, b"", value=selected_loan.borrow_amount)
            else:
                ERC20(selected_loan.principal_type).transfer(msg.sender, selected_loan.borrow_amount)

            interest: uint256 = (selected_loan.fixed_interest_rate * selected_loan.borrow_amount) / 100
            self.loan_details[_loan_id].current_debt = selected_loan.borrow_amount + interest
            self.loan_details[_loan_id].collateral_deposited = over_collateralized_amount

        if selected_loan.loan_type == self.borrower_loan :
            if selected_loan.principal_type == empty(address):
                if msg.value < estimated_principle:
                    raise "Insufficient Lend Amount For Collateral"
                raw_call(selected_loan.borrower, b"", value=estimated_principle)
            else:
                ERC20(selected_loan.principal_type).transferFrom(msg.sender, selected_loan.borrower, estimated_principle)

            self.loan_details[_loan_id].borrow_amount = estimated_principle
            self.loan_details[_loan_id].current_debt = estimated_principle
            
    if selected_loan.time_limit:
        self.loan_timers[_loan_id] = block.timestamp + selected_loan.time_amount
    
    log LoanAccepted(_loan_id, selected_loan)
   

@external 
def propose_new_terms_after_acceptance(_loan_id: uint256,  _margin_cutoff: uint256, _fixed_intererst_rate: uint256, _time_amount: uint256):
    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]

    if selected_loan.state != self.accepted:
        raise "Loan ! Accepted State"
    
    if msg.sender not in [selected_loan.lender, selected_loan.borrower ]:
        raise "! Permission To Propose"
    
    proposer: bytes32 = keccak256("Nothing")
    if msg.sender == selected_loan.borrower:
        proposer = self.borrower_proposal
    if msg.sender == selected_loan.lender:
        proposer = self.lender_proposal

    _new_time_amount: uint256 = selected_loan.time_amount

    if selected_loan.time_limit:
        if _time_amount > 0 :
            _new_time_amount = _time_amount
       
    new_loan_proposal: Loan = Loan({
        borrower: selected_loan.borrower,
        lender: selected_loan.lender,
        margin_cutoff: _margin_cutoff,
        collateral_ratio: selected_loan.collateral_ratio,
        fixed_interest_rate: _fixed_intererst_rate,
        borrow_amount: selected_loan.borrow_amount,
        time_limit: selected_loan.time_limit,
        time_amount: _new_time_amount,
        collateral_type: selected_loan.collateral_type,
        collateral_deposited: selected_loan.collateral_deposited,
        principal_type: selected_loan.principal_type,
        current_debt: selected_loan.current_debt,
        access_control: selected_loan.access_control,
        state: selected_loan.state,
        loan_type: selected_loan.loan_type
    })

    
    self.loan_proposals[_loan_id][proposer] = new_loan_proposal
    self.loan_proposal_tracker[_loan_id][proposer] = True
    log ProposalPushed(_loan_id, proposer, new_loan_proposal)


@external
def accept_new_proposal(_loan_id: uint256):

    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]
    if selected_loan.state != self.accepted:
        raise "Loan ! Accepted State"

    
    lender: address = selected_loan.lender
    borrower: address = selected_loan.borrower

    proposal: bytes32 = keccak256("nothing")
    if msg.sender == lender:
        proposal = self.borrower_proposal
    elif msg.sender == borrower:
        proposal = self.lender_proposal
    else:
        raise "! Access"
    
    if not self.loan_proposal_tracker[_loan_id][proposal]:
        raise "No Proposal To Accept"


    selected_proposal: Loan = self.loan_proposals[_loan_id][proposal]
    self.loan_details[_loan_id] = selected_proposal

    if selected_proposal.time_limit:
        self.loan_timers[_loan_id] = block.timestamp + selected_proposal.time_amount

    log ProposalAccepted(_loan_id, proposal, selected_proposal)

@external
@payable 
def repay_loan(_loan_id: uint256):
    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]

    if selected_loan.state != self.accepted:
        raise "Loan ! Accepted State" 

    total_debt: uint256 = selected_loan.current_debt 
    collateral_deposited:uint256 = selected_loan.collateral_deposited

   
    if selected_loan.principal_type == empty(address):
        if msg.value < total_debt:
            raise "Not Enough Repay Amount"
        raw_call(selected_loan.lender, b"", value=msg.value)

        ERC20(selected_loan.collateral_type).transfer(selected_loan.borrower, selected_loan.collateral_deposited)

    if selected_loan.principal_type != empty(address):
        ERC20(selected_loan.principal_type).transferFrom(msg.sender, selected_loan.lender, total_debt)

        if selected_loan.collateral_type == empty(address):
            raw_call(selected_loan.borrower, b"", value=selected_loan.collateral_deposited)
        else:
            ERC20(selected_loan.collateral_type).transfer(msg.sender, selected_loan.collateral_deposited)


    self.loan_details[_loan_id].state = self.fulfilled
    self.loan_details[_loan_id].current_debt = 0

    log LoanRepaid(_loan_id, selected_loan)
 

@external 
def liquidate_loan(_loan_id: uint256):
    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]
    
    if selected_loan.state != self.accepted:
        raise "Loan State ! Liquidatable"
   
    margin_cutoff_in_usd: uint256 = 0
    deposited_collateral_in_usd: uint256 = 0
    over_collateralized_collateral_in_usd: uint256 = 0
    
    margin_cutoff_in_usd, deposited_collateral_in_usd, over_collateralized_collateral_in_usd = self.get_margin_cutoff_in_usd(selected_loan)

    if selected_loan.time_limit:
        if block.timestamp > self.loan_timers[_loan_id]:
                amount_given_to_liquidator: uint256 = (LIQUIDATION_FEE * selected_loan.collateral_deposited) / 100
                amount_given_to_lender: uint256 = selected_loan.collateral_deposited - amount_given_to_liquidator
                
                if selected_loan.collateral_type == empty(address):
                    
                    raw_call(selected_loan.lender, b"", value=amount_given_to_lender)
                    raw_call(msg.sender, b"", value=amount_given_to_liquidator)
               
                else:
                    ERC20(selected_loan.collateral_type).transfer(selected_loan.lender, amount_given_to_lender)
                    ERC20(selected_loan.collateral_type).transfer(msg.sender, amount_given_to_liquidator)

                self.loan_details[_loan_id].state = self.fulfilled
                self.loan_details[_loan_id].current_debt = 0
                self.loan_details[_loan_id].collateral_deposited = 0

                log LoanLiquidated(_loan_id, self.loan_details[_loan_id])
        else:
            raise "Time ! Exceeded"

    if not selected_loan.time_limit:
       
        if deposited_collateral_in_usd < margin_cutoff_in_usd:
            
            amount_given_to_liquidator: uint256 = (LIQUIDATION_FEE * selected_loan.collateral_deposited) / 100
            amount_given_to_lender: uint256 = selected_loan.collateral_deposited - amount_given_to_liquidator

           
            if selected_loan.collateral_type == empty(address):
             
                raw_call(selected_loan.lender, b"", value=amount_given_to_lender)
                raw_call(msg.sender, b"", value=amount_given_to_liquidator)
           
            else:
                
                ERC20(selected_loan.collateral_type).transfer(selected_loan.lender, amount_given_to_lender)
                ERC20(selected_loan.collateral_type).transfer(msg.sender, amount_given_to_liquidator)

           
            self.loan_details[_loan_id].state = self.fulfilled
            self.loan_details[_loan_id].current_debt = 0
            self.loan_details[_loan_id].collateral_deposited = 0

            log LoanLiquidated(_loan_id, self.loan_details[_loan_id])
        else:
            raise "Loan ! Liquidatable"

@external
@payable 
def propose_loan_buyout(_loan_id: uint256, _buyout_amount: uint256):
    
    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]
    if selected_loan.state != self.accepted:
        raise "Loan ! Accepted State"

 
    if msg.sender == selected_loan.lender:
        raise "You Cant Buy Your Own Loan"

    if self.loan_buyouts[_loan_id][msg.sender] != 0:
        raise "Cancel Initial Buyout"

    

    if selected_loan.principal_type == empty(address):
        assert msg.value >= _buyout_amount, "Not Enough Deposited"
    else:
        ERC20(selected_loan.principal_type).transferFrom(msg.sender, self, _buyout_amount)

    self.loan_buyouts[_loan_id][msg.sender] = _buyout_amount

    log BuyoutProposed(_loan_id, msg.sender, _buyout_amount)


@external 
def cancel_loan_buyout(_loan_id: uint256):
  
    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]
   
    if self.loan_buyouts[_loan_id][msg.sender] == 0:
        raise "No Initial Buyout Or Accepted"

    deposited_amount: uint256 = self.loan_buyouts[_loan_id][msg.sender]

    if selected_loan.principal_type == empty(address):
       raw_call(msg.sender, b"", value=deposited_amount)
    else:
        ERC20(selected_loan.principal_type).transfer(msg.sender, deposited_amount)
    
    self.loan_buyouts[_loan_id][msg.sender] = 0

    log BuyOutCanceled(_loan_id, msg.sender, deposited_amount)


@external 
def accept_loan_buyout(_loan_id: uint256, _buyer: address):
    
    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]
    if selected_loan.state != self.accepted:
        raise "Loan ! Accepted State"

    if msg.sender != selected_loan.lender:
        raise "!Permission To Accept Buyout"

    if self.loan_buyouts[_loan_id][_buyer] == 0:
        raise "No Initial Buyout For Acceptance"
    buyout_amount: uint256 = self.loan_buyouts[_loan_id][_buyer]

   
    if selected_loan.principal_type == empty(address):
        raw_call(selected_loan.lender, b"", value=buyout_amount)
    else:
        ERC20(selected_loan.principal_type).transfer(selected_loan.lender, buyout_amount)

    self.loan_details[_loan_id].lender = _buyer
    
    log LoanBought(_loan_id, _buyer, buyout_amount)

@external # 
def deactivate_loan(_loan_id: uint256):
    
    self.check_loan_exist(_loan_id)
    selected_loan: Loan = self.loan_details[_loan_id]


    self.check_loan_state_is_proposed(selected_loan.state)

    loan_type: uint256 =  selected_loan.loan_type
    creator: address = empty(address)

    if loan_type == self.lender_loan:
        if msg.sender != selected_loan.lender:
            raise "No Permision To Deactivate"
   
        if selected_loan.principal_type == empty(address):
            raw_call(selected_loan.lender, b"", value=selected_loan.borrow_amount)
        else: 
            ERC20(selected_loan.principal_type).transfer(selected_loan.lender, selected_loan.borrow_amount)

        self.loan_details[_loan_id].state = self.deactivated
   
        log LoanDeactivated(_loan_id, self.loan_details[_loan_id])

    if loan_type == self.borrower_loan:
        if msg.sender != selected_loan.borrower:
            raise "No Permision To Deactivate"

        if selected_loan.collateral_type == empty(address):
            raw_call(selected_loan.borrower, b"", value=selected_loan.collateral_deposited)
        else:
            ERC20(selected_loan.collateral_type).transfer(selected_loan.borrower, selected_loan.collateral_deposited)

        self.loan_details[_loan_id].state = self.deactivated

        log LoanDeactivated(_loan_id, self.loan_details[_loan_id])

@external
@payable
def top_up_collateral(loan_id: uint256, amount: uint256):

    self.check_loan_exist(loan_id)
    selected_loan: Loan = self.loan_details[loan_id]

    if selected_loan.state != self.accepted:
        raise "Loan ! Accepted State"

    if selected_loan.collateral_type == empty(address):
        self.loan_details[loan_id].collateral_deposited += msg.value
        log CollateralTopUp(loan_id, self.loan_details[loan_id].collateral_deposited)
    else:
        ERC20(selected_loan.collateral_type).transferFrom(msg.sender, self, amount)
        self.loan_details[loan_id].collateral_deposited += amount
        log CollateralTopUp(loan_id, self.loan_details[loan_id].collateral_deposited)

    

@external
def add_token_support(token_address: address):
    if msg.sender != self.owner:
        raise "!Permission To Add Token"
    self.supported_assets[token_address] = True

@external
def add_price_feed_address(asset: address, price_feed_address: address):
    if msg.sender != self.owner:
        raise "!Owner Permission"
    self.price_feeds[asset] = price_feed_address


# INTERNAL FUNCTIONS

@internal
def _collectDeposit(asset_deposited: address, amount_desired: uint256, amount_deposited: uint256, msgSender: address):
    # transfer the asset with an ERC20 Token interface 
    if asset_deposited != empty(address):
        success: bool = ERC20(asset_deposited).transferFrom(msgSender, self, amount_desired)
        if not success:
            raise "Failed to Collect Initial Deposit"
    else:
        # check if the asset desired to deposit equals the actual asset deposited i.e msg.value
        if amount_desired < amount_deposited:
            raise "Amount Desired < Amount Supplied"

# VIEW FUNCTIONS
@internal
@view
def check_loan_exist(_loan_id: uint256):
    if not self.loan_existence_tracker[_loan_id]:
        raise "Loan Does Not Exist"

@internal
@view
def check_loan_state_is_proposed(state: bytes32):
    if state != self.proposed:
        raise "Loan ! In Proposed State"

@internal
@view
def check_loan_access(selected_loan: Loan, sender: address) :
    if selected_loan.access_control:
        if selected_loan.loan_type == self.lender_loan:
            if selected_loan.borrower != sender: 
                raise "! Loan Recipient"

        if selected_loan.loan_type == self.borrower_loan: 
            if selected_loan.lender != sender: 
                raise "! Loan Recipient"

@internal
@view
def generate_id(_user_custom_id: String[30]) -> bytes32:
    _renegotiaited_loan_id: bytes32 = keccak256(_user_custom_id)
    return _renegotiaited_loan_id

@internal
@view
def get_asset_prices(collateral_type: address, principal_type: address) -> (uint256, uint256):

    collateral_price_feed: address = self.price_feeds[collateral_type]
    principal_price_feed: address = self.price_feeds[principal_type]

     # Not Needed
    round_id: uint80 = 0  
    started_at: uint256 = 0  
    updated_at: uint256 = 0  
    answered_in_round: uint80 = 0  

    int_collateral_price: int256 = 0 
    int_principal_price: int256 = 0

    round_id, int_collateral_price, started_at, updated_at, answered_in_round  = AggregatorV3Interface(collateral_price_feed).latestRoundData()
    round_id, int_principal_price, started_at, updated_at, answered_in_round  = AggregatorV3Interface(principal_price_feed).latestRoundData()

   
    collateral_price: uint256 = convert(int_collateral_price, uint256)
    principal_price: uint256 = convert(int_principal_price, uint256)

    return collateral_price, principal_price

@internal 
@view
def get_margin_cutoff_in_usd(selected_loan: Loan) -> (uint256, uint256, uint256):

    collateral_price_feed: address = self.price_feeds[selected_loan.collateral_type]
    principal_price_feed: address = self.price_feeds[selected_loan.principal_type]

    # Not Needed
    round_id: uint80 = 0  
    started_at: uint256 = 0
    updated_at: uint256 = 0 
    answered_in_round: uint80 = 0  

    int_collateral_price: int256 = 0 
    int_principal_price: int256 = 0  

    round_id, int_collateral_price, started_at, updated_at, answered_in_round = AggregatorV3Interface(collateral_price_feed).latestRoundData()
    round_id, int_principal_price, started_at, updated_at, answered_in_round = AggregatorV3Interface(principal_price_feed).latestRoundData()

    collateral_price: uint256 = convert(int_collateral_price, uint256)
    principal_price: uint256 = convert(int_principal_price, uint256)

    deposited_collateral_in_usd: uint256 = (collateral_price * selected_loan.collateral_deposited) / 10**18
    over_collateralized_collateral_in_usd: uint256 = (deposited_collateral_in_usd * selected_loan.collateral_ratio) / 100


    total_debt: uint256 = selected_loan.current_debt
    total_debt_in_usd: uint256 = (total_debt * principal_price) / 10**18 

    margin_cutoff_in_usd: uint256 = (total_debt_in_usd * selected_loan.margin_cutoff) / 100

    return margin_cutoff_in_usd, deposited_collateral_in_usd, over_collateralized_collateral_in_usd


@internal
@view
def get_estimated_amount(selected_loan: Loan, collateral_price: uint256, principal_price: uint256) -> uint256:
    estimated_amount: uint256 = 0
    
    if selected_loan.loan_type == self.lender_loan:
        # we need to get the collateral needed to be depoisted by the borrower
        principal_type: address = selected_loan.principal_type
        collateral_type: address = selected_loan.collateral_type

        principal_deposited_in_usd: uint256 = (selected_loan.borrow_amount * principal_price) / 10**18
        over_collateralized_amount_in_usd: uint256 = (principal_deposited_in_usd * selected_loan.collateral_ratio) / 100
        approx_over_collateralized_borrower_deposit: uint256 = (over_collateralized_amount_in_usd * 10**18) / collateral_price

        estimated_amount = approx_over_collateralized_borrower_deposit

    if selected_loan.loan_type == self.borrower_loan:
        # we need to get the principal needed to be depoisted by the lender for the loan
        interest_to_be_paid: uint256 = (selected_loan.fixed_interest_rate * selected_loan.collateral_deposited) / 100
        
        total_collateral_deposited: uint256 = selected_loan.collateral_deposited - interest_to_be_paid
        total_collateral_deposited_in_usd: uint256 = (total_collateral_deposited * collateral_price) / 10**18

        estimated_principle_in_usd: uint256 = (total_collateral_deposited_in_usd / selected_loan.collateral_ratio) * 100
        estimated_principle: uint256 = (estimated_principle_in_usd * 10**18) / principal_price

        estimated_amount = estimated_principle

    return estimated_amount


# GETTER FUNCTIONS

@external
@view
def get_loan_Details_by_id(loan_id: uint256) -> Loan:
    selected_loan: Loan = self.loan_details[loan_id]
    return selected_loan

@external
@view
def get_renegotiated_loan_by_its_id(loan_id: uint256, user_custom_id: String[30]) -> Loan:
    _renegotiaited_loan_id: bytes32 = keccak256(user_custom_id)
    renegotiaited_loan: Loan = self.loan_renegotiations[loan_id][_renegotiaited_loan_id]
    return renegotiaited_loan

@external
@view 
def calulate_required_loan_principal_or_collateral_for_acceptance(loan_id: uint256) -> uint256 :
    selected_loan: Loan = self.loan_details[loan_id]

    collateral_price: uint256 = 0
    principal_price: uint256 = 0

    collateral_price, principal_price = self.get_asset_prices(selected_loan.collateral_type, selected_loan.principal_type)
    
    estimated_amount: uint256 = self.get_estimated_amount(selected_loan, collateral_price, principal_price)

    return estimated_amount


@external
@view 
def calulate_require_loan_principal_or_collateral_for_renegotiation_acceptance(loan_id: uint256, user_custom_id: String[30]) -> uint256 :
    _renegotiaited_loan_id: bytes32 = keccak256(user_custom_id)
    renegotiaited_loan: Loan = self.loan_renegotiations[loan_id][_renegotiaited_loan_id]

    collateral_price: uint256 = 0
    principal_price: uint256 = 0

    collateral_price, principal_price = self.get_asset_prices(renegotiaited_loan.collateral_type, renegotiaited_loan.principal_type)
    
    estimated_amount: uint256 =  self.get_estimated_amount(renegotiaited_loan, collateral_price, principal_price)

    return estimated_amount


@external
@view
def get_margin_cutoff_in_collateral(loan_id: uint256) -> uint256:
    selected_loan: Loan = self.loan_details[loan_id]

    margin_cutoff_in_usd: uint256 = 0
    deposited_collateral_in_usd: uint256 = 0
    over_collateralized_collateral_in_usd: uint256 = 0

    margin_cutoff_in_usd, deposited_collateral_in_usd, over_collateralized_collateral_in_usd = self.get_margin_cutoff_in_usd(selected_loan)

    collateral_price: uint256 = 0
    principal_price: uint256 = 0

    collateral_price, principal_price = self.get_asset_prices(selected_loan.collateral_type, selected_loan.principal_type)

    # get the margin cutoff in terms of the collateral
    margin_cutoff_in_collateral: uint256 = (margin_cutoff_in_usd * 10**18) / collateral_price

    return margin_cutoff_in_collateral

@external
@view
def get_health_status(loan_id: uint256) -> uint256:
    selected_loan: Loan = self.loan_details[loan_id]

    margin_cutoff_in_usd: uint256 = 0
    deposited_collateral_in_usd: uint256 = 0
    over_collateralized_collateral_in_usd: uint256 = 0

    # margin cutoff usd , deposited collateral in usd and over collateralized collateral deposit
    margin_cutoff_in_usd, deposited_collateral_in_usd, over_collateralized_collateral_in_usd = self.get_margin_cutoff_in_usd(selected_loan)

    health_status: uint256 = 0 # 1 - safe # 2 - inbetween #3 - unsafe and can be liquidated


    if deposited_collateral_in_usd > over_collateralized_collateral_in_usd:
        health_status = 1    
    if deposited_collateral_in_usd < margin_cutoff_in_usd:
        health_status = 3
    if deposited_collateral_in_usd > margin_cutoff_in_usd and deposited_collateral_in_usd < over_collateralized_collateral_in_usd:
        health_status = 2

    return health_status