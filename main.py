"""
WA-DriveSync-Pro: Commercial Turnkey Mobile Sync Engine
=========================================================
Brand: WA DriveSync AI Pro
Architect & Developer: Waqar Aslam Piracha | Enterprise Automation & AI Solutions
Contact: waqarpiracha@gmail.com | WhatsApp: +92 313 437 9963
LinkedIn: https://www.linkedin.com/in/Waqar-A-Piracha
Website: https://waqar-piracha-consultant.netlify.app

Rules Enforced:
- flet==0.25.2 only
- Zero binary or C/Rust dependencies (pure Python standard library: urllib.request, json, base64, datetime, math, os, re, zipfile)
- Native Gemini 2.5 Flash REST API with Base64 inline_data
- Turnkey zero-friction experience for commercial end-users
"""

import base64
from datetime import datetime
import json
import math
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

import flet as ft

# ==============================================================================
# SAMPLE TEST DATA FOR ZERO-SETUP COMMERCIAL DEMO
# ==============================================================================
SAMPLE_WHATSAPP_CHAT = """14/10/2026, 09:15 AM - Messages and calls are end-to-end encrypted. No one outside of this chat can read or listen to them.
14/10/2026, 09:16 AM - Muhammad Ali (Logistics): 3 trucks dispatched from Rahim Yar Khan plant towards Lahore Central DC.
14/10/2026, 09:22 AM - Tariq Mehmood (Purchasing): PO-99482 confirmed by supplier. 45 pallets raw packaging material arriving tomorrow at 11 AM.
14/10/2026, 09:35 AM - Waqar Piracha: Excellent. Ensure goods receipt entry (MIGO) is scheduled in SAP immediately upon arrival.
14/10/2026, 10:04 AM - Sarah Khan (Finance): Outstanding RTGS payment of PKR 4,250,000 cleared for Metro C&C invoice #INV-8821.
14/10/2026, 10:45 AM - Usman Sheikh (Distribution): Stock coverage alert: Shampoo 200ml at Islamabad DC is below 5 days of safety stock.
14/10/2026, 11:10 AM - Waqar Piracha: DRP model run completed. Dispatched 1,200 cartons from Fecto Hub to balance Islamabad coverage to 14 days.
14/10/2026, 11:30 AM - Bilal Ahmed (Transport): Vehicle LEA-4921 reached Lahore Gate 2. Inspection in progress.
"""

SAMPLE_INVOICE_ROWS = [
    {"field": "Laminate Film Roll 400mm", "value": "PKR 540,000", "details": "60 Rolls @ PKR 9,000/roll - Batch #L-882"},
    {"field": "Outer Corrugated Cartons", "value": "PKR 325,000", "details": "5,000 Units @ PKR 65/unit - 5-Ply Heavy Duty"},
    {"field": "Freight & Palletization Fee", "value": "PKR 120,000", "details": "Dedicated 40ft Container RYK to Lahore"},
    {"field": "Sales Tax (GST 18%)", "value": "PKR 226,800", "details": "FBR Registered Withholding Tax applied"},
    {"field": "Total Invoice Payable", "value": "PKR 1,485,000", "details": "Net 30 Days Terms - Bank Alfalah Ref #INV-9941"},
]


def main(page: ft.Page):
    page.title = "WA DriveSync AI Pro | Developed by Waqar Aslam Piracha"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    page.bgcolor = "#0B111A"

    # Color Palette: Commercial Dark Emerald & Gold
    C_EMERALD = "#10B981"
    C_EMERALD_DARK = "#064E3B"
    C_GOLD = "#F59E0B"
    C_GOLD_LIGHT = "#FDE68A"
    C_SURFACE = "#152232"
    C_SURFACE_LIGHT = "#1E2D42"
    C_TEXT_MUTED = "#94A3B8"
    C_ACCENT_BLUE = "#38BDF8"

    # --------------------------------------------------------------------------
    # In-Memory State & Storage
    # --------------------------------------------------------------------------
    parsed_messages = []
    active_chat_filter = "ALL"  # ALL, GROUP, DIRECT
    current_pdf_bytes = None
    current_pdf_name = ""
    extracted_pdf_data = []

    # Sync Dashboard Metrics
    sync_history = [
        {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "type": "System Init", "detail": "Engine ready for turnkey operations", "status": "Ready"}
    ]
    metrics = {
        "messages_synced": 0,
        "pdfs_synced": 0,
        "last_sync": "Not yet synchronized"
    }

    # Stored Credentials
    stored_gemini_key = page.client_storage.get("gemini_api_key") or ""
    stored_cloud_url = page.client_storage.get("cloud_bridge_url") or ""
    stored_oauth_token = page.client_storage.get("cloud_oauth_token") or ""

    # --------------------------------------------------------------------------
    # Notification Helper
    # --------------------------------------------------------------------------
    def notify(message: str, is_error: bool = False, is_gold: bool = False):
        bg = "#DC2626" if is_error else (C_GOLD if is_gold else C_EMERALD)
        sb = ft.SnackBar(
            content=ft.Text(message, color=ft.colors.WHITE, weight=ft.FontWeight.W_500),
            bgcolor=bg,
            duration=3500,
        )
        try:
            page.open(sb)
        except Exception:
            page.snack_bar = sb
            page.snack_bar.open = True
            page.update()

    # --------------------------------------------------------------------------
    # WhatsApp Parsing Algorithm
    # --------------------------------------------------------------------------
    def parse_chat_content(raw_text: str, default_chat: str = "WhatsApp Chat"):
        results = []
        if not raw_text:
            return results

        p1 = re.compile(r"^\[?(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\]?\s*[-:]\s*([^:]+):\s*(.*)$")
        lines = raw_text.splitlines()
        current_msg = None
        senders_seen = set()

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            if "Messages and calls are end-to-end encrypted" in line_str:
                continue
            if "created group" in line_str or "added you" in line_str:
                continue

            match = p1.match(line_str)
            if match:
                if current_msg:
                    results.append(current_msg)

                d_str = match.group(1).strip()
                t_str = match.group(2).strip()
                s_str = match.group(3).strip()
                m_str = match.group(4).strip()
                senders_seen.add(s_str)

                # Sentiment & Action Item Analysis
                m_lower = m_str.lower()
                action_tag = "General Info"
                if any(k in m_lower for k in ["po-", "po ", "order", "invoice", "carton", "pallet", "rfq"]):
                    action_tag = "📦 Order / Procurement"
                elif any(k in m_lower for k in ["urgent", "alert", "shortage", "delayed", "asap", "critical"]):
                    action_tag = "🚨 Urgent Action Required"
                elif any(k in m_lower for k in ["truck", "dispatched", "transit", "gate", "arrival", "shipment"]):
                    action_tag = "🚚 Logistics In-Transit"
                elif any(k in m_lower for k in ["payment", "rtgs", "cleared", "paid", "bank", "pkr", "transfer"]):
                    action_tag = "💰 Financial Clearance"
                elif any(k in m_lower for k in ["migo", "sap", "miro", "drp", "kinaxis", "system"]):
                    action_tag = "⚙️ SAP / ERP Update"

                current_msg = {
                    "date": d_str,
                    "time": t_str,
                    "sender": s_str,
                    "message": m_str,
                    "chat_name": default_chat,
                    "chat_type": "Group",
                    "action_tag": action_tag
                }
            else:
                if current_msg:
                    current_msg["message"] += " " + line_str

        if current_msg:
            results.append(current_msg)

        is_group = len(senders_seen) > 2
        for r in results:
            r["chat_type"] = "Group" if is_group else "1-to-1"

        return results

    # ==============================================================================
    # TAB 1: 💬 WHATSAPP GROUP & 1-TO-1 CHAT PARSER
    # ==============================================================================
    chat_text_box = ft.TextField(
        multiline=True,
        min_lines=2,
        max_lines=5,
        hint_text="Paste WhatsApp chat export here or pick a .txt/.zip export file...",
        bgcolor=C_SURFACE,
        border_color=C_SURFACE_LIGHT,
        focused_border_color=C_EMERALD,
        text_size=12,
        color=ft.colors.WHITE,
    )

    chat_stats_text = ft.Text("No messages parsed yet", size=12, color=C_TEXT_MUTED)
    chat_table_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    chat_progress = ft.ProgressBar(visible=False, color=C_EMERALD, bgcolor=C_SURFACE_LIGHT)

    def render_chat_table():
        filtered = []
        for m in parsed_messages:
            if active_chat_filter == "ALL":
                filtered.append(m)
            elif active_chat_filter == "GROUP" and m["chat_type"] == "Group":
                filtered.append(m)
            elif active_chat_filter == "DIRECT" and m["chat_type"] == "1-to-1":
                filtered.append(m)

        grp_count = sum(1 for x in parsed_messages if x["chat_type"] == "Group")
        dir_count = sum(1 for x in parsed_messages if x["chat_type"] == "1-to-1")
        chat_stats_text.value = f"Total: {len(parsed_messages)} | Groups: {grp_count} | 1-to-1: {dir_count} | Visible: {len(filtered)}"

        if not filtered:
            chat_table_container.controls = [
                ft.Container(
                    padding=20,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Icon(ft.icons.CHAT_BUBBLE_OUTLINE, size=40, color=C_TEXT_MUTED),
                            ft.Text("No messages loaded. Click 'Load Sample Chat' or 'Pick .txt/.zip'", color=C_TEXT_MUTED, size=13),
                        ]
                    )
                )
            ]
            page.update()
            return

        rows = []
        for m in filtered:
            is_g = m["chat_type"] == "Group"
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(f"{m['date']} {m['time']}", size=11, color=C_TEXT_MUTED)),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text("GROUP" if is_g else "1-to-1", size=9, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                bgcolor=C_EMERALD_DARK if is_g else "#1E3A8A",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4,
                            )
                        ),
                        ft.DataCell(ft.Text(m["sender"], size=12, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)),
                        ft.DataCell(ft.Text(m["message"], size=12, color="#E2E8F0")),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(m["action_tag"], size=10, color=C_GOLD_LIGHT),
                                bgcolor="#451A03",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4,
                            )
                        ),
                    ]
                )
            )

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Timestamp", size=12, weight=ft.FontWeight.BOLD, color=C_GOLD_LIGHT)),
                ft.DataColumn(ft.Text("Type", size=12, weight=ft.FontWeight.BOLD, color=C_GOLD_LIGHT)),
                ft.DataColumn(ft.Text("Sender", size=12, weight=ft.FontWeight.BOLD, color=C_GOLD_LIGHT)),
                ft.DataColumn(ft.Text("Message Content", size=12, weight=ft.FontWeight.BOLD, color=C_GOLD_LIGHT)),
                ft.DataColumn(ft.Text("Sentiment / Action Item", size=12, weight=ft.FontWeight.BOLD, color=C_GOLD_LIGHT)),
            ],
            rows=rows,
            border=ft.border.all(1, C_SURFACE_LIGHT),
            border_radius=8,
            heading_row_color=C_SURFACE,
        )

        chat_table_container.controls = [
            ft.Row(scroll=ft.ScrollMode.AUTO, controls=[data_table])
        ]
        page.update()

    def filter_chat_changed(e):
        nonlocal active_chat_filter
        idx = e.control.selected_index
        active_chat_filter = "ALL" if idx == 0 else ("GROUP" if idx == 1 else "DIRECT")
        render_chat_table()

    def load_demo_chat(e):
        nonlocal parsed_messages
        parsed_messages = parse_chat_content(SAMPLE_WHATSAPP_CHAT, "National Logistics Group")
        chat_text_box.value = SAMPLE_WHATSAPP_CHAT
        notify(f"✓ Loaded {len(parsed_messages)} sample WhatsApp group & 1-to-1 messages!", is_gold=True)
        render_chat_table()

    def parse_manual_chat(e):
        nonlocal parsed_messages
        text = chat_text_box.value or ""
        if not text.strip():
            notify("Please paste WhatsApp messages first!", is_error=True)
            return
        parsed_messages = parse_chat_content(text, "Manual Chat Import")
        notify(f"✓ Parsed {len(parsed_messages)} messages successfully!")
        render_chat_table()

    def export_chat_to_excel_and_sheets(e):
        if not parsed_messages:
            notify("No messages to export! Please load or paste messages first.", is_error=True)
            return

        chat_progress.visible = True
        page.update()

        def do_export():
            try:
                # 1. Export locally as Excel-compatible CSV (with UTF-8 BOM)
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_filename = f"WhatsApp_Sync_{timestamp_str}.csv"
                save_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                if not os.path.exists(save_dir):
                    save_dir = os.path.abspath(".")
                file_path = os.path.join(save_dir, csv_filename)

                with open(file_path, "w", encoding="utf-8-sig") as f:
                    f.write("Date,Time,Chat Type,Sender,Message,Sentiment / Action Item\n")
                    for m in parsed_messages:
                        msg_clean = m["message"].replace('"', '""').replace("\n", " ")
                        f.write(f'"{m["date"]}","{m["time"]}","{m["chat_type"]}","{m["sender"]}","{msg_clean}","{m["action_tag"]}"\n')

                # 2. Push to Google Sheets if connected
                cloud_url = page.client_storage.get("cloud_bridge_url") or stored_cloud_url
                sheet_synced = False
                if cloud_url and cloud_url.startswith("http"):
                    try:
                        payload = {"action": "save_messages", "messages": parsed_messages}
                        req = urllib.request.Request(
                            cloud_url,
                            data=json.dumps(payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"}
                        )
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            res_json = json.loads(resp.read().decode("utf-8"))
                            if res_json.get("success"):
                                sheet_synced = True
                    except Exception:
                        pass

                # Update sync metrics
                metrics["messages_synced"] += len(parsed_messages)
                metrics["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                sync_history.insert(0, {
                    "timestamp": metrics["last_sync"],
                    "type": "Chat Sync",
                    "detail": f"{len(parsed_messages)} messages saved to {csv_filename}" + (" & Google Sheets" if sheet_synced else ""),
                    "status": "Success"
                })

                msg = f"✓ Saved Excel/CSV to {csv_filename}!" + (" Also synced to Google Sheets." if sheet_synced else "")
                notify(msg, is_gold=True)

            except Exception as ex:
                notify(f"Export error: {str(ex)}", is_error=True)
            finally:
                chat_progress.visible = False
                page.update()

        threading.Thread(target=do_export, daemon=True).start()

    def on_chat_file_picked(e: ft.FilePickerResultEvent):
        nonlocal parsed_messages
        if not e.files:
            return
        picked = e.files[0]
        try:
            raw_text = ""
            if picked.name.endswith(".zip"):
                with zipfile.ZipFile(picked.path, "r") as zf:
                    txts = [f for f in zf.namelist() if f.endswith(".txt")]
                    if txts:
                        with zf.open(txts[0]) as zf_txt:
                            raw_text = zf_txt.read().decode("utf-8", errors="ignore")
            else:
                with open(picked.path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()

            parsed_messages = parse_chat_content(raw_text, picked.name.replace(".txt", "").replace(".zip", ""))
            chat_text_box.value = raw_text[:300] + ("\n... [truncated]" if len(raw_text) > 300 else "")
            notify(f"✓ Parsed {len(parsed_messages)} messages from {picked.name}!", is_gold=True)
            render_chat_table()
        except Exception as ex:
            notify(f"Error opening file: {str(ex)}", is_error=True)

    chat_file_picker = ft.FilePicker(on_result=on_chat_file_picked)
    page.overlay.append(chat_file_picker)

    tab_chat = ft.Container(
        expand=True,
        padding=12,
        content=ft.Column(
            expand=True,
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("💬 WhatsApp Chat & Group AI Parser", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                        ft.Chip(label=ft.Text("Turnkey AI", size=10, color=C_GOLD_LIGHT), bgcolor="#451A03"),
                    ]
                ),
                chat_text_box,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "📂 Pick .txt / .zip",
                            icon=ft.icons.ATTACH_FILE,
                            on_click=lambda _: chat_file_picker.pick_files(allow_multiple=False, allowed_extensions=["txt", "zip"]),
                            style=ft.ButtonStyle(bgcolor=C_SURFACE_LIGHT, color=ft.colors.WHITE),
                        ),
                        ft.ElevatedButton(
                            "✨ Parse Text",
                            icon=ft.icons.CHECK,
                            on_click=parse_manual_chat,
                            style=ft.ButtonStyle(bgcolor=C_SURFACE_LIGHT, color=ft.colors.WHITE),
                        ),
                        ft.ElevatedButton(
                            "🧪 Load Sample Chat",
                            icon=ft.icons.PLAY_CIRCLE,
                            on_click=load_demo_chat,
                            style=ft.ButtonStyle(bgcolor="#1E3A8A", color=ft.colors.WHITE),
                        ),
                    ]
                ),
                ft.Divider(color=C_SURFACE_LIGHT, height=1),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                    controls=[
                        ft.CupertinoSegmentedButton(
                            selected_index=0,
                            on_change=filter_chat_changed,
                            controls=[
                                ft.Text("All Chats", size=11),
                                ft.Text("Groups Only", size=11),
                                ft.Text("1-to-1 Only", size=11),
                            ]
                        ),
                        ft.ElevatedButton(
                            "💾 Export to Excel & Sheets",
                            icon=ft.icons.DOWNLOAD,
                            on_click=export_chat_to_excel_and_sheets,
                            style=ft.ButtonStyle(bgcolor=C_EMERALD, color=ft.colors.WHITE),
                        ),
                    ]
                ),
                chat_stats_text,
                chat_progress,
                ft.Container(
                    expand=True,
                    content=chat_table_container,
                    border=ft.border.all(1, C_SURFACE_LIGHT),
                    border_radius=8,
                    bgcolor="#0D1520",
                    padding=6,
                )
            ]
        )
    )

    # ==============================================================================
    # TAB 2: 📄 1-CLICK PDF-TO-EXCEL EXTRACTOR
    # ==============================================================================
    pdf_info_text = ft.Text("Select any PDF invoice or statement to extract tables", size=12, color=C_TEXT_MUTED)
    pdf_table_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    pdf_progress = ft.ProgressBar(visible=False, color=C_GOLD, bgcolor=C_SURFACE_LIGHT)

    def render_pdf_table():
        if not extracted_pdf_data:
            pdf_table_container.controls = [
                ft.Container(
                    padding=20,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Icon(ft.icons.PICTURE_AS_PDF, size=40, color=C_TEXT_MUTED),
                            ft.Text("No PDF parsed yet. Pick a PDF or click 'Load Demo Invoice'", color=C_TEXT_MUTED, size=13),
                        ]
                    )
                )
            ]
            page.update()
            return

        rows = []
        for item in extracted_pdf_data:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item.get("field", ""), size=12, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE)),
                        ft.DataCell(ft.Text(item.get("value", ""), size=12, color=C_GOLD_LIGHT, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(item.get("details", ""), size=11, color=C_TEXT_MUTED)),
                    ]
                )
            )

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Extracted Field / Line Item", size=12, weight=ft.FontWeight.BOLD, color=C_GOLD_LIGHT)),
                ft.DataColumn(ft.Text("Value / Amount", size=12, weight=ft.FontWeight.BOLD, color=C_GOLD_LIGHT)),
                ft.DataColumn(ft.Text("Details / Description", size=12, weight=ft.FontWeight.BOLD, color=C_GOLD_LIGHT)),
            ],
            rows=rows,
            border=ft.border.all(1, C_SURFACE_LIGHT),
            border_radius=8,
            heading_row_color=C_SURFACE,
        )

        pdf_table_container.controls = [
            ft.Row(scroll=ft.ScrollMode.AUTO, controls=[data_table])
        ]
        page.update()

    def on_pdf_picked(e: ft.FilePickerResultEvent):
        nonlocal current_pdf_bytes, current_pdf_name
        if not e.files:
            return
        picked = e.files[0]
        current_pdf_name = picked.name
        try:
            with open(picked.path, "rb") as pf:
                current_pdf_bytes = pf.read()
            kb = round(len(current_pdf_bytes) / 1024, 1)
            pdf_info_text.value = f"Selected: {current_pdf_name} ({kb} KB) - Ready for AI extraction"
            pdf_info_text.color = ft.colors.WHITE
            notify(f"✓ PDF loaded: {current_pdf_name}", is_gold=True)
            page.update()
        except Exception as ex:
            notify(f"Error loading PDF: {str(ex)}", is_error=True)

    pdf_file_picker = ft.FilePicker(on_result=on_pdf_picked)
    page.overlay.append(pdf_file_picker)

    def load_demo_invoice(e):
        nonlocal current_pdf_bytes, current_pdf_name
        current_pdf_name = "Commercial_Tax_Invoice_9941.pdf"
        current_pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000098 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n180\n%%EOF"
        pdf_info_text.value = f"Selected: {current_pdf_name} (Commercial Demo Asset)"
        pdf_info_text.color = ft.colors.WHITE
        notify("✓ Demo invoice loaded! Click 'Extract with Gemini AI'.", is_gold=True)
        page.update()

    def run_pdf_ai_extraction(e):
        nonlocal extracted_pdf_data
        if not current_pdf_bytes:
            notify("Please pick a PDF or click 'Load Demo Invoice' first!", is_error=True)
            return

        pdf_progress.visible = True
        page.update()

        def do_extract():
            nonlocal extracted_pdf_data
            try:
                gemini_key = page.client_storage.get("gemini_api_key") or stored_gemini_key
                b64_pdf = base64.b64encode(current_pdf_bytes).decode("utf-8")

                if gemini_key and len(gemini_key.strip()) > 10:
                    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key.strip()}"
                    prompt = (
                        "Extract all structured line items, invoice/order details, tables, key-value pairs, "
                        "and financial/operational numbers from this document. "
                        "Return ONLY valid JSON matching this schema: "
                        '{"items": [{"field": "...", "value": "...", "details": "..."}]}'
                    )
                    payload = {
                        "contents": [
                            {
                                "parts": [
                                    {"inline_data": {"mime_type": "application/pdf", "data": b64_pdf}},
                                    {"text": prompt}
                                ]
                            }
                        ],
                        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1}
                    }
                    req = urllib.request.Request(
                        api_url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=45) as resp:
                        g_json = json.loads(resp.read().decode("utf-8"))
                        text_resp = g_json["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(text_resp)
                        extracted_pdf_data = parsed.get("items", [])
                else:
                    time.sleep(1.0)
                    extracted_pdf_data = SAMPLE_INVOICE_ROWS

                notify(f"✓ Extracted {len(extracted_pdf_data)} structured line items!", is_gold=True)
                render_pdf_table()

            except Exception as ex:
                notify(f"AI Extraction error: {str(ex)}", is_error=True)
            finally:
                pdf_progress.visible = False
                page.update()

        threading.Thread(target=do_extract, daemon=True).start()

    def save_pdf_to_excel_and_drive(e):
        if not extracted_pdf_data:
            notify("Please extract PDF data before saving!", is_error=True)
            return

        pdf_progress.visible = True
        page.update()

        def do_save():
            try:
                # 1. Save locally as Excel CSV
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                clean_name = current_pdf_name.replace(".pdf", "") if current_pdf_name else "Extracted_PDF"
                out_name = f"{clean_name}_{ts}.csv"
                save_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                if not os.path.exists(save_dir):
                    save_dir = os.path.abspath(".")
                out_path = os.path.join(save_dir, out_name)

                with open(out_path, "w", encoding="utf-8-sig") as f:
                    f.write("Line Item / Field,Value / Amount,Details\n")
                    for it in extracted_pdf_data:
                        f_name = it.get("field", "").replace('"', '""')
                        val = it.get("value", "").replace('"', '""')
                        det = it.get("details", "").replace('"', '""')
                        f.write(f'"{f_name}","{val}","{det}"\n')

                # 2. Push to Google Drive / Sheets if connected
                cloud_url = page.client_storage.get("cloud_bridge_url") or stored_cloud_url
                drive_synced = False
                if cloud_url and cloud_url.startswith("http"):
                    try:
                        b64 = base64.b64encode(current_pdf_bytes).decode("utf-8") if current_pdf_bytes else ""
                        payload = {
                            "action": "upload_pdf_and_extract",
                            "fileName": current_pdf_name,
                            "base64Pdf": b64,
                            "extractedData": extracted_pdf_data
                        }
                        req = urllib.request.Request(
                            cloud_url,
                            data=json.dumps(payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"}
                        )
                        with urllib.request.urlopen(req, timeout=30) as resp:
                            res_json = json.loads(resp.read().decode("utf-8"))
                            if res_json.get("success"):
                                drive_synced = True
                    except Exception:
                        pass

                # Update metrics
                metrics["pdfs_synced"] += 1
                metrics["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                sync_history.insert(0, {
                    "timestamp": metrics["last_sync"],
                    "type": "PDF Extract",
                    "detail": f"{len(extracted_pdf_data)} rows saved to {out_name}" + (" & Google Drive" if drive_synced else ""),
                    "status": "Success"
                })

                msg = f"✓ Saved Excel/CSV to {out_name}!" + (" Synced to Google Drive." if drive_synced else "")
                notify(msg, is_gold=True)

            except Exception as ex:
                notify(f"Save error: {str(ex)}", is_error=True)
            finally:
                pdf_progress.visible = False
                page.update()

        threading.Thread(target=do_save, daemon=True).start()

    tab_pdf = ft.Container(
        expand=True,
        padding=12,
        content=ft.Column(
            expand=True,
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("📄 1-Click PDF-to-Excel Extractor", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                        ft.Chip(label=ft.Text("Gemini 2.5 Flash", size=10, color=C_GOLD_LIGHT), bgcolor="#451A03"),
                    ]
                ),
                pdf_info_text,
                ft.Row(
                    wrap=True,
                    spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "📄 Pick PDF Document",
                            icon=ft.icons.PICTURE_AS_PDF,
                            on_click=lambda _: pdf_file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"]),
                            style=ft.ButtonStyle(bgcolor=C_SURFACE_LIGHT, color=ft.colors.WHITE),
                        ),
                        ft.ElevatedButton(
                            "🧪 Load Demo Invoice",
                            icon=ft.icons.RECEIPT,
                            on_click=load_demo_invoice,
                            style=ft.ButtonStyle(bgcolor="#1E3A8A", color=ft.colors.WHITE),
                        ),
                        ft.ElevatedButton(
                            "⚡ Extract with Gemini AI",
                            icon=ft.icons.BOLT,
                            on_click=run_pdf_ai_extraction,
                            style=ft.ButtonStyle(bgcolor=C_GOLD, color="#0F172A"),
                        ),
                    ]
                ),
                ft.Divider(color=C_SURFACE_LIGHT, height=1),
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.ElevatedButton(
                            "💾 Save as Excel (.xlsx/.csv) & Sync to Drive",
                            icon=ft.icons.CLOUD_UPLOAD,
                            on_click=save_pdf_to_excel_and_drive,
                            style=ft.ButtonStyle(bgcolor=C_EMERALD, color=ft.colors.WHITE),
                        ),
                    ]
                ),
                pdf_progress,
                ft.Container(
                    expand=True,
                    content=pdf_table_container,
                    border=ft.border.all(1, C_SURFACE_LIGHT),
                    border_radius=8,
                    bgcolor="#0D1520",
                    padding=6,
                )
            ]
        )
    )

    # ==============================================================================
    # TAB 3: ☁️ CLOUD SYNC DASHBOARD
    # ==============================================================================
    stat_msg_text = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=C_EMERALD)
    stat_pdf_text = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=C_GOLD)
    stat_last_sync_text = ft.Text("Never", size=13, color="#E2E8F0")

    history_list_view = ft.ListView(expand=True, spacing=6, padding=4)

    def refresh_dashboard_ui():
        stat_msg_text.value = str(metrics["messages_synced"])
        stat_pdf_text.value = str(metrics["pdfs_synced"])
        stat_last_sync_text.value = metrics["last_sync"]

        history_list_view.controls.clear()
        for h in sync_history:
            card = ft.Container(
                bgcolor=C_SURFACE,
                padding=10,
                border_radius=8,
                border=ft.border.all(1, C_SURFACE_LIGHT),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Icon(ft.icons.CHECK_CIRCLE, color=C_EMERALD, size=20),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text(f"{h['type']}: {h['detail']}", size=12, color=ft.colors.WHITE, weight=ft.FontWeight.W_500),
                                        ft.Text(h["timestamp"], size=10, color=C_TEXT_MUTED),
                                    ]
                                )
                            ]
                        ),
                        ft.Chip(label=ft.Text(h["status"], size=10, color=ft.colors.WHITE), bgcolor=C_EMERALD_DARK),
                    ]
                )
            )
            history_list_view.controls.append(card)
        page.update()

    tab_dashboard = ft.Container(
        expand=True,
        padding=16,
        content=ft.Column(
            expand=True,
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("☁️ Cloud Sync & Audit Dashboard", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                        ft.IconButton(ft.icons.REFRESH, icon_color=C_GOLD, on_click=lambda _: refresh_dashboard_ui()),
                    ]
                ),
                # Metrics Cards Row
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Container(
                            expand=True,
                            bgcolor=C_SURFACE,
                            padding=12,
                            border_radius=8,
                            border=ft.border.all(1, C_SURFACE_LIGHT),
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Messages Synced", size=11, color=C_TEXT_MUTED),
                                    stat_msg_text,
                                ]
                            )
                        ),
                        ft.Container(
                            expand=True,
                            bgcolor=C_SURFACE,
                            padding=12,
                            border_radius=8,
                            border=ft.border.all(1, C_SURFACE_LIGHT),
                            content=ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("PDFs Extracted", size=11, color=C_TEXT_MUTED),
                                    stat_pdf_text,
                                ]
                            )
                        ),
                    ]
                ),
                ft.Container(
                    bgcolor=C_SURFACE,
                    padding=12,
                    border_radius=8,
                    border=ft.border.all(1, C_SURFACE_LIGHT),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Last Synchronized:", size=12, color=C_TEXT_MUTED),
                            stat_last_sync_text,
                        ]
                    )
                ),
                ft.Text("Recent Sync Audit Log:", size=13, weight=ft.FontWeight.BOLD, color=C_TEXT_MUTED),
                ft.Container(
                    expand=True,
                    content=history_list_view,
                    border=ft.border.all(1, C_SURFACE_LIGHT),
                    border_radius=8,
                    bgcolor="#0D1520",
                    padding=6,
                )
            ]
        )
    )

    # ==============================================================================
    # TAB 4: 🛠️ IN-APP SETUP WIZARD & HELP CENTER (Zero Technical Friction)
    # ==============================================================================
    in_gemini_key = ft.TextField(
        value=stored_gemini_key,
        label="Gemini AI API Key (Optional)",
        hint_text="Paste your Google AI Studio key here (or leave blank for demo mode)",
        password=True,
        can_reveal_password=True,
        bgcolor=C_SURFACE,
        border_color=C_SURFACE_LIGHT,
        focused_border_color=C_GOLD,
        text_size=12,
    )

    in_cloud_url = ft.TextField(
        value=stored_cloud_url,
        label="Google Drive & Sheets Bridge URL / Webhook",
        hint_text="https://script.google.com/macros/s/.../exec (or custom webhook)",
        bgcolor=C_SURFACE,
        border_color=C_SURFACE_LIGHT,
        focused_border_color=C_GOLD,
        text_size=12,
    )

    in_oauth_token = ft.TextField(
        value=stored_oauth_token,
        label="Google OAuth / Sync Token (Optional)",
        hint_text="Bearer token or custom auth header",
        password=True,
        can_reveal_password=True,
        bgcolor=C_SURFACE,
        border_color=C_SURFACE_LIGHT,
        focused_border_color=C_GOLD,
        text_size=12,
    )

    def save_wizard_settings(e):
        page.client_storage.set("gemini_api_key", in_gemini_key.value.strip())
        page.client_storage.set("cloud_bridge_url", in_cloud_url.value.strip())
        page.client_storage.set("cloud_oauth_token", in_oauth_token.value.strip())
        notify("✓ Turnkey Settings Saved! You are ready to sync.", is_gold=True)

    def test_connection_ping(e):
        url = in_cloud_url.value.strip()
        if not url or not url.startswith("http"):
            notify("Offline Demo Mode is active. Add a Bridge URL to test live cloud.", is_gold=True)
            return

        def run_test():
            notify("Testing cloud connection...")
            try:
                payload = {"action": "test_connection"}
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("success"):
                        notify(f"✓ Cloud Connected! Sheet: {data.get('spreadsheetTitle', 'Master Database')}", is_gold=True)
                    else:
                        notify(f"Cloud Note: {data.get('error')}", is_error=True)
            except Exception as ex:
                notify(f"Connection test: {str(ex)}", is_error=True)

        threading.Thread(target=run_test, daemon=True).start()

    tab_wizard = ft.Container(
        expand=True,
        padding=16,
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=12,
            controls=[
                # Turnkey Brand Header
                ft.Container(
                    bgcolor=C_SURFACE,
                    padding=14,
                    border_radius=10,
                    border=ft.border.all(1, C_GOLD),
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text("WA DriveSync AI Pro", size=16, weight=ft.FontWeight.BOLD, color=C_GOLD_LIGHT),
                                    ft.Chip(label=ft.Text("Turnkey Edition", size=10, color=ft.colors.WHITE), bgcolor="#78350F"),
                                ]
                            ),
                            ft.Text("Engineered by Waqar Aslam Piracha | Enterprise Automation Specialist", size=12, color=ft.colors.WHITE),
                            ft.Text("Automate WhatsApp operational workflows, invoice extraction, and spreadsheet updates with zero manual effort.", size=11, color=C_TEXT_MUTED),
                            ft.Divider(color=C_SURFACE_LIGHT, height=1),
                            ft.Row(
                                wrap=True,
                                spacing=8,
                                controls=[
                                    ft.ElevatedButton("WhatsApp Support", icon=ft.icons.CHAT, url="https://wa.me/923134379963", style=ft.ButtonStyle(bgcolor=C_EMERALD_DARK, color=ft.colors.WHITE)),
                                    ft.ElevatedButton("LinkedIn", icon=ft.icons.LINK, url="https://www.linkedin.com/in/Waqar-A-Piracha", style=ft.ButtonStyle(bgcolor="#1E3A8A", color=ft.colors.WHITE)),
                                    ft.ElevatedButton("Consulting Portfolio", icon=ft.icons.LANGUAGE, url="https://waqar-piracha-consultant.netlify.app", style=ft.ButtonStyle(bgcolor=C_SURFACE_LIGHT, color=ft.colors.WHITE)),
                                ]
                            )
                        ]
                    )
                ),

                # In-App Setup Form
                ft.Container(
                    bgcolor=C_SURFACE,
                    padding=14,
                    border_radius=10,
                    border=ft.border.all(1, C_SURFACE_LIGHT),
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("⚡ In-App Cloud Configuration", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                            in_gemini_key,
                            in_cloud_url,
                            in_oauth_token,
                            ft.Row(
                                wrap=True,
                                spacing=8,
                                controls=[
                                    ft.ElevatedButton("💾 Save Configuration", icon=ft.icons.SAVE, on_click=save_wizard_settings, style=ft.ButtonStyle(bgcolor=C_GOLD, color="#0F172A")),
                                    ft.ElevatedButton("🧪 Test Connection", icon=ft.icons.CHECK_CIRCLE_OUTLINE, on_click=test_connection_ping, style=ft.ButtonStyle(bgcolor=C_SURFACE_LIGHT, color=ft.colors.WHITE)),
                                ]
                            )
                        ]
                    )
                ),

                # Expandable Help & User Guide Accordion
                ft.ExpansionTile(
                    title=ft.Text("📘 How to Export WhatsApp Chats (1-Click)", size=13, weight=ft.FontWeight.BOLD, color=C_EMERALD),
                    initially_expanded=True,
                    controls=[
                        ft.Container(
                            padding=10,
                            bgcolor="#0A1017",
                            border_radius=8,
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text("1. Open any WhatsApp chat or group.", size=12, color="#E2E8F0"),
                                    ft.Text("2. Tap the 3 dots in the top right > 'More' > 'Export Chat'.", size=12, color="#E2E8F0"),
                                    ft.Text("3. Choose 'Without Media' to generate a lightweight .txt or .zip file.", size=12, color="#E2E8F0"),
                                    ft.Text("4. In Tab 1, tap '📂 Pick .txt/.zip' and click '💾 Export to Excel & Sheets'!", size=12, color=C_GOLD_LIGHT),
                                ]
                            )
                        )
                    ]
                ),

                ft.ExpansionTile(
                    title=ft.Text("📄 How to Parse PDF Invoices & Orders (1-Click)", size=13, weight=ft.FontWeight.BOLD, color=C_ACCENT_BLUE),
                    initially_expanded=False,
                    controls=[
                        ft.Container(
                            padding=10,
                            bgcolor="#0A1017",
                            border_radius=8,
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text("1. In Tab 2, tap '📄 Pick PDF Document'.", size=12, color="#E2E8F0"),
                                    ft.Text("2. Select any invoice, delivery note, or purchase order received on WhatsApp.", size=12, color="#E2E8F0"),
                                    ft.Text("3. Tap '⚡ Extract with Gemini AI' to pull line items and amounts.", size=12, color="#E2E8F0"),
                                    ft.Text("4. Tap '💾 Save as Excel & Sync to Drive' to save locally and to the cloud.", size=12, color=C_GOLD_LIGHT),
                                ]
                            )
                        )
                    ]
                ),

                ft.ExpansionTile(
                    title=ft.Text("🔑 Free Gemini 2.5 Flash API Key Guide", size=13, weight=ft.FontWeight.BOLD, color=C_GOLD_LIGHT),
                    initially_expanded=False,
                    controls=[
                        ft.Container(
                            padding=10,
                            bgcolor="#0A1017",
                            border_radius=8,
                            content=ft.Column(
                                spacing=6,
                                controls=[
                                    ft.Text("Gemini 2.5 Flash is 100% free for up to 15 requests/minute via Google AI Studio.", size=12, color="#E2E8F0"),
                                    ft.ElevatedButton("Open Google AI Studio", icon=ft.icons.OPEN_IN_NEW, url="https://aistudio.google.com/app/apikey", style=ft.ButtonStyle(bgcolor="#1E3A8A", color=ft.colors.WHITE)),
                                ]
                            )
                        )
                    ]
                ),
            ]
        )
    )

    # --------------------------------------------------------------------------
    # Master Navigation Setup
    # --------------------------------------------------------------------------
    main_content = ft.Container(expand=True, content=tab_chat)

    def nav_changed(e):
        idx = e.control.selected_index
        if idx == 0:
            main_content.content = tab_chat
        elif idx == 1:
            main_content.content = tab_pdf
        elif idx == 2:
            main_content.content = tab_dashboard
            refresh_dashboard_ui()
        elif idx == 3:
            main_content.content = tab_wizard
        page.update()

    bottom_nav = ft.NavigationBar(
        selected_index=0,
        on_change=nav_changed,
        bgcolor="#0F172A",
        indicator_color=C_EMERALD_DARK,
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.CHAT_BUBBLE_OUTLINE, selected_icon=ft.icons.CHAT_BUBBLE, label="Chat Parser"),
            ft.NavigationBarDestination(icon=ft.icons.PICTURE_AS_PDF_OUTLINED, selected_icon=ft.icons.PICTURE_AS_PDF, label="PDF Extractor"),
            ft.NavigationBarDestination(icon=ft.icons.CLOUD_SYNC_OUTLINED, selected_icon=ft.icons.CLOUD_SYNC, label="Sync Dashboard"),
            ft.NavigationBarDestination(icon=ft.icons.SETTINGS_OUTLINED, selected_icon=ft.icons.SETTINGS, label="Setup & Help"),
        ]
    )

    # Commercial Header with Developer Branding
    app_bar = ft.Container(
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        bgcolor="#0F172A",
        border=ft.border.only(bottom=ft.BorderSide(1, C_SURFACE_LIGHT)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.icons.SYNC_ALT, color=C_GOLD, size=22),
                            bgcolor=C_SURFACE,
                            padding=6,
                            border_radius=8,
                        ),
                        ft.Column(
                            spacing=1,
                            controls=[
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Text("WA DriveSync AI Pro", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                                        ft.Container(
                                            content=ft.Text("COMMERCIAL", size=9, weight=ft.FontWeight.BOLD, color="#0F172A"),
                                            bgcolor=C_GOLD,
                                            padding=ft.padding.symmetric(horizontal=5, vertical=1),
                                            border_radius=4,
                                        )
                                    ]
                                ),
                                ft.Text("Developed by Waqar Aslam Piracha", size=11, color=C_TEXT_MUTED),
                            ]
                        )
                    ]
                ),
                ft.IconButton(
                    icon=ft.icons.HELP_OUTLINE,
                    icon_color=C_GOLD,
                    tooltip="Open Setup & Help",
                    on_click=lambda _: setattr(bottom_nav, "selected_index", 3) or nav_changed(type("E", (), {"control": bottom_nav})()),
                )
            ]
        )
    )

    # Sticky Footer
    footer = ft.Container(
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor="#0A0F17",
        border=ft.border.only(top=ft.BorderSide(1, "#1E293B")),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("© 2026 Waqar Aslam Piracha | Enterprise Automation", size=10, color=C_TEXT_MUTED),
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Icon(ft.icons.CHECK_CIRCLE, size=12, color=C_EMERALD),
                        ft.Text("Zero Setup Ready", size=10, color=C_EMERALD, weight=ft.FontWeight.W_500),
                    ]
                )
            ]
        )
    )

    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[
                app_bar,
                main_content,
                footer,
            ]
        )
    )
    page.navigation_bar = bottom_nav
    render_chat_table()
    render_pdf_table()


if __name__ == "__main__":
    ft.app(target=main)
