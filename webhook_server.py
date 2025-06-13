#!/usr/bin/env python3
from fastapi import FastAPI, Request, HTTPException, status
import uvicorn
import hmac
import hashlib
import json
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Webhook Test Server")

# Webhook secret
WEBHOOK_SECRET = "9aKvjEw7z892XhGM4ajh0mAH"  # Without the 'whsec_' prefix

@app.post("/api/webhooks/dodo")
async def handle_dodo_webhook(request: Request):
    """Handle webhooks from Dodo Payments with enhanced security"""
    try:
        body = await request.body()
        signature = request.headers.get("webhook-signature", "")
        timestamp = request.headers.get("webhook-timestamp", "")
        
        # Enhanced webhook verification
        if not signature or not timestamp:
            logger.warning("Webhook received without proper signature headers")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing webhook signature")
        
        # Check timestamp to prevent replay attacks
        try:
            webhook_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_diff = datetime.utcnow() - webhook_time
            if time_diff.total_seconds() > 300:  # 5 minutes tolerance
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Webhook timestamp too old")
        except ValueError:
            logger.warning(f"Invalid webhook timestamp: {timestamp}")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid webhook timestamp")
        
        # Verify webhook signature
        if not verify_webhook_signature(body, signature, timestamp):
            logger.warning("Webhook signature verification failed")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid webhook signature")
        
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid JSON payload")
        
        event_type = payload.get("type")
        data = payload.get("data", {})
        
        # Log webhook received
        logger.info(f"Verified Dodo webhook received: {event_type}")
        
        return {"status": "received", "event_type": event_type}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Webhook processing failed")

def verify_webhook_signature(payload: bytes, signature: str, timestamp: str) -> bool:
    """Verify webhook signature from Dodo Payments with proper security"""
    try:
        webhook_secret = WEBHOOK_SECRET
        
        # Remove 'whsec_' prefix if present
        if webhook_secret.startswith('whsec_'):
            webhook_secret = webhook_secret[6:]
        
        # Create expected signature using HMAC-SHA256
        message = f"{timestamp}.{payload.decode('utf-8')}"
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)
        
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)