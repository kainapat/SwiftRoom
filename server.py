"""
SwiftRoom Server — AsyncIO Concurrent Chat Server
รัน: python server.py [host] [port]  (ค่าเริ่มต้น localhost 8888)
"""
import asyncio
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOST = "127.0.0.1"
PORT = 8888

# room_name -> set of StreamWriter
rooms: dict[str, set[asyncio.StreamWriter]] = {}
# writer -> {username, room, addr, connect_time}
clients: dict[asyncio.StreamWriter, dict] = {}
usernames: set[str] = set([])
lock = asyncio.Lock()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def send(writer: asyncio.StreamWriter, msg: str):
    try:
        writer.write((msg + "\n").encode("utf-8"))
        await writer.drain()
    except (ConnectionResetError, BrokenPipeError):
        pass


async def broadcast(room: str, msg: str, exclude=None):
    """ส่งข้อความถึงทุกคนในห้อง (แยกห้องชัดเจน ไม่ข้ามห้อง)"""
    targets = list(rooms.get(room, set()))
    for w in targets:
        if w is exclude:
            continue
        await send(w, msg)


def valid_name(name: str) -> str | None:
    """คืน None ถ้าผ่าน, คืนเหตุผลถ้าไม่ผ่าน"""
    if not name or len(name) > 20:
        return "ชื่อต้องยาว 1-20 ตัวอักษร"
    if " " in name or "|" in name:
        return "ชื่อห้ามมีช่องว่างหรือเครื่องหมาย |"
    if name.startswith("/"):
        return "ชื่อห้ามขึ้นต้นด้วย /"
    return None


async def leave_room(writer, announce=True):
    info = clients.get(writer)
    if not info or not info["room"]:
        return None
    room = info["room"]
    ts = now_str()
    async with lock:
        if room in rooms and writer in rooms[room]:
            rooms[room].discard(writer)
        info["room"] = None
    if announce:
        await broadcast(room, f"LEAVE|{ts}|{info['username']}|{room}")
    await send(writer, f"ROOM|")  # บอก client ว่าตอนนี้ไม่มีห้อง
    await send(writer, f"SYS|[{ts}] คุณออกจากห้อง '{room}' แล้ว (Leave Room Time: {ts})")
    return room


async def join_room(writer, room: str):
    info = clients[writer]
    ts = now_str()
    # ออกจากห้องเก่าก่อน (ไม่ประกาศซ้ำซ้อน — ประกาศ leave ให้ห้องเก่า)
    old = info["room"]
    if old == room:
        await send(writer, f"ERROR|คุณอยู่ในห้อง '{room}' อยู่แล้ว")
        return
    if old:
        async with lock:
            if old in rooms and writer in rooms[old]:
                rooms[old].discard(writer)
        await broadcast(old, f"LEAVE|{ts}|{info['username']}|{old}")
    async with lock:
        rooms.setdefault(room, set()).add(writer)
        info["room"] = room
    await send(writer, f"ROOM|{room}")
    await send(writer, f"SYS|[{ts}] คุณเข้าร่วมห้อง '{room}' แล้ว (Join Room Time: {ts}) | ห้องนี้มี {len(rooms[room])} คน")
    await broadcast(room, f"JOIN|{ts}|{info['username']}|{room}", exclude=writer)


async def handle_command(writer, line: str) -> bool:
    """คืน True = ยังอยู่ต่อ, False = ให้ตัดการเชื่อมต่อ"""
    info = clients[writer]
    parts = line.strip().split()
    cmd = parts[0].lower()
    arg = " ".join(parts[1:]).strip() if len(parts) > 1 else ""
    ts = now_str()

    if cmd == "/create":
        if not arg:
            await send(writer, "ERROR|วิธีใช้: /create <room_name>")
        elif " " in arg or "|" in arg or len(arg) > 30:
            await send(writer, "ERROR|ชื่อห้องห้ามมีช่องว่างหรือ | และยาวไม่เกิน 30 ตัว")
        elif arg in rooms:
            await send(writer, f"ERROR|ห้อง '{arg}' มีอยู่แล้ว ใช้ /join {arg} เพื่อเข้าร่วม")
        else:
            async with lock:
                rooms[arg] = set()
            await send(writer, f"SYS|[{ts}] สร้างห้อง '{arg}' สำเร็จ")
            await join_room(writer, arg)

    elif cmd == "/join":
        if not arg:
            await send(writer, "ERROR|วิธีใช้: /join <room_name>")
        elif arg not in rooms:
            await send(writer, f"ERROR|ห้อง '{arg}' ไม่มีอยู่ ใช้ /rooms ดูห้องทั้งหมด หรือ /create {arg} เพื่อสร้าง")
        else:
            await join_room(writer, arg)

    elif cmd == "/leave":
        if not info["room"]:
            await send(writer, "ERROR|ตอนนี้คุณไม่ได้อยู่ในห้องใดเลย")
        else:
            await leave_room(writer)

    elif cmd == "/rooms":
        async with lock:
            if not rooms:
                await send(writer, "INFO|ยังไม่มีห้องเลย สร้างด้วย /create <room_name>")
            else:
                lines = [f"{r} ({len(m)} คน)" for r, m in rooms.items()]
                await send(writer, "INFO|ห้องทั้งหมด: " + " | ".join(lines))

    elif cmd == "/users":
        if not info["room"]:
            await send(writer, "ERROR|คุณไม่ได้อยู่ในห้อง ใช้ /join <room_name> ก่อน")
        else:
            room = info["room"]
            names = [clients[w]["username"] for w in rooms.get(room, set()) if w in clients]
            await send(writer, f"INFO|ผู้ใช้ในห้อง '{room}' ({len(names)} คน): " + ", ".join(sorted(names)))

    elif cmd == "/rename":
        if not arg:
            await send(writer, "ERROR|วิธีใช้: /rename <new_name>")
        else:
            reason = valid_name(arg)
            if reason:
                await send(writer, f"ERROR|{reason}")
            elif arg in usernames:
                await send(writer, f"ERROR|ชื่อ '{arg}' ถูกใช้แล้ว กรุณาเลือกชื่ออื่น")
            else:
                old = info["username"]
                async with lock:
                    usernames.discard(old)
                    usernames.add(arg)
                    info["username"] = arg
                await send(writer, f"SYS|[{ts}] เปลี่ยนชื่อ {old} -> {arg} สำเร็จ")
                if info["room"]:
                    await broadcast(info["room"], f"SYS|[{ts}] {old} เปลี่ยนชื่อเป็น {arg}")

    elif cmd in ("/quit", "/exit"):
        await send(writer, "BYE|ขอบคุณที่ใช้ SwiftRoom แล้วเจอกันใหม่!")
        return False

    elif cmd == "/help":
        await send(writer, "INFO|คำสั่ง: /create <ห้อง> | /join <ห้อง> | /leave | /rooms | /users | /rename <ชื่อใหม่> | /quit | /help")

    else:
        await send(writer, f"ERROR|คำสั่ง '{cmd}' ไม่รู้จัก พิมพ์ /help ดูคำสั่งทั้งหมด")

    return True


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info("peername")
    connect_time = now_str()
    print(f"[{connect_time}] เชื่อมต่อใหม่จาก {addr} (Connection Time)")

    await send(writer, f"SYS|ยินดีต้อนรับสู่ SwiftRoom! (เชื่อมต่อเมื่อ {connect_time})")
    await send(writer, "ASK_USERNAME|กรุณาตั้งชื่อผู้ใช้ (Username):")

    username = None
    try:
        while True:
            raw = await reader.readline()
            if not raw:
                writer.close()
                return
            candidate = raw.decode("utf-8", errors="replace").strip()
            reason = valid_name(candidate)
            if reason:
                await send(writer, f"ERROR|{reason} ลองใหม่อีกครั้ง:")
                await send(writer, "ASK_USERNAME|ชื่อผู้ใช้:")
                continue
            async with lock:
                if candidate in usernames:
                    await send(writer, f"ERROR|ชื่อ '{candidate}' ถูกใช้แล้ว กรุณาเลือกชื่ออื่น:")
                    await send(writer, "ASK_USERNAME|ชื่อผู้ใช้:")
                    continue
                usernames.add(candidate)
                username = candidate
                clients[writer] = {"username": username, "room": None, "addr": addr, "connect_time": connect_time}
            break

        await send(writer, f"OK|สวัสดี {username}! เชื่อมต่อเมื่อ {connect_time} | พิมพ์ /help ดูคำสั่ง | /create <ห้อง> เพื่อเริ่ม")
        print(f"[{now_str()}] ผู้ใช้ '{username}' ลงทะเบียนจาก {addr}")

        while True:
            raw = await reader.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            if line.startswith("/"):
                stay = await handle_command(writer, line)
                if not stay:
                    break
            else:
                info = clients.get(writer)
                if not info or not info["room"]:
                    await send(writer, "ERROR|คุณยังไม่ได้เข้าห้อง ใช้ /create <ห้อง> หรือ /join <ห้อง> ก่อน แล้วค่อยพิมพ์ข้อความ")
                    continue
                ts = now_str()
                room = info["room"]
                await broadcast(room, f"CHAT|{ts}|{info['username']}|{line}")
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        info = clients.pop(writer, None)
        if info:
            async with lock:
                usernames.discard(info["username"])
                if info["room"] and info["room"] in rooms:
                    rooms[info["room"]].discard(writer)
            if info["room"]:
                ts = now_str()
                await broadcast(info["room"], f"LEAVE|{ts}|{info['username']}|{info['room']}")
            print(f"[{now_str()}] '{info.get('username')}' ตัดการเชื่อมต่อ (เคยอยู่ห้อง {info.get('room')})")
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def main():
    import sys
    host, port = HOST, PORT
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    server = await asyncio.start_server(handle_client, host, port)
    print("=" * 50)
    print(f" SwiftRoom Server พร้อมแล้วที่ {host}:{port}")
    print(f" เริ่มเมื่อ {now_str()} | รอ Client เชื่อมต่อ...")
    print("=" * 50)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nปิด Server แล้ว")
