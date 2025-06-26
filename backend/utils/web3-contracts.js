import { ethers } from "ethers"
import dotenv from 'dotenv'

import ProductRegistryJSON from "../contracts/ProductRegistry.json" with { type: 'json' }


dotenv.config()

const web3provider = new ethers.JsonRpcProvider("http://127.0.0.1:7545")

const accounts = await web3provider.listAccounts()
const adminWallet = await web3provider.getSigner(accounts[0].address)

// console.log('Admin wallet: ', accounts[0].address)

const productContract = new ethers.Contract(
  ProductRegistryJSON.networks["5777"].address, ProductRegistryJSON.abi, adminWallet
)

export { web3provider, productContract, adminWallet }
