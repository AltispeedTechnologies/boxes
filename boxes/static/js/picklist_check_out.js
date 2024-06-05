function verify_package() {
    window.display_error_message();
    $("#savingicon").show();
    let picklist_id = $("#tracking_code").attr("data-picklist-id");
    let form_data = {tracking_code: $("#tracking_code").val()};

    $.ajax({
        type: "POST",
        url: "/picklists/" + picklist_id + "/checkout/verify",
        headers: {
            "X-CSRFToken": window.csrf_token
        },
        contentType: "application/json",
        data: JSON.stringify(form_data),
        success: function(response) {
            $("#savingicon").hide();
            if (response.success) {
                let package_id = response.package.id;

                if (packages.has(package_id)) {
                    window.display_error_message(["Parcel already in list"]);
                } else {
                    display_packages(response.package);
                    packages.add(package_id);
                    $("#tracking_code").val("");
                    $("#successicon").show();
                    $("#successicon").fadeOut(1000);
                }
            } else {
                window.display_error_message(response.errors);
            }
        },
        error: function(xhr, status, error) {
            window.display_error_message(error);
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

$(document).ready(function() {
    $("#tracking_code").keydown(function(event) {
        if (event.keyCode === 13) {  // Enter key
            event.preventDefault();
            verify_package();
        }
    });

    $("#picklistCheckOutModal .btn-primary").on("click", function() {
        let packages_array = Array.from(packages);
        let payload = {"ids": packages_array};

        $.ajax({
            type: "POST",
            url: "/packages/checkout",
            headers: {"X-CSRFToken": window.csrf_token},
            data: payload,
            success: function(response) {
                if (response.success) {
                    window.location.reload();
                } else {
                    window.display_error_message(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });
});