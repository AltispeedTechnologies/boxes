function update_pagination_links() {
    // Convert the Set to a comma-separated string
    let selected_ids_str = Array.from(window.selected_packages).join(",");

    // Update each pagination link with the selected_ids parameter
    document.querySelectorAll(".pagination .page-link").forEach(link => {
        let url = new URL(link.href, window.location.origin);
        url.searchParams.set("selected_ids", selected_ids_str);
        link.href = url.toString();
    });

    $(document).trigger("selectedPackagesUpdated");
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
        window.selected_packages.add(package_id);
    } else {
        window.selected_packages.delete(package_id);
    }

    update_pagination_links();
}

function init_checkbox() {
    window.last_checked = null;

    if (typeof window.selected_packages === "undefined" || window.selected_packages === null) {
        window.selected_packages = new Set();
    }

    if (window.selected_packages.size > 0) { update_pagination_links(); }

    $(document).off("click", ".package-checkbox").on("click", ".package-checkbox", function(e) {
        let package_id = this.id.split("-")[1];
        
        if (!last_checked) {
            window.last_checked = this;
            update_package_selection(this.checked, package_id);
            return;
        }

        if (e.shiftKey && window.last_checked) {
            handle_shift_select(this, window.last_checked);
        } else {
            update_package_selection(this.checked, package_id);
        }

        window.last_checked = this;
    });
}

window.manage_init_func(".package-checkbox", "table_select", init_checkbox);
