function verify_package() {
    window.display_error_message();
    $("#savingicon").show();
    let picklist_id = $("#tracking_code").attr("data-picklist-id");
    let form_data = {tracking_code: $("#tracking_code").val()};

    if (picklist_id !== "") {
        form_data["picklist_id"] = picklist_id;
    }

    window.ajax_request({
        type: "POST",
        url: "/packages/checkout/verify",
        payload: JSON.stringify(form_data),
        content_type: "application/json",
        on_success: function(response) {
            let package_id = response.package.id;

            if (window.queued_packages.has(package_id)) {
                window.display_error_message(["Parcel already in list"]);
            } else {
                display_packages(response.package);
                window.queued_packages.add(package_id);
                $("#successicon").show();
                $("#successicon").fadeOut(1000);
            }
        },
        on_response: function() {
            $("#tracking_code").val("");
            $("#savingicon").hide();
        }
    });
}

function display_packages(pkg) {
    let new_row = $(".visually-hidden")
        .clone()
        .removeClass("visually-hidden")
        .attr("data-row-id", pkg.id);

    let account = `<a href="/accounts/${pkg.account_id}/packages">${pkg.account}</a>`;
    new_row.find("td:nth-child(1)").html(account);

    let tracking_code = `<a href="/packages/${pkg.id}">${pkg.tracking_code}</a>`;
    new_row.find("td:nth-child(2)").html(tracking_code);

    new_row.find("td:nth-child(3)").text("$" + pkg.price);
    new_row.find("td:nth-child(4)").text(pkg.comments);

    $("tbody").append(new_row);
}

function init_picklist_checkout_page() {
    $("#tracking_code").off("keydown").on("keydown", function(event) {
        if (event.keyCode === 13) {  // Enter key
            event.preventDefault();
            verify_package();
        }
    });

    $("#checkOutModal .btn-primary").off("click").on("click", function() {
        let packages_array = Array.from(window.queued_packages);
        let payload = {"ids": packages_array};

        window.ajax_request({
            type: "POST",
            url: "/packages/checkout/submit",
            payload: payload,
            on_success: function(response) {
                window.queued_packages.clear();
                window.location.reload();
            }
        });
    });
}

if ($("div#picklistcheckout").length !== 0 || $("div#checkoutpage").length !== 0) {
    init_picklist_checkout_page();
}
