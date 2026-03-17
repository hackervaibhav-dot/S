from flask import Flask, request, jsonify, render_template_string
import requests
import os
import hashlib
import asyncio
import httpx
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

app = Flask(__name__)

HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip"
}

def sha256_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest().upper()

def convert_time(seconds):
    if seconds <= 0:
        return "EXPIRED", "0d 0h 0m 0s"
    target_date = datetime.now() + timedelta(seconds=seconds)
    date_str = target_date.strftime("%Y-%m-%d %H:%M:%S")
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    time_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(secs)}s"
    return date_str, time_str

async def decode_eat_token(eat_token: str):
    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            callback_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
            response = await client.get(callback_url, follow_redirects=False)

            if 300 <= response.status_code < 400 and "Location" in response.headers:
                redirect_url = response.headers["Location"]
                parsed_url = urlparse(redirect_url)
                query_params = parse_qs(parsed_url.query)

                token_value = query_params.get("access_token", [None])[0]
                account_id = query_params.get("account_id", [None])[0]
                account_nickname = query_params.get("nickname", [None])[0]
                region = query_params.get("region", [None])[0]

                if not token_value or not account_id:
                    return {"error": "Failed to extract data from Garena"}
            else:
                return {"error": "Invalid access token or session expired"}

            openid_url = "https://topup.pk/api/auth/player_id_login"
            openid_headers = { 
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-MM,en-US;q=0.9,en;q=0.8",
                "Content-Type": "application/json",
                "Origin": "https://topup.pk",
                "Referer": "https://topup.pk/",
                "User-Agent": "Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36",
                "X-Requested-With": "mark.via.gp",
            }
            payload = {"app_id": 100067, "login_id": str(account_id)}
            
            openid_res = await client.post(openid_url, headers=openid_headers, json=payload)
            openid_data = openid_res.json()
            open_id = openid_data.get("open_id")
            
            if not open_id:
                return {"error": "Failed to extract open_id"}

            return {
                "status": "success",
                "account_id": account_id,
                "account_nickname": account_nickname,
                "open_id": open_id,
                "access_token": token_value,
                "region": region
            }

    except Exception as e:
        return {"error": "Server error"}

# ORIGINAL UI - SIRF WORDS HATAYE
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>STILLRARE | Master Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { font-family: 'Inter', sans-serif; }
        body { 
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            color: #f8fafc; 
            min-height: 100vh;
        }
        .glass-panel { 
            background: rgba(30, 41, 59, 0.6); 
            backdrop-filter: blur(20px); 
            border: 1px solid rgba(255,255,255,0.08); 
            border-radius: 24px; 
            padding: 24px; 
            margin-bottom: 20px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .input-field { 
            background: rgba(15, 23, 42, 0.8); 
            border: 1px solid rgba(255,255,255,0.1); 
            padding: 16px 20px; 
            border-radius: 16px; 
            width: 100%; 
            margin-bottom: 12px; 
            color: white; 
            outline: none; 
            font-size: 15px;
            transition: all 0.3s ease;
        }
        .input-field:focus { 
            border-color: #3b82f6; 
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        .input-field::placeholder { color: #64748b; }
        .btn-primary { 
            width: 100%; 
            padding: 16px; 
            border-radius: 16px; 
            font-weight: 700; 
            font-size: 13px; 
            text-transform: uppercase; 
            letter-spacing: 1.5px; 
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 20px 40px -10px rgba(0,0,0,0.5); }
        .btn-primary:active { transform: translateY(0); }
        .console { 
            background: #020617; 
            border-radius: 16px; 
            padding: 16px; 
            font-family: 'JetBrains Mono', monospace; 
            font-size: 12px; 
            color: #4ade80; 
            max-height: 200px; 
            overflow-y: auto; 
            margin-top: 16px; 
            border: 1px solid rgba(255,255,255,0.05);
            display: none;
        }
        .console.show { display: block; }
        .section-title { 
            font-size: 11px; 
            text-transform: uppercase; 
            letter-spacing: 0.2em; 
            font-weight: 800;
            margin-bottom: 4px;
        }
        .step-badge { 
            font-size: 11px; 
            color: #94a3b8; 
            font-weight: 600;
        }
        .mode-btn {
            flex: 1;
            padding: 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255,255,255,0.05);
            color: #94a3b8;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .mode-btn.active {
            background: rgba(59, 130, 246, 0.2);
            border-color: #3b82f6;
            color: #3b82f6;
        }
        .gradient-text {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .glow {
            position: absolute;
            width: 100px;
            height: 100px;
            background: radial-gradient(circle, rgba(59,130,246,0.4) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
        .hidden { display: none; }
    </style>
</head>
<body class="p-4 max-w-md mx-auto pb-24">

    <!-- Header -->
    <header class="text-center py-10 relative">
        <div class="glow" style="top: 50%; left: 50%; transform: translate(-50%, -50%); width: 200px; height: 200px;"></div>
        <h1 class="text-5xl font-black italic tracking-tighter mb-2 relative z-10">
            <span class="bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">STILLRARE</span>
        </h1>
        <p class="text-slate-500 text-xs uppercase tracking-[0.4em] font-semibold">Master Hub</p>
    </header>

    <!-- EAT Decoder -->
    <div class="glass-panel border-l-4 border-green-500">
        <div class="flex justify-between items-center mb-4">
            <div>
                <div class="section-title text-green-400"><i class="fas fa-key mr-2"></i>Eat Token Decoder</div>
                <div class="step-badge">Get Access Token from EAT</div>
            </div>
            <i class="fas fa-shield-alt text-green-500/50 text-2xl"></i>
        </div>
        <input type="text" id="eat_input" class="input-field" placeholder="Paste EAT Token Here">
        <button onclick="decodeEat()" class="btn-primary bg-gradient-to-r from-green-600 to-emerald-600 text-white">
            Decode & Auto-Fill
        </button>
        <pre id="decode_out" class="console"></pre>
    </div>

    <!-- Bind Email -->
    <div class="glass-panel border-l-4 border-purple-500">
        <div class="flex justify-between items-center mb-4">
            <div>
                <div class="section-title text-purple-400"><i class="fas fa-plus-circle mr-2"></i>Bind New Email</div>
                <div class="step-badge">BIND</div>
            </div>
            <span class="text-xs bg-purple-500/20 text-purple-300 px-3 py-1 rounded-full font-bold">NEW</span>
        </div>
        <input type="text" id="bind_token" class="input-field" placeholder="Access Token">
        <input type="email" id="bind_email" class="input-field" placeholder="New Email to Bind">
        <button onclick="bindEmail()" class="btn-primary bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
            Send OTP & Bind
        </button>
        <pre id="bind_out" class="console"></pre>
    </div>

    <!-- Change Email -->
    <div class="glass-panel border-l-4 border-blue-500">
        <div class="flex justify-between items-center mb-4">
            <div>
                <div class="section-title text-blue-400"><i class="fas fa-exchange-alt mr-2"></i>Change Email</div>
                <div class="step-badge">CHANGE</div>
            </div>
            <i class="fas fa-sync text-blue-500/50 text-2xl"></i>
        </div>
        
        <input type="text" id="change_token" class="input-field" placeholder="Access Token">
        
        <div class="flex gap-2 mb-2">
            <input type="email" id="old_email" class="input-field flex-1" placeholder="OLD EMAIL (Auto-fetch)" readonly>
            <button onclick="fetchOldEmail()" class="bg-blue-600 px-4 rounded-xl text-sm font-bold">Fetch</button>
        </div>
        
        <input type="email" id="new_email" class="input-field" placeholder="NEW EMAIL">
        
        <div class="flex gap-3 mb-4">
            <button onclick="setChangeMethod('otp')" id="btn_method_otp" class="mode-btn active">Verify with OTP</button>
            <button onclick="setChangeMethod('sec')" id="btn_method_sec" class="mode-btn">Verify with Security Code</button>
        </div>

        <div id="change_step1_div">
            <button onclick="changeStep1()" class="btn-primary bg-gradient-to-r from-orange-600 to-red-600 text-white mb-3">
                [Step 1] Send OTP to OLD Email
            </button>
        </div>
        
        <div id="change_step2_div" class="hidden">
            <input type="text" id="change_otp_or_sec" class="input-field" placeholder="Enter OTP or Security Code">
            <button onclick="changeStep2()" class="btn-primary bg-gradient-to-r from-blue-600 to-cyan-600 text-white mb-3">
                [Step 2] Verify Identity
            </button>
        </div>
        
        <div id="change_step3_div" class="hidden">
            <button onclick="changeStep3()" class="btn-primary bg-gradient-to-r from-green-600 to-emerald-600 text-white mb-3">
                [Step 3] Send OTP to NEW Email
            </button>
        </div>
        
        <div id="change_step4_div" class="hidden">
            <input type="text" id="change_new_otp" class="input-field" placeholder="Enter OTP from NEW Email">
            <button onclick="changeStep4()" class="btn-primary bg-gradient-to-r from-purple-600 to-pink-600 text-white mb-3">
                [Step 4] Verify New OTP
            </button>
        </div>
        
        <div id="change_step5_div" class="hidden">
            <button onclick="changeStep5()" class="btn-primary bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                [Step 5] Create Rebind Request
            </button>
        </div>
        
        <pre id="change_out" class="console"></pre>
    </div>

    <!-- Unbind Email -->
    <div class="glass-panel border-l-4 border-red-500">
        <div class="flex justify-between items-center mb-4">
            <div>
                <div class="section-title text-red-400"><i class="fas fa-unlink mr-2"></i>Unbind Email</div>
                <div class="step-badge">UNBIND</div>
            </div>
            <i class="fas fa-trash-alt text-red-500/50 text-2xl"></i>
        </div>
        
        <input type="text" id="unbind_token" class="input-field" placeholder="Access Token">
        
        <div class="flex gap-2 mb-2">
            <input type="email" id="unbind_email" class="input-field flex-1" placeholder="Linked Email (Auto-fetch)" readonly>
            <button onclick="fetchUnbindEmail()" class="bg-red-600 px-4 rounded-xl text-sm font-bold">Fetch</button>
        </div>
        
        <div class="flex gap-3 mb-4">
            <button onclick="setUnbindMethod('otp')" id="btn_unbind_otp" class="mode-btn active">Use OTP</button>
            <button onclick="setUnbindMethod('sec')" id="btn_unbind_sec" class="mode-btn">Use Security Code</button>
        </div>

        <div id="unbind_send_otp_div">
            <button onclick="unbindSendOtp()" class="btn-primary bg-gradient-to-r from-orange-600 to-red-600 text-white mb-3">
                Send OTP to Email
            </button>
        </div>
        
        <div id="unbind_verify_div" class="hidden">
            <input type="text" id="unbind_otp_or_sec" class="input-field" placeholder="Enter OTP or Security Code">
            <button onclick="unbindVerify()" class="btn-primary bg-gradient-to-r from-blue-600 to-cyan-600 text-white mb-3">
                Verify & Unbind
            </button>
        </div>
        
        <pre id="unbind_out" class="console"></pre>
    </div>

    <!-- Account Utilities -->
    <div class="glass-panel">
        <div class="flex justify-between items-center mb-4">
            <div>
                <div class="section-title text-slate-400"><i class="fas fa-tools mr-2"></i>Account Utilities</div>
                <div class="step-badge">Management Tools</div>
            </div>
            <i class="fas fa-cog text-slate-500/50 text-2xl"></i>
        </div>
        <input type="text" id="util_token" class="input-field" placeholder="Access Token">
        <div class="grid grid-cols-1 gap-3">
            <button onclick="util('check')" class="btn-primary bg-slate-700/50 text-slate-200 border border-slate-600">
                Check Bind Status
            </button>
            <button onclick="util('cancel')" class="btn-primary bg-orange-900/30 text-orange-300 border border-orange-700/30">
                Cancel Pending Request
            </button>
            <button onclick="util('links')" class="btn-primary bg-purple-900/30 text-purple-300 border border-purple-700/30">
                View Linked Platforms
            </button>
            <button onclick="util('revoke')" class="btn-primary bg-red-900/30 text-red-400 border border-red-700/30">
                Revoke Access Token
            </button>
        </div>
        <pre id="util_out" class="console"></pre>
    </div>

    <div class="text-center py-8 text-slate-600 text-xs">
        <p>STILLRARE Master Hub v2.0</p>
        <p class="mt-1">REVOKE YOUR ACCESS TOKEN AFTER USING</p>
    </div>

    <script>
        let session = { change: {}, unbind: {} };
        let accountRegion = 'IND';
        let changeMethod = 'otp';
        let unbindMethod = 'otp';

        function showConsole(id) { document.getElementById(id).classList.add('show'); }
        function log(id, text) { 
            const el = document.getElementById(id);
            el.textContent = text;
            showConsole(id);
        }

        async function fetchOldEmail() {
            const token = document.getElementById('change_token').value.trim();
            if(!token) return alert('Enter Access Token first');
            
            const res = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'check', token})
            });
            const data = await res.json();
            
            if(data.email) {
                document.getElementById('old_email').value = data.email;
                log('change_out', `✓ Old email fetched: ${data.email}`);
            } else {
                log('change_out', '✗ No email found or invalid token');
            }
        }

        async function fetchUnbindEmail() {
            const token = document.getElementById('unbind_token').value.trim();
            if(!token) return alert('Enter Access Token first');
            
            const res = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'check', token})
            });
            const data = await res.json();
            
            if(data.email) {
                document.getElementById('unbind_email').value = data.email;
                log('unbind_out', `✓ Email fetched: ${data.email}`);
            } else {
                log('unbind_out', '✗ No email found');
            }
        }

        async function decodeEat() {
            const eat = document.getElementById('eat_input').value.trim();
            if(!eat) return alert('Please enter EAT token');
            
            log('decode_out', 'Decoding EAT token...');
            
            const res = await fetch('/api/decode', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({eat_token: eat})
            });
            const data = await res.json();
            
            if(data.access_token) {
                accountRegion = data.region || 'IND';
                document.getElementById('bind_token').value = data.access_token;
                document.getElementById('change_token').value = data.access_token;
                document.getElementById('unbind_token').value = data.access_token;
                document.getElementById('util_token').value = data.access_token;
                log('decode_out', `✓ Decoded! Region: ${accountRegion}\\nToken: ${data.access_token.substring(0,25)}...`);
                fetchOldEmail();
                fetchUnbindEmail();
            } else {
                log('decode_out', `✗ Failed: ${data.error || 'Unknown error'}`);
            }
        }

        async function bindEmail() {
            const token = document.getElementById('bind_token').value.trim();
            const email = document.getElementById('bind_email').value.trim();
            
            if(!token || !email) return alert('Fill all fields');
            
            log('bind_out', 'Sending OTP...');
            
            const res = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'send_otp',
                    token: token,
                    email: email,
                    region: accountRegion
                })
            });
            const data = await res.json();
            
            if(data.result === 0) {
                const otp = prompt('Enter OTP received on email:');
                if(!otp) return;
                
                log('bind_out', 'Verifying OTP...');
                
                const vRes = await fetch('/api/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        action: 'verify_otp',
                        token: token,
                        email: email,
                        otp: otp
                    })
                });
                const vData = await vRes.json();
                
                if(vData.verifier_token) {
                    log('bind_out', 'Creating bind request...');
                    
                    await fetch('/api/action', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            action: 'cancel',
                            token: token
                        })
                    });
                    
                    const bRes = await fetch('/api/action', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            action: 'create_bind',
                            token: token,
                            email: email,
                            verifier: vData.verifier_token
                        })
                    });
                    const bData = await bRes.json();
                    
                    if(bData.result === 0) {
                        log('bind_out', `✓ BIND CREATED!\\nEmail: ${email}\\nTime Left: ${bData.time_remaining}`);
                    } else {
                        log('bind_out', `✗ Failed: ${JSON.stringify(bData)}`);
                    }
                } else {
                    log('bind_out', `✗ Invalid OTP: ${JSON.stringify(vData)}`);
                }
            } else {
                log('bind_out', `✗ Failed: ${JSON.stringify(data)}`);
            }
        }

        function setChangeMethod(method) {
            changeMethod = method;
            document.getElementById('btn_method_otp').classList.toggle('active', method === 'otp');
            document.getElementById('btn_method_sec').classList.toggle('active', method === 'sec');
            
            const input = document.getElementById('change_otp_or_sec');
            const step1Btn = document.querySelector('#change_step1_div button');
            
            if(method === 'otp') {
                input.placeholder = 'Enter OTP from OLD Email';
                if(step1Btn) step1Btn.textContent = '[Step 1] Send OTP to OLD Email';
            } else {
                input.placeholder = 'Enter Security Code (Plain Text)';
                if(step1Btn) step1Btn.textContent = '[Step 1] Use Security Code';
            }
        }

        async function changeStep1() {
            session.change.token = document.getElementById('change_token').value.trim();
            session.change.old_email = document.getElementById('old_email').value.trim();
            session.change.new_email = document.getElementById('new_email').value.trim();
            
            if(!session.change.token || !session.change.old_email || !session.change.new_email) {
                return alert('Fill all fields');
            }
            
            if(changeMethod === 'sec') {
                log('change_out', '[SECURITY CODE MODE] Enter your security code directly');
                document.getElementById('change_step2_div').classList.remove('hidden');
                document.getElementById('change_otp_or_sec').placeholder = 'Enter Security Code (Plain Text)';
                document.getElementById('change_otp_or_sec').value = '';
                return;
            }
            
            log('change_out', '[Step 1] Sending OTP to old email...');
            
            const res = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'send_otp',
                    token: session.change.token,
                    email: session.change.old_email,
                    region: accountRegion
                })
            });
            const data = await res.json();
            
            if(data.result === 0) {
                document.getElementById('change_step2_div').classList.remove('hidden');
                log('change_out', `✓ OTP sent to ${session.change.old_email}\\n\\n[Step 2] Enter OTP and click Verify`);
            } else {
                log('change_out', `✗ Failed: ${JSON.stringify(data)}`);
            }
        }

        async function changeStep2() {
            const otpOrSec = document.getElementById('change_otp_or_sec').value.trim();
            if(!otpOrSec) return alert('Enter OTP or Security Code');
            
            log('change_out', '[Step 2] Verifying identity...');
            
            let payload = {
                action: 'verify_identity',
                token: session.change.token,
                email: session.change.old_email
            };
            
            if(changeMethod === 'otp') {
                payload.otp = otpOrSec;
            } else {
                payload.secondary_password = otpOrSec;
            }
            
            const res = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if(data.identity_token) {
                session.change.identity_token = data.identity_token;
                document.getElementById('change_step3_div').classList.remove('hidden');
                log('change_out', `✓ Identity Verified!\\n\\n[Step 3] Click to send OTP to new email`);
            } else {
                log('change_out', `✗ Verification Failed: ${JSON.stringify(data)}`);
            }
        }

        async function changeStep3() {
            log('change_out', '[Step 3] Sending OTP to new email...');
            
            const res = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'send_otp',
                    token: session.change.token,
                    email: session.change.new_email,
                    region: accountRegion
                })
            });
            const data = await res.json();
            
            if(data.result === 0) {
                document.getElementById('change_step4_div').classList.remove('hidden');
                log('change_out', `✓ OTP sent to ${session.change.new_email}\\n\\n[Step 4] Enter OTP and click Verify`);
            } else {
                log('change_out', `✗ Failed: ${JSON.stringify(data)}`);
            }
        }

        async function changeStep4() {
            const otp = document.getElementById('change_new_otp').value.trim();
            if(!otp) return alert('Enter OTP from new email');
            
            log('change_out', '[Step 4] Verifying new OTP...');
            
            const res = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'verify_otp',
                    token: session.change.token,
                    email: session.change.new_email,
                    otp: otp
                })
            });
            const data = await res.json();
            
            if(data.verifier_token) {
                session.change.verifier_token = data.verifier_token;
                document.getElementById('change_step5_div').classList.remove('hidden');
                log('change_out', `✓ New Email Verified!\\n\\n[Step 5] Click to Create Rebind Request`);
            } else {
                log('change_out', `✗ Verification Failed: ${JSON.stringify(data)}`);
            }
        }

        async function changeStep5() {
            log('change_out', '[Step 5] Creating rebind request...');
            
            const res = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'create_rebind',
                    token: session.change.token,
                    identity_token: session.change.identity_token,
                    verifier_token: session.change.verifier_token,
                    email: session.change.new_email
                })
            });
            const data = await res.json();
            
            if(data.result === 0) {
                log('change_out', `✓ REBIND CREATED!\\nOld: ${session.change.old_email}\\nNew: ${session.change.new_email}\\nTime Left: ${data.time_remaining}`);
                
                document.getElementById('change_step2_div').classList.add('hidden');
                document.getElementById('change_step3_div').classList.add('hidden');
                document.getElementById('change_step4_div').classList.add('hidden');
                document.getElementById('change_step5_div').classList.add('hidden');
            } else {
                log('change_out', `✗ Failed: ${JSON.stringify(data)}`);
            }
        }

        function setUnbindMethod(method) {
            unbindMethod = method;
            document.getElementById('btn_unbind_otp').classList.toggle('active', method === 'otp');
            document.getElementById('btn_unbind_sec').classList.toggle('active', method === 'sec');
            
            const sendOtpDiv = document.getElementById('unbind_send_otp_div');
            const verifyDiv = document.getElementById('unbind_verify_div');
            
            if(method === 'otp') {
                sendOtpDiv.style.display = 'block';
                verifyDiv.classList.add('hidden');
                document.getElementById('unbind_otp_or_sec').placeholder = 'Enter OTP';
            } else {
                sendOtpDiv.style.display = 'none';
                verifyDiv.classList.remove('hidden');
                document.getElementById('unbind_otp_or_sec').placeholder = 'Enter Security Code';
                document.getElementById('unbind_otp_or_sec').value = '';
            }
        }

        async function unbindSendOtp() {
            session.unbind.token = document.getElementById('unbind_token').value.trim();
            session.unbind.email = document.getElementById('unbind_email').value.trim();
            
            if(!session.unbind.token || !session.unbind.email) {
                return alert('Fill all fields');
            }
            
            log('unbind_out', 'Sending OTP...');
            
            const res = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'send_otp',
                    token: session.unbind.token,
                    email: session.unbind.email,
                    region: accountRegion
                })
            });
            const data = await res.json();
            
            if(data.result === 0) {
                document.getElementById('unbind_verify_div').classList.remove('hidden');
                log('unbind_out', `✓ OTP sent to ${session.unbind.email}\\n\\nEnter OTP and click Verify`);
            } else {
                log('unbind_out', `✗ Failed: ${JSON.stringify(data)}`);
            }
        }

        async function unbindVerify() {
            const token = session.unbind.token || document.getElementById('unbind_token').value.trim();
            const email = session.unbind.email || document.getElementById('unbind_email').value.trim();
            const otpOrSec = document.getElementById('unbind_otp_or_sec').value.trim();
            
            if(!token || !email || !otpOrSec) return alert('Fill all fields');
            
            log('unbind_out', 'Verifying identity...');
            
            let payload = {
                action: 'verify_identity',
                token: token,
                email: email
            };
            
            if(unbindMethod === 'otp') {
                payload.otp = otpOrSec;
            } else {
                payload.secondary_password = otpOrSec;
            }
            
            const vRes = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const vData = await vRes.json();
            
            if(vData.identity_token) {
                log('unbind_out', 'Creating unbind request...');
                
                const uRes = await fetch('/api/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        action: 'create_unbind',
                        token: token,
                        identity: vData.identity_token
                    })
                });
                const uData = await uRes.json();
                
                if(uData.result === 0) {
                    log('unbind_out', `✓ UNBIND CREATED!\\nTime Left: ${uData.time_remaining}`);
                    
                    document.getElementById('unbind_verify_div').classList.add('hidden');
                    if(unbindMethod === 'otp') {
                        document.getElementById('unbind_send_otp_div').style.display = 'block';
                    }
                } else {
                    log('unbind_out', `✗ Failed: ${JSON.stringify(uData)}`);
                }
            } else {
                log('unbind_out', `✗ Verification Failed: ${JSON.stringify(vData)}`);
            }
        }

        async function util(action) {
            const token = document.getElementById('util_token').value.trim();
            if(!token) return alert('Enter Access Token');
            
            log('util_out', `Processing ${action}...`);
            
            const res = await fetch('/api/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action, token})
            });
            const data = await res.json();
            
            if(action === 'check' && data.request_exec_countdown) {
                const days = Math.floor(data.request_exec_countdown / 86400);
                const hours = Math.floor((data.request_exec_countdown % 86400) / 3600);
                const mins = Math.floor((data.request_exec_countdown % 3600) / 60);
                const secs = data.request_exec_countdown % 60;
                
                log('util_out', `Status: ${data.email_to_be ? 'PENDING' : (data.email ? 'CONFIRMED' : 'NONE')}\\n` +
                    (data.email ? `Current: ${data.email}\\n` : '') +
                    (data.email_to_be ? `Pending: ${data.email_to_be}\\n` : '') +
                    `\\nTime Left: ${days}d ${hours}h ${mins}m ${secs}s`);
            } else {
                log('util_out', JSON.stringify(data, null, 2));
            }
        }
    </script>
</body>
</html>'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/decode', methods=['POST'])
def decode():
    try:
        data = request.get_json()
        result = asyncio.run(decode_eat_token(data.get('eat_token', '')))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Server error"})

@app.route('/api/action', methods=['POST'])
def action():
    try:
        data = request.get_json()
        act = data.get('action')
        token = data.get('token')
        
        if act == 'send_otp':
            url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
            payload = {
                'app_id': "100067",
                'access_token': token,
                'email': data.get('email'),
                'locale': "en_MA",
                'region': data.get('region', 'IND')
            }
            r = requests.post(url, data=payload, headers=HEADERS, timeout=10)
            return jsonify(r.json())
        
        elif act == 'verify_otp':
            url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
            payload = {
                'app_id': "100067",
                'access_token': token,
                'email': data.get('email'),
                'otp': data.get('otp')
            }
            r = requests.post(url, data=payload, headers=HEADERS, timeout=10)
            return jsonify(r.json())
        
        elif act == 'verify_identity':
            url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
            payload = {
                'app_id': "100067",
                'access_token': token,
                'email': data.get('email')
            }
            
            if data.get('otp'):
                payload['otp'] = data.get('otp')
            elif data.get('secondary_password'):
                payload['secondary_password'] = sha256_hash(data.get('secondary_password'))
            
            r = requests.post(url, data=payload, headers=HEADERS, timeout=10)
            return jsonify(r.json())
        
        elif act == 'create_bind':
            url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
            payload = {
                'app_id': "100067",
                'access_token': token,
                'verifier_token': data.get('verifier'),
                'secondary_password': "91B4D142823F7D20C5F08DF69122DE43F35F057A988D9619F6D3138485C9A203",
                'email': data.get('email')
            }
            r = requests.post(url, data=payload, headers=HEADERS, timeout=10)
            result = r.json()
            if result.get('result') == 0:
                date_str, time_str = convert_time(259200)
                result['confirmation_date'] = date_str
                result['time_remaining'] = time_str
            return jsonify(result)
        
        elif act == 'create_rebind':
            url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
            payload = {
                'identity_token': data.get('identity_token'),
                'email': data.get('email'),
                'app_id': '100067',
                'verifier_token': data.get('verifier_token'),
                'access_token': token
            }
            r = requests.post(url, data=payload, headers=HEADERS, timeout=10)
            result = r.json()
            if result.get('result') == 0:
                date_str, time_str = convert_time(259200)
                result['confirmation_date'] = date_str
                result['time_remaining'] = time_str
            return jsonify(result)
        
        elif act == 'create_unbind':
            url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
            payload = {
                'app_id': "100067",
                'access_token': token,
                'identity_token': data.get('identity')
            }
            r = requests.post(url, data=payload, headers=HEADERS, timeout=10)
            result = r.json()
            if result.get('result') == 0:
                date_str, time_str = convert_time(259200)
                result['confirmation_date'] = date_str
                result['time_remaining'] = time_str
            return jsonify(result)
        
        elif act == 'cancel':
            url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
            payload = {'app_id': "100067", 'access_token': token}
            r = requests.post(url, data=payload, headers=HEADERS, timeout=10)
            return jsonify(r.json())
        
        elif act == 'check':
            url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
            payload = {'app_id': "100067", 'access_token': token}
            r = requests.get(url, params=payload, headers=HEADERS, timeout=10)
            result = r.json()
            
            countdown = result.get('request_exec_countdown', 0)
            if countdown > 0:
                date_str, time_str = convert_time(countdown)
                result['confirmation_date'] = date_str
                result['time_remaining'] = time_str
            
            return jsonify(result)
        
        elif act == 'links':
            url = "https://100067.connect.garena.com/bind/app/platform/info/get"
            r = requests.get(url, params={'access_token': token}, headers=HEADERS, timeout=10)
            if r.status_code in [200, 201]:
                return jsonify(r.json())
            return jsonify({"error": "Failed", "status": r.status_code})
        
        elif act == 'revoke':
            url = f"https://100067.connect.garena.com/oauth/logout?access_token={token}"
            r = requests.get(url, timeout=10)
            if r.text.strip() == '{"result":0}':
                return jsonify({"result": 0, "message": "TOKEN REVOKED"})
            return jsonify({"result": -1, "response": r.text})
        
        else:
            return jsonify({"error": "Unknown action"})
            
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🔥 STILLRARE Master Hub Running...")
    print("="*50)
    print("✓ Auto-fetch Old Email")
    print("✓ Auto-fetch Unbind Email")
    print("✓ Security Code Fixed")
    print("✓ Real FF Time Display")
    print("="*50)
    print(f"🌐 http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)