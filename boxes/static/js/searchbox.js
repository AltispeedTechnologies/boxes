/**
 * @file searchbox.js
 * @description Package search filters and Select2-backed search box.
 * @see docs/api/javascript.md
 */


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

/**
 * Initialize package search box and Select2.
 */
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
            if (!customer_id) {
                // Avoid /accounts//packages (404). Require a selected account.
                let $sel = $("#customer_select");
                $sel.addClass("is-invalid");
                if (!$sel.next(".invalid-feedback").length) {
                    $sel.after(
                        '<div class="invalid-feedback d-block">Select a customer before searching.</div>'
                    );
                }
                return;
            }
            window.location.href = "/accounts/" + customer_id + "/packages";
        } else if (filter === "tracking_code") {
            let query = (form.find('input[name="q"]').val() || "").trim();
            let search_url = $(this).data("search");
            // Empty query is allowed: show results page (not 404)
            let full_url = search_url + "?q=" + encodeURIComponent(query) + "&filter=" + encodeURIComponent(filter);
            window.location.href = full_url;
        }
    });

    $("#customer_select").off("select2:select.searchguard").on("select2:select.searchguard", function() {
        $(this).removeClass("is-invalid");
        $(this).nextAll(".invalid-feedback").remove();
    });

    $("#showallbtn").off("click").on("click", function(event) {
        event.preventDefault();
        window.location.href = $(this).data("search") + "?q=&filter=";
    });
}

$(init_searchbox_page);
