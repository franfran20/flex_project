# @version 0.3.7

version: constant(uint256) = 0

decimals: public(uint8)
latestAnswer: public(int256)
latestTimestamp: public(uint256)
latestRound: public(uint80)

getAnswer: public(HashMap[uint80, int256])
getTimestamp: public(HashMap[uint80, uint256])
getStartedAt: public(HashMap[uint80, uint256])


@external
def __init__(_decimals: uint8, _initialAnswer: int256):
    self.decimals = _decimals
    
    self.latestAnswer = _initialAnswer
    self.latestTimestamp = block.timestamp
    new_latest_round: uint80 = self.latestRound + 1
    self.latestRound = new_latest_round

    self.getAnswer[new_latest_round] = _initialAnswer
    self.getTimestamp[new_latest_round] = block.timestamp
    self.getStartedAt[new_latest_round] = block.timestamp

@external
def updateAnswer(_answer: int256):
    self.latestAnswer = _answer
    self.latestTimestamp = block.timestamp
    new_latest_round: uint80 = self.latestRound + 1
    self.latestRound = new_latest_round

    self.getAnswer[new_latest_round] = _answer
    self.getTimestamp[new_latest_round] = block.timestamp
    self.getStartedAt[new_latest_round] = block.timestamp


@external 
def updateRoundData(_roundId: uint80, _answer: int256, _timestamp: uint256, _startedAt: uint256):
    self.latestAnswer = _answer
    self.latestTimestamp = _timestamp

    self.getAnswer[_roundId] = _answer
    self.getTimestamp[_roundId] = _timestamp
    self.getStartedAt[_roundId] = _startedAt


@external
@view
def getRoundData(_roundId: uint80) -> (uint80, int256, uint256, uint256, uint80):
    return _roundId, self.getAnswer[_roundId], self.getStartedAt[_roundId], self.getTimestamp[_roundId], _roundId


@external
@view
def latestRoundData() -> (uint80, int256, uint256, uint256, uint80):
    return self.latestRound, self.getAnswer[self.latestRound], self.getStartedAt[self.latestRound], self.getTimestamp[self.latestRound], self.latestRound
