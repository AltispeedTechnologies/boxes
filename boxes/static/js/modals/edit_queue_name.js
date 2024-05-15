$(document).ready(function() {
    let queue_id = null;

    $('[data-bs-target="#editQueueNameModal"]').on("click", function() {
        let queue_name = $("#queue_select option:selected").text();
        queue_id = Number($("#queue_select option:selected").val());
        $("#editQueueNameModal").find("#queue_name").val(queue_name);
    });

    $("#editQueueNameModal .btn-primary").on("click", function() {
        let new_queue_name = $("#editQueueNameModal").find("#queue_name").val();
        payload = {
            id: queue_id,
            description: new_queue_name
        };

        $.ajax({
            type: "POST",
            url: "/queues/" + queue_id + "/update",
            headers: {"X-CSRFToken": window.csrf_token},
            data: JSON.stringify(payload),
            success: function(response) {
                if (response.success) {
                    $("#queue_select option:selected").text(new_queue_name);
                    $("#editQueueNameModal").modal("hide");
                } else {
                    console.error(response.errors);
                }
            },
            error: function(xhr, status, error) {
                console.error("An error occurred:", error);
            }
        });
    });
});
