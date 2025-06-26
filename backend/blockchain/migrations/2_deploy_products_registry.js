const ProductRegistry = artifacts.require("ProductRegistry")

module.exports = function (deployer) {
  deployer.deploy(ProductRegistry)
}
