$(function () {
    $("#useHistory").click(function () {
        if ($(this).is(":checked")) {
            $("#analysisAggDiv").show();
        } else {
            $("#analysisAggDiv").hide();
        }
    });
});