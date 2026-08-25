import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from num2words import num2words

app = Flask(__name__)
app.secret_key = 'fortune_enterprise_crm_secure_key_99'

# --- FILE UPLOAD CONFIGURATION ---
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect('fortune_billing.db')
    cursor = conn.cursor()
    
    # 1. Users Table (Admin)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    
    # 2. Customers Table (CRM)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE,
            title TEXT,
            name TEXT,
            phone TEXT,
            address TEXT,
            photo_filename TEXT,
            total_orders INTEGER DEFAULT 0,
            total_business REAL DEFAULT 0.0
        )
    ''')

    # 3. Inventory Items Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code TEXT UNIQUE,
            name TEXT,
            cost REAL,
            hsn_sac TEXT,
            unit TEXT,
            image_filename TEXT,
            default_cgst REAL DEFAULT 0.0,
            default_sgst REAL DEFAULT 0.0,
            default_igst REAL DEFAULT 0.0
        )
    ''')

    # 4. Locations & Default GST Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_name TEXT UNIQUE,
            tax_type TEXT -- e.g., 'LOCAL' (CGST+SGST) or 'INTERSTATE' (IGST)
        )
    ''')

    # 5. Advanced Quotations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_no TEXT UNIQUE,
            date TEXT,
            customer_id INTEGER,
            top_right_text TEXT,
            items_json TEXT,
            sub_total REAL,
            tax_breakdown_json TEXT,
            grand_total REAL,
            amount_in_words TEXT,
            pdf_filename TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')
    
    # Insert default admin if not exists
    cursor.execute('SELECT * FROM users WHERE username = "admin"')
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                       ('admin', generate_password_hash('admin123')))
    
    conn.commit()
    conn.close()

# Initialize the new robust database
init_db()

# --- AUTHENTICATION ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('fortune_billing.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- MAIN DASHBOARD (The 3 Buttons) ---
@app.route('/')
def dashboard():
    if 'logged_in' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')

# --- 1. CUSTOMER DATABASE ROUTE ---
@app.route('/customers', methods=['GET', 'POST'])
def manage_customers():
    if 'logged_in' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect('fortune_billing.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        
        # Handle Customer Photo Upload
        photo_filename = ""
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Ensure unique filename using timestamp
                unique_filename = f"cust_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                photo_filename = unique_filename

        # Generate Unique Customer ID (e.g., CUST-001)
        cursor.execute('SELECT COUNT(*) FROM customers')
        count = cursor.fetchone()[0] + 1
        customer_id = f"CUST-{count:03d}"

        cursor.execute('''
            INSERT INTO customers (customer_id, title, name, phone, address, photo_filename)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer_id, title, name, phone, address, photo_filename))
        conn.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('manage_customers'))

    cursor.execute('SELECT * FROM customers ORDER BY id DESC')
    customers = cursor.fetchall()
    conn.close()
    return render_template('customers.html', customers=customers)

# --- 2. ITEM & RATE DATA ROUTE ---
@app.route('/items', methods=['GET', 'POST'])
def manage_items():
    if 'logged_in' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect('fortune_billing.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        item_code = request.form['item_code']
        name = request.form['name']
        cost = float(request.form['cost'])
        hsn_sac = request.form['hsn_sac']
        unit = request.form['unit']
        cgst = float(request.form['cgst'])
        sgst = float(request.form['sgst'])
        igst = float(request.form['igst'])

        # Handle Item Image Upload
        image_filename = ""
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"item_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                image_filename = unique_filename

        try:
            cursor.execute('''
                INSERT INTO items (item_code, name, cost, hsn_sac, unit, image_filename, default_cgst, default_sgst, default_igst)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item_code, name, cost, hsn_sac, unit, image_filename, cgst, sgst, igst))
            conn.commit()
            flash('Item added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Item Code already exists!', 'error')
            
        return redirect(url_for('manage_items'))

    cursor.execute('SELECT * FROM items ORDER BY id DESC')
    items = cursor.fetchall()
    conn.close()
    return render_template('items.html', items=items)

# --- 3. QUOTATION BILLING ENGINE ---
@app.route('/quotation')
def new_quotation():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    conn = sqlite3.connect('fortune_billing.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch data for the dropdowns
    cursor.execute('SELECT * FROM customers ORDER BY name ASC')
    customers = cursor.fetchall()
    
    cursor.execute('SELECT * FROM items ORDER BY name ASC')
    items = cursor.fetchall()

    # Fetch Past Quotations for the Sidebar History
    cursor.execute('''
        SELECT q.id, q.quote_no, q.date, c.name, q.grand_total 
        FROM quotations q 
        JOIN customers c ON q.customer_id = c.id 
        ORDER BY q.id DESC LIMIT 15
    ''')
    history = cursor.fetchall()
    
    conn.close()
    return render_template('quotation.html', customers=customers, items=items, history=history)

@app.route('/generate', methods=['POST'])
def generate():
    if 'logged_in' not in session: return redirect(url_for('login'))

    # Safely grab form data using .get() to prevent missing key errors
    title = request.form.get('title', 'Mr.')
    customer_name = request.form.get('customer_name', '').strip()
    customer_address = request.form.get('customer_address', '').strip()
    top_right_text = request.form.get('top_right_text', '')

    # Connect to Database
    conn = sqlite3.connect('fortune_billing.db')
    cursor = conn.cursor()

    # Check if customer exists, or create a new one silently
    cursor.execute('SELECT id FROM customers WHERE name = ?', (customer_name,))
    cust = cursor.fetchone()

    if cust:
        customer_id = cust[0]
        cursor.execute('UPDATE customers SET title = ?, address = ? WHERE id = ?', (title, customer_address, customer_id))
    else:
        cursor.execute('SELECT COUNT(*) FROM customers')
        count = cursor.fetchone()[0] + 1
        new_cid = f"CUST-{count:03d}"
        cursor.execute('''
            INSERT INTO customers (customer_id, title, name, address, phone, photo_filename, total_orders, total_business) 
            VALUES (?, ?, ?, ?, "", "", 0, 0.0)
        ''', (new_cid, title, customer_name, customer_address))
        customer_id = cursor.lastrowid
        
    # Get all the array items from the form
    item_names = request.form.getlist('item_name[]')
    hsns = request.form.getlist('hsn[]')
    qtys = request.form.getlist('qty[]')
    units = request.form.getlist('unit[]')
    prices = request.form.getlist('price[]')
    cgsts = request.form.getlist('cgst[]')
    sgsts = request.form.getlist('sgst[]')
    igsts = request.form.getlist('igst[]')

    items_list = []
    sub_total = 0.0
    tax_breakdown = {} 
    
    # Loop through rows with extreme safety against blank fields
    for i in range(len(item_names)):
        if not item_names[i].strip(): 
            continue # Skip blank rows silently!
            
        qty = float(qtys[i]) if qtys[i] else 0.0
        price = float(prices[i]) if prices[i] else 0.0
        
        cgst_pct = float(cgsts[i]) if cgsts[i] else 0.0
        sgst_pct = float(sgsts[i]) if sgsts[i] else 0.0
        igst_pct = float(igsts[i]) if igsts[i] else 0.0
        
        total_gst_pct = cgst_pct + sgst_pct + igst_pct
        base_amount = qty * price
        sub_total += base_amount
        
        cgst_amount = base_amount * (cgst_pct / 100)
        sgst_amount = base_amount * (sgst_pct / 100)
        igst_amount = base_amount * (igst_pct / 100)
        
        total_gst_amount = cgst_amount + sgst_amount + igst_amount
        row_total = base_amount + total_gst_amount
        
        if cgst_pct > 0:
            label = f"CGST @ {cgst_pct}%"
            tax_breakdown[label] = tax_breakdown.get(label, 0) + cgst_amount
        if sgst_pct > 0:
            label = f"SGST @ {sgst_pct}%"
            tax_breakdown[label] = tax_breakdown.get(label, 0) + sgst_amount
        if igst_pct > 0:
            label = f"IGST @ {igst_pct}%"
            tax_breakdown[label] = tax_breakdown.get(label, 0) + igst_amount

        items_list.append({
            "index": len(items_list) + 1,
            "name": item_names[i],
            "hsn": hsns[i],
            "qty": qty,
            "unit": units[i],
            "price": price,
            "gst_percent": total_gst_pct,
            "gst_amount": total_gst_amount,
            "row_total": row_total
        })

    total_tax_amount = sum(tax_breakdown.values())
    grand_total = sub_total + total_tax_amount
    amount_in_words = num2words(int(round(grand_total)), lang='en_IN').title() + " Rupees Only"
    date_str = datetime.now().strftime("%d/%m/%Y")

    # Insert new quotation
    cursor.execute('''
        INSERT INTO quotations 
        (date, customer_id, top_right_text, items_json, sub_total, tax_breakdown_json, grand_total, amount_in_words) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date_str, customer_id, top_right_text, json.dumps(items_list), sub_total, json.dumps(tax_breakdown), grand_total, amount_in_words))
    
    quote_id = cursor.lastrowid
    quote_no = f"Quote-{quote_id}"
    cursor.execute('UPDATE quotations SET quote_no = ? WHERE id = ?', (quote_no, quote_id))
    
    # Update CRM Business Stats
    cursor.execute('UPDATE customers SET total_orders = total_orders + 1, total_business = total_business + ? WHERE id = ?', (grand_total, customer_id))
    
    conn.commit()
    conn.close()

    return redirect(url_for('view_bill', bill_id=quote_id))

@app.route('/bill/<int:bill_id>')
def view_bill(bill_id):
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    conn = sqlite3.connect('fortune_billing.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch the Quote AND the Customer details together
    cursor.execute('''
        SELECT q.*, c.title, c.name as customer_name, c.address as customer_address 
        FROM quotations q 
        JOIN customers c ON q.customer_id = c.id 
        WHERE q.id = ?
    ''', (bill_id,))
    bill = cursor.fetchone()
    conn.close()

    if bill:
        items = json.loads(bill['items_json'])
        tax_breakdown = json.loads(bill['tax_breakdown_json'])
        return render_template('template.html', bill=bill, items=items, tax_breakdown=tax_breakdown)
    return "Bill not found", 404

@app.route('/history')
def history():
    if 'logged_in' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect('fortune_billing.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT q.*, c.name as customer_name 
        FROM quotations q 
        JOIN customers c ON q.customer_id = c.id 
        ORDER BY q.id DESC
    ''')
    bills = cursor.fetchall()
    conn.close()
    return render_template('history.html', bills=bills)

# --- DELETE QUOTATION ROUTE ---
@app.route('/delete_quote/<int:quote_id>', methods=['POST'])
def delete_quote(quote_id):
    if 'logged_in' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect('fortune_billing.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM quotations WHERE id = ?', (quote_id,))
    conn.commit()
    conn.close()
    flash('Quotation deleted permanently!', 'success')
    return redirect(url_for('history'))

# --- DELETE ITEM ROUTE ---
@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    if 'logged_in' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect('fortune_billing.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    flash('Item deleted permanently!', 'success')
    return redirect(url_for('manage_items'))

# --- EDIT & DELETE CUSTOMER ROUTES ---
@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    if 'logged_in' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect('fortune_billing.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
    conn.commit()
    conn.close()
    flash('Customer deleted permanently!', 'success')
    return redirect(url_for('manage_customers'))

@app.route('/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer(customer_id):
    if 'logged_in' not in session: return redirect(url_for('login'))
    conn = sqlite3.connect('fortune_billing.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        
        cursor.execute('''
            UPDATE customers 
            SET title = ?, name = ?, phone = ?, address = ?
            WHERE id = ?
        ''', (title, name, phone, address, customer_id))
        conn.commit()
        conn.close()
        flash('Customer details updated successfully!', 'success')
        return redirect(url_for('manage_customers'))

    cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
    customer = cursor.fetchone()
    conn.close()
    return render_template('edit_customer.html', customer=customer)

# --- SERVER RUNNER ---
if __name__ == '__main__':
    import os
    from waitress import serve
    
    # Read Render's dynamic port, or use 5000 as a fallback for local testing
    port = int(os.environ.get("PORT", 5000))
    
    print(f"Starting Advanced Fortune Power+ CRM on port {port}...")
    
    # Bind to '0.0.0.0' so Render can see the open port
    serve(app, host='0.0.0.0', port=port)
