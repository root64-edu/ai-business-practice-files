/** @OnlyCurrentDoc */
function sayHello() {
  SpreadsheetApp.getUi().alert("안녕하세요");
}

function readWrite() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var name = sheet.getRange("A2").getValue();
  Logger.log("A2의 값: " + name);
  sheet.getRange("C2").setValue("확인: " + name);
}

function markLowQty() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var last = sheet.getLastRow();
  for (var i = 2; i <= last; i++) {
    var qty = sheet.getRange(i, 3).getValue();
    if (qty <= 0) {
      sheet.getRange(i, 4).setValue("확인 필요");
    }
  }
}

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu("실습 도구")
    .addItem("수량 확인", "markLowQty")
    .addItem("인사말", "sayHello")
    .addToUi();
}
