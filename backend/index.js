import express from "express"
import cors from "cors"
import bodyParser from "body-parser"
import dotenv from 'dotenv'
import cookieParser from 'cookie-parser'

import userRoutes from "./routes/userRoutes.js"
import productRoutes from "./routes/productRoutes.js"


dotenv.config()

const PORT = process.env.EXPRESS_JS_BACKEND_PORT

const app = express()

app.use(cors())
app.use(cookieParser())
app.use(express.json())
app.use(bodyParser.json())
app.use(express.urlencoded({ extended: true }))

app.use("/api/users", userRoutes)
app.use("/api/products", productRoutes)

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`)
})
