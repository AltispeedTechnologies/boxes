/**
 * @file mgmt/users.js
 * @description Management users list search/filter.
 */

function search_users() {
    var search_query = $("#userquery").val();
    var filter = $("#userfilter").val() || "all";
    var url = new URL(window.location.href);
    var params = new URLSearchParams(url.search);
    params.set("q", search_query);
    params.set("filter", filter);
    params.delete("page");
    url.search = params.toString();
    window.location.href = url.href;
}

function init_user_mgmt_page() {
    $("#searchusers").off("click").on("click", search_users);
    $("#userfilter").off("change").on("change", search_users);
    $("#userquery").off("keydown").on("keydown", function(event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            search_users();
        }
    });
}

$(init_user_mgmt_page);
