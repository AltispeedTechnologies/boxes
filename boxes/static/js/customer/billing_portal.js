window.ajax_request({
    type: "GET",
    url: "/customer/payments/portal/redir",
    on_success: function(response) {
        window.location.href = response.url;
    }
});
