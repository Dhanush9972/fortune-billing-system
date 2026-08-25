# 🏢 Fortune Power+ Enterprise CRM & Billing System

A secure, offline, Python-based Enterprise Resource Planning (ERP) and Customer Relationship Management (CRM) web application. Designed to generate pixel-perfect, highly customized PDF quotations, this tool allows businesses to manage clients, track inventory, and handle complex granular Indian taxation standards (CGST, SGST, IGST) dynamically.

**Developed by:** [@Dhanush9972](https://github.com/Dhanush9972)

---

## ✨ Key Features

* **👥 Smart CRM (Customer Database):** * Add and edit client profiles with custom avatars/logos.
    * Automatically tracks total order count and total lifetime business value per client.
* **📦 ERP Inventory Engine:** * Manage product catalogs with unique serial codes and item images.
    * Configure default granular tax overrides (CGST, SGST, IGST) on a per-item basis.
* **📄 Dynamic Quotation Generator:** * Smart dropdowns auto-fill customer details and inventory pricing/taxes instantly.
    * Mix predefined database items with manual, on-the-fly line items.
* **🖨️ Pixel-Perfect PDF Rendering:** * Uses `html2pdf.js` for high-fidelity A4 document generation.
    * Automatically injects transparent authorized signature overlays and massive enterprise banner headers.
    * Converts numerical grand totals into standard Indian Rupee words (e.g., "One Lakh Twenty Thousand...").
* **🌗 Modern UI & Security:** * Persistent Dark/Light mode user interface.
    * Protected by encrypted `Werkzeug` hashed login credentials.
    * Deployed locally using the high-performance `Waitress` WSGI production server.
* ## Data base system locally in .db format:
  To store the data of previous customers and item data and etc
---

## 🧮 How the Billing Engine Works

The backend handles mathematical breakdowns row-by-row before calculating the final grand total to ensure absolute accounting accuracy.

1.  **Base Amount:** `Quantity × Price Per Unit`
2.  **Granular Tax (Per Row):**
    * `CGST Amount = Base Amount × (CGST % / 100)`
    * `SGST Amount = Base Amount × (SGST % / 100)`
    * `IGST Amount = Base Amount × (IGST % / 100)`
3.  **Summary Aggregation:** The backend scans all items and dynamically groups matching tax percentages (e.g., combining all items with 9% SGST into a single neat summary row) for the final ledger.

---

## 🛠️ Installation & Setup

If you are setting this application up on a local machine or for a new client, follow these steps:

### 1. Clone the Repository:

bash
git clone [https://github.com/Dhanush9972/fortune-billing-system.git](https://github.com/Dhanush9972/fortune-billing-system.git)

cd fortune-billing-system

### 2. Create and Activate a Virtual Environment:
Isolate the project dependencies safely:

### Windows:

Bash
python -m venv .venv
.\.venv\Scripts\activate

### Mac/Linux:

Bash
python3 -m venv .venv
source .venv/bin/activate

### 3. Install Dependencies

Bash
pip install -r requirements.txt

### 4. Setup Client Assets
To ensure the PDFs render perfectly, place the following images inside the static/uploads/ folder:

logo.png: The main banner image (ideally 800x200px) that spans the top of the PDF.

signature.png: A transparent PNG of the authorized signatory.

(Note: The SQLite database fortune_billing.db will automatically generate on the first run if it does not exist).

### 5. Run the Production Server
Start the secure Waitress server:

Bash
python app.py
Access the App: Open a web browser and navigate to http://127.0.0.1:5000

### Having a database 
1.to store customer data
2.To store item datas

### Default Login:
 admin / admin123

### To change the password 
use update_pass.py 
1. go to update_pass.py and write the username and password of your choice
2. save the file
3. go to terminal and run the ("update_pass.py") file
4. use command : python update_pass.py

Developed by  ❤️ Dhanush R 

Github : ("Dhanush9972")
