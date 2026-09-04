# ⚡ SwiftRoom Chat

> Two-mode CLI Chat: TCP AsyncIO rooms + UDP Multicast groups — with Rich UI
> แชท CLI 2 โหมด: ห้อง TCP (AsyncIO) + กลุ่ม Multicast (UDP) — หน้าจอ Rich สวยทั้งคู่

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![AsyncIO](https://img.shields.io/badge/TCP-AsyncIO-green)](https://docs.python.org/3/library/asyncio.html)
[![Multicast](https://img.shields.io/badge/UDP-Multicast-orange)](https://en.wikipedia.org/wiki/Multicast)
[![Rich](https://img.shields.io/badge/UI-Rich-cyan)](https://github.com/Textualize/rich)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

## 🧭 Choose Mode | เลือกโหมด

| Mode | Run | Best for |
|---|---|---|
| 🖥️ **TCP rooms** ([go](#tcp-mode)) | `python server.py` + `python client.py` | หลายห้องบน server กลาง, มี `/create /join /rooms` |
| 📡 **Multicast groups** ([go](#multicast-mode)) | `python multicast_server.py` + `python multicast_client.py` | P2P ผ่าน Class D `239.x`, heartbeat presence |

## 📑 Contents | สารบัญ

- [Install](#install) — ติดตั้งครั้งเดียวใช้ได้ทั้ง 2 โหมด
- [TCP Mode](#tcp-mode) — Features, Demo, Run, Commands, Try
- [Multicast Mode](#multicast-mode) — Concepts, Rooms, Demo, Run, Commands
- [Shared](#shared) — Structure, Architecture, UI, Errors
- [License](#license)

---

<a id="install"></a>
## 📦 Install | ติดตั้ง (ครั้งเดียวใช้ทั้ง 2 โหมด)

```powershell
cd "$env:USERPROFILE\Desktop\SwiftRoom"
pip install -r requirements.txt
```

---

<a id="tcp-mode"></a>
# 🖥️ TCP Mode | โหมด TCP

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

## 🚀 Run TCP | วิธีรัน

```powershell
# หน้าต่างที่ 1 — Server:
python server.py
# หรือ: python server.py 127.0.0.1 8888

# หน้าต่างที่ 2, 3, ... — Client:
python client.py
```

> Open 2+ terminals to test concurrent rooms.
> เปิดหลาย terminal เพื่อทดสอบหลายห้องพร้อมกัน

## 📚 Commands | คำสั่งทั้งหมด (TCP)

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

## 🧪 Try This | ลองตามนี้ (TCP)

1. Client A: `/create room1` → พิมพ์ `สวัสดี room1`
2. Client B: `/create room2` → พิมพ์ `สวัสดี room2`
3. ผล: A เห็นเฉพาะ room1, B เห็นเฉพาะ room2 — แยกห้องชัดเจน
4. ลอง `/rooms`, `/users`, `/rename ชื่อใหม่`, `/leave`, `/join room1`

---

<a id="multicast-mode"></a>
# 📡 Multicast Mode | โหมดมัลติแคสต์ (UDP)

> P2P chat over UDP multicast (Class D) + Rich UI + heartbeat presence
> แชทแบบ P2P ผ่าน UDP multicast + หน้าจอ Rich + heartbeat

## หลักการสั้นๆ | Concepts

- **Unicast** = 1:1, **Broadcast** = 1:ทุกคนในวง, **Multicast** = 1:เฉพาะสมาชิกกลุ่ม (Class D `224.0.0.0`–`239.255.255.255`)
- Client คุยกันเองตรงๆ ไม่ผ่าน server กลาง | Server เป็นแค่ **Logger** join ทั้ง 3 กลุ่มเพื่อ log ไม่ได้ relay
- **TTL:** `1`=local (ทดสอบเครื่องเดียว), `<32`=site, `<64`=organization, `<128+`=global
- **Loopback** `1` = เครื่องส่งได้รับข้อความตัวเองด้วย (จำเป็นตอนเทสเครื่องเดียว)

## ห้อง Multicast | Rooms

| ห้อง | Multicast IP | พอร์ต |
|---|---|---|
| room1 | `239.1.1.10` | 5000 |
| room2 | `239.1.1.20` | 6000 |
| room3 | `239.1.1.30` | 7000 |

> ใช้ช่วง `239.x` (administratively scoped) แทน `224.0.0.1-3` ที่เป็น reserved ใช้จริงจะพัง

## 🎬 Demo | ตัวอย่าง (Multicast)

```text
⚡ SwiftRoom Multicast ⚡  |  👤 Guy  |  🏠 room1 (239.1.1.10:5000)
------------------------------------------------------------
[2026-09-04 16:02:07] → Guy เข้าร่วมห้อง
[2026-09-04 16:02:12] → Joji เข้าร่วมห้อง   # โชว์ครั้งเดียว (heartbeat ต่อจากนี้เงียบ)
[2026-09-04 16:02:20] Guy: สวัสดี room1
[2026-09-04 16:02:25] Joji: สวัสดีเหมือนกัน!

# Client ใน room2 (239.1.1.20:6000) ไม่เห็นข้อความข้างบน ✅
```

## วิธีรัน Multicast | Run

```powershell
# หน้าต่างที่ 1 — Logger กลาง:
python multicast_server.py
# หน้าต่างที่ 2, 3, ... — Client:
python multicast_client.py
```

1. ตั้ง nickname (1-20 ตัว ไม่มีช่องว่าง)
2. เลือกห้อง 1/2/3 (พิมพ์ `/help` ดูคำสั่ง หรือ `/exit` ออก)
3. พิมพ์ข้อความส่งได้เลย ลองพิมพ์ไทยได้ (UTF-8)
4. ทดสอบแยกห้อง: ห้อง 1 คุยกัน ห้อง 2 ต้องไม่เห็น

## คำสั่ง Multicast | Commands

| Command | ความหมาย |
|---|---|
| `/list` | ดูสมาชิกในห้อง (จาก heartbeat 5 วิ, timeout 15 วิ) |
| `/leave` | ออกห้องกลับไปเมนูเลือกห้อง (ส่ง `BYE` + drop membership) |
| `/exit` | ปิดโปรแกรม |
| `/help` | แสดงความช่วยเหลือ |

---

<a id="shared"></a>
# 🧩 Shared | ส่วนกลาง

<a id="project-structure"></a>
## 🏗️ Project Structure | โครงสร้าง

```text
SwiftRoom/
├── server.py            # TCP AsyncIO server: rooms, clients, broadcast, timestamps
├── client.py            # TCP AsyncIO + Rich client: welcome, colors, status
├── multicast_server.py  # UDP Multicast Logger: join 3 กลุ่ม, log JOIN/LEAVE/CHAT
├── multicast_client.py  # UDP Multicast + Rich + Thread รับ/ส่ง, heartbeat
├── CONTEXT.md           # ศัพท์โดเมน (Room, Member, Heartbeat, Logger, Join/Leave/Exit)
├── requirements.txt     # rich>=13.0
└── README.md
```

## ⚙️ Architecture | สถาปัตยกรรม

**TCP:**
- **Server:** `asyncio.start_server` + `dict rooms` + `dict clients` + `asyncio.Lock` กัน race, broadcast แยกตามห้อง
- **Client:** 2 concurrent tasks — `listen_loop` รับข้อความ + `input_loop` รับคีย์บอร์ดผ่าน `run_in_executor` (เพราะ `input()` เป็น blocking)
- **Protocol:** บรรทัด `TAG|payload` เช่น `CHAT|timestamp|user|msg`, `JOIN|...`, `LEAVE|...`, `SYS|...`, `ERROR|...`, `ROOM|...`
- **Why AsyncIO?** งานนี้เป็น I/O-bound (รอ network) AsyncIO เบากว่า Threading รองรับหลายร้อย connection ใน process เดียว

**Multicast:**
- **Client:** UDP socket + `IP_ADD_MEMBERSHIP` + `IP_MULTICAST_TTL=1` + `IP_MULTICAST_LOOP=1`, 2 thread (recv + heartbeat) + main thread รับ input
- **Presence:** `HELLO` ทุก 5 วิ, `BYE` ตอนออก; `Join` = HELLO ครั้งแรกหรือกลับมาหลังหายเกิน timeout (heartbeat ระหว่างนั้นเงียบ ไม่พิมพ์รัว)
- **Validate:** ตรวจ IP ว่าอยู่ใน Class D จริง และปฏิเสธช่วง reserved `224.0.0.0/24`
- ศัพท์โดเมนดูที่ [CONTEXT.md](./CONTEXT.md)

## 🎨 UI & Timestamps

- Header แสดงชื่อโปรแกรม + `👤 user` + `🏠 room`
- สี: 💛 เหลือง=ระบบ / ⬜ ขาว=แชท / 💚 เขียว=เข้า / ❤️ แดง=ออก+error (ทั้ง TCP และ Multicast)
- Timestamp `YYYY-MM-DD HH:MM:SS` ทุกเหตุการณ์: Connection / Join / Leave / Message

## 🛡️ Error Handling | การจัดการข้อผิดพลาด

**TCP:**
- ชื่อซ้ำ → `ERROR` + ให้ตั้งใหม่
- ห้องไม่มี → แนะนำ `/rooms` หรือ `/create`
- คำสั่งผิด → แนะนำ `/help`
- พิมพ์แชทโดยยังไม่เข้าห้อง → เตือนให้ `/join` ก่อน
- Client หลุด → ลบออกจากห้อง + broadcast `LEAVE`

**Multicast:**
- nickname ผิดรูปแบบ → ปฏิเสธก่อนเข้าห้อง
- เลือกห้องผิด / IP ไม่ใช่ Class D / ช่วง reserved → ปฏิเสธพร้อมเหตุผล
- คำสั่งผิด → แนะนำ `/help`

---

<a id="license"></a>
## 📄 License

MIT — ดูเพิ่มที่ [LICENSE](./LICENSE)
