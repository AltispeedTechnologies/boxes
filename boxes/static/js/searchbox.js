function change_selected_filter(filter) {
    var search_input_container = $("#search_input_container");
    var customer_select_container = $("#customer_select_container");

    if (filter === "customer") {
        search_input_container.addClass("d-none");
        customer_select_container.removeClass("d-none");
    } else {
        customer_select_container.addClass("d-none");
        search_input_container.removeClass("d-none");
    }
}

$(document).ready(function() {
    let csrf_token = window.get_cookie("csrftoken");

    change_selected_filter(filter);

    $("#customer_select").select2({
        ajax: {
            url: "/accounts/search",
            dataType: "json",
            delay: 250,
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
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

    if (account_id && account_name) {
        var new_option = new Option(account_name, account_id, true, true);
        $("#customer_select").append(new_option).trigger("change");
    }
    
    $("#filter_select").change(function() {
        var filter = $(this).val();
        change_selected_filter(filter);
    });

    $("#searchbtn").click(function(event) {
        event.preventDefault();
        var form = $(this).closest("form");
        var filter = form.find('select[name="filter"]').val();

        if (filter === "customer") {
            var customer_id = $("#customer_select").val();
            window.location.href = "/accounts/" + customer_id + "/packages";
        } else if (filter === "tracking_code") {
            var query = form.find('input[name="q"]').val();
            var search_url = $(this).data("search");
            var full_url = search_url + "?q=" + encodeURIComponent(query) + "&filter=" + encodeURIComponent(filter);
            window.location.href = full_url;
        }
    });
});
