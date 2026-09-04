"""
SwiftRoom Client — AsyncIO + Rich Terminal UI
รัน: python client.py [host] [port]  (ค่าเริ่มต้น localhost 8888)
ต้องติดตั้ง: pip install rich
"""
import asyncio
import sys
from rich.console import Console

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

HOST = "127.0.0.1"
PORT = 8888

console = Console()
state = {"username": "?", "room": None}


def show_welcome():
    console.clear()
    title = Text("⚡ SwiftRoom Chat ⚡", style="bold cyan", justify="center")
    body = Text(
        "โปรแกรมแชท CLI แบบ Concurrent ด้วย AsyncIO\n"
        "หลายห้อง • หลายผู้ใช้ • แยกห้องชัดเจน • Timestamp ทุกเหตุการณ์",
        justify="center",
    )
    console.print(Panel(body, title=title, border_style="cyan", padding=(1, 2)))
    t = Table(show_header=False, box=None, padding=(0, 1))
    t.add_column("cmd", style="green bold")
    t.add_column("desc", style="white")
    t.add_row("/create <ห้อง>", "สร้างห้องใหม่ + เข้าห้องอัตโนมัติ")
    t.add_row("/join <ห้อง>", "เข้าร่วมห้องที่มีอยู่")
    t.add_row("/leave", "ออกจากห้องปัจจุบัน")
    t.add_row("/rooms", "ดูห้องทั้งหมด + จำนวนคน")
    t.add_row("/users", "ดูรายชื่อคนในห้องปัจจุบัน")
    t.add_row("/rename <ชื่อ>", "เปลี่ยนชื่อผู้ใช้")
    t.add_row("/quit", "ออกจากโปรแกรม")
    t.add_row("/help", "แสดงความช่วยเหลือ")
    console.print(Panel(t, title="[yellow]คำสั่งพื้นฐาน[/yellow]", border_style="yellow"))
    console.print("[dim]สี: [yellow]เหลือง=ระบบ[/yellow] | [white]ขาว=แชท[/white] | [green]เขียว=เข้า[/green] | [red]แดง=ออก/ผิดพลาด[/red][/dim]\n")


def show_status():
    room = state["room"] or "[red]ยังไม่เข้าห้อง[/red]"
    console.print(
        f"[bold cyan]SwiftRoom[/bold cyan] | 👤 [bold]{state['username']}[/bold] | 🏠 {room} "
        f"[dim]| พิมพ์ข้อความเพื่อคุย / /help เพื่อดูคำสั่ง[/dim]"
    )
    console.print("[dim]" + "-" * 60 + "[/dim]")


def handle_server_line(line: str):
    """แปลงโปรโตคอล TAG|... เป็นข้อความสี rich"""
    if "|" not in line:
        console.print(line)
        return
    tag, _, rest = line.partition("|")

    if tag == "ASK_USERNAME":
        return
    elif tag == "OK":
        console.print(f"[yellow]✔ {rest}[/yellow]")
    elif tag == "SYS":
        console.print(f"[yellow]{rest}[/yellow]")
        # ดักจับ rename สำเร็จเพื่ออัปเดต prompt: "เปลี่ยนชื่อ OLD -> NEW สำเร็จ"
        if "เปลี่ยนชื่อ" in rest and "->" in rest:
            try:
                new = rest.split("->")[1].strip().split()[0]
                if new:
                    state["username"] = new
            except Exception:
                pass
    elif tag == "INFO":
        console.print(f"[cyan]{rest}[/cyan]")
    elif tag == "ERROR":
        console.print(f"[bold red]✘ {rest}[/bold red]")
    elif tag == "CHAT":
        parts = rest.split("|", 2)
        if len(parts) == 3:
            ts, user, msg = parts
            me = " (คุณ)" if user == state["username"] else ""
            console.print(f"[dim][{ts}][/dim] [bold magenta]{user}{me}:[/bold magenta] [white]{msg}[/white]")
        else:
            console.print(f"[white]{rest}[/white]")
    elif tag == "JOIN":
        parts = rest.split("|", 2)
        if len(parts) == 3:
            ts, user, room = parts
            console.print(f"[green]→ [{ts}] {user} เข้าร่วมห้อง '{room}' (Join Room Time)[/green]")
        else:
            console.print(f"[green]{rest}[/green]")
    elif tag == "LEAVE":
        parts = rest.split("|", 2)
        if len(parts) == 3:
            ts, user, room = parts
            console.print(f"[red]← [{ts}] {user} ออกจากห้อง '{room}' (Leave Room Time)[/red]")
        else:
            console.print(f"[red]{rest}[/red]")
    elif tag == "ROOM":
        state["room"] = rest.strip() or None
        if state["room"]:
            console.print(f"[dim]📍 ตอนนี้คุณอยู่ในห้อง '{state['room']}'[/dim]")
        else:
            console.print("[dim]📍 ตอนนี้คุณไม่ได้อยู่ในห้องใด[/dim]")
    elif tag == "BYE":
        console.print(f"[yellow]{rest}[/yellow]")
    else:
        console.print(rest)


async def listen_loop(reader: asyncio.StreamReader):
    while True:
        raw = await reader.readline()
        if not raw:
            console.print("[bold red]ขาดการเชื่อมต่อจาก Server[/bold red]")
            break
        line = raw.decode("utf-8", errors="replace").rstrip("\n")
        if line:
            handle_server_line(line)


async def input_loop(reader, writer: asyncio.StreamWriter):
    loop = asyncio.get_running_loop()
    while True:
        try:
            prompt = f"[{state['username']}@{state['room'] or 'lobby'}]> "
            line = await loop.run_in_executor(None, input, prompt)
        except (EOFError, KeyboardInterrupt):
            line = "/quit"
        line = line.strip()
        if not line:
            continue
        try:
            writer.write((line + "\n").encode("utf-8"))
            await writer.drain()
        except (ConnectionResetError, BrokenPipeError, RuntimeError):
            break
        if line.lower() in ("/quit", "/exit"):
            await asyncio.sleep(0.5)
            break


async def do_handshake(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> bool:
    """handshake แบบ sync ก่อนเริ่ม concurrent loop — เสถียร ไม่ race"""
    loop = asyncio.get_running_loop()
    while True:
        raw = await reader.readline()
        if not raw:
            console.print("[red]Server ปิดการเชื่อมต่อ[/red]")
            return False
        line = raw.decode("utf-8", errors="replace").rstrip("\n")
        if not line:
            continue
        tag, _, rest = line.partition("|")
        if tag == "SYS":
            console.print(f"[yellow]{rest}[/yellow]")
        elif tag == "ERROR":
            console.print(f"[bold red]✘ {rest}[/bold red]")
        elif tag == "ASK_USERNAME":
            try:
                name = await loop.run_in_executor(None, input, "ตั้งชื่อผู้ใช้ของคุณ: ")
            except (EOFError, KeyboardInterrupt):
                return False
            name = name.strip()
            if not name:
                console.print("[red]ชื่อห้ามว่าง[/red]")
                # ส่งชื่อว่างไปให้ server ปฏิเสธแล้ววนรอบใหม่ (server จะส่ง ASK กลับมา)
                writer.write(b"\n")
                await writer.drain()
                continue
            state["username"] = name
            writer.write((name + "\n").encode("utf-8"))
            await writer.drain()
        elif tag == "OK":
            console.print(f"[yellow]✔ {rest}[/yellow]")
            return True
        else:
            handle_server_line(line)


async def main():
    host, port = HOST, PORT
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    show_welcome()

    try:
        reader, writer = await asyncio.open_connection(host, port)
    except (ConnectionRefusedError, OSError) as e:
        console.print(f"[bold red]เชื่อมต่อ {host}:{port} ไม่ได้: {e}[/bold red]")
        console.print("[yellow]เปิด Server ก่อนด้วย: python server.py[/yellow]")
        return

    ok = await do_handshake(reader, writer)
    if not ok:
        try:
            writer.close()
        except Exception:
            pass
        return

    show_status()
    console.print("[dim]พิมพ์ /help เพื่อดูคำสั่งทั้งหมด | พิมพ์ข้อความธรรมดาเพื่อส่งแชทในห้อง[/dim]\n")

    listen_task = asyncio.create_task(listen_loop(reader))
    input_task = asyncio.create_task(input_loop(reader, writer))

    done, pending = await asyncio.wait(
        [listen_task, input_task], return_when=asyncio.FIRST_COMPLETED
    )
    for t in pending:
        t.cancel()
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass
    console.print("[yellow]ออกจาก SwiftRoom แล้ว บาย! 👋[/yellow]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nออกแล้ว")
