import { Router } from "express"
import crypto from "crypto"
import dotenv from 'dotenv'
import { parseUnits } from "ethers"
import qrcode from "qrcode"
import path from "path"

import { productContract, adminWallet } from "../utils/web3-contracts.js"
import { db } from "../utils/db.js"


dotenv.config()


const router = Router()

const KEY = Buffer.from(process.env.AES_ENCRYPTION_KEY, 'base64')

const qrDir = path.join(import.meta.dirname, "..", "qr")
const algorithm = "aes-256-cbc"
const product_fields = ["productId", "name", "batchNumber", "manufacturingDate", "description", "price"]
const user_types = ["Manufacturer", "Seller", "Customer"]


async function generateQRCode(productId) {
  const qrPath = path.join(qrDir, `${productId}.png`)
  await qrcode.toFile(qrPath, productId, {
    errorCorrectionLevel: "H"
  })

  return qrPath
}

function encryptAES(text) {
  const iv = crypto.randomBytes(16)
  const cipher = crypto.createCipheriv(algorithm, KEY, iv)
  const encrypted = cipher.update(text, "utf8", 'base64') + cipher.final('base64')
  return iv.toString('base64') + ":" + encrypted
}

router.post("/register", async (req, res) => {
  const manufacturer = req.cookies["username"]

  db.get(
    "SELECT * FROM users WHERE username = ? AND role = 'Manufacturer'",
    [manufacturer], async (err, _manufacturer) => {
      if (err) {
        console.error(err)
        return res.status(500).json({ error: "Database error: " + err.message })
      }

      if (!_manufacturer)
        return res.status(401).json({ error: "Unauthorized manufacturer" })

      let encryptedData = {}
      for (let attr of product_fields) {
        if (req.body[attr] === undefined || req.body[attr] === null)
          return res.status(400).json({ error: "Missing field: " + attr })
        encryptedData[attr] = encryptAES(req.body[attr])
      }

      const { productId } = req.body
      const { name, batchNumber, manufacturingDate, description, price } = encryptedData

      try {
        const tx = await productContract.connect(adminWallet).registerProduct(
          productId, name, batchNumber, manufacturingDate, description,
          price, manufacturer, manufacturer + " (Manufacturer)", {
            gasLimit: 500000,
            gasPrice: parseUnits("5", "gwei")
          })

        await tx.wait()
        await generateQRCode(productId)

        res.status(200).json({ message: "Product registered" })
      } catch (e) {
        console.error("Contract call failed:", e)
        res.status(500).json({ error: e.message })
      }
    }
  )
})


router.post("/transfer", async (req, res) => {
  const { productId, toUsername, toUserType } = req.body

  const fromUsername = req.cookies['username']
  const currentUserRole = req.cookies['role']

  if (!["Manufacturer", "Seller"].includes(currentUserRole))
    return res.status(403).json({ error: "Only Manufacturer or Seller can transfer products" })

  if (!["Manufacturer", "Seller"].includes(toUserType))
    return res.status(403).json({ error: "Expected Seller or Customer, but got " + toUserType })

  const targetRole = toUserType
   
  try {
    db.get(
      "SELECT * FROM users WHERE username = ? AND role = ?",
      [toUsername, targetRole], async (err, targetUser) => {
        if (err) {
          console.error(err)
          return res.status(500).json({ error: "Database error: " + err.message })
        }

        if (!targetUser)
          return res.status(404).json({ error: "Target user not found or invalid role" })

        try {
          const tx = await productContract.connect(adminWallet).transferProduct(
            productId, fromUsername + ` (${currentUserRole})`, toUsername + ` (${targetRole})`, {
              gasLimit: 500000,
              gasPrice: parseUnits("5", "gwei")
          })

          await tx.wait()
          res.status(200).json({ message: "Product transferred", txHash: tx.hash })
        } catch (err2) {
          console.error("Contract execution failed:", err2)
          res.status(500).json({ error: "Contract execution failed: " + err2.message })
        }
      }
    )
  } catch (err4) {
    res.status(500).json({ error: err4.message })
  }
})


router.post("/verify/:pid", async (req, res) => {
  const productId = req.params.pid

  try {
    const [manufacturer, currentOwner] = await productContract.verifyProduct(productId)//, {
    //   gasLimit: 500000,
    //   gasPrice: parseUnits("5", "gwei")
    // })

    if (!manufacturer || manufacturer.length === 0)
      return res.status(404).json({ valid: false, message: "Product not found" })

    db.get(
      'SELECT username FROM users WHERE username = ? AND role = "Manufacturer"',
      [manufacturer], (err, _manufacturer) => {
        if (err) {
          console.error(err)
          return res.status(500).json({ error: "Database error: " + err.message })
        }

        if (!_manufacturer)
          return res.status(404).json({ valid: false, message: "Manufacturer not registered" })

        return res.status(200).json({
          valid: true, productId, manufacturer, currentOwner
        })
      }
    )
  } catch (err) {
    if (err.reason != "Product not found")
      console.error("Verification failed:", err)
    res.status(500).json({ valid: false, error: "Verification failed: " + err.message })
  }
})


export default router
