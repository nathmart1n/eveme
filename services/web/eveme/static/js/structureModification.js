function displayDivDemo(elementValue) {
    if (elementValue.value == 'add') {
        document.getElementById("createNew").style.display = 'flex';
        document.getElementById("updateOld").style.display = 'none';
    } else {
        document.getElementById("createNew").style.display = 'none';
        document.getElementById("add").style.display = 'none';
        document.getElementById("delete").style.display = 'flex';
        document.getElementById("deleteStructure").value = document.getElementById("tradeRoute").value;
    }
 }