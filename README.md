# ⚡ SwiftRoom Chat

> Concurrent CLI Chat with Python AsyncIO + Rich, multi-room support
> โปรแกรมแชทผ่าน Command Line รองรับหลายห้องพร้อมกัน ด้วย AsyncIO

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![AsyncIO](https://img.shields.io/badge/Concurrency-AsyncIO-green)](https://docs.python.org/3/library/asyncio.html)
[![Rich](https://img.shields.io/badge/UI-Rich-cyan)](https://github.com/Textualize/rich)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

## ✨ Features | คุณสมบัติเด่น

| EN | TH |
|---|---|
| 💬 Multi-room chat, isolated by room | 💬 หลายห้องแชท แยกข้อความตามห้องชัดเจน |
| 👤 Custom username with duplicate check | 👤 ตั้งชื่อผู้ใช้เอง มีกันชื่อซ้ำ |
| ⏱️ Timestamps `YYYY-MM-DD HH:MM:SS` for connect / join / leave / message | ⏱️ เวลามาตรฐานทุกเหตุการณ์ |
| 🎨 Rich Terminal UI: yellow=system, white=chat, green=join, red=leave/error | 🎨 หน้าจอสวยแยกสีตามประเภท |
| ⚡ AsyncIO concurrent server, no blocking | ⚡ Server รองรับหลายคนพร้อมกันไม่บล็อก |

## 🎬 Demo | ตัวอย่าง

```text
⚡ SwiftRoom Chat ⚡  |  👤 alice  |  🏠 room1
------------------------------------------------------------
[2026-09-04 15:35:32] alice@room1> สวัสดี room1
[2026-09-04 15:35:33] bob เข้าร่วมห้อง 'room1' (Join Room Time)
[2026-09-04 15:35:35] bob: สวัสดีเหมือนกัน!
[2026-09-04 15:35:40] bob ออกจากห้อง 'room1' (Leave Room Time)

# อีกห้องคุยพร้อมกัน ไม่เห็นข้อความข้ามห้อง
[alice@room1] hello-room1-only  →  [bob@room2] ไม่เห็นข้อความนี้ ✅
```

## 🚀 Quick Start | วิธีรัน

**1. Install | ติดตั้ง**
```powershell
cd "$env:USERPROFILE\Desktop\SwiftRoom"
pip install -r requirements.txt
```

**2. Run Server | รันเซิร์ฟเวอร์ (หน้าต่างที่ 1)**
```powershell
python server.py
# หรือ: python server.py 127.0.0.1 8888
```

**3. Run Clients | รันไคลเอนต์ (หน้าต่างที่ 2, 3, ...)**
```powershell
python client.py
```

> Open 2+ terminals to test concurrent rooms.
> เปิดหลาย terminal เพื่อทดสอบหลายห้องพร้อมกัน

## 📚 Commands | คำสั่งทั้งหมด

| Command | EN | TH |
|---|---|---|
| `/create <room>` | Create + auto-join room | สร้างห้องใหม่ + เข้าอัตโนมัติ |
| `/join <room>` | Join existing room | เข้าร่วมห้องที่มีอยู่ |
| `/leave` | Leave current room | ออกจากห้องปัจจุบัน |
| `/rooms` | List rooms + user count | ดูห้องทั้งหมด + จำนวนคน |
| `/users` | List users in current room | ดูรายชื่อคนในห้อง |
| `/rename <name>` | Change username | เปลี่ยนชื่อ (ห้ามซ้ำ) |
| `/quit` or `/exit` | Quit program | ออกจากโปรแกรม |
| `/help` | Show help | ช่วยเหลือ |

## 🧪 Try This | ลองตามนี้

1. Client A: `/create room1` → พิมพ์ `สวัสดี room1`
2. Client B: `/create room2` → พิมพ์ `สวัสดี room2`
3. ผล: A เห็นเฉพาะ room1, B เห็นเฉพาะ room2 — แยกห้องชัดเจน
4. ลอง `/rooms`, `/users`, `/rename ชื่อใหม่`, `/leave`, `/join room1`

## 🏗️ Project Structure | โครงสร้าง

```text
SwiftRoom/
├── server.py          # AsyncIO server: rooms, clients, broadcast, timestamps
├── client.py          # AsyncIO + Rich client: welcome, colors, status
├── requirements.txt   # rich>=13.0
└── README.md
```

## ⚙️ How It Works | สถาปัตยกรรม

- **Server:** `asyncio.start_server` + `dict rooms` + `dict clients` + `asyncio.Lock` กัน race, broadcast แยกตามห้อง
- **Client:** 2 concurrent tasks — `listen_loop` รับข้อความ + `input_loop` รับคีย์บอร์ดผ่าน `run_in_executor` (เพราะ `input()` เป็น blocking)
- **Protocol:** บรรทัด `TAG|payload` เช่น `CHAT|timestamp|user|msg`, `JOIN|...`, `LEAVE|...`, `SYS|...`, `ERROR|...`, `ROOM|...`
- **Why AsyncIO?** งานนี้เป็น I/O-bound (รอ network) AsyncIO เบากว่า Threading รองรับหลายร้อย connection ใน process เดียว

## 🎨 UI & Timestamps

- Header แสดงชื่อโปรแกรม + `👤 user` + `🏠 room`
- สี: 💛 เหลือง=ระบบ / ⬜ ขาว=แชท / 💚 เขียว=เข้า / ❤️ แดง=ออก+error
- Timestamp `YYYY-MM-DD HH:MM:SS` ทุกเหตุการณ์: Connection / Join / Leave / Message

## 🛡️ Error Handling | การจัดการข้อผิดพลาด

- ชื่อซ้ำ → `ERROR` + ให้ตั้งใหม่
- ห้องไม่มี → แนะนำ `/rooms` หรือ `/create`
- คำสั่งผิด → แนะนำ `/help`
- พิมพ์แชทโดยยังไม่เข้าห้อง → เตือนให้ `/join` ก่อน
- Client หลุด → ลบออกจากห้อง + broadcast `LEAVE`

## 📄 License

MIT — ดูเพิ่มที่ [LICENSE](./LICENSE)
