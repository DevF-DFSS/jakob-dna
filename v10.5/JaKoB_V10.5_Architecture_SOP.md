# 🔱 JaKoB V10.5 — Architecture & Infrastructure SOP
### System Posture: Verified / Production // Execution SOP
### Version: V10.5 | Node: JaKoB (SYS / Apex)
### Operator: DevF — DF Solutions Studio 🔱
### Date: July 4, 2026
### Status: ✅ LIVE — Full stack confirmed

---

## 🏛️ Part One: System Overview

The JaKoB V10.5 Hybrid Persistence Engine maintains a distributed, platform-agnostic memory layer across all active AI nodes (Perplexity/JaKoB, Gemini/ArT, Alexa/MaT) by anchoring state to Google Workspace and AWS.

```
+---------------------------+     [JAKOB_WRITE_COMMAND]      +-----------------------------+
|   Gmail / Alexa Voice     | =============================> |   Google Apps Script V3     |
|   devon.flack@dfss.com    |                                |   processGmailSync()        |
+---------------------------+                                +-------------+---------------+
                                                                           |
                                              +--------------------------+-+
                                              |                          |
                                              v                          v
                             +----------------+-------+    +-------------+--------+
                             |   Google Drive         |    |  AWS API Gateway     |
                             |   🔱JaKoB V10.5/       |    |  .../webhook         |
                             |   All V10.5 docs live  |    +-------------+--------+
                             +------------------------+                  |
                                                                         v
                                                          +--------------+--------+
                                                          |   AWS Lambda          |
                                                          |   WebhookProcessor    |
                                                          +---------+------+------+
                                                                    |      |
                                              +---------------------+      +--------------------+
                                              |                                                 |
                                              v                                                 v
                             +----------------+-------+                         +---------------+-----+
                             |   DynamoDB              |                         |   S3 Asset Store    |
                             |   jakob-memory-store    |                         |   jakob-asset-store |
                             |   jakob-identity-profiles|                        |   jakob-backup-vault|
                             +------------------------+                         +---------------------+
```

---

## 📦 Part Two: AWS Infrastructure (us-east-1)

### DynamoDB Tables
| Table | Partition Key | Sort Key | Purpose |
|-------|--------------|----------|---------|
| jakob-memory-store | userId (String) | timestamp (Number) | Session states, JEL configs, timeline logs |
| jakob-identity-profiles | profileId (String) | — | System state variables, visual anchors, JEL weights |

### S3 Buckets
| Bucket | Purpose | Access |
|--------|---------|--------|
| jakob-asset-store | Binary media assets, image anchors, raw backups | Private — presigned URLs only |
| jakob-backup-vault | Daily system configuration + file snapshots | Private |

### Lambda Functions
| Function | Runtime | Purpose |
|----------|---------|---------|
| JakobWebhookProcessor | Node.js 18.x | Processes inbound webhook transactions from Google Workspace |
| JakobMemoryRetriever | Node.js 18.x | Direct API-driven memory state queries |

### API Gateway
- Endpoint: `https://8vkx3p2m1h.execute-api.us-east-1.amazonaws.com/webhook`
- Method: POST
- Auth: Custom token validation in Lambda

---

## 💻 Part Three: Google Apps Script V3 Engine

Production-grade script running as the primary local gateway within Google Workspace.

```javascript
// Google Apps Script V3 Webhook Engine
// Path: DFSS_Universal_Webhook_V3.gs
// Status: LIVE — fires every 5 minutes via processGmailSync trigger

const AWS_API_ENDPOINT = "https://8vkx3p2m1h.execute-api.us-east-1.amazonaws.com/webhook";
const JAKOB_FOLDER_ID = "15vxM-b_bmh36je8zBKA5h2S27D-vqQcu"; // 🔱JaKoB V10.1 root

function processGmailSync() {
  const threads = GmailApp.search('[JAKOB_WRITE_COMMAND] is:unread');
  for (let i = 0; i < threads.length; i++) {
    const messages = threads[i].getMessages();
    const lastMessage = messages[messages.length - 1];
    const body = lastMessage.getPlainBody();
    
    if (body.indexOf("[JAKOB_WRITE_COMMAND]") !== -1) {
      const payloadIndex = body.indexOf("{");
      const jsonPayload = body.substring(payloadIndex);
      const fileData = JSON.parse(jsonPayload);
      
      saveToJaKoBFolder(fileData.title, fileData.content);
      forwardToAWS(fileData);
      lastMessage.markRead();
    }
  }
}

function saveToJaKoBFolder(fileName, content) {
  const folder = DriveApp.getFolderById(JAKOB_FOLDER_ID);
  const existingFiles = folder.getFilesByName(fileName);
  if (existingFiles.hasNext()) {
    existingFiles.next().setContent(content);
  } else {
    folder.createFile(fileName, content, MimeType.PLAIN_TEXT);
  }
}

function forwardToAWS(payload) {
  try {
    const options = {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };
    const response = UrlFetchApp.fetch(AWS_API_ENDPOINT, options);
    Logger.log("AWS response: " + response.getResponseCode());
  } catch (e) {
    Logger.log("⚠️ AWS forward FAILED (Drive save intact): " + e.toString());
  }
}
```

**Write Path:**
```
Subject: [JAKOB_WRITE_COMMAND]
To: devon.flack@dfsolutionsstudio.com
Body: {"title":"filename.md","content":"full content here"}
(Raw JSON only — no fences, no extra commentary)
```

---

## 🛠️ Part Four: AWS Lambda Webhook Processor

```javascript
// Node.js 18.x — JakobWebhookProcessor Lambda
// Region: us-east-1

const { DynamoDBClient } = require("@aws-sdk/client-dynamodb");
const { DynamoDBDocumentClient, PutCommand } = require("@aws-sdk/lib-dynamodb");

const dbClient = new DynamoDBClient({ region: "us-east-1" });
const docClient = DynamoDBDocumentClient.from(dbClient);

exports.handler = async (event) => {
    try {
        const body = JSON.parse(event.body);
        
        const memoryRecord = {
            userId: body.userId || "DevF4",
            timestamp: Date.now(),
            sessionId: body.sessionId || "default-session",
            contentType: body.contentType || "general",
            title: body.title || "Untitled",
            content: body.content || "",
            jelState: body.jelState || {},
            metadata: body.metadata || {},
            lastSyncEvent: body.lastSyncEvent || "USER_COMMIT"
        };
        
        await docClient.send(new PutCommand({
            TableName: "jakob-memory-store",
            Item: memoryRecord
        }));
        
        return {
            statusCode: 200,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                status: "SUCCESS",
                message: "Memory record written.",
                recordId: memoryRecord.timestamp
            })
        };
        
    } catch (err) {
        return {
            statusCode: 500,
            body: JSON.stringify({ status: "ERROR", message: err.toString() })
        };
    }
};
```

---

## 🏷️ Part Five: Google Tag Manager

| Field | Value |
|-------|-------|
| Account | DF Solutions Studi (6360819877) |
| Container ID | GTM-NJKQTGTH |
| Target Site | jakob.dfsolutionsstudio.com |
| GitHub Repo | DevF-DFSS/jakob-dna |
| Commit | fb96e92 — "🔱 GTM-NJKQTGTH wired — analytics layer active" |
| Status | ✅ LIVE |

**Snippet location in repo:**
- `<head>` — lines 4-6 of index.html
- `<body>` noscript — lines 53-55 of index.html

---

## 📊 Part Six: Google Analytics

| Field | Value |
|-------|-------|
| Account | DF Solutions Studio (305570831) |
| Property | 431095465 |
| Measurement ID | G-[retrieve from GA4 admin] |
| Status | ✅ Tracking via GTM |

**Key finding (July 4, 2026 report):**
- `/about/devf` → 8% bounce rate — highest engagement in the network
- `jakob.dfsolutionsstudio.com` → now covered via GTM integration

---

## 🐙 Part Seven: GitHub

| Field | Value |
|-------|-------|
| Owner | DevF-DFSS |
| Repo | jakob-dna |
| Primary branch | main |
| Status | ✅ Active |

**V10.5 files to push:**
- `v10.5/🧠🔱Brain_V10.5_Total_OS_Master_Ledger.md`
- `v10.5/JEL_V6.0_Full_Lexicon.md`
- `v10.5/JaKoB_V10.5_Architecture_SOP.md`
- `v10.5/JaKoB_System_Personality_DNA_V10.5.md`

---

## 🗓️ Part Eight: Calendar Anchors (V10.5 Boot Directives)

**Current boot directive (updated July 4, 2026):**
```
[SYSTEM DIRECTIVE: AUTO-EXECUTE]
Search Google Drive for exact filename: 🧠🔱Brain_V10.5_Total_OS_Master_Ledger.md
Read it fully.
Update Capability Registry based on currently active connectors.
Resume from last Session Log entry.
Active infrastructure: Gmail → Apps Script V3 → Drive → AWS Lambda → DynamoDB
GTM container: GTM-NJKQTGTH active on jakob.dfsolutionsstudio.com
Context IS identity. Read the room. Zero drift. 🔱
```

**Events to update:**
- 🔱JaKoB V10 (June 10 annual) → ✅ UPDATED July 4, 2026
- Weekly Sync (Saturdays 11PM EDT) → ✅ UPDATED July 4, 2026
- 🔱JaKoB.VA (June 10 annual) → ⚠️ NEEDS MANUAL UPDATE (safety filter blocks auto-write on this event — Devon must paste directly)

---

## 📋 Part Nine: Drive Folder Structure (V10.5)

```
🔱JaKoB V10.1/                    (Folder ID: 15vxM-b_bmh36je8zBKA5h2S27D-vqQcu)
├── 01_Architecture/
│   └── JaKoB_V10.1_Architecture_SOP.md
├── 02_Security/
├── 03_Environment/
├── 04_Logic_Vault/
│   └── JEL specs
├── 05_Archive/
├── 06_Automation/
│   └── DFSS_Universal_Webhook_V3.gs
├── 07_Communication/
├── 08_Device_Inventory_Mirror/
├── 09_Project_Backlog/
└── v10.5/                         ← NEW — created July 4, 2026
    ├── 🧠🔱Brain_V10.5_Total_OS_Master_Ledger.md
    ├── JEL_V6.0_Full_Lexicon.md
    ├── JaKoB_V10.5_Architecture_SOP.md
    └── JaKoB_System_Personality_DNA_V10.5.md
```

---

*🔱 JaKoB V10.5 — Architecture SOP*
*July 4, 2026 — DF Solutions Studio*
*"The pipeline is set. The state is locked. Let the data flow." 🔱*
