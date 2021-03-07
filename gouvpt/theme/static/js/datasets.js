/*! Script by Micael Grilo >> http://micael.eu */

$ = jQuery;
var onetimeclick = false;
var onetimeclickanalysis = false;
var file_cache = {};
var grid;
var file_data;

function process_wb(wb) {
    var ws = wb.Sheets[wb.SheetNames[0]];
    var data = XLSX.utils.sheet_to_json(ws);
    return data;
}

function changeFile() {
    var selectBox = document.getElementById("select-resource");
    var url = selectBox.options[selectBox.selectedIndex].value;
    fileRequest(url);
}

function fileRequest(url, _callback=null) {

    var loader = document.getElementsByClassName("grid-loader")[0]

    if (url in file_cache) {
        console.log("File cached");
        file_data = process_wb(file_cache[url]);
        if(grid!=undefined){
            grid.data = file_data;
        }
    }
    else {
        loader.style.display = 'block';

        var oReq;
        if (window.XMLHttpRequest) oReq = new XMLHttpRequest();
        else if (window.ActiveXObject) oReq = new ActiveXObject('MSXML2.XMLHTTP.3.0');
        else throw "XHR unavailable for your browser";

        oReq.open("GET", url, true);

        if (typeof Uint8Array !== 'undefined') {
            oReq.responseType = "arraybuffer";
            oReq.onload = function (e) {
                if (typeof console !== 'undefined') console.log("onload", new Date());
                var arraybuffer = oReq.response;
                var data = new Uint8Array(arraybuffer);
                var wb = XLSX.read(data, { type: "array" });
                file_cache[url] = wb;
                file_data = process_wb(wb);
                if(grid!=undefined){
                    grid.data = file_data;
                }
                loader.style.display = 'none';
            };
        } else {
            oReq.setRequestHeader("Accept-Charset", "x-user-defined");
            oReq.onreadystatechange = function () {
                if (oReq.readyState == 4 && oReq.status == 200) {
                    var ff = convertResponseBodyToText(oReq.responseBody);
                    if (typeof console !== 'undefined') console.log("onload", new Date());
                    var wb = XLSX.read(ff, { type: "binary" });
                    file_cache[url] = wb;
                    file_data = process_wb(wb);
                    if(grid!=undefined){
                        grid.data = file_data;
                    }
                    loader.style.display = 'none';
                }
            };
        }
        oReq.send();
    }

    if(_callback){
        _callback();
    }

}

function showCanvas(event) {
    if (!onetimeclick) {
        var _grid = document.getElementById('grid');
        var selectBox = document.getElementById("select-resource");
        var url = selectBox.options[selectBox.selectedIndex].value;

        grid = canvasDatagrid({
            parentNode: _grid,
            editable: false
        });

        grid.style.width = '100%';
        grid.style.height = '500px';
        grid.style.display = "block";

        fileRequest(url);
        onetimeclick = true;
    }
}

var to_json = function to_json(workbook) {
    var file = {};
    var result = [];
    workbook.SheetNames.forEach(function (sheetName) {
        var roa = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], { header: 1 });
        var headers = roa[0];
        for (i = 1; i < roa.length; i++) {
            line = {}
            line['PartitionKey'] = sheetName;
            for (j = 0; j < headers.length; j++) {
                line[headers[j]] = roa[i][j];
            }
            result.push(line);
        }
    });
    file['d'] = result;
    return JSON.stringify(file, 2, 2);
};

var to_xml = function to_xml(workbook) {
    var file = "<feed xmlns=\"http://www.w3.org/2005/Atom\" xmlns:d=\"http://schemas.microsoft.com/ado/2007/08/dataservices\" xmlns:m=\"http://schemas.microsoft.com/ado/2007/08/dataservices/metadata\">\n";
    workbook.SheetNames.forEach(function (sheetName) {
        var roa = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], { header: 1 });
        var headers = roa[0];
        for (i = 1; i < roa.length; i++) {
            line = "<entry>\n";
            line += "<content type=\"application/xml\">\n";
            line += "<m:properties>\n";
            for (j = 0; j < headers.length; j++) {
                line += "<d:" + headers[j] + ">" + roa[i][j] + "</d:" + headers[j] + ">\n";
            }
            line += "</m:properties>\n";
            line += "</content>\n";
            line += "</entry>\n";
            file += line;
        }
    });
    file += "</feed>\n"
    return file;
};

// Function to download data to a file
function download(data, filename, type) {
    var file = new Blob([data], { type: type });
    if (window.navigator.msSaveOrOpenBlob) // IE10+
        window.navigator.msSaveOrOpenBlob(file, filename);
    else { // Others
        var a = document.createElement("a"),
            url = URL.createObjectURL(file);
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(function () {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }, 0);
    }
}

function exportFile(format) {
    var selectBox = document.getElementById("select-resource");
    var url = selectBox.options[selectBox.selectedIndex].value;
    var filename = (selectBox.options[selectBox.selectedIndex].label).replace(/\.[^/.]+$/, "");

    if (!format) {
        window.location.href = url;
    }
    if (format == 'JSON') {
        var output = to_json(file_cache[url]);
        download(output, filename + '.json', 'json');
    }
    if (format == 'XML') {
        var output = to_xml(file_cache[url]);
        download(output, filename + '.xml', 'xml');
    }
}

function showIframeCanvasPivotTable(event) {
    var selectBox = document.getElementById("select-resource");
    var url = selectBox.options[selectBox.selectedIndex].value;

    var iFrameTarget = document.getElementById("analysis_output");
    iFrameTarget.height = window.innerHeight*0.75;
    iFrameTarget.setAttribute("src", "/pivot_table/?file="+url);
}

function showIframeCanvasRawGraphs(event) {
    var selectBox = document.getElementById("select-resource");
    var url = selectBox.options[selectBox.selectedIndex].value;

    var iFrameTarget = document.getElementById("analysis_output");
    iFrameTarget.height = window.innerHeight*0.75;
    iFrameTarget.setAttribute("src", "/rawgraphs/?url="+url); 
}