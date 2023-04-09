from flask import (
    Flask,
    request,
    render_template,
    session,
    redirect,
    url_for,
    jsonify,
    make_response
)
import mysql.connector
import jwt
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = b's3cr3t_k3y'
db = mysql.connector.connect(
    host = "localhost",
    database = "nerdlabs",
    user = "admin",
    password = "pass"
)
db.autocommit = True
cur = db.cursor()

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return make_response(jsonify({'message': 'Token missing!'}), 401)

        try:
            data = jwt.decode(token, app.secret_key)
            cur.execute('SELECT username FROM customer WHERE username = %s', [data['username']])
            cust_id = cur.fetchone()
        except:
            return make_response(jsonify({
                'message': 'Token invalid!'
            }), 401)
        return func(cust_id, *args, **kwargs)
    return decorated

@app.route('/userid')
@token_required
def get_custid(cust_id):
    return make_response(jsonify({'cust_id': cust_id}), 200)

@app.route('/')
def root():
    return render_template('homepage.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        cur.execute("SELECT cust_id, password FROM customer WHERE username = %s", [username])
        user = cur.fetchone()
        if user is None:
            error = "Incorrect username."
        elif not password == user[1]:
            error = "Incorrect password."
        if error:
            return make_response(
                'Could not verify',
                401,
                {'WWW-Authenticate' : 'Basic realm = "Invalid credentials!"'}
            )
        else:
            token = jwt.encode({
                'cust_id': user[0],
                #'expiry': datetime.utcnow() + timedelta(minutes=30)
            }, app.secret_key)
            return make_response(jsonify({'token' : token}), 201)
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        if not password or not username:
            error = 'Username and password required.'
        if error is None:
            cur.execute("INSERT INTO test VALUES (%s, %s)", [username, password])
            return make_response('Successfully registered!', 201)
        else:
            return make_response('Invalid response!', 202)
    else:
        return render_template('auth/register.html')

@app.route('/data', methods=['GET', 'POST'])
def get_data():
    if request.method == 'POST':
        try:
            cur.execute(f"SELECT * FROM {request.form['data']}")
            keys = cur.column_names
            values = cur.fetchall()
            res = {
                "message": None,
                "title": request.form['data'],
                "attributes": keys,
                "records": values
            }
        except mysql.connector.Error as err:
            res = {
                "message": err
            }
    else:
        res = None
    return render_template('data.html', context=res)
   

# <---------------------------------------PRODUCTS-------------------------------------------------------------->

# Searching for a product using PID
@app.route('/product/id/<prod_id>')
def get_product(prod_id):
    prod_type = ['motherboard', 'gpu', 'processor', 'ram', 'storage', 'psu', 'cabinet']
    category = prod_type[int(prod_id)//100]
    res = dict()
    cur.execute(f'SELECT * FROM product WHERE product.prod_id = %s', [prod_id])
    keys = cur.column_names
    values = cur.fetchone()
    res['product'] = dict(zip(keys, values))
    cur.execute(f'SELECT * FROM {category} WHERE {category}.prod_id = %s', [prod_id])
    keys = cur.column_names
    values = cur.fetchone()
    res['meta'] = dict(zip(keys, values))
    cur.execute('SELECT * FROM review WHERE review.prod_id = %s', [prod_id])
    keys = cur.column_names
    values = cur.fetchall()
    review = list()
    for val in values:
        review.append(dict(zip(keys, val)))
    res['review'] = review
    res['category'] = category
    return render_template('product/product.html', context=res)

# Searching for a product using product brand
@app.route('/product/brand/<brand>')
def get_product_brand(brand):
    cur.execute("SELECT * FROM product WHERE brand = %s", [brand])
    keys = cur.column_names
    records = cur.fetchall()
    res = {
        "brand": brand,
        "attributes": keys,
        "products": records,
    }
    return render_template('product/brand.html', context=res)

# Get all products in a particular category
@app.route('/product/category/<category>')
def get_product_category(category):
    cur.execute(f"SELECT * FROM product, {category} WHERE product.prod_id={category}.prod_id")
    keys = cur.column_names
    records = cur.fetchall()
    res = {
        "category": category,
        "attributes": keys,
        "products": records
    }
    return render_template('product/category.html', context=res)

# <---------------------------------------CUSTOMER-------------------------------------------------------------->

# Get all customers in the database
@app.route('/customer')
def get_customers():
    cur.execute("SELECT * FROM customer")
    keys = cur.column_names
    records = cur.fetchall()
    res = {
        "attributes": keys,
        "customers": records
    }
    return render_template('customer/customer.html', context=res)

# Get customer details using customer ID
@app.route('/customer/id/<cust_id>')
def get_customer(cust_id):
    cur.execute("SELECT * FROM customer WHERE cust_id = %s", [cust_id])
    keys = cur.column_names
    records = cur.fetchall()
    res = {
        "attributes": keys,
        "customers": records
    }
    return render_template('customer/customer.html', context=res)

# Get customer details using customer username
@app.route('/customer/username/<username>')
def get_customer_username(username):
    cur.execute("SELECT * FROM customer WHERE username = %s", [username])
    keys = cur.column_names
    records = cur.fetchall()
    res = {
        "attributes": keys,
        "customers": records
    }
    return render_template('customer/customer.html', context=res)

# Get all customers in a particular pincode
@app.route('/customer/pincode/<addr_pin>')
def get_customer_pincode(addr_pin):
    cur.execute("SELECT * FROM customer WHERE addr_pin = %s", [addr_pin])
    keys = cur.column_names
    records = cur.fetchall()
    res = {
        "attributes": keys,
        "customers": records
    }
    return render_template('customer/customer.html', context=res)

# Get all customers in a particular city
@app.route('/customer/city/<city>')
def get_customer_city(city):
    cur.execute("SELECT * FROM customer WHERE addr_city = %s", [city])
    keys = cur.column_names
    records = cur.fetchall()
    res = {
        "attributes": keys,
        "customers": records
    }
    return render_template('customer/customer.html', context=res)

if __name__ == '__main__':
    app.run()
