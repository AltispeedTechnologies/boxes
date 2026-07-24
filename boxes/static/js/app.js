/**
 * @file app.js
 * @description Global AJAX helpers, CSRF, Select2 utilities, debounce,
 *              BoxesPage mount/unmount registry, and htmx app-shell hooks.
 * @see docs/api/javascript.md
 *
 * htmx shell notes
 * ----------------
 * base.html boosts links/forms inside #app-main only (navbar stays mounted).
 * Page scripts in {% block javascript %} load on FULL document navigation.
 * On boosted navigations the head is not re-parsed, so:
 *   - Prefer BoxesPage.register("page-id", { mount, unmount })
 *   - Set data-page / {% block page_id %} so afterSettle can remount
 *   - unmount should tear down listeners/widgets the module owns
 * Do not reintroduce Turbo.
 */

// ---------------------------------------------------------------------------
// BoxesPage registry
// ---------------------------------------------------------------------------

/**
 * Lightweight page-module registry for full loads and htmx swaps.
 * register(name, { mount(el), unmount(el) })
 */
window.BoxesPage = (function() {
    var modules = Object.create(null);
    var active_name = null;
    var active_el = null;

    function register(name, hooks) {
        if (!name) {
            console.warn("BoxesPage.register: name is required");
            return;
        }
        modules[name] = hooks || {};
    }

    function resolve_page_name(root) {
        if (!root) {
            return null;
        }
        if (root.getAttribute && root.getAttribute("data-page")) {
            var on_root = root.getAttribute("data-page").trim();
            if (on_root) {
                return on_root;
            }
        }
        var nested = root.querySelector ? root.querySelector("[data-page]") : null;
        if (nested) {
            var name = nested.getAttribute("data-page");
            return name ? name.trim() : null;
        }
        return null;
    }

    function unmount() {
        if (active_name && modules[active_name] && typeof modules[active_name].unmount === "function") {
            try {
                modules[active_name].unmount(active_el);
            } catch (err) {
                console.warn("BoxesPage.unmount error for " + active_name, err);
            }
        }
        active_name = null;
        active_el = null;
    }

    function mount(root) {
        root = root || document.getElementById("app-main");
        var name = resolve_page_name(root);
        active_el = root || null;
        active_name = null;

        if (!name || !modules[name]) {
            return;
        }

        active_name = name;
        if (typeof modules[name].mount === "function") {
            try {
                modules[name].mount(root);
            } catch (err) {
                console.warn("BoxesPage.mount error for " + name, err);
            }
        }
    }

    function get_active() {
        return { name: active_name, el: active_el };
    }

    return {
        register: register,
        mount: mount,
        unmount: unmount,
        get_active: get_active
    };
})();

// ---------------------------------------------------------------------------
// Global utility functions
// ---------------------------------------------------------------------------

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
};

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
};

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
};

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
};

/// Generic debounce function to rate-limit e.g. async requests
window.debounce = function(func, wait) {
    let timeout;
    return function() {
        const context = this, args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
};

/// Properly validate price inputs, and do not allow any extra characters
window.format_price_input = function(input_element) {
    var value = input_element.val();
    var cursor_position = input_element[0].selectionStart;

    // Remove all non-numeric characters except the decimal point
    value = value.replace(/[^0-9\.]/g, "");
    var split = value.split(".");

    // Handle multiple decimals
    if (split.length > 2) {
        value = split[0] + "." + split[1].slice(0, 2);
    } else if (split.length === 2) {
        split[1] = split[1].slice(0, 2);
        value = split.join(".");
    }

    // Limit integer part to 6 digits
    if (split[0].length > 6) {
        value = value.slice(0, 6) + (split.length === 2 ? "." + split[1] : "");
    }

    // Format value with two decimal places if the decimal is present
    if (value.includes(".")) {
        var float_value = parseFloat(value).toFixed(2);
        if (isNaN(float_value)) {
            float_value = "0.00";
        }
        value = float_value;
    }

    input_element.val(value);

    // Adjust cursor position to handle formatting
    var new_cursor_position = cursor_position;

    // Ensure the cursor position doesn't exceed the value length
    if (new_cursor_position > value.length) {
        new_cursor_position = value.length;
    }

    input_element[0].setSelectionRange(new_cursor_position, new_cursor_position);
};

// Grab picklist data appropriately
window.picklist_data = (function() {
    let last_fetch = 0;
    let cache = null;
    let fetch_promise = null;

    return async function() {
        const now = Date.now();

        // If there's a fetch in progress, return the existing promise
        if (fetch_promise) {
            return fetch_promise;
        }

        // Use cache if the last fetch was less than 1000 milliseconds ago and cache is available
        if (last_fetch > 0 && (now - last_fetch) < 1000 && cache !== null) {
            return cache;
        }

        fetch_promise = $.ajax({
            type: "GET",
            url: "/picklists/query",
            headers: {
                "X-CSRFToken": window.get_cookie("csrftoken")
            }
        }).then(response => {
            cache = response.results;
            last_fetch = Date.now();
            fetch_promise = null;
            return cache;
        }).catch(error => {
            fetch_promise = null;
            throw error;
        });

        return fetch_promise;
    };
})();

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
                $.each(response.form_errors, function(field, errors) {
                    if (errors.length > 0) {
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
            if (xhr.responseJSON && xhr.responseJSON.errors) {
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

// ---------------------------------------------------------------------------
// Shared page widgets + navbar active state
// ---------------------------------------------------------------------------

/**
 * Document-ready / afterSettle bootstrap for shared UI widgets.
 * Safe to call on full load and after every htmx settle of #app-main.
 */
function init_page(event) {
    var context = document.getElementById("app-main") || document;

    // Timestamps are stored in the database as UTC, this does the conversion
    // client-side to the current browser time
    $(context).find(".timestamp").each(function() {
        var iso_timestamp = $(this).data("timestamp");
        if (iso_timestamp !== "") {
            var local_time = new Date(iso_timestamp).toLocaleString();
            $(this).text(local_time);
        }
    });

    // Dispose leftover Bootstrap tooltips bound to swapped-out nodes, then recreate
    $(context).find("[data-bs-tooltip=yes]").each(function() {
        var existing = bootstrap.Tooltip.getInstance(this);
        if (existing) {
            existing.dispose();
        }
    });
    var tooltip_trigger_list = [].slice.call(context.querySelectorAll("[data-bs-tooltip=yes]"));
    tooltip_trigger_list.map(function(tooltip_trigger_el) {
        return new bootstrap.Tooltip(tooltip_trigger_el);
    });
}

/**
 * Highlight navbar links from the current path (navbar is outside hx-boost).
 */
function update_navbar_active(pathname) {
    var path = pathname || window.location.pathname;
    var navbar = document.getElementById("app-navbar");
    if (!navbar) {
        return;
    }

    navbar.querySelectorAll(".nav-link").forEach(function(link) {
        link.classList.remove("active");
        var href = link.getAttribute("href");
        if (!href || href === "#") {
            return;
        }

        // Exact match for home; prefix match for other routes
        var is_active = false;
        if (href === "/") {
            is_active = path === "/";
        } else if (path === href || path.indexOf(href) === 0) {
            // Avoid /packages matching /packages/checkin when the Search link is /packages/
            if (href === "/packages/" || href === "/packages") {
                is_active = path === "/packages/" || path === "/packages" || path.indexOf("/packages/search") === 0;
            } else if (href.indexOf("/packages/checkin") === 0) {
                is_active = path.indexOf("/packages/checkin") === 0;
            } else if (href.indexOf("/packages/checkout") === 0) {
                is_active = path.indexOf("/packages/checkout") === 0;
            } else {
                is_active = true;
            }
        }

        if (is_active) {
            link.classList.add("active");
        }
    });

    // Mark dropdown parents active when a child route matches
    navbar.querySelectorAll(".nav-item.dropdown").forEach(function(item) {
        var child_active = false;
        item.querySelectorAll(".dropdown-item").forEach(function(item_link) {
            var child_href = item_link.getAttribute("href");
            if (!child_href || child_href === "#") {
                return;
            }
            if (path === child_href || path.indexOf(child_href) === 0) {
                child_active = true;
            }
        });
        var toggle = item.querySelector(".nav-link.dropdown-toggle");
        if (toggle && child_active) {
            toggle.classList.add("active");
        }
    });
}

/**
 * If htmx swapped main after login/logout without refreshing the navbar,
 * force a full document load so auth chrome matches session state.
 */
function ensure_auth_chrome() {
    var main = document.getElementById("app-main");
    var nav = document.getElementById("app-navbar");
    if (!main || !nav) {
        return;
    }
    var mainAuth = main.getAttribute("data-auth");
    var navAuth = nav.getAttribute("data-auth");
    if (mainAuth !== null && navAuth !== null && mainAuth !== navAuth) {
        window.location.reload();
    }
}

/**
 * Keep page chrome (title bars) visible under the sticky navbar after
 * full loads and htmx swaps. Browsers occasionally leave scroll mid-page
 * or leave sticky positioning stale until the next scroll event.
 */
function scroll_shell_to_top() {
    try {
        if ("scrollRestoration" in window.history) {
            window.history.scrollRestoration = "manual";
        }
    } catch (err) {
        // ignore
    }
    var reset = function() {
        window.scrollTo(0, 0);
        if (document.documentElement) {
            document.documentElement.scrollTop = 0;
        }
        if (document.body) {
            document.body.scrollTop = 0;
        }
    };
    reset();
    // Second pass after layout: fixes sticky-nav overlap until a user scroll
    window.requestAnimationFrame(function() {
        reset();
        // Tiny nudge then back to 0 forces sticky reflow in Chromium
        if ((window.scrollY || 0) === 0) {
            window.scrollTo(0, 1);
            window.scrollTo(0, 0);
        }
    });
}

function boot_app_main() {
    ensure_auth_chrome();
    init_page();
    window.BoxesPage.mount(document.getElementById("app-main"));
    update_navbar_active();
    scroll_shell_to_top();
}

// Full document load
$(function() {
    boot_app_main();
});

// ---------------------------------------------------------------------------
// htmx app-shell hooks
// ---------------------------------------------------------------------------

document.addEventListener("htmx:configRequest", function(event) {
    var token = window.get_cookie("csrftoken");
    if (token) {
        event.detail.headers["X-CSRFToken"] = token;
    }
});

document.addEventListener("htmx:beforeSwap", function(event) {
    var target = event.detail && event.detail.target;
    if (target && target.id === "app-main") {
        window.BoxesPage.unmount();
    }
});

document.addEventListener("htmx:afterSettle", function(event) {
    var target = event.detail && event.detail.target;
    // outerHTML swap may leave target as parent; always re-boot from #app-main
    if (!target || target.id === "app-main" || (target.querySelector && target.querySelector("#app-main")) || target.id === undefined) {
        boot_app_main();
    }
});

document.addEventListener("htmx:historyRestore", function() {
    boot_app_main();
});
