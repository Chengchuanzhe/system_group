
function readWorkbookFromLocalFile(file, callback) {
        var reader = new FileReader();
        reader.onload = function(e) {
            var data = e.target.result;
            var workbook = XLSX.read(data, {type: 'binary'});
            if(callback) callback(workbook);
        };
        reader.readAsBinaryString(file);
}

 function readWorkbook(workbook) {
        var sheetNames = workbook.SheetNames; // 工作表名称集合
        var worksheet = workbook.Sheets[sheetNames[0]]; // 这里我们只读取第一张sheet
        var csv = XLSX.utils.sheet_to_csv(worksheet);
        csv = csv.replaceAll('\n', ';');
        console.log(csv)
        document.getElementById('addCourseStudentList').value = csv;
        // $("#result").csv2table(csv);

}

$(function (){
    document.getElementById('studentExcelUpload').addEventListener('change', function(e) {
			var files = e.target.files;
			console.log(files);
			if(files.length === 0) return;
			var f = files[0];
			console.log(f)
			if(!/\.xlsx$/g.test(f.name)) {
				alert('仅支持读取xlsx格式！');
				return;
			}
			readWorkbookFromLocalFile(f, function(workbook) {
				readWorkbook(workbook);
			});
		});
});