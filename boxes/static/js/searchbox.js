
function change_selected_filter(filter) {
    let search_input_container = $("#search_input_container");
    let customer_select_container = $("#customer_select_container");

    if (filter === "customer") {
        search_input_container.addClass("d-none");
        customer_select_container.removeClass("d-none");
    } else {
        customer_select_container.addClass("d-none");
        search_input_container.removeClass("d-none");
    }
}

function init_searchbox_page() {
    change_selected_filter(window.filter);

    if ($("#customer_select").length === 0 || $("#customer_select").data("select2") === undefined) {
        $("#customer_select").select2({
            ajax: {
                url: "/accounts/search",
                dataType: "json",
                delay: 250,
                beforeSend: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", window.get_cookie("csrftoken"));
                },
                data: function (params) {
                    return {
                        term: params.term,
                        page: params.page
                    };
                },
                processResults: function (data, params) {
                    return {
                        results: data.results,
                    };
                },
                cache: true
            },
            placeholder: "Search for an account",
            minimumInputLength: 1,
            width: "240px",
        });
        window.select2properheight("#customer_select");

        if (window.account_id && window.account_name) {
            let new_option = new Option(window.account_name, window.account_id, true, true);
            $("#customer_select").append(new_option).trigger("change");
        }
    }

    $("#customer_select").off("select2:select").on("select2:select", function() {
        let customer_id = $("#customer_select").val();
        window.location.href = "/accounts/" + customer_id + "/packages";
    });
    
    $("#filter_select").off("change").on("change", function() {
        let filter = $(this).val();
        change_selected_filter(filter);
    });

    $("#searchbtn").off("click").on("click", function(event) {
        event.preventDefault();
        let form = $(this).closest("form");
        let filter = form.find('select[name="filter"]').val();

        if (filter === "customer") {
            let customer_id = $("#customer_select").val();
            window.location.href = "/accounts/" + customer_id + "/packages";
        } else if (filter === "tracking_code") {
            let query = form.find('input[name="q"]').val();
            let search_url = $(this).data("search");
            let full_url = search_url + "?q=" + encodeURIComponent(query) + "&filter=" + encodeURIComponent(filter);
            window.location.href = full_url;
        }
    });

    $("#showallbtn").off("click").on("click", function(event) {
        event.preventDefault();
        window.location.href = $(this).data("search") + "?q=&filter=";
    });
}

window.manage_init_func("div#searchbox", "searchbox", init_searchbox_page);
