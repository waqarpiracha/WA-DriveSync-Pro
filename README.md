# WA-DriveSync-Pro (Enterprise Edition)
### Autonomous AI Sync Engine: WhatsApp (Groups & 1-to-1) to Google Drive & Google Sheets

[![Build Android APK](https://github.com/waqarpiracha/WA-DriveSync-Pro/actions/workflows/build-apk.yml/badge.svg)](https://github.com/waqarpiracha/WA-DriveSync-Pro/actions/workflows/build-apk.yml)
[![Developer: Waqar Aslam Piracha](https://img.shields.io/badge/Developer-Waqar%20Aslam%20Piracha-10B981?style=flat&logo=linkedin)](https://www.linkedin.com/in/Waqar-A-Piracha)
[![License: Commercial](https://img.shields.io/badge/License-Commercial-F59E0B.svg)](LICENSE)
[![Framework](https://img.shields.io/badge/Framework-Flet%200.25.2-blue.svg)](https://flet.dev)

---

## 🌟 Executive Overview
**WA-DriveSync-Pro** is a commercial-grade Android mobile application engineered for supply chain planners, procurement teams, finance controllers, and enterprise operations. It connects WhatsApp (both Group Chats and 1-to-1 direct chats) directly to Google Drive and Google Sheets using Google's **Gemini 2.5 Flash AI**, enabling 1-click structured data extraction and automated archiving.

### 💼 Developer Profile & Enterprise Inquiries
- **Lead Architect & Developer:** **Waqar Aslam Piracha**
- **Title:** Senior Business Intelligence Consultant & Automation Specialist
- **Contact:** [waqarpiracha@gmail.com](mailto:waqarpiracha@gmail.com) | **WhatsApp:** [+92 313 437 9963](https://wa.me/923134379963)
- **LinkedIn:** [linkedin.com/in/Waqar-A-Piracha](https://www.linkedin.com/in/Waqar-A-Piracha)
- **Consulting Portfolio:** [waqar-piracha-consultant.netlify.app](https://waqar-piracha-consultant.netlify.app)
- **YouTube:** [@waqarpiracha](https://youtube.com/@waqarpiracha)

---

## 🚀 Core Features & Capabilities

### 1. 💬 Chat & Group Sync (1-Click to Google Sheets)
- **Multi-Format WhatsApp Parser:** Ingests exported `.txt` or `.zip` files, pasted text blocks, or live API streams.
- **Smart Filtering:** Seamlessly switch between **All Chats**, **Groups Only**, and **1-to-1 Chats**.
- **Automated Field Extraction:** Parses `Timestamp`, `Date`, `Time`, `Sender`, `Message Content`, and assigns an **AI Action Tag** (e.g., *Purchase Order*, *Logistics & Dispatch*, *Payment/Finance*, *Urgent Alert*, *SAP/ERP Workflow*).
- **1-Click Google Sheets Upload:** Posts structured rows directly into the `"WhatsApp_Messages"` sheet tab.

### 2. 📄 1-Click PDF-to-Sheet & Google Drive Extractor
- **Multimodal AI Analysis:** Transmits PDF files directly to the **Gemini 2.5 Flash REST API** (`inline_data` Base64) to extract structured line items, invoice numbers, tax breakdowns, and operational metrics without heavy binary libraries.
- **Cloud Document Archival:** Uploads the physical `.pdf` file to a dedicated `"WhatsApp_Synced_Files"` Google Drive folder and returns a direct clickable link.
- **Automated Spreadsheet Population:** Appends every extracted line item and table row into `"PDF_Extracted_Data"` with the hyperlinked Drive file.

### 3. 🔌 WhatsApp Live Auto-Connect
- Connects to any standard WhatsApp Web Gateway (Green-API, Ultramsg, or custom webhooks) using an Instance ID and Secret Token.
- Pulls incoming messages, delivery confirmations, and client purchase orders directly into the app buffer.
- Features an offline interactive test stream for buyer demos without requiring live credentials.

### 4. 📘 Buyer Setup Guide & Interactive Help Center
- **Guide 1:** Get your free Gemini 2.5 Flash API Key in 30 seconds via Google AI Studio.
- **Guide 2:** 2-Minute Google Drive & Sheets Bridge Setup with an interactive **"📋 Copy Google Apps Script Code"** button that puts the entire companion script onto the device clipboard.
- **Guide 3:** End-to-end tutorial covering WhatsApp chat exports, direct PDF parsing, and gateway pairing.
- **Persistent Local Settings:** Securely saves API keys and endpoint URLs to Android device storage (`client_storage`).

---

## 🏗️ Architecture & Technology Stack
- **Frontend & Mobile UI:** Python + [Flet 0.25.2](https://flet.dev)
- **Zero Binary Dependency Rule:** Uses only Python's standard library (`urllib.request`, `urllib.parse`, `json`, `base64`, `re`, `datetime`, `zipfile`) for 100% reliable Android compilation across architectures.
- **AI Engine:** Google Gemini 2.5 Flash Multimodal REST API (`v1beta`).
- **Cloud Backend:** Google Apps Script (`google_sheets_drive_bridge.gs`) deployed as a serverless Web App.
- **CI/CD Pipeline:** GitHub Actions compiling release APK with Flutter 3.24.5 & Java 17.

---

## 📲 Quick Setup for Google Drive & Sheets Companion Bridge
1. Open [Google Sheets](https://sheets.new) and create a new spreadsheet.
2. Navigate to **Extensions** > **Apps Script**.
3. Replace all existing text with the contents of [`google_sheets_drive_bridge.gs`](./google_sheets_drive_bridge.gs) (or use the **"Copy Code"** button inside the app's Help tab).
4. Click **Deploy** > **New deployment** > Select **Web app**.
   - **Execute as:** `Me (your Google account)`
   - **Who has access:** `Anyone`
5. Copy the generated Web App URL and paste it into **WA-DriveSync-Pro** under **Settings & Help** > **Google Apps Script Web App URL**.

---

## 🔒 Security & Privacy
- Zero intermediate cloud servers: all data travels directly from the user's mobile device to their own Google Drive and Google Sheets instance.
- API keys and tokens are stored exclusively on the user's local device storage.
