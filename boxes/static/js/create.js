let packages = new Set();
let acct_is_locked = true;

function handle_create_package() {
    var csrf = window.get_cookie("csrftoken");
    var tracking_code = $("#id_tracking_code").val();
    var price = $("#id_price").val();
    var carrier_id = $("#id_carrier_id").val();
    var account_id = $("#id_account_id").val();
    var package_type_id = $("#id_type_id").val();
    var comments = $("#id_comments").val();
    var carrier = $("#id_carrier_id").find(":selected").text();
    var account = $("#id_account_id").find(":selected").text();
    var package_type = $("#id_type_id").find(":selected").text();

    var form_data = {
        "tracking_code": tracking_code,
        "price": price,
        "carrier_id": carrier_id,
        "account_id": account_id,
        "package_type_id": package_type_id,
        "comments": comments
    };

    $.ajax({
        type: "POST",
        url: "/packages/new",
        headers: {
            "X-CSRFToken": csrf
        },
        data: form_data,
        success: function(response) {
            if (response.success) {
                packages.add(response.id);
                displayErrorMessage();

                var new_row = document.querySelector(".visually-hidden").cloneNode(true);
                new_row.classList.remove("visually-hidden");
                new_row.querySelector("td:nth-child(1)").innerText = account;
                new_row.querySelector("td:nth-child(2)").innerText = tracking_code;
                new_row.querySelector("td:nth-child(3)").innerText = "$".concat(price);
                new_row.querySelector("td:nth-child(4)").innerText = carrier;
                new_row.querySelector("td:nth-child(5)").innerText = package_type;
                new_row.querySelector("td:nth-child(6)").innerText = comments;
                document.querySelector("tbody").appendChild(new_row);

                if (!acct_is_locked) {
                    $("#id_account_id").val(null).trigger("change");
                }
            } else {
                displayErrorMessage(response.errors);
            }
        },
        error: function(xhr, status, error) {
            displayErrorMessage(xhr.responseJSON.errors);
        }
    });
}

$(document).ready(function() {
    window.initialize_async_select2("account", "/accounts/search/");
    window.initialize_async_select2("carrier", "/carriers/search/");
    window.initialize_async_select2("type", "/types/search/");

    $("#toggle_lock_btn").click(function() {
        acct_is_locked = !acct_is_locked;
        if(acct_is_locked) {
            $("#lock_icon").removeClass("fa-unlock").addClass("fa-lock");
        } else {
            $("#lock_icon").removeClass("fa-lock").addClass("fa-unlock");
        }
    });

    $("#checkinbtn").click(function(event) {
        event.preventDefault();
        var csrf = window.get_cookie("csrftoken");

        let packages_array = [...packages];
        let packages_payload = {"ids": packages_array};

        $.ajax({
            type: "POST",
            url: "/packages/checkin",
            headers: {
                "X-CSRFToken": csrf
            },
            data: packages_payload,
            success: function(response) {
                if (response.success) {
                    window.open("/packages/label?ids=".concat(packages_array.toString()), "_blank");
                    document.querySelectorAll("tbody tr:not(.visually-hidden)").forEach(row => row.remove());
                } else {
                    console.log("Not successful");
                }
            },
            error: function(xhr, status, error) {
                console.log(error);
            }
        });
    });

    $("#createbtn").click(function(event) {
        event.preventDefault();
        handle_create_package();
    });

    $("#id_tracking_code").keydown(function(event) {
        if (event.keyCode === 13) {  // 13 is the Enter key
            event.preventDefault();
            handle_create_package();
        }
    });
});

function displayErrorMessage(errors) {
    var messages_div = $(".messages");

    // Clear all existing messages if errors are not provided
    if (!errors) {
        messages_div.empty();
        return;
    }

    var error_message = "";

    // Loop through the errors object and concatenate error messages
    Object.keys(errors).forEach(function(key) {
        error_message += errors[key][0] + " "; // Append the first error message for each key
    });

    // Create and append alert div with the concatenated error message
    var alert_div = $("<div></div>").addClass("alert alert-danger").text(error_message.trim());
    
    // Clear all existing messages before appending the new error message
    messages_div.empty();

    // Append alert_div only if error_message is not empty
    if(error_message.trim() !== "") {
        messages_div.append(alert_div);
    }
}
