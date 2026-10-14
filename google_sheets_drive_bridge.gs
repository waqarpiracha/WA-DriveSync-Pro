/**
 * WA-DriveSync-Pro Google Drive & Google Sheets Companion Bridge
 * Developed by Waqar Aslam Piracha | Enterprise Automation & AI Solutions
 * Contact: waqarpiracha@gmail.com | WhatsApp: +92 313 437 9963
 * LinkedIn: https://www.linkedin.com/in/Waqar-A-Piracha
 * 
 * Deployment Instructions:
 * 1. Open Google Sheets (create a new blank spreadsheet or open existing).
 * 2. Click "Extensions" > "Apps Script".
 * 3. Delete any code in Code.gs and replace it completely with this script.
 * 4. Click "Deploy" > "New deployment".
 * 5. Select type "Web app".
 *    - Description: WA-DriveSync-Pro Bridge
 *    - Execute as: Me (your Google account)
 *    - Who has access: Anyone
 * 6. Click "Deploy", authorize permissions, and copy the Web App URL!
 * 7. Paste the Web App URL into the WA-DriveSync-Pro Android App Settings.
 */

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "online",
    service: "WA-DriveSync-Pro Companion Bridge",
    version: "1.0.0",
    developer: "Waqar Aslam Piracha | Enterprise Automation & AI Solutions",
    timestamp: new Date().toISOString()
  })).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.tryLock(30000);

  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonResponse({ success: false, error: "Empty POST body received" }, 400);
    }

    var payload = JSON.parse(e.postData.contents);
    var action = payload.action || "test_connection";

    var ss;
    if (payload.spreadsheetId && payload.spreadsheetId.trim() !== "") {
      ss = SpreadsheetApp.openById(payload.spreadsheetId.trim());
    } else {
      ss = SpreadsheetApp.getActiveSpreadsheet();
      if (!ss) {
        // Fallback: look for or create a default spreadsheet
        var files = DriveApp.getFilesByName("WA_DriveSync_Pro_Master_Database");
        if (files.hasNext()) {
          ss = SpreadsheetApp.open(files.next());
        } else {
          ss = SpreadsheetApp.create("WA_DriveSync_Pro_Master_Database");
        }
      }
    }

    if (action === "test_connection") {
      return jsonResponse({
        success: true,
        message: "Successfully connected to Google Drive & Google Sheets!",
        spreadsheetTitle: ss.getName(),
        spreadsheetUrl: ss.getUrl(),
        userEmail: Session.getActiveUser().getEmail() || "Authorized Account",
        timestamp: new Date().toLocaleString()
      });
    }

    if (action === "save_messages") {
      return handleSaveMessages(ss, payload);
    }

    if (action === "upload_pdf_and_extract") {
      return handleUploadPdfAndExtract(ss, payload);
    }

    return jsonResponse({ success: false, error: "Unrecognized action: " + action }, 400);

  } catch (err) {
    return jsonResponse({
      success: false,
      error: err.toString(),
      stack: err.stack
    }, 500);
  } finally {
    lock.releaseLock();
  }
}

/**
 * Saves parsed WhatsApp Group and 1-to-1 messages into "WhatsApp_Messages" sheet tab.
 */
function handleSaveMessages(ss, payload) {
  var sheetName = "WhatsApp_Messages";
  var sheet = ss.getSheetByName(sheetName);
  var isNew = false;

  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    isNew = true;
  }

  var headers = [
    "Sync Timestamp",
    "Chat Type (Group / 1-to-1)",
    "Chat / Group Name",
    "Message Date",
    "Message Time",
    "Sender Name / Number",
    "Message Content",
    "AI Action Item / Summary",
    "Data Source"
  ];

  if (isNew || sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    var headerRange = sheet.getRange(1, 1, 1, headers.length);
    headerRange.setBackground("#064E3B"); // Rich Emerald Green
    headerRange.setFontColor("#FFFFFF");
    headerRange.setFontWeight("bold");
    headerRange.setFontFamily("Roboto");
    sheet.setFrozenRows(1);
  }

  var messages = payload.messages || [];
  if (!Array.isArray(messages) || messages.length === 0) {
    return jsonResponse({ success: true, count: 0, message: "No messages to insert", sheetUrl: ss.getUrl() });
  }

  var syncTimestamp = new Date().toLocaleString();
  var rowsToAppend = [];

  for (var i = 0; i < messages.length; i++) {
    var m = messages[i];
    rowsToAppend.push([
      syncTimestamp,
      m.chat_type || "Group",
      m.chat_name || "General Chat",
      m.date || "",
      m.time || "",
      m.sender || "Unknown",
      m.message || "",
      m.ai_tag || "General",
      m.source || "WA-DriveSync-Pro Mobile"
    ]);
  }

  var startRow = sheet.getLastRow() + 1;
  sheet.getRange(startRow, 1, rowsToAppend.length, headers.length).setValues(rowsToAppend);

  // Auto-resize columns for readability
  try {
    sheet.autoResizeColumns(1, 6);
  } catch (e) {}

  return jsonResponse({
    success: true,
    count: rowsToAppend.length,
    sheetName: sheetName,
    spreadsheetUrl: ss.getUrl(),
    message: "Successfully synchronized " + rowsToAppend.length + " WhatsApp messages into Google Sheets!"
  });
}

/**
 * Decodes Base64 PDF, saves to Google Drive folder "WhatsApp_Synced_Files",
 * and writes extracted line items into "PDF_Extracted_Data" sheet tab.
 */
function handleUploadPdfAndExtract(ss, payload) {
  var fileName = payload.fileName || ("WA_Doc_" + new Date().getTime() + ".pdf");
  var base64Pdf = payload.base64Pdf;
  var driveFileUrl = "";
  var driveFileId = "";

  // 1. Upload physical PDF to Google Drive in "WhatsApp_Synced_Files" folder
  if (base64Pdf && base64Pdf.length > 50) {
    var folderName = "WhatsApp_Synced_Files";
    var folders = DriveApp.getFoldersByName(folderName);
    var targetFolder;
    if (folders.hasNext()) {
      targetFolder = folders.next();
    } else {
      targetFolder = DriveApp.createFolder(folderName);
    }

    var decodedBytes = Utilities.base64Decode(base64Pdf);
    var pdfBlob = Utilities.newBlob(decodedBytes, "application/pdf", fileName);
    var driveFile = targetFolder.createFile(pdfBlob);
    
    // Set file accessible with link
    try {
      driveFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    } catch (e) {}

    driveFileUrl = driveFile.getUrl();
    driveFileId = driveFile.getId();
  }

  // 2. Write Extracted Content to "PDF_Extracted_Data" tab
  var sheetName = "PDF_Extracted_Data";
  var sheet = ss.getSheetByName(sheetName);
  var isNew = false;

  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    isNew = true;
  }

  var headers = [
    "Extraction Timestamp",
    "File Name",
    "Google Drive File Link",
    "Document Type",
    "Key Identifier (Invoice / PO / Ref #)",
    "Extracted Field / Line Item",
    "Value / Amount",
    "Additional Details / Summary"
  ];

  if (isNew || sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    var headerRange = sheet.getRange(1, 1, 1, headers.length);
    headerRange.setBackground("#1E3A8A"); // Executive Navy Blue
    headerRange.setFontColor("#FFFFFF");
    headerRange.setFontWeight("bold");
    headerRange.setFontFamily("Roboto");
    sheet.setFrozenRows(1);
  }

  var items = payload.extractedData || [];
  var syncTime = new Date().toLocaleString();
  var rowsToAppend = [];
  var driveLinkFormula = driveFileUrl ? ('=HYPERLINK("' + driveFileUrl + '", "Open in Drive")') : "N/A";

  if (Array.isArray(items) && items.length > 0) {
    for (var j = 0; j < items.length; j++) {
      var it = items[j];
      rowsToAppend.push([
        syncTime,
        fileName,
        driveLinkFormula,
        it.doc_type || payload.documentType || "PDF Document",
        it.key_identifier || payload.keyIdentifier || "N/A",
        it.field_name || it.item || "Data Entry",
        it.value || it.amount || "",
        it.details || payload.summary || ""
      ]);
    }
  } else {
    // If no items list, insert 1 summary row
    rowsToAppend.push([
      syncTime,
      fileName,
      driveLinkFormula,
      payload.documentType || "Document",
      payload.keyIdentifier || "N/A",
      "Full Document Content",
      payload.totalAmount || "N/A",
      payload.summary || "Extracted via Gemini 2.5 Flash AI"
    ]);
  }

  var startRow = sheet.getLastRow() + 1;
  sheet.getRange(startRow, 1, rowsToAppend.length, headers.length).setValues(rowsToAppend);

  try {
    sheet.autoResizeColumns(1, 5);
  } catch (e) {}

  return jsonResponse({
    success: true,
    fileName: fileName,
    fileUrl: driveFileUrl,
    fileId: driveFileId,
    rowsWritten: rowsToAppend.length,
    sheetName: sheetName,
    spreadsheetUrl: ss.getUrl(),
    message: "PDF uploaded to Drive & " + rowsToAppend.length + " extracted rows written to Sheets!"
  });
}

function jsonResponse(data, statusCode) {
  var output = ContentService.createTextOutput(JSON.stringify(data));
  output.setMimeType(ContentService.MimeType.JSON);
  return output;
}
