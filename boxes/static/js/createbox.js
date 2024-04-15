$(document).ready(function() {
    var csrfToken = window.get_cookie("csrftoken");

    $("#id_account_id").select2({
        ajax: {
            url: "/accounts/search/",
            dataType: "json",
            delay: 250,
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            },
            data: function(params) {
                return {
                    term: params.term,
                    page: params.page
                };
            },
            processResults: function(data, params) {
                return {
                    results: data.results,
                };
            },
            cache: true
        },
        placeholder: "Search for an account",
        minimumInputLength: 1,
    });
});
