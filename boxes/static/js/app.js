$(document).ready(function() {
    $(".select-select2").select2();

    $(".timestamp").each(function() {
        var iso_timestamp = $(this).data("timestamp");
        if (iso_timestamp !== "") {
            var local_time = new Date(iso_timestamp).toLocaleString();
            $(this).text(local_time);
        }
    });
});

window.get_cookie = function(name) {
    var cookie_value = null;
    if (document.cookie && document.cookie !== "") {
        var cookies = document.cookie.split(";");
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookie_value = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookie_value;
}

window.initialize_async_select2 = function(field_name, search_url, dropdown_parent_selector) {
    let csrf_token = window.get_cookie("csrftoken");

    var select2_options = {
        ajax: {
            url: search_url,
            dataType: "json",
            delay: 250,
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            },
            data: function(params) {
                return {
                    term: params.term,
                    page: params.page
                };
            },
            processResults: function(data, params) {
                return {
                    results: data.results,
                };
            },
            cache: true
        },
        placeholder: "Search for " + field_name,
        minimumInputLength: 1,
        width: "100%",
        tags: true,
        createTag: function (params) {
            var term = $.trim(params.term);
            if (term === "") {
                return null;
            }

            var exists = false;
            $("#id_" + field_name + "_id").find("option").each(function() {
                if ($.trim($(this).text()).replace(/\s\(Create new\)$/, '').toUpperCase() === term.toUpperCase()) {
                    exists = true;
                    return false;
                }
            });

            if (!exists) {
                return {
                    id: term,
                    text: term + " (Create new)",
                    newTag: true
                }
            }

            return null;
        }
    };

    // Add the dropdownParent option only if dropdown_parent_selector is provided
    if (dropdown_parent_selector) {
        select2_options.dropdownParent = $(dropdown_parent_selector);
    }

    $(dropdown_parent_selector).find("#id_" + field_name + "_id").select2(select2_options);
}

$("[data-bs-target=\"#print\"]").on("click", function() {
    row_id = $(this).data("row-id");
    window.open("/packages/label?ids=" + row_id);
});

window.select2properheight = function(select2_name) {
    var $select2container = $(select2_name).next(".select2-container");
    var $selection = $select2container.find(".select2-selection--single");

    $selection.css({
        "height": "38px",
        "padding": "0"
    });

    $selection.find(".select2-selection__rendered").css({
        "line-height": "38px"
    });

    $selection.find(".select2-selection__arrow").css({
        "height": "38px",
        "top": "50%",
        "transform": "translateY(-50%)"
    });
}
