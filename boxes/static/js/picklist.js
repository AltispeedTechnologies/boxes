$(document).ready(function() {
    $("#picklistview").click(function(event) {
        event.preventDefault();
        let base_url = "/packages/picklists/";
        let picklist_id = $("#picklist-select-view").find(":selected").val();
        window.location.href = base_url + picklist_id;
    });
});
