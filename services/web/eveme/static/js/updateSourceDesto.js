function updateDesto() {
    //window.alert("Cock")
    var source = document.getElementById("source")
    var sourceSelect = source.options[source.selectedIndex].text;
    var destination = document.getElementById("destination")
    for (let i = destination.options.length - 1; i >= 0; i--) {
        if (destination.options[i] === sourceSelect) {
            destination.options.splice(i, 1)
        }
    }
}

function updateSource() {
    var destination = document.getElementById("destination")
    var destinationSelect = destination.options[destination.selectedIndex].text;
    var source = document.getElementById("source")

}