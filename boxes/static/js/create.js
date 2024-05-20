let packages = new Set();
var locks = {
    acct_is_locked: true,
    type_is_locked: true,
    carrier_is_locked: true
};

function handle_create_package() {
    let selected_queue = localStorage.getItem("selected_queue");

    let tracking_code = $("#id_tracking_code").val();
    let price = $("#price").val();
    let carrier_id = $("#id_carrier_id").val();
    let account_id = $("#id_account_id").val();
    let package_type_id = $("#id_package_type_id").val();
    let inside = $("#id_inside").prop("checked");
    let comments = $("#id_comments").val();
    var carrier = $("#id_carrier_id").find(":selected").text();
    var account = $("#id_account_id").find(":selected").text();
    var package_type = $("#id_package_type_id").find(":selected").text();

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
            "X-CSRFToken": window.csrf_token
        },
        data: form_data,
        success: function(response) {
            $(".is-invalid").removeClass("is-invalid");
            if (response.success) {
                packages.add(response.id);
                form_data.id = response.id;
                form_data.carrier = carrier;
                form_data.account = account;
                form_data.package_type = package_type;

                display_packages(form_data);
                reset_form_fields();
                $(document).trigger("rowsUpdated");
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
    $("#price").val("6.00").trigger("change");
    $("#id_inside").prop("checked", false);
    if (!locks["acct_is_locked"]) {
        $("#id_account_id").val(null).trigger("change");
    }

    if (!locks["carrier_is_locked"]) {
        $("#id_carrier_id").val(null).trigger("change");
    }

    if (!locks["type_is_locked"]) {
        $("#id_package_type_id").val(null).trigger("change");
    }
}

function display_packages(response) {
    $("#checkinbtn").prop("disabled", false);

    let new_row = $(".visually-hidden")
        .clone()
        .removeClass("visually-hidden")
        .attr("data-row-id", response.id);

    new_row.find("td:nth-child(1)").text(response.account)
        .attr("data-id", response.account_id);
    new_row.find("td:nth-child(2)").text(response.tracking_code);
    new_row.find("td:nth-child(3)").text(`$${response.price}`);
    new_row.find("td:nth-child(4)").text(response.carrier)
        .attr("data-id", response.carrier_id);
    new_row.find("td:nth-child(5)").text(response.package_type)
        .attr("data-id", response.package_type_id);

    if (response.inside) {
        const icon = '<i class="fas fa-check-circle text-warning"></i>';
        new_row.find("td:nth-child(6)").html(icon).attr("data-id", "True");
    } else {
        const icon = '<i class="fas fa-times-circle text-info"></i>';
        new_row.find("td:nth-child(6)").html(icon).attr("data-id", "False");
    }

    new_row.find("td:nth-child(7)").text(response.comments);

    $("tbody").append(new_row);
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
    let selected_queue = localStorage.getItem("selected_queue");

    let packages_array = [...packages];
    let packages_payload = { ids: packages_array, queue_id: selected_queue };
    $.ajax({
        type: "POST",
        url: "/packages/checkin",
        headers: {
            "X-CSRFToken": window.csrf_token
        },
        data: packages_payload,
        success: function(response) {
            if (response.success) {
                window.display_error_message();
                window.open(`/packages/label?ids=${packages_array.toString()}`, "_blank");
                document.querySelectorAll("tbody tr:not(.visually-hidden)").forEach(row => row.remove());
                $(document).trigger("rowsUpdated");
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
    $.ajax({
        type: "GET",
        url: "/queues/" + selected_queue + "/packages",
        headers: {
            "X-CSRFToken": window.csrf_token
        },
        success: function(response) {
            document.querySelectorAll("tbody tr:not(.visually-hidden)").forEach(row => row.remove());
            packages.clear();

            if (response.success && response.packages.length > 0) {
                response.packages.forEach(function(package) {
                    packages.add(package.id);
                    display_packages(package);
                });

                $(document).trigger("rowsUpdated");
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
        localStorage.setItem("selected_queue", $("#queue_select").val());
        load_queue($("#queue_select").val());
    }

    window.initialize_async_select2("account", "/accounts/search");
    window.initialize_async_select2("carrier", "/carriers/search");
    window.initialize_async_select2("package_type", "/types/search");

    $("#toggle_acct_lock_btn, #toggle_type_lock_btn, #toggle_carrier_lock_btn").click(function() {
        var lock_state_key = $(this).data("lock-state");
        locks[lock_state_key] = !locks[lock_state_key];
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

    $("#price").select2();
    window.select2properheight("#price");

    $("#id_package_type_id").on("select2:select", function(event) {
        $("#price").val(event.params.data.default_price).trigger("change");
    });
});
