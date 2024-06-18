function init_checkout_page() {
    $(document).off("checkoutPackageValid").on("checkoutPackageValid", function(event, pkg) {
        console.log(pkg);
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

if ($("div#checkoutpage").length !== 0 || $("div#picklistcheckout").length !== 0) {
    init_checkout_page();
}
