# College Inventory Management System (CIMS) 🏛️
### Shri Shivaji Science College, Amravati
*Academic Session: 2025–2026 | B.Sc - Data Analytics & Computer Science*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.x-red.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Database](https://img.shields.io/badge/Database-SQLite3-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org)
[![UI](https://img.shields.io/badge/UI-Cyber%20Glassmorphism%20%7C%20Bootstrap%205-06b6d4.svg)](https://getbootstrap.com)
[![Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()

---

## 📖 Overview

The **College Inventory Management System (CIMS)** is a role-differentiated digital resource and inventory governance platform engineered for **Shri Shivaji Science College, Amravati**. It replaces manual paper logbooks and disconnected spreadsheets with a transparent, state-driven workflow for allocating laboratory apparatus, IT hardware, sports kits, and classroom stationery.

---

## ✨ Key Features

1. **Requisitions Without Login (For Students & Teachers)**:
   - Students and faculty members can browse the catalog and submit requisitions without needing an account.
   - Generates an instant, unique **Tracking Code** (e.g. `SSC-1006-105`).

2. **Live Work-in-Progress Tracking**:
   - 24/7 public tracking portal (`/track`).
   - Dynamic 4-stage visual timeline stepper:
     $$\text{Submitted} \longrightarrow \text{Faculty Review} \longrightarrow \text{Stock Reserved} \longrightarrow \text{Handover Completed}$$
   - Displays real-time status: **Pending**, **Approved**, **Declined** (with mandatory justification), or **Completed**.

3. **Faculty & Principal Role-Based Control Console (RBAC)**:
   - Secure cryptographic password hashing (PBKDF2/SHA-256 via Werkzeug).
   - **3-Stage Workflow Decision Engine**:
     - **Pending Review**: Inspect incoming requisitions with live stock balances.
     - **Approve**: Dynamically increments `reserved_quantity`, protecting against double-allocation.
     - **Decline**: Requires mandatory justification remarks to prevent arbitrary rejections.
     - **Complete / Handover**: Atomically deducts physical warehouse stock and releases reserved allocation.

4. **Dynamic Stock Reservation Mathematics**:
   $$\text{Available Quantity} = \text{Physical Quantity} - \text{Reserved Quantity}$$

5. **Inventory Master & Replenishment**:
   - Master registry across Laboratory, CS/IT, Sports, AV Aids, and Stationery.
   - One-click stock replenishment (`Stock In`) with audit logging.
   - Low-stock visual warnings when inventory reaches safety thresholds.

6. **Institutional Audit Trail & Ledger**:
   - Immutable log of all replenishments, reservations, releases, and withdrawals.
   - Print/Export-ready ledger for college NAAC accreditation and administrative audits.

7. **Aesthetics & UI**:
   - Ultra-modern **Cyber Black & Electric Blue Glassmorphism** theme.
   - Custom SVG emblem with the college Sanskrit motto: *श्री शिवाजी विज्ञान महाविद्यालय, अमरावती • विद्वान् सर्वत्र पूज्यते*.

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Backend** | Python (Flask 3.x) | REST routes, session management, workflow logic |
| **Security** | Werkzeug Security | PBKDF2/SHA-256 cryptographic password hashing |
| **Database** | SQLite3 | Relational data persistence with foreign keys |
| **Frontend** | HTML5, CSS3, JavaScript | Responsive Cyber Glassmorphism UI & micro-animations |
| **Styling** | Bootstrap 5 & Bootstrap Icons | Layout grid, responsive components |

---

## 🚀 Installation & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/college-inventory-management.git
cd college-inventory-management
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run the Web Application
```bash
python app.py
```

Open your browser at:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo Login Accounts

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Faculty (Teacher)** | `faculty@shivajisc.org` | `faculty123` | Department requests, Stock check, Restock |
| **Principal (Approver)** | `principal@shivajisc.org` | `principal123` | Multi-stage approvals, Remarks, Analytics |
| **Administrator** | `admin@shivajisc.org` | `admin123` | Full access, User provisioning, Asset registration |

---

## 👥 Project Team

**Department of Computer Science & Data Analytics (2025–2026)**  
**Shri Shivaji Science College, Amravati**

- **Yash Kale**
- **Athar Khan**
- **Anushka Deshmukh**
- **Shravani Ujjainkar**
- **Gayatri Kathale**

*Project Synopsis: College Inventory Management System (CIMS)*
