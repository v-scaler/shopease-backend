# ShopEase - E-Commerce Backend API

A robust RESTful API built with Django and Django REST Framework (DRF) featuring secure JWT authentication, dynamic cart management, order handling, and integrated Razorpay payment gateway verification.

## 🚀 Features
* **JWT Authentication**: Token-based authentication securing protected endpoints.
* **Product & Category Management**: Clean API endpoints to organize e-commerce inventory.
* **Cart & Order Processing**: Dynamic cart total calculations and automatic order generation.
* **Payment Gateway Integration**: Complete payment lifecycle using the Razorpay Python SDK.
* **Signature Verification**: Server-side HMAC-SHA256 signature verification for order status updates (`PENDING` $\rightarrow$ `PAID`).

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/v-scaler/shopease-backend.git
   cd shopease-backend

2. **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt

4. **Configure Environment Variables:**
    Create a .env file in the root directory and add your credentials:
    ```env
    SECRET_KEY=your_django_secret_key
    RAZORPAY_KEY_ID=your_razorpay_key_id
    RAZORPAY_KEY_SECRET=your_razorpay_key_secret

5. **Run migrations and start the server:**
    ```bash
    python manage.py migrate
    python manage.py runserver

### 🔌 API Endpoints Reference

| Endpoint | Method | Access | Description |
| :--- | :--- | :--- | :--- |
| `/api/token/` | `POST` | Public | Obtain JWT access and refresh tokens |
| `/api/token/refresh/` | `POST` | Public | Refresh expired JWT access tokens |
| `/api/products/` | `GET` | Public | List all available products |
| `/api/cart/` | `GET`, `POST` | Authenticated | Manage user shopping cart items |
| `/api/orders/create_razorpay_order/` | `POST` | Authenticated | Converts cart items into an order and initializes a Razorpay order |
| `/api/orders/verify_payment/` | `POST` | Authenticated | Verifies HMAC-SHA256 payment signature and marks order as Paid |
