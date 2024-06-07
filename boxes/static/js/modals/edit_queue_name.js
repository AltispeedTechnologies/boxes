function edit_queue_name() {
    let queue_id = null;

    $("[data-bs-target=\"#editQueueNameModal\"]").off("click").on("click", function() {
        let queue_name = $("#queue_select option:selected").text();
        queue_id = Number($("#queue_select option:selected").val());
        $("#editQueueNameModal").find("#queue_name").val(queue_name);
    });

    $("#editQueueNameModal .btn-primary").off("click").on("click", function() {
        let new_queue_name = $("#editQueueNameModal").find("#queue_name").val();
        let payload = {
            id: queue_id,
            description: new_queue_name
        };

        window.ajax_request({
            type: "POST",
            url: "/queues/" + queue_id + "/update",
            payload: JSON.stringify(payload),
            on_success: function() {
                $("#queue_select option:selected").text(new_queue_name);
                $("#editQueueNameModal").modal("hide");
            }
        });
    });
}

if ($("#editQueueNameModal").length !== 0) {
    edit_queue_name();
}
