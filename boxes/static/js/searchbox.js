function get_cookie(name) {
    var cookie_value = null;
    if (document.cookie && document.cookie !== "") {
        var cookies = document.cookie.split(";");
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookie_value = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookie_value;
}

document.getElementById("filter_select").addEventListener("change", function() {
    var selected_filter = this.value;
    var search_input_container = document.getElementById("search_input_container");
    var customer_select_container = document.getElementById("customer_select_container");
    
    if (selected_filter === "customer") {
        search_input_container.classList.add("d-none");
        customer_select_container.classList.remove("d-none");
        
        let csrf_token = get_cookie("csrftoken"); // Retrieve the CSRF token

        $("#customer_select").select2({
            ajax: {
                url: "/accounts/search/",
                dataType: "json",
                delay: 250,
                beforeSend: function(xhr) {
                    xhr.setRequestHeader("X-CSRFToken", csrf_token);
                },
                data: function (params) {
                    return {
                        term: params.term,
                        page: params.page
                    };
                },
                processResults: function (data, params) {
                    return {
                        results: data.results,
                    };
                },
                cache: true
            },
            placeholder: "Search for an account",
            minimumInputLength: 1,
        });
    } else {
        customer_select_container.classList.add("d-none");
        search_input_container.classList.remove("d-none");
    }
});

var picklist_data = typeof picklist_data === "undefined" ? null : picklist_data;
if (picklist_data) {
    $("#picklist-select").select2({
        data: picklist_data
    });
}
