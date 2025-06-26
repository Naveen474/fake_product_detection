import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk, messagebox
import requests, serial, cv2, uuid
from pyzbar.pyzbar import decode


ser = serial.Serial("COM6", 9600)

API_BASE = "http://localhost:5000/api"


def label_to_key(label: str):
  words = label.split()
  return words[0].lower() + "".join(w.title() for w in words[1:])


user_fields = {
  "Manufacturer": ["Company Name", "License Number", "Manager", "Brand", "Phone", "Address"],
  "Seller": ["Company Name", "Phone", "Manager", "Brand", "Address"],
  "Customer": ["Full Name", "Phone", "Address"],
}

product_labels = {
  "productId": "Product ID",
  "name": "Product Name",
  "batchNumber": "Batch Number",
  "manufacturingDate": "Manufacturing Date",
  "description": "Description",
  "price": "Price",
}

padding = {"ipadx": 5, "ipady": 5, "padx": 5, "pady": 5}


class BlockchainApp:
  def __init__(self, root):
    self.root = root
    self.root.title("Blockchain Product Verification")
    self.root.minsize(600, 400)
    self.root.focus()
    self.session = {}
    self.username_var = tk.StringVar()
    self.password_var = tk.StringVar()
    self.role_var = tk.StringVar(value="Customer")
    self.product_id_var = tk.StringVar()
    self.status_var = tk.StringVar(value="Not logged in")
    self.auth_frame = ttk.Frame(root, padding=20)
    self.auth_frame.grid_columnconfigure((0,), weight=1, uniform="Silent_Creme")
    self.auth_frame.grid_columnconfigure((1,), weight=2, uniform="Silent_Creme")
    self.main_frame = ttk.Frame(root, padding=20)
    self.main_frame.grid_columnconfigure((0,), weight=2, uniform="Silent_Creme")
    self.build_auth_ui()
    self.build_main_ui()
    self.auth_frame.pack(expand=True)

  def build_auth_ui(self):
    frame = self.auth_frame
    ttk.Label(frame, text="Fake Product Detection", font=("Arial", 24, "bold")).grid(
      row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=(10, 40)
    )
    ttk.Label(frame, text="Username").grid(row=1, column=0, sticky="nsew", **padding)

    ttk.Entry(frame, textvariable=self.username_var).grid(row=1, column=1, sticky="nsew", **padding)
    ttk.Label(frame, text="Password").grid(row=2, column=0, sticky="nsew", **padding)

    ttk.Entry(frame, textvariable=self.password_var, show="*").grid(row=2, column=1, sticky="nsew", **padding)
    ttk.Label(frame, text="Role").grid(row=3, column=0, sticky="nsew", **padding)

    role_box = ttk.Combobox(
      frame, textvariable=self.role_var, values=["Manufacturer", "Seller", "Customer"], state="readonly"
    )
    role_box.grid(row=3, column=1, sticky="nsew", **padding)

    ttk.Button(frame, text="Login", command=self.login).grid(row=4, column=0, sticky="nsew", **padding)
    ttk.Button(frame, text="Register", command=self.register).grid(row=4, column=1, sticky="nsew", **padding)

  def build_main_ui(self):
    frame = self.main_frame
    ttk.Label(frame, textvariable=self.status_var, font=("Arial", 24, "bold")).grid(
      row=0, column=0, pady=(10, 40), sticky="nsew"
    )
    ttk.Button(frame, text="Verify Product (QR)", command=self.verify_product).grid(
      row=1, column=0, sticky="nsew", **padding
    )

    self.sell_btn = ttk.Button(frame, text="Sell Product", command=self.sell_product)
    self.register_prod_btn = ttk.Button(
      frame, text="Register Product", command=self.open_register_product_window
    )

    self.add_seller_btn = ttk.Button(frame, text="Add Seller", command=self.open_add_seller_window)
    ttk.Button(frame, text="Logout", command=self.logout).grid(row=5, column=0, sticky="nsew", **padding)

  def switch_to_main_ui(self):
    self.auth_frame.pack_forget()
    self.status_var.set(f"Welcome {self.session['username']} ({self.session['role']})")

    if self.session["role"] == "Manufacturer":
      self.add_seller_btn.grid(row=4, column=0, sticky="nsew", **padding)
      self.register_prod_btn.grid(row=3, column=0, sticky="nsew", **padding)

    else:
      self.add_seller_btn.grid_forget()
      self.register_prod_btn.grid_forget()

    if self.session["role"] == "Customer":
      self.sell_btn.grid_forget()
    else:
      self.sell_btn.grid(row=2, column=0, sticky="nsew", **padding)

    self.main_frame.pack(expand=True)

  def logout(self):
    self.session = {}
    self.username_var.set("")
    self.password_var.set("")
    self.role_var.set("Customer")
    self.status_var.set("Not logged in")
    self.main_frame.pack_forget()
    self.auth_frame.pack()

  def register(self):
    role = self.role_var.get().strip()
    confirm_password = tk.StringVar()

    window = tk.Toplevel(self.root)
    window.title(f"{role} Registration")
    window.minsize(400, 400)

    frame = ttk.Frame(window, padding=20)
    frame.grid_columnconfigure((0,), weight=1, uniform="Silent_Creme")
    frame.grid_columnconfigure((1,), weight=2, uniform="Silent_Creme")

    submit_btn = ttk.Button(frame, text="Submit", command=lambda: submit_extended_registration(fields))

    def submit_extended_registration(fields):
      payload = {k: v.get().strip() for k, v in fields.items()}

      if not payload["username"] or not payload["password"]:
        return messagebox.showerror("Input Error", "Username and Password are required.")

      if self.password_var.get() != confirm_password.get():
        return messagebox.showerror("Input Error", "Confirm Password is not as same as the Password.")

      if role not in ("Manufacturer", "Customer"):
        return messagebox.showerror("Unsupported Role", f"Registration for role {role} not supported here.")

      submit_btn.config(text="Submitting...")
      payload["role"] = role

      try:
        res = requests.post(f"{API_BASE}/users/register", json=payload)
        if res.status_code == 201:
          data = res.json()
          self.session = {"username": data["username"], "role": data["role"]}
          messagebox.showinfo("Registered", f"Account created!")
          self.switch_to_main_ui()
          window.destroy()

        else:
          messagebox.showerror(
            "Registration Failed", res.json().get("error", "Registration failed due to an unknown error.")
          )

      except Exception as e:
        messagebox.showerror("Error", str(e))

    if role == "Seller":
      return messagebox.showerror("Unauthorized", "You can't register as a Seller.")

    frame.pack()
    fields = {"username": self.username_var, "password": self.password_var}

    ttk.Label(frame, text="Username").grid(row=0, column=0, sticky="ew", **padding)
    ttk.Entry(frame, textvariable=fields["username"]).grid(row=0, column=1, sticky="ew", **padding)

    ttk.Label(frame, text="Password").grid(row=1, column=0, sticky="ew", **padding)
    ttk.Entry(frame, textvariable=fields["password"], show="*").grid(
      row=1, column=1, sticky="ew", **padding
    )

    ttk.Label(frame, text="Confirm Password").grid(row=2, column=0, sticky="ew", **padding)
    ttk.Entry(frame, textvariable=confirm_password, show="*").grid(
      row=2, column=1, sticky="ew", **padding
    )

    for row, attr in enumerate(user_fields[role], 3):
      display_text = label_to_key(attr)
      fields[display_text] = tk.StringVar()
      ttk.Label(frame, text=attr).grid(row=row, column=0, sticky="ew", **padding)
      ttk.Entry(frame, textvariable=fields[display_text]).grid(row=row, column=1, sticky="ew", **padding)
    submit_btn.grid(row=row + 1, column=0, columnspan=2, sticky="nsew", **padding)

  def login(self):
    payload = {
      "username": self.username_var.get().strip(),
      "password": self.password_var.get().strip(),
      "role": self.role_var.get().strip(),
    }

    if not payload["username"] or not payload["password"]:
      return messagebox.showerror("Input Error", "Username and Password are required.")

    try:
      res = requests.post(f"{API_BASE}/users/login", json=payload)
      if res.status_code == 200:
        data = res.json()
        self.session = {"username": data["username"], "role": data["role"]}
        messagebox.showinfo("Login Success", f"Welcome {data['username']} ({data['role']})")
        self.switch_to_main_ui()

      else:
        messagebox.showerror(
          "Login Failed",
          res.json().get("error", "Login failed due to an unknown error.")
        )

    except Exception as e:
      messagebox.showerror("Error", str(e))

  def scan_product_qr_code(self, win_title, result_var=None, callback=None):
    cap = cv2.VideoCapture(0)
    window = tk.Toplevel(self.root)
    window.title(win_title)
    window.minsize(400, 400)

    win_frame = ttk.Frame(window, padding=20)
    win_frame.grid_columnconfigure((0,), weight=1, uniform="Silent_Creme")
    win_frame.grid_columnconfigure((1,), weight=2, uniform="Silent_Creme")
    win_frame.pack()

    camera_feed = tk.Label(win_frame)
    camera_feed.grid(row=0, column=0, columnspan=2, sticky="ew")

    def on_close():
      cap.release()
      window.destroy()

    def update_frame():
      ret, frame = cap.read()
      if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        camera_feed.imgtk = imgtk
        camera_feed.configure(image=imgtk)
        decoded_objs = decode(frame)

        for obj in decoded_objs:
          qr_data = obj.data.decode("utf-8")
          if result_var is not None:
            result_var.set(qr_data)

          if callback:
            callback(qr_data)
            return on_close()

      camera_feed.after(10, update_frame)

    window.protocol("WM_DELETE_WINDOW", on_close)
    update_frame()
    return win_frame, on_close

  def verify_product(self):
    def submit_verification_request(product_id):
      try:
        if product_id is None:
          return

        res = requests.post(f"{API_BASE}/products/verify/" + product_id, cookies=self.session)
        status = ("GENUINE" if res.status_code == 200 and res.json().get("valid") else "FAKE")
        ser.write(f"{status}\n".encode())

        if status == "GENUINE":
          data = res.json()
          messagebox.showinfo(
            "Verified",
            f'Product ID: {data.get("productId")}\nManufacturer: {data.get("manufacturer")}.\n'
            f'Current Owner: {data.get("currentOwner")}',
          )

        else:
          messagebox.showerror("Invalid", res.json().get("message", "Product not found or tampered."))

      except Exception as e:
        messagebox.showerror("Error", str(e))

    self.scan_product_qr_code("Verify Product", callback=submit_verification_request)

  def sell_product(self):
    if not self.session:
      return messagebox.showerror("Login Required", "Please login to sell products.")

    role = self.session.get("role")
    if role not in ("Manufacturer", "Seller"):
      return messagebox.showerror("Unauthorized", "Only Manufacturer or Seller can sell products.")

    pid_var, to_user_var, to_user_type_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
    frame, on_close = self.scan_product_qr_code("Sell Product", pid_var)
    ttk.Label(frame, text="Product ID").grid(row=1, column=0, sticky="ew", **padding)
    ttk.Entry(frame, textvariable=pid_var).grid(row=1, column=1, sticky="ew", **padding)

    ttk.Label(frame, text="Recipient Username").grid(row=2, column=0, sticky="ew", **padding)
    ttk.Entry(frame, textvariable=to_user_var).grid(row=2, column=1, sticky="ew", **padding)

    ttk.Label(frame, text="Recipient User Type").grid(row=3, column=0, sticky="ew", **padding)
    ttk.Entry(frame, textvariable=to_user_type_var).grid(row=3, column=1, sticky="ew", **padding)

    def submit_transfer(var = None):
      product_id = pid_var.get().strip()
      to_username = to_user_var.get().strip()
      to_user_type = to_user_type_var.get().strip()
      if not product_id or not to_username or not to_user_type:
        return messagebox.showerror("Input Error", "Both fields are required.")
      try:
        res = requests.post(
          f"{API_BASE}/products/transfer",
          cookies=self.session,
          json={"productId": product_id, "toUsername": to_username, "toUserType": to_user_type},
        )
        if res.status_code == 200:
          messagebox.showinfo(
            "Transfer Success", f"Product {product_id} transferred to {to_username} ({to_user_type}).",
          )
        else:
          messagebox.showerror(
            "Transfer Failed",
            res.json().get("error", "Transfer failed with an unknown error."),
          )
      except Exception as e:
        messagebox.showerror("Error", str(e))
      finally:
        on_close()

    ttk.Button(frame, text="Sell", command=submit_transfer).grid(
      row=4, columnspan=2, pady=10, sticky="nsew"
    )

  def open_add_seller_window(self):
    if not self.session or self.session.get("role") != "Manufacturer":
      return messagebox.showerror(
        "Unauthorized", "Only manufacturers can add sellers."
      )
    window = tk.Toplevel(self.root)
    window.title("Add New Seller")
    window.minsize(400, 400)
    frame = ttk.Frame(window, padding=20)
    frame.grid_columnconfigure((0,), weight=1, uniform="Silent_Creme")
    frame.grid_columnconfigure((1,), weight=2, uniform="Silent_Creme")
    frame.pack()
    field_vars = {}
    for idx, attr in enumerate(
      ["name", "username", "password"] + user_fields["Seller"]
    ):
      display_text = label_to_key(attr)
      ttk.Label(frame, text=display_text).grid(
        row=idx, column=0, sticky="ew", **padding
      )
      field_vars[display_text] = tk.StringVar()
      ttk.Entry(
        frame,
        textvariable=field_vars[display_text],
        show="*" if display_text == "password" else "",
      ).grid(row=idx, column=1, sticky="ew", **padding)

    def submit_seller():
      payload = {k: v.get().strip() for k, v in field_vars.items()}
      if not all(payload.values()):
        return messagebox.showerror("Input Error", "All fields are required.")
      payload["manufacturer"] = self.session[
        "username"
      ]  # identify who is adding this seller
      try:
        res = requests.post(f"{API_BASE}/users/add-seller", json=payload)
        if res.status_code == 201:
          messagebox.showinfo("Success", f"Seller added!")
          window.destroy()
        else:
          messagebox.showerror(
            "Failed",
            res.json().get("error", "Unable to register seller, caused by an unknown error."),
          )
      except Exception as e:
        messagebox.showerror("Error", str(e))

    ttk.Button(frame, text="Add Seller", command=submit_seller).grid(
      row=len(field_vars), columnspan=2, sticky="nsew", **padding
    )

  def open_register_product_window(self):
    if not self.session:
      return messagebox.showerror(
        "Login Required", "Please log in to register products."
      )
    if self.session.get("role") != "Manufacturer":
      return messagebox.showerror(
        "Unauthorized", "Only manufacturers can register products."
      )
    window = tk.Toplevel(self.root)
    window.title("Register New Product")
    window.minsize(400, 300)
    frame = ttk.Frame(window, padding=20)
    frame.grid_columnconfigure((0,), weight=1, uniform="Silent_Creme")
    frame.grid_columnconfigure((1,), weight=2, uniform="Silent_Creme")
    frame.pack()
    field_vars = {}
    for idx, (key, value) in enumerate(product_labels.items()):
      if key == 'productId':
        field_vars[key] = tk.StringVar(value=str(uuid.uuid4())[:8])
        continue
      ttk.Label(frame, text=value).grid(row=idx, column=0, sticky="ew", **padding)
      field_vars[key] = tk.StringVar()
      ttk.Entry(frame, textvariable=field_vars[key]).grid(
        row=idx, column=1, sticky="ew", **padding
      )

    def submit_product():
      product_data = {k: field_vars[k].get().strip() for k in product_labels}
      if not all(product_data.values()):
        return messagebox.showerror("Input Error", "All fields are required.")
      try:
        res = requests.post(
          f"{API_BASE}/products/register",
          json=product_data,
          cookies=self.session,
        )
        if res.status_code == 200:
          messagebox.showinfo("Success", f"Product {product_data['productId']} registered.")
          window.destroy()
        else:
          messagebox.showerror(
            "Failed",
            res.json().get("error", "Registration failed with an unknown error."),
          )
      except Exception as e:
        messagebox.showerror("Error", str(e))

    ttk.Button(frame, text="Submit", command=submit_product).grid(
      row=7, columnspan=2, sticky="nsew", **padding
    )


if __name__ == "__main__":
  root = tk.Tk()
  app = BlockchainApp(root)
  root.mainloop()
