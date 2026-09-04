"""
SwiftRoom Multicast Logger (Server) — UDP Multicast observer
รัน: python multicast_server.py

หลักการ (สั้น):
- Unicast = 1:1, Broadcast = 1:ทุกคนในวง, Multicast = 1:เฉพาะสมาชิกกลุ่ม (Class D 224.0.0.0-239.255.255.255)
- Server นี้เป็นแค่ Logger กลาง: join ทั้ง 3 กลุ่มเพื่อ log JOIN/LEAVE/CHAT ไม่ได้ relay ข้อความ
- Client คุยกันเองแบบ P2P ผ่าน multicast ตรงๆ

TTL แนะนำ: 1=local (ทดสอบเครื่องเดียว), <32=site, <64=organization, <128+=global
Loopback=1 หมายถึงเครื่องส่งจะได้รับข้อความตัวเองด้วย (จำเป็นตอนทดสอบบนเครื่องเดียว)
"""
import socket
import struct
import json
import sys
import threading
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

console = Console()

# ใช้ช่วง 239.x (administratively scoped) แทน 224.0.0.1-3 ที่เป็น reserved
ROOMS = [
    ("room1", "239.1.1.10", 5000),
    ("room2", "239.1.1.20", 6000),
    ("room3", "239.1.1.30", 7000),
]

lock = threading.Lock()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def make_listener(mcast_ip, port):
    """สร้าง UDP socket + join multicast group ด้วย IP_ADD_MEMBERSHIP"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("", port))
    except OSError as e:
        console.print(f"[bold red][{now()}] ❌ bind port {port} ไม่ได้: {e}[/bold red]")
        raise
    # join group: 0.0.0.0 = ฟังทุก interface
    mreq = struct.pack("4s4s", socket.inet_aton(mcast_ip), socket.inet_aton("0.0.0.0"))
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    except OSError as e:
        console.print(f"[bold red][{now()}] ❌ join {mcast_ip}:{port} ไม่ได้: {e}[/bold red]")
        raise
    return sock


def listen_room(room, mcast_ip, port):
    try:
        sock = make_listener(mcast_ip, port)
    except OSError:
        return
    console.print(f"[dim][{now()}] 👂 Logger ฟัง {room} ที่ {mcast_ip}:{port}[/dim]")
    seen = set()
    while True:
        try:
            data, addr = sock.recvfrom(65535)
            try:
                pkt = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                with lock:
                    console.print(f"[yellow][{now()}] [{room}] ⚠️ packet เสียจาก {addr}: {e}[/yellow]")
                continue
            ptype = pkt.get("type", "?")
            user = pkt.get("user", "?")
            msg = pkt.get("msg", "")
            ts = pkt.get("ts", now())
            with lock:
                if ptype == "HELLO" and user not in seen:
                    seen.add(user)
                    console.print(f"[green][{ts}] [{room}] → {user} เข้าร่วม (JOIN)[/green] [dim]{addr[0]}[/dim]")
                elif ptype == "BYE":
                    seen.discard(user)
                    console.print(f"[red][{ts}] [{room}] ← {user} ออกจากห้อง (LEAVE)[/red]")
                elif ptype == "CHAT":
                    console.print(f"[dim][{ts}][/dim] [cyan][{room}][/cyan] [bold magenta]{user}:[/bold magenta] [white]{msg}[/white]")
        except Exception as e:
            with lock:
                console.print(f"[yellow][{now()}] [{room}] ⚠️ exception: {e}[/yellow]")


def main():
    console.clear()
    title = Text("⚡ SwiftRoom Multicast Logger ⚡", style="bold cyan", justify="center")
    body = Text(
        "Unicast = 1:1  •  Broadcast = 1:ทุกคน  •  Multicast = 1:เฉพาะกลุ่ม\n"
        f"เริ่มเมื่อ {now()}  •  TTL แนะนำ local=1, site<32, org<64  •  ฟังทั้ง 3 กลุ่ม (ไม่ relay)",
        justify="center",
    )
    console.print(Panel(body, title=title, border_style="cyan", padding=(1, 2)))
    t = Table(title="กลุ่มที่กำลังฟัง", show_header=True, header_style="bold magenta")
    t.add_column("ห้อง", style="white")
    t.add_column("Multicast IP", style="yellow")
    t.add_column("พอร์ต", style="cyan", justify="right")
    for room, ip, port in ROOMS:
        t.add_row(room, ip, str(port))
    console.print(t)
    console.print("[dim]สี: [green]เขียว=เข้า[/green] | [red]แดง=ออก[/red] | [white]ขาว=แชท[/white] | [yellow]เหลือง=เตือน[/yellow][/dim]\n")
    threads = []
    for room, ip, port in ROOMS:
        t = threading.Thread(target=listen_room, args=(room, ip, port), daemon=True)
        t.start()
        threads.append(t)
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        console.print("\n[yellow]ปิด Logger แล้ว[/yellow]")


if __name__ == "__main__":
    main()
