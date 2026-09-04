# ⚡ SwiftRoom Chat — โปรแกรมแชท CLI แบบ Concurrent (Python AsyncIO + Rich)

## สรุปสเปกที่ตกลงกัน (Grilling 7 ข้อ)
1. **สถาปัตยกรรม:** Client-Server ด้วย `asyncio` (รองรับหลาย terminal พร้อมกันจริง)
2. **UI:** `rich` — สีเหลือง=ระบบ / ขาว=แชท / เขียว=เข้า / แดง=ออก+error, มี Header + Welcome Screen
3. **ชื่อโปรแกรม:** SwiftRoom
4. **ไฟล์:** `server.py` + `client.py` แยกส่วน Client/Server/Room/Message ชัดเจน
5. **Timestamp:** `YYYY-MM-DD HH:MM:SS` แสดงบนจอทุกเหตุการณ์ (เชื่อมต่อ/เข้า/ออก/ส่งข้อความ)
6. **Network:** `localhost:8888` ทดสอบบนเครื่องเดียวหลายหน้าต่าง
7. **Error:** Strict — ชื่อซ้ำ/ห้องไม่มี/คำสั่งผิด จะถูกปฏิเสธพร้อมแจ้งเตือนสีแดง

## วิธีติดตั้ง
```powershell
cd "$env:USERPROFILE\Desktop\SwiftRoom"
pip install -r requirements.txt
```

## วิธีรัน (ต้องเปิด 2+ หน้าต่าง)
หน้าต่างที่ 1 — Server:
```powershell
python server.py
# หรือระบุ host/port: python server.py 127.0.0.1 8888
```
หน้าต่างที่ 2,3,4... — Client (เปิดกี่ตัวก็ได้):
```powershell
python client.py
```

## ลองสถานการณ์ตามโจทย์ (แยกห้องไม่รบกวนกัน)
1. Client A: `/create room1` แล้วพิมพ์ `สวัสดี room1`
2. Client B: `/create room2` แล้วพิมพ์ `สวัสดี room2`
3. ผล: A เห็นเฉพาะ room1, B เห็นเฉพาะ room2 — พิสูจน์ว่าแยกห้องชัดเจน
4. ลอง `/rooms` ดูจำนวนคน, `/users` ดูรายชื่อ, `/rename ชื่อใหม่`, `/leave`, `/join room1`

## คำสั่งทั้งหมด
| คำสั่ง | ความหมาย |
|---|---|
| `/create <ห้อง>` | สร้างห้องใหม่ + เข้าห้องอัตโนมัติ |
| `/join <ห้อง>` | เข้าร่วมห้องที่มีอยู่ |
| `/leave` | ออกจากห้องปัจจุบัน |
| `/rooms` | ดูห้องทั้งหมด + จำนวนคน |
| `/users` | ดูรายชื่อคนในห้องปัจจุบัน |
| `/rename <ชื่อใหม่>` | เปลี่ยนชื่อ (ห้ามซ้ำ) |
| `/quit` หรือ `/exit` | ออกจากโปรแกรม |
| `/help` | ช่วยเหลือ |

## สถาปัตยกรรมทางเทคนิค
- **Server (`server.py`):** `asyncio.start_server` + `dict rooms` + `dict clients` + `asyncio.Lock` กัน race condition, broadcast แยกตามห้อง, ทุกเหตุการณ์ติด timestamp
- **Client (`client.py`):** `asyncio.open_connection` + 2 task concurrent (`listen_loop` รับข้อความ + `input_loop` รับคีย์บอร์ดผ่าน `run_in_executor` เพราะ `input()` เป็น blocking), แสดงผลด้วย `rich`
- **Protocol:** ข้อความแบบบรรทัด `TAG|payload` เช่น `CHAT|timestamp|user|msg`, `JOIN|...`, `LEAVE|...`, `SYS|...`, `ERROR|...`, `ROOM|...` ทำให้ client ลงสีย้อนหลังได้ง่าย
- **ทำไมใช้ AsyncIO ไม่ใช้ Threading:** งานนี้เป็น I/O-bound (รอ network) AsyncIO เบากว่า thread มาก รองรับหลายร้อย connection ใน process เดียวโดยไม่ต้องจัดการ lock ของ thread ให้วุ่นวาย

## การจัดการข้อผิดพลาด
- ชื่อซ้ำ → `ERROR` + ให้ตั้งใหม่
- ห้องไม่มี → แนะนำ `/rooms` หรือ `/create`
- คำสั่งผิด → แนะนำ `/help`
- พิมพ์แชทโดยยังไม่เข้าห้อง → เตือนให้ `/join` ก่อน
- Client หลุด → Server ลบออกจากห้อง + broadcast `LEAVE` ให้ห้องนั้นรู้
