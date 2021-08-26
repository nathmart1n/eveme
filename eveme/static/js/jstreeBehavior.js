$(function () { $('#jstreeDiv').jstree({
    "checkbox" : {
        "three_state": false,
        "cascade" : 'down',
        "cascade_to_hidden": true
    },
    "plugins": ["checkbox"]
}); });

$('#jstreeDiv').on("changed.jstree", function (e, data) {
    console.log(data.selected);
});

function submitMe(){ 
    var selectedElmsinfo = [];

    var selectedElms = $('#jstreeDiv').jstree("get_selected", true);
        $.each(selectedElms, function() {
            if (!this.id.startsWith("j")) {
                selectedElmsinfo.push(this.id);
            }
        });
        var str1 = "[";
        var str2 = "]";
        var res = str1.concat(selectedElmsinfo.join(","), str2);
        document.getElementById('jsfields').value = res;
}