"""
SwiftRoom Multicast Client — UDP + Thread รับ/ส่งแบบ non-blocking
รัน: python multicast_client.py
"""
import socket
import struct
import json
import sys
import threading
import time
import ipaddress
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

console = Console()

ROOMS = {
    "1": ("room1", "239.1.1.10", 5000),
    "2": ("room2", "239.1.1.20", 6000),
    "3": ("room3", "239.1.1.30", 7000),
}
TTL = 1              # local network (site<32, org<64, global<128)
LOOPBACK = 1         # 1 = รับข้อความตัวเองด้วย (จำเป็นตอนเทสเครื่องเดียว)
HEARTBEAT_SEC = 5
MEMBER_TIMEOUT = 15


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_valid_multicast(ip: str) -> tuple[bool, str]:
    """ตรวจว่า IP อยู่ใน Class D 224.0.0.0-239.255.255.255 จริงไหม"""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False, "รูปแบบ IP ไม่ถูกต้อง"
    if not addr.is_multicast:
        return False, "ไม่อยู่ในช่วง Class D (224.0.0.0-239.255.255.255)"
    if ipaddress.ip_address(ip) in ipaddress.ip_network("224.0.0.0/24"):
        return False, "อยู่ในช่วง reserved 224.0.0.0/24 ใช้ 239.x แทน"
    return True, "OK"


def show_welcome():
    console.clear()
    title = Text("⚡ SwiftRoom Multicast ⚡", style="bold cyan", justify="center")
    body = Text(
        "Unicast = 1:1  •  Broadcast = 1:ทุกคน  •  Multicast = 1:เฉพาะกลุ่ม\n"
        "UDP + Thread รับ/ส่ง • Heartbeat ทุก 5 วิ • UTF-8 ไทยได้",
        justify="center",
    )
    console.print(Panel(body, title=title, border_style="cyan", padding=(1, 2)))


def show_room_table():
    t = Table(title="ห้อง Multicast ที่มีให้เลือก", show_header=True, header_style="bold magenta")
    t.add_column("เลือก", style="green bold", justify="center")
    t.add_column("ห้อง", style="white")
    t.add_column("Multicast IP", style="yellow")
    t.add_column("พอร์ต", style="cyan", justify="right")
    for key, (room, ip, port) in ROOMS.items():
        t.add_row(key, room, ip, str(port))
    console.print(t)


def show_status(nickname, room, mcast_ip, port):
    console.print(
        f"[bold cyan]SwiftRoom[/bold cyan] | 👤 [bold]{nickname}[/bold] "
        f"| 🏠 [bold]{room}[/bold] [dim]({mcast_ip}:{port})[/dim]"
    )
    console.print("[dim]" + "-" * 60 + "[/dim]")


def show_help():
    t = Table(show_header=False, box=None, padding=(0, 1))
    t.add_column("cmd", style="green bold")
    t.add_column("desc", style="white")
    t.add_row("/list", "ดูสมาชิกในห้องปัจจุบัน")
    t.add_row("/leave", "ออกห้องกลับไปเมนูเลือกห้อง")
    t.add_row("/exit", "ปิดโปรแกรม")
    t.add_row("/help", "แสดงความช่วยเหลือนี้")
    console.print(Panel(t, title="[yellow]คำสั่ง[/yellow]", border_style="yellow"))


def run_room_session(nickname, room, mcast_ip, port):
    """เข้า 1 ห้องจนกว่าจะ /leave (คืน 'leave') หรือ /exit (คืน 'exit')"""
    # --- สร้าง socket + join group ---
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("", port))
    except OSError as e:
        console.print(f"[bold red]❌ bind port {port} ไม่ได้ (อาจมีโปรแกรมใช้อยู่): {e}[/bold red]")
        return
    mreq = struct.pack("4s4s", socket.inet_aton(mcast_ip), socket.inet_aton("0.0.0.0"))
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    except OSError as e:
        console.print(f"[bold red]❌ join group {mcast_ip} ไม่ได้: {e}[/bold red]")
        return
    # TTL + loopback สำหรับฝั่งส่ง
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, TTL)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, LOOPBACK)

    members: dict[str, float] = {}
    stop = threading.Event()

    def send_pkt(ptype, msg=""):
        pkt = json.dumps({"type": ptype, "user": nickname, "room": room, "msg": msg, "ts": now()}, ensure_ascii=False)
        try:
            sock.sendto(pkt.encode("utf-8"), (mcast_ip, port))
        except (OSError, UnicodeEncodeError) as e:
            console.print(f"[yellow]⚠️ ส่งไม่สำเร็จ: {e}[/yellow]")

    def recv_loop():
        while not stop.is_set():
            try:
                data, _ = sock.recvfrom(65535)
                pkt = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            except OSError:
                break
            if pkt.get("room") != room:
                continue
            user, ptype = pkt.get("user", "?"), pkt.get("type", "?")
            ts = pkt.get("ts", now())
            if ptype == "HELLO":
                last = members.get(user)
                expired = last is None or (time.time() - last) > MEMBER_TIMEOUT
                members[user] = time.time()
                # Join = HELLO ครั้งแรกหรือกลับมาหลังหายไปเกิน timeout; heartbeat ระหว่างนั้นต้องเงียบ
                if expired and user != nickname:
                    console.print(f"[green]→ [{ts}] {user} เข้าร่วมห้อง[/green]")
            elif ptype == "BYE":
                was_member = user in members
                members.pop(user, None)
                if was_member and user != nickname:
                    console.print(f"[red]← [{ts}] {user} ออกจากห้อง[/red]")
            elif ptype == "CHAT":
                last = members.get(user)
                expired = last is None or (time.time() - last) > MEMBER_TIMEOUT
                members[user] = time.time()
                if expired and user != nickname:
                    console.print(f"[green]→ [{ts}] {user} เข้าร่วมห้อง[/green]")
                me = " (คุณ)" if user == nickname else ""
                console.print(f"[dim][{ts}][/dim] [bold magenta]{user}{me}:[/bold magenta] [white]{pkt.get('msg','')}[/white]")
    def heartbeat_loop():
        while not stop.is_set():
            send_pkt("HELLO")
            time.sleep(HEARTBEAT_SEC)

    console.print(f"\n[bold green]✅ {nickname} เข้าห้อง '{room}'[/bold green] [dim]({mcast_ip}:{port})[/dim]")
    show_status(nickname, room, mcast_ip, port)
    console.print("[dim]พิมพ์ข้อความส่งได้เลย | /list /leave /exit /help[/dim]\n")

    threading.Thread(target=recv_loop, daemon=True).start()
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    send_pkt("HELLO")

    action = "exit"
    try:
        while True:
            try:
                line = input(f"[{nickname}@{room}]> ").strip()
            except (EOFError, KeyboardInterrupt):
                line = "/exit"
            if not line:
                continue
            if line == "/exit":
                send_pkt("BYE")
                action = "exit"
                break
            elif line == "/leave":
                send_pkt("BYE")
                action = "leave"
                break
            elif line == "/list":
                fresh = [u for u, t in members.items() if time.time() - t < MEMBER_TIMEOUT]
                console.print(f"[cyan]สมาชิกในห้อง '{room}' ({len(fresh)} คน): " + ", ".join(sorted(fresh)) + "[/cyan]")
            elif line == "/help":
                show_help()
            elif line.startswith("/"):
                console.print("[bold red]❌ คำสั่งไม่รู้จัก พิมพ์ /help ดูคำสั่งทั้งหมด[/bold red]")
            else:
                send_pkt("CHAT", line)
    finally:
        stop.set()
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
            sock.close()
        except OSError:
            pass
        if action == "leave":
            console.print(f"[dim]ออกจากห้อง '{room}' แล้ว กลับไปเมนูเลือกห้อง[/dim]")
    return action


def main():
    show_welcome()
    console.print("[dim]สี: [yellow]เหลือง=ระบบ[/yellow] | [white]ขาว=แชท[/white] | [green]เขียว=เข้า[/green] | [red]แดง=ออก/error[/red][/dim]\n")
    nickname = input("ตั้ง nickname ของคุณ: ").strip()
    if not nickname or len(nickname) > 20 or " " in nickname:
        console.print("[bold red]❌ nickname ต้องยาว 1-20 ตัว ไม่มีช่องว่าง[/bold red]")
        return

    while True:
        show_room_table()
        console.print("  [dim]พิมพ์ /help ดูคำสั่ง | /exit ปิดโปรแกรม[/dim]")
        choice = input("เลือกห้อง (1/2/3): ").strip()
        if choice in ("/exit", "/quit", "q", "exit"):
            console.print("[yellow]ออกจาก SwiftRoom Multicast แล้ว บาย! 👋[/yellow]")
            return
        if choice == "/help":
            show_help()
            continue
        if choice not in ROOMS:
            console.print("[bold red]❌ ไม่มีห้องนี้ กรุณาเลือก 1/2/3[/bold red]")
            continue
        room, mcast_ip, port = ROOMS[choice]

        ok, reason = is_valid_multicast(mcast_ip)
        if not ok:
            console.print(f"[bold red]❌ IP {mcast_ip} ใช้ไม่ได้: {reason}[/bold red]")
            continue

        action = run_room_session(nickname, room, mcast_ip, port)
        if action == "exit":
            console.print("[yellow]ออกจาก SwiftRoom Multicast แล้ว บาย! 👋[/yellow]")
            return
        # action == "leave" → วนกลับไปเมนูเลือกห้อง


if __name__ == "__main__":
    main()
