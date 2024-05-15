$(document).ready(function() {
    $(".timestamp").each(function() {
        var iso_timestamp = $(this).data("timestamp");
        if (iso_timestamp !== "") {
            var local_time = new Date(iso_timestamp).toLocaleString();
            $(this).text(local_time);
        }
    });

    var tooltip_trigger_list = [].slice.call(document.querySelectorAll('[data-bs-tooltip="yes"]'))
    var tooltip_list = tooltip_trigger_list.map(function (tooltip_trigger_el) {
        return new bootstrap.Tooltip(tooltip_trigger_el)
    })

    let picklist_count = 0;
    $(document).on("picklistQuery", function(event) {
        if (++picklist_count === picklist_total_functions) {
            $.ajax({
                type: "GET",
                url: "/picklists/query",
                headers: {
                    "X-CSRFToken": window.csrf_token
                },
                success: function(response) {
                    $(document).trigger("picklistQueryDone", [response.results]);
                }
            });
        }
    });
});

let picklist_total_functions = 0;
$(document).on("wantPicklistQuery", function(event) {
    picklist_total_functions++;
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

window.csrf_token = window.get_cookie("csrftoken");

window.initialize_async_select2 = function(field_name, search_url, dropdown_parent_selector) {
    hr_field_name = field_name.replace(/bulk_|_/g, function(match) {
        return match === "_" ? " " : "";
    });

    var select2_options = {
        ajax: {
            url: search_url,
            dataType: "json",
            delay: 250,
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", window.csrf_token);
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
        placeholder: "Search for " + hr_field_name,
        minimumInputLength: 1,
        width: "100%"
    };

    // Add the dropdownParent option only if dropdown_parent_selector is provided
    if (dropdown_parent_selector) {
        select2_options.dropdownParent = $(dropdown_parent_selector);
        $(dropdown_parent_selector).find("#id_" + field_name + "_id").select2(select2_options);
    } else {
        $("#id_" + field_name + "_id").select2(select2_options);
    }

    window.select2properheight("#id_" + field_name + "_id");
}


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

window.display_error_message = function(errors) {
    var messages_div = $(".messages");

    // Clear all existing messages if errors are not provided
    if (!errors) {
        messages_div.empty();
        return;
    }

    var error_message = "";

    // Loop through the errors object and concatenate error messages
    Object.keys(errors).forEach(function(key) {
        error_message += errors[key] + " "; // Append the first error message for each key
    });

    // Create and append alert div with the concatenated error message
    var alert_div = $("<div></div>").addClass("alert alert-danger").text(error_message.trim());
    
    // Clear all existing messages before appending the new error message
    messages_div.empty();

    // Append alert_div only if error_message is not empty
    if (error_message.trim() !== "") {
        messages_div.append(alert_div);
    }
}

window.debounce = function(func, wait) {
    let timeout;
    return function() {
        const context = this, args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}
