# SwiftRoom — Ubiquitous Language (Domain Model)

> Glossary only. No implementation details.

## Terms

- **Room (Multicast Group)**: a named chat scope bound to one (`multicast_ip`, `port`) pair. A Member in a Room sees only messages sent to that pair.
- **Member**: a person present in a Room, identified by Nickname within that Room.
- **Nickname**: the display name a Member chooses before joining. Must be unique within a Room.
- **Heartbeat (HELLO)**: a periodic presence signal a Member broadcasts so others can track membership without a central registry.
- **Logger**: a passive observer that joins every Room to record Join / Leave / Message events. It never relays messages.
- **Join**: the first HELLO from a Member, or a HELLO arriving after absence longer than the membership timeout. Shown once.
- **Leave**: the moment a Member stops receiving a Room's group traffic and returns to the room menu (`/leave` + `BYE`). The program keeps running.
- **Exit**: quitting the program entirely (`/exit`). Sends `BYE` then closes the socket.
- **Heartbeat vs Join rule**: HELLO received within the timeout only refreshes presence and stays silent; it never re-announces Join.
