from pydantic import BaseModel, Field, EmailStr
from typing import Literal, Optional, Dict, List
from datetime import datetime
from decimal import Decimal
import uuid

# Credit Pack Definitions
CREDIT_PACKS = {
    "starter": {
        "id": "pack_starter",
        "name": "Starter Pack",
        "price": 5.00,
        "credits": 10,
        "description": "Perfect for occasional decisions",
        "popular": False
    },
    "power": {
        "id": "pack_power", 
        "name": "Power Pack",
        "price": 10.00,
        "credits": 25,
        "description": "Best value for regular users",
        "popular": True
    },
    "boost": {
        "id": "pack_boost",
        "name": "Pro Boost",
        "price": 8.00,
        "credits": 40,
        "description": "Monthly add-on for Pro users",
        "popular": False
    }
}

# Subscription Plans for Dodo Payments
SUBSCRIPTION_PRODUCTS = {
    "pro_monthly": {
        "id": "sub_pro_monthly",
        "name": "Pro Plan - Monthly",
        "price": 12.00,
        "interval": "monthly",
        "description": "Unlimited decisions with premium features",
        "features": [
            "Unlimited decisions",
            "All 8 advisor personalities", 
            "Voice input/output",
            "Claude + GPT-4o access",
            "Visual tools panel",
            "PDF exports"
        ]
    }
}

# Payment Request Models
class PaymentRequest(BaseModel):
    product_id: str
    quantity: int = 1
    user_email: str
    customer_info: Optional[Dict] = None
    redirect_url: Optional[str] = None

class SubscriptionRequest(BaseModel):
    plan_id: str = "pro_monthly"
    user_email: str
    customer_info: Optional[Dict] = None
    billing_cycle: str = "monthly"

class WebhookPayload(BaseModel):
    type: str
    data: Dict
    timestamp: datetime
    id: str

# Database Models  
class PaymentDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payment_id: Optional[str] = None
    dodo_payment_id: Optional[str] = None
    user_id: str
    user_email: str
    product_id: str
    product_name: str
    amount: Decimal
    currency: str = "USD"
    quantity: int = 1
    credits_amount: int = 0
    status: Literal["pending", "succeeded", "failed", "cancelled"] = "pending"
    payment_method: Optional[str] = None
    dodo_customer_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = None

class SubscriptionDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subscription_id: Optional[str] = None
    dodo_subscription_id: Optional[str] = None
    user_id: str
    user_email: str
    plan_id: str
    plan_name: str
    amount: Decimal
    currency: str = "USD"
    billing_cycle: str = "monthly"
    status: Literal["active", "cancelled", "past_due", "incomplete", "trialing"] = "active"
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    cancelled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = None

# Response Models
class PaymentResponse(BaseModel):
    payment_id: str
    payment_link: str
    status: str
    amount: Decimal
    currency: str

class SubscriptionResponse(BaseModel):
    subscription_id: str
    status: str
    plan_name: str
    amount: Decimal
    current_period_end: Optional[datetime] = None

class BillingHistory(BaseModel):
    payments: List[PaymentDocument]
    subscriptions: List[SubscriptionDocument]
    total_spent: Decimal
    active_subscription: Optional[SubscriptionDocument] = None

class CustomerInfo(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    country: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None