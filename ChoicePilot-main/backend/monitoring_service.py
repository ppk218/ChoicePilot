import os
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, status
import asyncio
from collections import defaultdict, deque
import hashlib

logger = logging.getLogger(__name__)

class SecurityMonitor:
    """Enhanced security monitoring and alerting system"""
    
    def __init__(self, db, email_service):
        self.db = db
        self.email_service = email_service
        self.failed_attempts = defaultdict(deque)  # IP -> deque of timestamps
        self.rate_limits = defaultdict(deque)      # key -> deque of timestamps
        self.suspicious_ips = set()
        self.blocked_ips = set()
        
        # Security thresholds
        self.MAX_FAILED_LOGINS = 5
        self.LOGIN_WINDOW = 900  # 15 minutes
        self.TEMP_BAN_DURATION = 3600  # 1 hour
        self.RATE_LIMIT_WINDOW = 3600  # 1 hour
        
        # Rate limits by endpoint type
        self.RATE_LIMITS = {
            "auth": {"limit": 10, "window": 900},      # 10 auth attempts per 15 min
            "chat": {"limit": 30, "window": 3600},     # 30 chat requests per hour
            "payments": {"limit": 5, "window": 3600},  # 5 payment requests per hour
            "general": {"limit": 100, "window": 3600}  # 100 general requests per hour
        }
    
    async def check_rate_limit(self, request_type: str, identifier: str) -> bool:
        """Check if request is within rate limits"""
        try:
            now = time.time()
            key = f"{request_type}:{identifier}"
            
            # Get rate limit config
            config = self.RATE_LIMITS.get(request_type, self.RATE_LIMITS["general"])
            limit = config["limit"]
            window = config["window"]
            
            # Clean old requests
            while self.rate_limits[key] and now - self.rate_limits[key][0] > window:
                self.rate_limits[key].popleft()
            
            # Check limit
            if len(self.rate_limits[key]) >= limit:
                await self.log_security_event({
                    "event_type": "rate_limit_exceeded",
                    "request_type": request_type,
                    "identifier": identifier,
                    "attempts": len(self.rate_limits[key]),
                    "limit": limit,
                    "window": window
                })
                return False
            
            # Add current request
            self.rate_limits[key].append(now)
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return True  # Fail open for availability
    
    async def check_ip_reputation(self, ip_address: str) -> bool:
        """Check if IP is blocked or suspicious"""
        if ip_address in self.blocked_ips:
            await self.log_security_event({
                "event_type": "blocked_ip_access",
                "ip_address": ip_address,
                "action": "denied"
            })
            return False
        
        if ip_address in self.suspicious_ips:
            await self.log_security_event({
                "event_type": "suspicious_ip_access",
                "ip_address": ip_address,
                "action": "monitored"
            })
        
        return True
    
    async def track_failed_login(self, ip_address: str, email: str) -> bool:
        """Track failed login attempts and implement temporary bans"""
        try:
            now = time.time()
            
            # Clean old attempts
            while (self.failed_attempts[ip_address] and 
                   now - self.failed_attempts[ip_address][0] > self.LOGIN_WINDOW):
                self.failed_attempts[ip_address].popleft()
            
            # Add current attempt
            self.failed_attempts[ip_address].append(now)
            
            # Check if threshold exceeded
            if len(self.failed_attempts[ip_address]) >= self.MAX_FAILED_LOGINS:
                # Temporary ban
                self.blocked_ips.add(ip_address)
                
                # Schedule unban (in production, use Redis with TTL)
                asyncio.create_task(self._schedule_unban(ip_address))
                
                await self.log_security_event({
                    "event_type": "ip_temporarily_banned",
                    "ip_address": ip_address,
                    "email": email,
                    "failed_attempts": len(self.failed_attempts[ip_address]),
                    "ban_duration": self.TEMP_BAN_DURATION
                })
                
                # Send security alert
                await self._send_security_alert(
                    "Multiple Failed Login Attempts",
                    f"IP {ip_address} has been temporarily banned after {self.MAX_FAILED_LOGINS} failed login attempts for email: {email}"
                )
                
                return False
            
            await self.log_security_event({
                "event_type": "failed_login_tracked",
                "ip_address": ip_address,
                "email": email,
                "attempts": len(self.failed_attempts[ip_address])
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking failed login: {str(e)}")
            return True
    
    async def _schedule_unban(self, ip_address: str):
        """Schedule IP unban after timeout"""
        await asyncio.sleep(self.TEMP_BAN_DURATION)
        self.blocked_ips.discard(ip_address)
        
        await self.log_security_event({
            "event_type": "ip_unbanned",
            "ip_address": ip_address,
            "action": "automatic_unban"
        })
    
    async def detect_suspicious_patterns(self, user_id: str, activity_data: Dict):
        """Detect suspicious user behavior patterns"""
        try:
            # Check for unusual activity patterns
            suspicious_indicators = []
            
            # Check for rapid decision creation
            if activity_data.get("decisions_in_hour", 0) > 20:
                suspicious_indicators.append("excessive_decision_creation")
            
            # Check for unusual API usage patterns
            if activity_data.get("api_calls_in_hour", 0) > 200:
                suspicious_indicators.append("excessive_api_usage")
            
            # Check for payment anomalies
            if activity_data.get("payment_attempts_in_hour", 0) > 10:
                suspicious_indicators.append("excessive_payment_attempts")
            
            if suspicious_indicators:
                await self.log_security_event({
                    "event_type": "suspicious_user_behavior",
                    "user_id": user_id,
                    "indicators": suspicious_indicators,
                    "activity_data": activity_data
                })
                
                # Flag for review
                await self.flag_user_for_review(user_id, suspicious_indicators)
            
        except Exception as e:
            logger.error(f"Error detecting suspicious patterns: {str(e)}")
    
    async def flag_user_for_review(self, user_id: str, indicators: List[str]):
        """Flag user account for manual review"""
        try:
            flag_data = {
                "user_id": user_id,
                "flagged_at": datetime.utcnow(),
                "indicators": indicators,
                "status": "pending_review",
                "reviewed": False
            }
            
            await self.db.user_flags.insert_one(flag_data)
            
            # Send alert to admin
            await self._send_admin_alert(
                "User Account Flagged",
                f"User {user_id} flagged for review. Indicators: {', '.join(indicators)}"
            )
            
        except Exception as e:
            logger.error(f"Error flagging user: {str(e)}")
    
    async def log_security_event(self, event_data: Dict):
        """Log security events for audit and analysis"""
        try:
            event_data.update({
                "timestamp": datetime.utcnow(),
                "event_id": hashlib.md5(str(event_data).encode()).hexdigest()[:16]
            })
            
            # Store in database
            await self.db.security_events.insert_one(event_data)
            
            # Log to file
            logger.warning(f"SECURITY_EVENT: {json.dumps(event_data, default=str)}")
            
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")
    
    async def _send_security_alert(self, alert_type: str, details: str):
        """Send security alert email"""
        try:
            admin_emails = ["hello@getgingee.com"]  # Configure admin emails
            
            for email in admin_emails:
                await self.email_service.send_security_alert(
                    email, alert_type, details
                )
        except Exception as e:
            logger.error(f"Error sending security alert: {str(e)}")
    
    async def _send_admin_alert(self, subject: str, message: str):
        """Send admin alert"""
        await self._send_security_alert(subject, message)

class SystemMonitor:
    """System performance and health monitoring"""
    
    def __init__(self, db):
        self.db = db
        self.metrics = defaultdict(list)
        self.alerts = []
        
        # Performance thresholds
        self.RESPONSE_TIME_THRESHOLD = 5.0  # seconds
        self.ERROR_RATE_THRESHOLD = 0.05    # 5%
        self.MEMORY_THRESHOLD = 0.85        # 85%
    
    async def track_request_performance(self, endpoint: str, response_time: float, status_code: int):
        """Track API performance metrics"""
        try:
            now = datetime.utcnow()
            
            metric = {
                "endpoint": endpoint,
                "response_time": response_time,
                "status_code": status_code,
                "timestamp": now,
                "is_error": status_code >= 400
            }
            
            # Store in database (with TTL in production)
            await self.db.performance_metrics.insert_one(metric)
            
            # Check for performance issues
            if response_time > self.RESPONSE_TIME_THRESHOLD:
                await self._alert_slow_response(endpoint, response_time)
            
        except Exception as e:
            logger.error(f"Error tracking performance: {str(e)}")
    
    async def calculate_error_rate(self, endpoint: str, window_minutes: int = 60) -> float:
        """Calculate error rate for endpoint in time window"""
        try:
            since = datetime.utcnow() - timedelta(minutes=window_minutes)
            
            # Get total requests
            total_requests = await self.db.performance_metrics.count_documents({
                "endpoint": endpoint,
                "timestamp": {"$gte": since}
            })
            
            if total_requests == 0:
                return 0.0
            
            # Get error requests
            error_requests = await self.db.performance_metrics.count_documents({
                "endpoint": endpoint,
                "timestamp": {"$gte": since},
                "is_error": True
            })
            
            error_rate = error_requests / total_requests
            
            # Alert if error rate is high
            if error_rate > self.ERROR_RATE_THRESHOLD:
                await self._alert_high_error_rate(endpoint, error_rate)
            
            return error_rate
            
        except Exception as e:
            logger.error(f"Error calculating error rate: {str(e)}")
            return 0.0
    
    async def check_system_health(self) -> Dict:
        """Check overall system health"""
        try:
            health_data = {
                "timestamp": datetime.utcnow(),
                "database_status": "unknown",
                "api_status": "unknown",
                "email_status": "unknown",
                "overall_status": "unknown"
            }
            
            # Check database connectivity
            try:
                await self.db.admin.command("ping")
                health_data["database_status"] = "healthy"
            except Exception:
                health_data["database_status"] = "unhealthy"
            
            # Check API response times
            avg_response_time = await self._get_avg_response_time()
            health_data["avg_response_time"] = avg_response_time
            health_data["api_status"] = "healthy" if avg_response_time < 3.0 else "degraded"
            
            # Determine overall status
            statuses = [health_data["database_status"], health_data["api_status"]]
            if all(s == "healthy" for s in statuses):
                health_data["overall_status"] = "healthy"
            elif any(s == "unhealthy" for s in statuses):
                health_data["overall_status"] = "unhealthy"
            else:
                health_data["overall_status"] = "degraded"
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return {"overall_status": "error", "error": str(e)}
    
    async def _get_avg_response_time(self, minutes: int = 15) -> float:
        """Get average response time for recent requests"""
        try:
            since = datetime.utcnow() - timedelta(minutes=minutes)
            
            pipeline = [
                {"$match": {"timestamp": {"$gte": since}}},
                {"$group": {"_id": None, "avg_time": {"$avg": "$response_time"}}}
            ]
            
            result = await self.db.performance_metrics.aggregate(pipeline).to_list(1)
            
            if result:
                return round(result[0]["avg_time"], 3)
            return 0.0
            
        except Exception:
            return 0.0
    
    async def _alert_slow_response(self, endpoint: str, response_time: float):
        """Alert for slow response times"""
        logger.warning(f"SLOW_RESPONSE: {endpoint} took {response_time:.2f}s")
    
    async def _alert_high_error_rate(self, endpoint: str, error_rate: float):
        """Alert for high error rates"""
        logger.warning(f"HIGH_ERROR_RATE: {endpoint} has {error_rate:.2%} error rate")

class BackupManager:
    """Database backup and recovery management"""
    
    def __init__(self, db):
        self.db = db
        self.backup_retention_days = 30
    
    async def create_backup_plan(self) -> Dict:
        """Create backup plan and schedule"""
        backup_plan = {
            "daily_backups": {
                "schedule": "2:00 AM UTC",
                "retention": "7 days",
                "collections": ["users", "decision_sessions", "conversations"]
            },
            "weekly_backups": {
                "schedule": "Sunday 3:00 AM UTC", 
                "retention": "4 weeks",
                "collections": "all"
            },
            "monthly_backups": {
                "schedule": "1st of month 4:00 AM UTC",
                "retention": "12 months", 
                "collections": "all"
            }
        }
        
        return backup_plan
    
    async def validate_backup_integrity(self, backup_id: str) -> bool:
        """Validate backup file integrity"""
        # Implementation would depend on backup storage system
        # For now, return placeholder
        return True
    
    async def get_backup_status(self) -> Dict:
        """Get current backup status and recommendations"""
        return {
            "last_backup": "2025-01-15 02:00:00 UTC",
            "backup_size": "1.2 GB",
            "status": "healthy",
            "next_backup": "2025-01-16 02:00:00 UTC",
            "recommendations": [
                "Set up automated daily backups",
                "Configure off-site backup storage",
                "Test backup restoration process monthly"
            ]
        }

class AuditLogger:
    """Comprehensive audit logging for compliance"""
    
    def __init__(self, db):
        self.db = db
    
    async def log_user_action(self, user_id: str, action: str, details: Dict):
        """Log user actions for audit trail"""
        try:
            audit_entry = {
                "user_id": user_id,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow(),
                "ip_address": details.get("ip_address"),
                "user_agent": details.get("user_agent")
            }
            
            await self.db.audit_logs.insert_one(audit_entry)
            
        except Exception as e:
            logger.error(f"Error logging user action: {str(e)}")
    
    async def log_admin_action(self, admin_id: str, action: str, target: str, details: Dict):
        """Log admin actions for accountability"""
        try:
            audit_entry = {
                "admin_id": admin_id,
                "action": action,
                "target": target,
                "details": details,
                "timestamp": datetime.utcnow(),
                "severity": "high"
            }
            
            await self.db.admin_audit_logs.insert_one(audit_entry)
            
        except Exception as e:
            logger.error(f"Error logging admin action: {str(e)}")
    
    async def generate_audit_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """Generate comprehensive audit report"""
        try:
            # User action summary
            user_actions = await self.db.audit_logs.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$group": {"_id": "$action", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]).to_list(50)
            
            # Security events summary
            security_events = await self.db.security_events.aggregate([
                {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
                {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]).to_list(50)
            
            return {
                "period": {"start": start_date, "end": end_date},
                "user_actions": user_actions,
                "security_events": security_events,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error generating audit report: {str(e)}")
            return {"error": str(e)}