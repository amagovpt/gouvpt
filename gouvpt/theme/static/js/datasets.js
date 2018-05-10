var onetimeclick = false;


function process_wb(wb) {
    var ws = wb.Sheets[wb.SheetNames[0]];
    var data = XLSX.utils.sheet_to_json(ws);
    return data;
}

function showCanvas(event) {
    if (!onetimeclick){
        var _grid = document.getElementById('grid');
        var url = document.getElementById('fileurl').textContent;

        //console.log(url);
        var grid = canvasDatagrid({
            parentNode: _grid,
            editable: false
        });
        
        grid.style.width = '100%';
        grid.style.height = '500px';
        grid.style.display = "block";

        var oReq;
        if(window.XMLHttpRequest) oReq = new XMLHttpRequest();
        else if(window.ActiveXObject) oReq = new ActiveXObject('MSXML2.XMLHTTP.3.0');
        else throw "XHR unavailable for your browser";

        oReq.open("GET", url, true);

        if(typeof Uint8Array !== 'undefined') {
            oReq.responseType = "arraybuffer";
            oReq.onload = function(e) {
                if(typeof console !== 'undefined') console.log("onload", new Date());
                var arraybuffer = oReq.response;
                var data = new Uint8Array(arraybuffer);
                var wb = XLSX.read(data, {type:"array"});
                grid.data = process_wb(wb);
            };
        } else {
            oReq.setRequestHeader("Accept-Charset", "x-user-defined");	
            oReq.onreadystatechange = function() { if(oReq.readyState == 4 && oReq.status == 200) {
                var ff = convertResponseBodyToText(oReq.responseBody);
                if(typeof console !== 'undefined') console.log("onload", new Date());
                var wb = XLSX.read(ff, {type:"binary"});
                grid.data = process_wb(wb);
            } };
        }

        oReq.send();

        onetimeclick = true;
    }
}