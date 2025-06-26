import sqlite3lib from 'sqlite3'

const sqlite3 = sqlite3lib.verbose()

// Initialize database
const db = new sqlite3.Database('./app.db', err => {
  if (err)
    console.error("Error opening database:", err)
  else
    console.log("Database connected successfully.")
})

// Create a users table if it doesn't exist
db.run(`CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE,
  password TEXT,
  role TEXT,
  phone TEXT UNIQUE,
  address TEXT UNIQUE,
  metadata TEXT UNIQUE
)`, (err) => {
  if (err)
    console.log("Error creating table:", err)
})


export { db }
