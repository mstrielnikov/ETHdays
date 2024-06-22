// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2 <0.9.0;

contract Intent {
    bool public isIntent = true;
    bool public isFulfilled = false;
    string private intentDesc = "";
    uint256 public price;
    address private owner_address;
    address private executor_address;

    // event for EVM logging
    event OwnerSet(address indexed _owner);
    event FulfillIntent(address indexed _executor, uint256 _pay_amount, string _intent_describe);

    modifier onlyOwner() {
        require(msg.sender == owner_address, "Caller is not the owner of intent");
        _;
    }

    modifier onlyExecutor() {
        require(msg.sender == executor_address, "Caller is not the executor of intent");
        _;
    }    

    modifier notSatisfiedIntent() {
        require(isFulfilled == false, "This intent is satisfied already");
        _;
    }

    constructor() {
        owner_address = msg.sender;
        emit OwnerSet(owner_address);
    }

    function getOwner() external view returns (address) {
        return owner_address;
    }

    function getExecutor() external view returns (address) {
        return executor_address;
    }

    function getIntentDesc() external view returns(string memory) {
        return intentDesc;
    }

    function setExecutor(address _executor_address) public onlyOwner notSatisfiedIntent {
         require(_executor_address != owner_address, "Owner can't be the executor of his own intent");
        executor_address = _executor_address;
    }

    function setPrice(uint256 _price) public onlyOwner notSatisfiedIntent {
        require(_price > 0, "Unable to set the price to zero");
        price = _price;
    }

    function setIntentDesc(string memory _intent_desc) public onlyOwner notSatisfiedIntent {
        require(bytes(_intent_desc).length > 0, "Intent desc could not be empty string");
        intentDesc = _intent_desc;
    }

    function executeIntent() public onlyExecutor notSatisfiedIntent payable {        
        require(price > 0, "Price set to 0");
        require(price <= owner_address.balance, "Insufficient contract balance");
        (bool success, ) = executor_address.call{value: price}("");
        require(success, "Transfer failed");
        isFulfilled = true;
        emit FulfillIntent(executor_address, price, intentDesc);
    }

    fallback() external payable{}
    
    receive() external payable {}
}