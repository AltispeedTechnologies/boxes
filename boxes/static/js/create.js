let packages = new Set();
let acct_is_locked = true;

function handle_create_package() {
    let csrf = window.get_cookie("csrftoken");
    let selected_queue = localStorage.getItem("selected_queue");

    let tracking_code = $("#id_tracking_code").val();
    let price = $("#id_price").val();
    let carrier_id = $("#id_carrier_id").val();
    let account_id = $("#id_account_id").val();
    let package_type_id = $("#id_package_type_id").val();
    let inside = $("#id_inside").prop("checked");
    let comments = $("#id_comments").val();
    var carrier = $("#id_carrier_id").find(":selected").text().replace(" (Create new)", "");
    var account = $("#id_account_id").find(":selected").text().replace(" (Create new)", "");
    var package_type = $("#id_package_type_id").find(":selected").text().replace(" (Create new)", "");

    let form_data = {
        tracking_code: tracking_code,
        price: price,
        carrier_id: carrier_id,
        account_id: account_id,
        package_type_id: package_type_id,
        inside: inside,
        comments: comments,
        queue_id: selected_queue
    };

    $.ajax({
        type: "POST",
        url: "/packages/new",
        headers: {
            "X-CSRFToken": csrf
        },
        data: form_data,
        success: function(response) {
            $(".is-invalid").removeClass("is-invalid");
            if (response.success) {
                packages.add(response.id);
                form_data.carrier = carrier;
                form_data.account = account;
                form_data.package_type = package_type;

                display_packages(form_data);
                reset_form_fields();
            } else {
                handle_errors(response);
            }
        },
        error: function(xhr, status, error) {
            window.display_error_message(xhr.responseJSON.errors);
        }
    });

    $("#checkinbtn").prop("disabled", (packages.size == 0));
}

function reset_form_fields() {
    $("#id_tracking_code").val("");
    $("#id_price").val("6.00");
    $("#id_package_type_id").val(null).trigger("change");
    $("#id_inside").prop("checked", false);
    if (!acct_is_locked) {
        $("#id_account_id").val(null).trigger("change");
    }
}

function display_packages(response) {
    $("#checkinbtn").prop("disabled", false);

    let new_row = document.querySelector(".visually-hidden").cloneNode(true);
    new_row.classList.remove("visually-hidden");
    new_row.querySelector("td:nth-child(1)").innerText = response.account;
    new_row.querySelector("td:nth-child(2)").innerText = response.tracking_code;
    new_row.querySelector("td:nth-child(3)").innerText = `$${response.price}`;
    new_row.querySelector("td:nth-child(4)").innerText = response.carrier;
    new_row.querySelector("td:nth-child(5)").innerText = response.package_type;
    new_row.querySelector("td:nth-child(6)").innerText = response.comments;
    document.querySelector("tbody").appendChild(new_row);
}

function handle_errors(response) {
    if (response.errors) {
        window.display_error_message(response.errors);
    } else if (response.form_errors) {
        $.each(response.form_errors, function(field, errors) {
            if (errors.length > 0) {
                $("#id_" + field).addClass("is-invalid");
                $("#id_" + field).next(".invalid-feedback").text(errors[0]).show();
            }
        });
    }
}

function handle_checkin() {
    let csrf = window.get_cookie("csrftoken");
    let selected_queue = localStorage.getItem("selected_queue");

    let packages_array = [...packages];
    let packages_payload = { ids: packages_array, queue_id: selected_queue };
    $.ajax({
        type: "POST",
        url: "/packages/checkin",
        headers: {
            "X-CSRFToken": csrf
        },
        data: packages_payload,
        success: function(response) {
            if (response.success) {
                window.display_error_message();
                window.open(`/packages/label?ids=${packages_array.toString()}`, "_blank");
                document.querySelectorAll("tbody tr:not(.visually-hidden)").forEach(row => row.remove());
                packages.clear();
                $("#checkinbtn").prop("disabled", true);
            } else {
                window.display_error_message(response.errors);
            }
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
        }
    });

}

function load_queue(selected_queue) {
    let csrf = window.get_cookie("csrftoken");

    $.ajax({
        type: "GET",
        url: "/queues/" + selected_queue + "/packages",
        headers: {
            "X-CSRFToken": csrf
        },
        success: function(response) {
            document.querySelectorAll("tbody tr:not(.visually-hidden)").forEach(row => row.remove());
            packages.clear();

            if (response.success && response.packages.length > 0) {
                response.packages.forEach(function(package) {
                    package.account = package.package__account__description;
                    package.tracking_code = package.package__tracking_code;
                    package.price = package.package__price;
                    package.carrier = package.package__carrier__name;
                    package.package_type = package.package__package_type__description;
                    package.comments = package.package__comments;

                    packages.add(package.package__id);
                    display_packages(package);
                });
            } else if (response.success && response.packages.length == 0) {
                $("#checkinbtn").prop("disabled", true);
            } else if (!response.success) {
                console.log("No packages available for the selected queue.");
            }
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
        }
    });
}

$(document).ready(function() {
    let selected_queue = localStorage.getItem("selected_queue");
    if (selected_queue) {
        $("#queue_select").val(selected_queue);
        load_queue(selected_queue);
    } else {
        load_queue($("#queue_select").val());
    }

    window.initialize_async_select2("account", "/accounts/search/");
    window.initialize_async_select2("carrier", "/carriers/search/");
    window.initialize_async_select2("package_type", "/types/search/");

    $("#toggle_lock_btn").click(function() {
        acct_is_locked = !acct_is_locked;
        $(this).find("i").toggleClass("fa-lock fa-unlock");
    });

    $("#checkinbtn, #createbtn").click(function(event) {
        event.preventDefault();
        $(this).attr("id") === "checkinbtn" ? handle_checkin() : handle_create_package();
    });

    $("#id_tracking_code").keydown(function(event) {
        if (event.keyCode === 13) {  // Enter key
            event.preventDefault();
            handle_create_package();
        }
    });

    $("#queue_select").change(function() {
        var selected_queue = $(this).val();
        localStorage.setItem("selected_queue", selected_queue);
        load_queue(selected_queue);
    });
});
