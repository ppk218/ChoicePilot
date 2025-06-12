import os
import json
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from payment_models import (
    PaymentRequest, SubscriptionRequest, PaymentDocument, SubscriptionDocument,
    CREDIT_PACKS, SUBSCRIPTION_PRODUCTS, PaymentResponse, SubscriptionResponse,
    CustomerInfo
)

logger = logging.getLogger(__name__)

class DodoPaymentsService:
    def __init__(self, api_key: str, base_url: str = "https://api.dodopayments.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    async def create_payment_link(
        self, 
        request: PaymentRequest, 
        user_id: str,
        return_url: str = None
    ) -> PaymentResponse:
        """Create a payment link for credit pack purchase"""
        try:
            # Get product details
            if request.product_id not in CREDIT_PACKS:
                raise ValueError(f"Invalid product ID: {request.product_id}")
            
            product = CREDIT_PACKS[request.product_id]
            total_amount = product["price"] * request.quantity
            total_credits = product["credits"] * request.quantity
            
            # Create payment link using Dodo's static link format
            product_id = product["id"]  # This should be the actual Dodo product ID
            payment_url = f"{self.base_url}/buy/{product_id}"
            
            # Add query parameters
            params = {
                "quantity": request.quantity,
                "email": request.user_email,
                "redirect_url": return_url or f"{os.getenv('FRONTEND_URL')}/billing/success"
            }
            
            # Add customer info if provided
            if request.customer_info:
                params.update(request.customer_info)
            
            # Build full URL with parameters
            param_string = "&".join([f"{k}={v}" for k, v in params.items()])
            payment_link = f"{payment_url}?{param_string}"
            
            # Store payment record in database
            payment_doc = PaymentDocument(
                user_id=user_id,
                user_email=request.user_email,
                product_id=request.product_id,
                product_name=product["name"],
                amount=total_amount,
                quantity=request.quantity,
                credits_amount=total_credits,
                status="pending",
                metadata={
                    "dodo_product_id": product_id,
                    "payment_link": payment_link,
                    "return_url": return_url
                }
            )
            
            # Insert to database (this will be done in the route handler)
            
            return PaymentResponse(
                payment_id=payment_doc.id,
                payment_link=payment_link,
                status="pending",
                amount=total_amount,
                currency="USD"
            )
            
        except Exception as e:
            logger.error(f"Error creating payment link: {str(e)}")
            raise
    
    async def create_subscription(
        self,
        request: SubscriptionRequest,
        user_id: str,
        return_url: str = None
    ) -> SubscriptionResponse:
        """Create a subscription for Pro plan"""
        try:
            # Get plan details
            if request.plan_id not in SUBSCRIPTION_PRODUCTS:
                raise ValueError(f"Invalid plan ID: {request.plan_id}")
            
            plan = SUBSCRIPTION_PRODUCTS[request.plan_id]
            
            # For Dodo Payments, we'll use their subscription API
            subscription_data = {
                "product_id": plan["id"],  # This should be the actual Dodo subscription product ID
                "customer": {
                    "email": request.user_email,
                    **request.customer_info if request.customer_info else {}
                },
                "billing_cycle": request.billing_cycle,
                "metadata": json.dumps({
                    "user_id": user_id,
                    "plan_type": "pro"
                }),
                "success_url": return_url or f"{os.getenv('FRONTEND_URL')}/billing/success",
                "cancel_url": f"{os.getenv('FRONTEND_URL')}/billing/cancelled"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/subscriptions",
                    headers=self.headers,
                    json=subscription_data
                )
                response.raise_for_status()
                subscription_result = response.json()
            
            # Store subscription record
            subscription_doc = SubscriptionDocument(
                dodo_subscription_id=subscription_result.get("id"),
                user_id=user_id,
                user_email=request.user_email,
                plan_id=request.plan_id,
                plan_name=plan["name"],
                amount=plan["price"],
                billing_cycle=request.billing_cycle,
                status="active",
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                metadata={
                    "dodo_subscription_id": subscription_result.get("id"),
                    "checkout_url": subscription_result.get("checkout_url")
                }
            )
            
            return SubscriptionResponse(
                subscription_id=subscription_doc.id,
                status="active",
                plan_name=plan["name"],
                amount=plan["price"],
                current_period_end=subscription_doc.current_period_end
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Dodo API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise
    
    async def verify_webhook_signature(self, payload: bytes, signature: str, timestamp: str) -> bool:
        """Verify webhook signature from Dodo Payments"""
        try:
            # Implement webhook signature verification
            # This would use the webhook secret to verify the signature
            webhook_secret = os.getenv("DODO_WEBHOOK_SECRET")
            
            # For now, we'll implement basic verification
            # In production, you'd use the standardwebhooks library
            import hmac
            import hashlib
            
            expected_signature = hmac.new(
                webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    async def get_payment_status(self, dodo_payment_id: str) -> Dict[str, Any]:
        """Get payment status from Dodo Payments"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/payments/{dodo_payment_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting payment status: {str(e)}")
            raise
    
    async def cancel_subscription(self, dodo_subscription_id: str) -> bool:
        """Cancel a subscription"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/subscriptions/{dodo_subscription_id}/cancel",
                    headers=self.headers
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return False