# API Endpoints for Postman Testing

All endpoints are prefixed with `/api/v1`

Base URL: `http://localhost:8000/api/v1`

## Users Endpoints

### Get All Users
```
GET /api/v1/users/
Query Parameters:
  - skip: int (default: 0) - Number of records to skip
  - limit: int (default: 100) - Maximum number of records to return
```

### Get User by ID
```
GET /api/v1/users/{user_id}
Path Parameters:
  - user_id: int - User ID
```

### Get User by Phone Number
```
GET /api/v1/users/phone/{phone_number}
Path Parameters:
  - phone_number: string - User's phone number (e.g., "+1234567890")
```

### Search Users by Name
```
GET /api/v1/users/search/name/{name}
Path Parameters:
  - name: string - User's name (partial match)
```

---

## Sessions Endpoints

### Get All Sessions
```
GET /api/v1/sessions/
Query Parameters:
  - skip: int (default: 0)
  - limit: int (default: 100)
```

### Get Session by ID
```
GET /api/v1/sessions/{session_id}
Path Parameters:
  - session_id: UUID - Session UUID
```

### Get Sessions by Owner
```
GET /api/v1/sessions/owner/{owner_id}
Path Parameters:
  - owner_id: int - Owner's user ID
```

### Get Sessions by Status
```
GET /api/v1/sessions/status/{status}
Path Parameters:
  - status: string - "active" or "closed"
```

### Get All Active Sessions
```
GET /api/v1/sessions/active/all
```

---

## Invoices Endpoints

### Get All Invoices
```
GET /api/v1/invoices/
Query Parameters:
  - skip: int (default: 0)
  - limit: int (default: 100)
```

### Get Invoice by ID
```
GET /api/v1/invoices/{invoice_id}
Path Parameters:
  - invoice_id: int - Invoice ID
```

### Get Invoices by Payer
```
GET /api/v1/invoices/payer/{payer_id}
Path Parameters:
  - payer_id: int - Payer's user ID
```

### Get Invoices by Session
```
GET /api/v1/invoices/session/{session_id}
Path Parameters:
  - session_id: UUID - Session UUID
```

### Get Pending Invoices
```
GET /api/v1/invoices/pending/all
```

---

## Items Endpoints

### Get All Items
```
GET /api/v1/items/
Query Parameters:
  - skip: int (default: 0)
  - limit: int (default: 100)
```

### Get Item by ID
```
GET /api/v1/items/{item_id}
Path Parameters:
  - item_id: int - Item ID
```

### Get Items by Invoice
```
GET /api/v1/items/invoice/{invoice_id}
Path Parameters:
  - invoice_id: int - Invoice ID
```

### Get Items by Debtor
```
GET /api/v1/items/debtor/{debtor_id}
Path Parameters:
  - debtor_id: int - Debtor's user ID
```

### Get Unpaid Items
```
GET /api/v1/items/unpaid/all
```

### Get Items by Payment
```
GET /api/v1/items/payment/{payment_id}
Path Parameters:
  - payment_id: int - Payment ID
```

---

## Payments Endpoints

### Get All Payments
```
GET /api/v1/payments/
Query Parameters:
  - skip: int (default: 0)
  - limit: int (default: 100)
```

### Get Payment by ID
```
GET /api/v1/payments/{payment_id}
Path Parameters:
  - payment_id: int - Payment ID
```

### Get Payments by Payer
```
GET /api/v1/payments/payer/{payer_id}
Path Parameters:
  - payer_id: int - Payer's user ID
```

### Get Payments by Receiver
```
GET /api/v1/payments/receiver/{receiver_id}
Path Parameters:
  - receiver_id: int - Receiver's user ID
```

### Get Payments Between Users
```
GET /api/v1/payments/between/{payer_id}/{receiver_id}
Path Parameters:
  - payer_id: int - Payer's user ID
  - receiver_id: int - Receiver's user ID
```

---

## Example Postman Requests

### 1. Get All Users
```
GET http://localhost:8000/api/v1/users/?skip=0&limit=10
```

### 2. Get User by ID
```
GET http://localhost:8000/api/v1/users/1
```

### 3. Get User by Phone
```
GET http://localhost:8000/api/v1/users/phone/+1234567890
```

### 4. Get Active Sessions
```
GET http://localhost:8000/api/v1/sessions/active/all
```

### 5. Get Pending Invoices
```
GET http://localhost:8000/api/v1/invoices/pending/all
```

### 6. Get Unpaid Items
```
GET http://localhost:8000/api/v1/items/unpaid/all
```

### 7. Get Payments Between Users
```
GET http://localhost:8000/api/v1/payments/between/1/2
```

---

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- **Scalar UI**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json

