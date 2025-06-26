// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ProductRegistry {
  struct Product {
    string productId;
    string name;
    string batchNumber;
    string manufacturingDate;
    string description;
    string price;
    string manufacturer;
    uint256 timestamp;
    string currentOwner;
    bool isRegistered;
  }

  mapping(string => Product) private products;

  event ProductRegistered(
    string indexed productId,
    string indexed manufacturer
  );

  event ProductTransferred(
    string indexed productId,
    string indexed from,
    string indexed to
  );

  function registerProduct(
    string memory _productId,
    string memory _name,
    string memory _batchNumber,
    string memory _manufacturingDate,
    string memory _description,
    string memory _price,
    string memory _manufacturer,
    string memory _currentOwner
  ) public {
    require(!products[_productId].isRegistered, "Product already registered");

    products[_productId] = Product({
      productId: _productId,
      name: _name,
      batchNumber: _batchNumber,
      manufacturingDate: _manufacturingDate,
      description: _description,
      price: _price,
      timestamp: block.timestamp,
      manufacturer: _manufacturer,
      currentOwner: _currentOwner,
      isRegistered: true
    });

    emit ProductRegistered(_productId, _manufacturer);
  }

  function strcmp(string memory a, string memory b) internal pure returns(bool){
    bytes memory bytes_a = bytes(a);
    bytes memory bytes_b = bytes(b);
    return (bytes_a.length == bytes_b.length) && (keccak256(bytes_a) == keccak256(bytes_b));
  }

  function transferProduct(
    string memory _productId,
    string memory _from,
    string memory _to
  ) public {
    require(products[_productId].isRegistered, "Product not found");
    require(strcmp(products[_productId].currentOwner, _from), "Not product owner");

    string memory previousOwner = products[_productId].currentOwner;
    products[_productId].currentOwner = _to;

    emit ProductTransferred(_productId, previousOwner, _to);
  }

  function verifyProduct(string memory _productId) public view returns (
    string memory manufacturer, string memory currentOwner
  ) {
    require(products[_productId].isRegistered, "Product not found");

    Product memory product = products[_productId];
    return (product.manufacturer, product.currentOwner);
  }
}
