function request_create_package(form_data, hr_fields) {
    window.ajax_request({
        type: "POST",
        url: "/packages/checkin/create",
        payload: form_data,
        form_parent: "#checkinpage",
        on_success: function(response) {
            window.packages.add(response.id);
            form_data.package_id = response.id;
            form_data.carrier = hr_fields.carrier;
            form_data.account = hr_fields.account;
            form_data.package_type = hr_fields.package_type;

            if (response.tracking_code) {
                form_data.tracking_code = response.tracking_code;
            }

            display_packages(form_data);
            reset_form_fields();
            $(document).trigger("rowsUpdated");
        },
        on_response: function() {
            $(".is-invalid").removeClass("is-invalid");
        }
    });

    $("#checkinbtn").prop("disabled", (window.packages.size == 0));
}

function handle_create_package() {
    let selected_queue = localStorage.getItem("selected_queue");

    let tracking_code = $("#id_tracking_code").val();
    let price = $("#price").val();
    let carrier_id = $("#id_carrier_id").val();
    let account_id = $("#id_account_id").val();
    let package_type_id = $("#id_package_type_id").val();
    let inside = $("#id_inside").prop("checked");
    let comments = $("#id_comments").val();

    let hr_fields = {
        carrier: $("#id_carrier_id").find(":selected").text(),
        account: $("#id_account_id").find(":selected").text(),
        package_type: $("#id_package_type_id").find(":selected").text()
    };

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

    if (tracking_code === "") {
        $("#noTrackingCodeModal").modal("show");

        $("#noTrackingCodeModal .btn-primary").off().on("click", function() {
            form_data["tracking_code"] = null;
            request_create_package(form_data, hr_fields);
        });

        $("#noTrackingCodeModal .btn-secondary").off().on("click", function() {
            request_create_package(form_data, hr_fields);
        });
    } else {
        request_create_package(form_data, hr_fields);
    }
}

function reset_form_fields() {
    $("#id_tracking_code").val("");
    $("#id_inside").prop("checked", false);
    if (!window.locks["acct_is_locked"]) {
        $("#id_account_id").val(null).trigger("change");
        window.billable = true;
    }

    if (!window.locks["carrier_is_locked"]) {
        $("#id_carrier_id").val(null).trigger("change");
    }

    if (!window.locks["type_is_locked"]) {
        $("#id_package_type_id").val(null).trigger("change");
        window.default_price = null;
    }

    if (!window.locks["acct_is_locked"] && !window.locks["type_is_locked"]) {
        $("#price").val(null).trigger("change");
    }
}

function display_packages(response) {
    $("#checkinbtn").prop("disabled", false);

    let new_row = $("tbody#checkin").find(".visually-hidden")
        .clone()
        .removeClass("visually-hidden")
        .attr("data-row-id", response.package_id);

    new_row.find("td:nth-child(1) input").attr("id", "package-" + response.package_id);

    let account = `<a href="/accounts/${response.account_id}/packages">${response.account}</a>`;
    new_row.find("td:nth-child(2)").html(account)
        .attr("data-id", response.account_id);

    let tracking_code = `<a href="/packages/${response.package_id}">${response.tracking_code}</a>`;
    new_row.find("td:nth-child(3)").html(tracking_code);

    new_row.find("td:nth-child(4)").text(`$${response.price}`);
    new_row.find("td:nth-child(5)").text(response.carrier)
        .attr("data-id", response.carrier_id);
    new_row.find("td:nth-child(6)").text(response.package_type)
        .attr("data-id", response.package_type_id);

    if (response.inside) {
        const icon = '<i class="fas fa-check-circle text-warning"></i>';
        new_row.find("td:nth-child(7)").html(icon).attr("data-id", "True");
    } else {
        const icon = '<i class="fas fa-times-circle text-info"></i>';
        new_row.find("td:nth-child(7)").html(icon).attr("data-id", "False");
    }

    new_row.find("td:nth-child(8)").text(response.comments);

    $("tbody#checkin").append(new_row);
}

function handle_checkin() {
    let selected_queue = localStorage.getItem("selected_queue");

    let packages_array = [...window.packages];
    let packages_payload = { ids: packages_array, queue_id: selected_queue };
    window.ajax_request({
        type: "POST",
        url: "/packages/checkin/submit",
        payload: packages_payload,
        on_success: function(response) {
            window.open(`/packages/label?ids=${packages_array.toString()}`, "_blank");
            document.querySelectorAll("tbody#checkin tr:not(.visually-hidden)").forEach(row => row.remove());
            $(document).trigger("rowsUpdated");
            window.packages.clear();
            $("#checkinbtn").prop("disabled", true);
        }
    });
}

function load_queue(selected_queue) {
    window.ajax_request({
        type: "GET",
        url: "/queues/" + selected_queue + "/packages",
        on_success: function(response) {
            if (response.packages.length > 0) {
                response.packages.forEach(function(package) {
                    window.packages.add(package.package_id);
                    display_packages(package);
                });

                $(document).trigger("rowsUpdated");
            } else {
                $("#checkinbtn").prop("disabled", true);
            }
        },
        on_response: function(response) {
            document.querySelectorAll("tbody#checkin tr:not(.visually-hidden)").forEach(row => row.remove());
            window.packages.clear();
        }
    });
}

function init_create_page() {
    window.packages = new Set();
    window.billable = true;
    window.default_price = null;
    window.locks = {
        acct_is_locked: true,
        type_is_locked: true,
        carrier_is_locked: true
    };

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

    $("#toggle_acct_lock_btn, #toggle_type_lock_btn, #toggle_carrier_lock_btn").off("click").on("click", function() {
        var lock_state_key = $(this).data("lock-state");
        window.locks[lock_state_key] = !window.locks[lock_state_key];
        $(this).find("i").toggleClass("fa-lock fa-unlock");
    });

    $("#checkinbtn, #createbtn").off("click").on("click", function(event) {
        event.preventDefault();
        $(this).attr("id") === "checkinbtn" ? handle_checkin() : handle_create_package();
    });

    $("#id_tracking_code").off("keydown").on("keydown", function(event) {
        if (event.keyCode === 13) {  // Enter key
            event.preventDefault();
            handle_create_package();
        }
    });

    $("#queue_select").off("change").on("change", function() {
        var selected_queue = $(this).val();
        localStorage.setItem("selected_queue", selected_queue);
        load_queue(selected_queue);
    });

    $("#price").select2();
    window.select2properheight("#price");

    $("#id_package_type_id").off("select2:select").on("select2:select", function(event) {
        window.default_price = event.params.data.default_price;
        if (window.billable) {
            $("#price").val(window.default_price).trigger("change");
        }
    });

    $("#id_account_id").off("select2:select").on("select2:select", function(event) {
        window.billable = event.params.data.billable;
        if (window.billable && window.default_price) {
            $("#price").val(window.default_price).trigger("change");
        } else if (!window.billable) {
            $("#price").val("0.00").trigger("change");
        }
    });
}

if ($("#checkinpage").length !== 0) {
    init_create_page();
}
