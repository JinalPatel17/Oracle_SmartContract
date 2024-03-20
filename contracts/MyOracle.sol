// CCMP 606 Assignment 2
// MyOracle contract for getting the price of Ether in USD

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract MyOracle {
    address public owner;
    uint public ethPriceInUSD;
    bool public updateRequested;

    event PriceUpdated(uint newPrice);
    event UpdateRequested();

    constructor() {
        owner = msg.sender;
        updateRequested = false;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "The owner of this Contract call this Function is Mandatory.");
        _;
    }

    function setETHUSD(uint _price) external onlyOwner {
        ethPriceInUSD = _price;
        emit PriceUpdated(_price);
    }

    function getETHUSD() external view returns (uint) {
        return ethPriceInUSD;
    }

    function requestUpdate() external {
        updateRequested = true;
        emit UpdateRequested();
    }
}

