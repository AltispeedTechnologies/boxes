// Global Utility Functions

/// Used for actions (both bulk and single) to avoid duplicate queries
/// See the picklistQuery handler for more details
window.picklist_total_functions = 0;

/// Generic cookie function, currently only used for CSRF tokens
window.get_cookie = function(name) {
    var cookie_value = null;

    // Only act if there are cookies stored
    if (document.cookie && document.cookie !== "") {
        // Get all cookies
        var cookies = document.cookie.split(";");

        // Iterate on each cookie
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // If the cookie matches the name, set the cookie value and break
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookie_value = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    // Returns null if no cookies match the name, otherwise returns the value
    return cookie_value;
}
/// Instead of calling window.get_cookie for every request needing the CSRF
/// token, allow async calls to use this variable
window.csrf_token = window.get_cookie("csrftoken");

/// Given a unique identifier to a select2 box, ensure the height and width is
/// consistent
window.select2properheight = function(select2_name) {
    // Do nothing if select2_name does not exist
    if (!select2_name || $(select2_name).length === 0) {
        console.warn("window.select2properheight: select2_name not defined");
        return;
    }

    var $select2container = $(select2_name).next(".select2-container");

    // Do nothing if there are no items in the specified container
    if ($select2container.length === 0) {
        console.warn("window.select2properheight: no items in " + select2_name);
        return;
    }

    var $selection = $select2container.find(".select2-selection--single");

    // Increase the size of the select2 box accordingly
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

/// Create a select2 dropdown for items which get their data asynchronously
//// field_name: unique identifier for the dropdown
//// search_url: URL to submit async requests to
//// dropdown_parent_selector (optional): parent modal for the dropdown
window.initialize_async_select2 = function(field_name, search_url, dropdown_parent_selector) {
    // Equal to s/_/ /g - determines the best human-readable name for the placeholder
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

    // If this select box will be in a modal, ensure dropdownParent is set
    if (dropdown_parent_selector) {
        select2_options.dropdownParent = $(dropdown_parent_selector);
        $(dropdown_parent_selector).find("#id_" + field_name + "_id").select2(select2_options);
    } else {
        $("#id_" + field_name + "_id").select2(select2_options);
    }

    window.select2properheight("#id_" + field_name + "_id");
}

/// Display a custom error message on the screen
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

/// Generic debounce function to rate-limit e.g. async requests
window.debounce = function(func, wait) {
    let timeout;
    return function() {
        const context = this, args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

/// Properly validate price inputs, and do not allow any extra characters
window.format_price_input = function(input_element) {
    var value = input_element.val().replace(/[^0-9\.]/g, "");
    var split = value.split(".");
    if (split.length > 2) {
        value = split[0] + "." + split[1].slice(0, 2);
    } else if (split.length === 2) {
        split[1] = split[1].slice(0, 2);
        value = split.join(".");
    }
    if (split[0].length > 6) {
        value = value.slice(0, 6) + (split.length === 2 ? "." + split[1] : "");
    }
    input_element.val(value);
}

window.picklist_data = async function() {
    const response = await $.ajax({
        type: "GET",
        url: "/picklists/query",
        headers: {
            "X-CSRFToken": window.csrf_token
        }
    });
    return response.results;
};

/// Functionality to run once the content has fully loaded
function init_page() {
    // Timestamps are stored in the database as UTC, this does the conversion
    // client-side to the current browser time
    $(".timestamp").each(function() {
        var iso_timestamp = $(this).data("timestamp");
        if (iso_timestamp !== "") {
            var local_time = new Date(iso_timestamp).toLocaleString();
            $(this).text(local_time);
        }
    });

    // Set up tooltips for each HTML element that has data-bs-tooltip="yes"
    var tooltip_trigger_list = [].slice.call(document.querySelectorAll('[data-bs-tooltip="yes"]'));
    var tooltip_list = tooltip_trigger_list.map(function (tooltip_trigger_el) {
        return new bootstrap.Tooltip(tooltip_trigger_el)
    })
}

// Ensure turbo:load is only bound once when needed
window.turbo_load = {};

document.addEventListener("turbo:load", init_page);
