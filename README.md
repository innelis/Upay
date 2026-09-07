# UPay 💳

**A simulated digital wallet demonstrating the backend architecture behind fintech applications.**

UPay is an Opay-inspired wallet application where all money is completely fictional.

The project focuses on demonstrating how financial applications handle authentication, PIN-protected transactions, wallet balances, transaction records, peer-to-peer transfers, and payment flows — without connecting to real banks, cards, or payment providers.

![UPay screenshot](screenshott.png)

> ⚠️ **DEMO ONLY:** UPay does not process real money. All balances, transactions, networks, bills, and payments exist entirely inside the application's demo database.

## ✨ What You Can Try

After creating a demo account, you can:

* 💰 Start with a simulated **₦5,000 balance**
* 💳 Simulate **funding your wallet**
* 💸 Send demo money to another UPay user
* 📱 Purchase simulated airtime
* 💡 Pay simulated electricity, DSTV, internet, and water bills
* 📜 Browse your complete transaction history
* 🧾 Open individual transaction receipts
* 🔐 Protect sensitive transactions with a transaction PIN
* 👤 Manage your profile

You can create multiple demo accounts to test transfers between users.

## 🛠️ Built With

* **Python**
* **Flask**
* **Flask-SQLAlchemy**
* **Flask-Login**
* **Jinja2**
* **SQLite**
* **Vanilla CSS**
* **JavaScript**

No real payment processor or financial institution is connected to the application.

## ⚙️ How It Works

### Wallet

Each demo account has a wallet balance stored in the database.

Funding, transfers, airtime purchases, and bill payments update the balance within database transactions.

### Transactions

Every financial action creates a transaction record with a unique reference.

This provides an auditable history of activity and allows each transaction to have its own receipt.

### Peer-to-Peer Transfers

Users can transfer simulated funds to another UPay account using identifying information such as:

* Username
* Phone number
* Account number

The money moves only between users inside the demo database.

### Transaction PIN

Sensitive actions require the user's four-digit transaction PIN.

The PIN is stored securely as a hash rather than plain text.

## 🎯 What This Project Demonstrates

UPay demonstrates practical backend concepts relevant to fintech applications:

* Authentication and authorization
* Password and PIN hashing
* Relational database design
* Financial transaction modelling
* Atomic database operations
* Transaction history and audit trails
* Form validation
* Session management
* Receipt generation
* Server-side rendering
* Responsive UI development

## 🚀 Possible Improvements

Future versions could include:

* KYC and account verification
* Spending limits
* Savings goals
* Scheduled payments
* Recurring transactions
* Admin dashboard
* Transaction dispute system
* Notifications
* PostgreSQL deployment
* Integration with a real payment provider in a production environment

## 📁 Project Structure

```text
upay/
├── app.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── app_base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── fund.html
│   ├── transfer.html
│   ├── airtime.html
│   ├── bills.html
│   ├── history.html
│   ├── receipt.html
│   └── profile.html
└── static/
    ├── css/style.css
    └── js/app.js
```
