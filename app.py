import random
from math import gcd
import streamlit as st
import csv
import os
import subprocess

def store_data_in_db(name, gender, encrypted_data, n):
    # Convert each item in encrypted_data to a string and pass n as an argument
    command = ["node", "prisma_api.js", name, gender, *map(str, encrypted_data), str(n)]
    
    # Run the command and handle any errors
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("Data successfully stored in the database.")
        print("Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Failed to store data in the database.")
        print("Error:", e.stderr)

# Miller-Rabin primality test for prime generation
def is_prime(n, k=5):  # number of tests
    if n <= 1:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    # Write n-1 as 2^s * d
    s, d = 0, n - 1
    while d % 2 == 0:
        d //= 2
        s += 1

    def miller_test(d, n):
        a = random.randint(2, n - 2)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            return True
        while d != n - 1:
            x = pow(x, 2, n)
            d *= 2
            if x == 1:
                return False
            if x == n - 1:
                return True
        return False

    for _ in range(k):
        if not miller_test(d, n):
            return False
    return True

# Generate a random prime number
def generate_prime(bits):
    while True:
        num = random.getrandbits(bits)
        if is_prime(num):
            return num

# Function to compute modular inverse
def modinv(a, m):
    m0, x0, x1 = m, 0, 1
    if m == 1:
        return 0
    while a > 1:
        q = a // m
        m, a = a % m, m
        x0, x1 = x1 - q * x0, x0
    if x1 < 0:
        x1 += m0
    return x1

# Key generation for Paillier encryption
def generate_paillier_keypair(bits=512):
    # Step 1: Choose two distinct large prime numbers p and q
    p = generate_prime(bits)
    q = generate_prime(bits)
    
    # Step 2: Compute n = p * q
    n = p * q
    n_sq = n * n
    
    # Step 3: Choose g, typically g = n + 1
    g = n + 1
    
    # Step 4: Compute lambda = lcm(p-1, q-1)
    lambda_val = (p - 1) * (q - 1) // gcd(p - 1, q - 1)
    
    # Step 5: Compute mu = (L(g^lambda mod n^2))^(-1) mod n
    def L(u, n):
        return (u - 1) // n

    g_lambda = pow(g, lambda_val, n_sq)
    mu = modinv(L(g_lambda, n), n)
    
    public_key = (n, g)
    private_key = (lambda_val, mu, n)
    
    return public_key, private_key, n

# Function to encrypt a message
def encrypt(public_key, plaintext):
    n, g = public_key
    n_sq = n * n
    
    # Step 1: Choose a random r where 1 <= r <= n-1 and gcd(r, n) = 1
    r = random.randint(1, n - 1)
    while gcd(r, n) != 1:
        r = random.randint(1, n - 1)
    
    # Step 2: Compute ciphertext c = (g^m * r^n) mod n^2
    c = (pow(g, plaintext, n_sq) * pow(r, n, n_sq)) % n_sq
    return c

# Function to store encrypted data in a CSV file
def store_encrypted_data_csv(filename, name, gender, encrypted_data, decrypted_data):
    # Check if the file exists to write headers only once
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Write header if the file doesn't already exist
        if not file_exists:
            writer.writerow(['Name', 'Gender', 'Dosage Name Ciphertext', 'Age Ciphertext', 'Dosage Ciphertext', 'Price Ciphertext',
                             'Decrypted Age', 'Decrypted Dosage', 'Decrypted Price'])

        # Write the user's encrypted and decrypted data
        writer.writerow([
            name, gender,
            encrypted_data[0], encrypted_data[1], encrypted_data[2], encrypted_data[3],
            decrypted_data[0], decrypted_data[1], decrypted_data[2]
        ])

# Function to convert string to a number (for encryption)
def string_to_number(s):
    return int.from_bytes(s.encode(), 'big')

# Function to decrypt a ciphertext
def decrypt(private_key, ciphertext):
    lambda_val, mu, n = private_key
    n_sq = n * n
    
    # Step 1: Compute L(c^lambda mod n^2)
    c_lambda = pow(ciphertext, lambda_val, n_sq)
    l_value = (c_lambda - 1) // n
    
    # Step 2: Compute the plaintext as L(c^lambda mod n^2) * mu mod n
    plaintext = (l_value * mu) % n
    return plaintext

# Function to read encrypted data from CSV and calculate sum of decrypted prices
def calculate_decrypted_total_price(filename, private_key):
    total_price = 0
    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                # Get the encrypted price from the row
                encrypted_price = int(row['Price Ciphertext'])

                # Decrypt the encrypted price
                decrypted_price = decrypt(private_key, encrypted_price)

                # Add to the total price
                total_price += decrypted_price
            except KeyError:
                print("Error: Missing expected columns in CSV file.")
                break
    
    return total_price

# Streamlit app for pharmacy data collection
st.title("Pharmacy Data Collection with Paillier Homomorphic Encryption (CSV Storage)")

# Generate Paillier keys
public_key, private_key, n = generate_paillier_keypair(bits=128)  # Use smaller bits for demonstration purposes

# Create a single tab for encrypting data
st.header("Enter Data for Encryption")

# Input for user's biodata
with st.form("user_form"):
    st.header("Enter Your Biodata")
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])

    # Input for medicine details
    st.header("Enter Medicine Information")
    dosage_name = st.text_input("Dosage Name")
    dosage = st.number_input("Dosage (in mg)", min_value=1)
    price = st.number_input("Price per unit", min_value=0.0)

    submitted = st.form_submit_button("Submit")

# If the user submits the form, encrypt and store the data
if submitted:
    if name and dosage_name:
        # Convert dosage name to a number before encryption
        dosage_name_num = string_to_number(dosage_name)
        
        # Encrypt sensitive data (dosage name, age, dosage, price)
        encrypted_dosage_name = encrypt(public_key, dosage_name_num)
        encrypted_age = encrypt(public_key, int(age))
        encrypted_dosage = encrypt(public_key, int(dosage))
        encrypted_price = encrypt(public_key, int(price))

        # Decrypt sensitive data (dosage name, age, dosage, price)
        decrypted_age = decrypt(private_key, encrypted_age)
        decrypted_dosage = decrypt(private_key, encrypted_dosage)
        decrypted_price = decrypt(private_key, encrypted_price)

        # Prepare encrypted data for storage
        encrypted_data = [encrypted_dosage_name, encrypted_age, encrypted_dosage, encrypted_price]
        decrypted_data = [decrypted_age, decrypted_dosage, decrypted_price]

        # Store encrypted and decrypted data in a CSV file
        filename = "pharmacy_data.csv"
        store_encrypted_data_csv(filename, name, gender, encrypted_data, decrypted_data)

        st.success("Data encrypted and stored in Database!")

        # Show encrypted data in the app
        st.write("Encrypted Dosage Name:", encrypted_dosage_name)
        st.write("Encrypted Age:", encrypted_age)
        st.write("Encrypted Dosage:", encrypted_dosage)
        st.write("Encrypted Price:", encrypted_price)

        # Store the data in the database
        store_data_in_db(name, gender, encrypted_data, n)

       
    else:
        st.error("Please fill in all the fields!")
