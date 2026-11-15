/** @OnlyCurrentDoc */
function getConfirmedRows() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('추출');
  var data = sheet.getDataRange().getValues();
  var header = data[0];
  var confirmed = [];
  for (var i = 1; i < data.length; i++) {
    if (data[i][header.indexOf('확인')] === '확인') {
      confirmed.push(data[i]);
    }
  }
  return { header: header, rows: confirmed };
}

function checkRow(row, header) {
  var qty = row[header.indexOf('수량')];
  var price = row[header.indexOf('단가')];
  var amount = row[header.indexOf('금액')];
  var date = row[header.indexOf('날짜')];
  var errors = [];
  if (qty * price !== amount) {
    errors.push('금액 불일치: ' + qty + 'x' + price + '≠' + amount);
  }
  var d = new Date(date);
  if (isNaN(d.getTime())) {
    errors.push('날짜 형식 오류: ' + date);
  }
  return errors;
}

function moveToLedger() {
  var result = getConfirmedRows();
  var ledger = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('장부');
  var moved = 0;
  for (var i = 0; i < result.rows.length; i++) {
    var errors = checkRow(result.rows[i], result.header);
    if (errors.length === 0) {
      var row = result.rows[i].slice(0, 8);
      ledger.appendRow(row);
      moved++;
    } else Logger.log('행 ' + (i + 1) + ': ' + errors.join(', '));
  }
  SpreadsheetApp.getUi().alert(moved + '건을 장부에 추가했습니다.');
}

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('장부 도구')
    .addItem('확인된 행 → 장부로 옮기기', 'moveToLedger')
    .addToUi();
}
