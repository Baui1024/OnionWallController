//----------------Reboot----------------------- 
let reboot = document.getElementById("reboot")
reboot.addEventListener("click",function(){
var xhttp = new XMLHttpRequest();
xhttp.open("POST", "reboot", true);
xhttp.setRequestHeader("Content-Type", "application/octet-stream");
xhttp.onload = function () {
    if (xhttp.status === 200) {
        alert(xhttp.responseText)
    } else {
        alert(xhttp.responseText)
    }
};
xhttp.send("");
});

//----------------Upload Firmware-----------------------
let uploadFirmware = document.getElementById("uploadFirmware");
let form = document.querySelector(".firmwareupload"); 
form.onsubmit = function(event){
    event.preventDefault()
    let fileInput = document.getElementById("formFile");
    let formData = new FormData();
    if (!fileInput.files[0]){
        alert("No File Selected!")
        return
    }
    formData.append("file",fileInput.files[0],fileInput.files[0].name)
    console.log(formData)
    var xhttp = new XMLHttpRequest();

    xhttp.addEventListener("readystatechange", function() {
        if(this.readyState === 4) {
        alert(this.responseText)
        console.log(this.responseText);
        
        }
  });
//xhttp.setRequestHeader("Content-Type", "multipart/form-data");
// xhttp.onload = function () {
//     if (xhttp.status === 200) {
//         alert("Upload Complete, Please Reboot Device")
//     } else {
//         alert("Fehler beim Upload " + xhttp.responseText)
//     }
// };
xhttp.open("POST", "firmware", true);
xhttp.send(formData);
};
//----------------Network Settings-----------------------
const ip = document.querySelector('#ip');
const subnet = document.querySelector('#subnet');
const gateway = document.querySelector('#gateway');
const saveip = document.getElementById("saveip");
var mode = document.getElementById("mode");
mode.addEventListener("change", function() {
disableFields();
});
function disableFields() {
    if (mode.value == "dhcp") {
        ip.disabled = true;
        subnet.disabled = true;
        gateway.disabled = true;
        ip.value = ""
        subnet.value = ""
        gateway.value = ""
    }else {
        ip.disabled = false;
        subnet.disabled = false;
        gateway.disabled = false;
    }
}

disableFields()

let IPform = document.querySelector(".networksettingsupload"); 
IPform.onsubmit = function(event){
event.preventDefault()
console.log(ip.value)
checks = [[ip.value,"IP Address"],[subnet.value,"Subnet Mask"],[gateway.value,"Gateway"]]
if (mode.value == "dhcp"){
    var x = 3
}else{
    var x = 0
}  
    while (x<3 && ValidateIPaddress(checks[x][0],checks[x][1]) ){
        console.log(x)
        x++
    }    
    if (x==3){
        var networkSettings = {"ip" : checks[0][0],"subnet" : checks[1][0],"gateway" : checks[2][0],"mode" : mode.value}
        var xhttp = new XMLHttpRequest();
        xhttp.open("POST", "network_settings", true);
        xhttp.setRequestHeader("Content-Type", "application/json");      
        xhttp.onload = function () {
            if (xhttp.status === 200) {
                    alert(xhttp.responseText)
                } else {
                    alert("IP Settings not successfull " + xhttp.responseText)
                }
            };   
    xhttp.send(JSON.stringify(networkSettings));
    }    
}
function ValidateIPaddress(inputText,name){
    var ipformat = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    if(inputText.match(ipformat)){
        return true;
    }else{
        alert("You have entered an invalid "+name);
        return false;
    }
}
