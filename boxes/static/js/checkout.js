$(document).ready(function() {
    if (selected_packages.size > 0) { update_pagination_links(); }

    let last_checked = null;

    // Directly attaching the event listener to ensure it"s registered immediately
    $(document).on("click", ".package-checkbox", function(e) {
        let package_id = this.id.split("-")[1];
        
        // Check for the first click with a more reliable condition
        if (!last_checked) {
            last_checked = this;
            update_package_selection(this.checked, package_id);
            return;
        }

        if (e.shiftKey && last_checked) {
            handle_shift_select(this, last_checked);
        } else {
            update_package_selection(this.checked, package_id);
        }

        last_checked = this;
    });

    function update_pagination_links() {
        // Convert the Set to a comma-separated string
        let selected_ids_str = Array.from(selected_packages).join(",");

        // Update each pagination link with the selected_ids parameter
        document.querySelectorAll(".pagination .page-link").forEach(link => {
            let url = new URL(link.href, window.location.origin);
            url.searchParams.set("selected_ids", selected_ids_str);
            link.href = url.toString();
        });
    }

    function handle_shift_select(current, last) {
        let start = $(".package-checkbox").index(current);
        let end = $(".package-checkbox").index(last);
        $(".package-checkbox").slice(Math.min(start, end), Math.max(start, end) + 1).each(function() {
            this.checked = last.checked;
            update_package_selection(this.checked, this.id.split("-")[1]);
        });
    }

    function update_package_selection(is_checked, package_id) {
        if (is_checked) {
            selected_packages.add(package_id);
        } else {
            selected_packages.delete(package_id);
        }

        update_pagination_links();
    }

    $("#checkoutbtn").click(function(event) {
        event.preventDefault();
        let csrfToken = get_cookie("csrftoken");
        let packagesArray = Array.from(selected_packages);
        let packagesPayload = {"ids": packagesArray};

        $.ajax({
            type: "POST",
            url: "/packages/checkout",
            headers: {"X-CSRFToken": csrfToken},
            data: packagesPayload,
            success: function(response) {
                if (response.success) {
                    window.location.href = response.redirect_url;
                } else {
                    console.error("Checkout failed:", response.errors.join("; "));
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });
});
