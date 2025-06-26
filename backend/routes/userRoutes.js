import express from "express"
import crypto from "crypto"

import { db } from '../utils/db.js'


const user_fields = {
  "Manufacturer": ['username', 'password', 'companyName', 'licenseNumber', 'manager', 'brand', 'phone', 'address'],
  "Seller": ['username', 'password', 'companyName', 'phone', 'manager', 'brand', 'address'],
  "Customer": ['username', 'password', 'fullName', 'phone', 'address']
}

const router = express.Router()


function hashPassword(password) {
  return crypto.createHash('sha256').update(password).digest('hex')
}


router.post("/register", async (req, res) => {
  const role = req.body.role

  if (!["Manufacturer", "Customer"].includes(role))
    return res.status(400).json({ error: "Invalid role: " + role })

  for (let attr of user_fields[role]) {
    if (req.body[attr] === undefined || req.body[attr] === null)
      return res.status(400).json({ error: "Missing field: " + attr })
  }

  const { username, password, phone, address, ...metadataObj } = req.body

  db.get(
    `SELECT * FROM users WHERE username = ? AND role = ?`, [username, role],
    async (err, row) => {
      if (err) {
        console.error(err)
        return res.status(500).json({ error: "Database error" })
      }

      if (row)
        return res.status(409).json({ error: "User already exists" })

      for (let attr of user_fields[role]) {
        if (req.body[attr] === undefined || req.body[attr] === null)
          return res.status(400).json({
            error: `Missing field in ${role.toLowerCase()} details: ${attr}`
          })
      }

      const hashedPassword = hashPassword(password)
      const metadata = JSON.stringify(metadataObj)

      db.run(
        `INSERT INTO users (username, password, role, phone, address, metadata) VALUES (?, ?, ?, ?, ?, ?)`,
        [username, hashedPassword, role, phone, address, metadata], (err2) => {
          if (err2) {
            console.error(err2)
            return res.status(500).json({ error: "Failed to register user\n" + err2.message })
          }

          console.log(`${role} user registered: ${username}`)
          res.status(201).json({ message: "User registered successfully", username, role })
        }
      )
    }
  )
})


router.post("/login", (req, res) => {
  const { username, password, role } = req.body

  const hashedPassword = hashPassword(password)

  db.get(
    `SELECT * FROM users WHERE username = ? AND password = ? AND role = ?`,
    [username, hashedPassword, role], (err, row) => {
      if (err) {
        console.error(err)
        return res.status(500).json({ error: "Database error" })
      }

      if (!row)
        return res.status(401).json({ error: "Invalid username or password. Did you register yet?" })

      console.log(`${username} (${role}) logged in`)
      res.status(200).json({
        message: "Login successful", username, role,
      })
    }
  )
})

router.post("/add-seller", async (req, res) => {
  for (let attr of user_fields["Seller"]) {
    if (req.body[attr] === undefined || req.body[attr] === null)
      return res.status(400).json({ error: "Missing field for seller: " + attr })
  }

  const { manufacturer, username, password, phone, address, ...metadataObj } = req.body

  db.get(
    `SELECT * FROM users WHERE username = ? AND role = "Seller"`,
    [username],
    async (err, existingUser) => {
      if (err) {
        console.error(err)
        return res.status(500).json({ error: "Database error" })
      }

      if (existingUser)
        return res.status(409).json({ error: "Username already exists" })

      const hashedPassword = hashPassword(password)
      const metadata = JSON.stringify(metadataObj)

      db.run(
        `INSERT INTO users (username, password, role, phone, address, metadata) VALUES (?, ?, 'Seller', ?, ?, ?)`,
        [username, hashedPassword, phone, address, metadata], (err2) => {
          if (err2) {
            let err_msg = err2.message
            const matches = /^.+UNIQUE constraint failed: (.+)$/gm.exec(err2.message)
            if (matches != null)
              err_msg = `The given ${matches[1]} is already used by another account.`

            return res.status(500).json({ error: err_msg })
          }

          console.log(`Seller account created: ${username}`)

          res.status(201).json({
            message: "Seller added successfully", username
          })
        }
      )
    }
  )
})


export default router
