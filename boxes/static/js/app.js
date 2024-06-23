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
    var hr_field_name = field_name.split("_")[1];

    var select2_options = {
        ajax: {
            url: search_url,
            dataType: "json",
            delay: 250,
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", window.get_cookie("csrftoken"));
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
        $(dropdown_parent_selector).find("#" + field_name).select2(select2_options);
    } else {
        $("#" + field_name).select2(select2_options);
    }

    window.select2properheight("#" + field_name);
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

// Grab picklist data appropriately
window.picklist_data = async function() {
    const response = await $.ajax({
        type: "GET",
        url: "/picklists/query",
        headers: {
            "X-CSRFToken": window.get_cookie("csrftoken")
        }
    });
    return response.results;
};

// Generic ajax request wrapper, for deduplication
window.ajax_request = function({ type, url, payload = null, content_type = "application/x-www-form-urlencoded; charset=UTF-8", process_data = true, form_parent = null, on_success, on_response }) {
    $.ajax({
        type: type,
        url: url,
        headers: {
            "X-CSRFToken": window.get_cookie("csrftoken")
        },
        data: payload,
        contentType: content_type,
        processData: process_data,
        success: function(response) {
            window.display_error_message();
            $(".is-invalid").removeClass("is-invalid");
            $(".invalid-feedback").text("").hide();

            if (on_response) {
                on_response(response);
            }

            if (response.success) {
                on_success(response);
            } else if (response.form_errors) {
                console.log(response.form_errors);
                $.each(response.form_errors, function(field, errors) {
                    if (errors.length > 0) {
                        console.log(field);
                        if (form_parent) {
                            var selector = "input[name=\"" + field + "\"], select[name=\"" + field + "\"]";
                            $(form_parent).find(selector).addClass("is-invalid");
                            $(form_parent).find("div.invalid-feedback[name=\"" + field + "\"]").text(errors[0]).show();
                        } else {
                            $("#" + field).addClass("is-invalid");
                            $("#" + field).next(".invalid-feedback").text(errors[0]).show();
                        }
                    }
                });
            } else {
                window.display_error_message(response.errors || ["An unexpected error occurred."]);
            }
        },
        error: function(xhr, status, error) {
            let error_message = "An unexpected error occurred.";
            if (xhr.responseJSON && xhr.responsePlJSON.errors) {
                error_message = xhr.responseJSON.errors;
            } else if (error) {
                error_message = [error];
            } else if (xhr.statusText) {
                error_message = [xhr.statusText];
            }
            window.display_error_message(error_message);
        }
    });
};

/// Functionality to run once the content has fully loaded
function init_page(event) {
    var context = document;
    if (event && event.type === "turbo:before-render") {
        var context = event.detail.newBody;
    } else if (event && event.type === "turbo:before-frame-render") {
        var context = event.detail.newFrame;
    }

    // Timestamps are stored in the database as UTC, this does the conversion
    // client-side to the current browser time
    $(context).find(".timestamp").each(function() {
        var iso_timestamp = $(this).data("timestamp");
        if (iso_timestamp !== "") {
            var local_time = new Date(iso_timestamp).toLocaleString();
            $(this).text(local_time);
        }
    });

    // Set up tooltips for each HTML element that has data-bs-tooltip="yes"
    var tooltip_trigger_list = [].slice.call(context.querySelectorAll('[data-bs-tooltip="yes"]'));
    var tooltip_list = tooltip_trigger_list.map(function (tooltip_trigger_el) {
        return new bootstrap.Tooltip(tooltip_trigger_el)
    })

    // Specific links are within a Turbo Frame but have a response not containing the current Turbo Frame
    // Allow an override for this, so Turbo Drive can kick in
    $(document).off("click", "a[data-bypass-frame]").on("click", "a[data-bypass-frame]", function(event) {
        event.preventDefault();
        var url = $(this).attr("href");
        Turbo.visit(url);
    });

    $(document).on("click", "turbo-frame#package-table a", function(event) {
        // Prevent the default action
        event.preventDefault();

        // Navigate using Turbo with action "advance" to update the history stack
        Turbo.visit($(this).attr("href"), { action: "advance" });
    });
}

$(document).on({
    "turbo:load": init_page,
    "turbo:before-render": function(event) {
        init_page(event);
    },
    "turbo:before-frame-render": function(event) {
        init_page(event);
    }
});

$(document).off("turbo:visit").on("turbo:visit", function() {
    // Set the last visited URL
    sessionStorage.setItem("last_visited_url", window.location.href);
});
