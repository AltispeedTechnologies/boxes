function search_accounts() {
    let search_query = $("#accountquery").val();

    // Set the query and use Turbo to visit it
    var url = new URL(window.location.href);
    var params = new URLSearchParams(url.search);
    params.set("q", search_query);
    url.search = params.toString();
    Turbo.visit(url.href);
}

function init_account_mgmt_page() {
    $("#searchaccounts").off("click").on("click", search_accounts);

    $("#accountquery").off("keydown").on("keydown", function(event) {
        // Enter key
        if (event.keyCode === 13) {
            event.preventDefault();
            search_accounts();
        }
    });
}

window.manage_init_func("div#accountmgmt", "accounts", init_account_mgmt_page);
