var current_id = null;

$(document).ready(function() {
    window.picklist_total_functions++;

    $(document).on("picklistQueryDone", function(event, data) {
        $("#picklist-select").select2({
            data: data,
            dropdownParent: "#removePicklistModal",
            width: "100%"
        });
    });

    $.ajax({
        url: "/modals/picklistmgmt",
        type: "GET",
        headers: {
            "X-CSRFToken": window.csrf_token
        },
        success: function(response) {
            $("#modalContainer").html(response);
            $(document).trigger("picklistQuery");
            $(document).trigger("modalsLoaded");
        },
        error: function() {
            console.error("Error loading modals");
        }
    });
});

$(document).on("click", ".removebtn", function() {
    var $tr = $(this).closest("tr");
    var count = $tr.find("#count").text();
    current_id = $tr.attr("data-id");

    if (count > 0) {
        $("#itemsnotpresent").hide();
        $("#itemspresent").show();
    } else {
        $("#itemspresent").hide();
        $("#itemsnotpresent").show();
    }
});

$(document).on("modalsLoaded", function() {
    $("#removePicklistModal .btn-primary").on("click", function() {
        var new_picklist = $("#picklist-select").val();

        if (new_picklist === "null") {
            var payload = {};
        } else {
            var payload = {picklist_id: new_picklist};
        }

        $.ajax({
            url: "/picklists/" + current_id + "/remove",
            type: "POST",
            headers: {
                "X-CSRFToken": window.csrf_token
            },
            contentType: "application/json",
            data: JSON.stringify(payload),
            success: function(response) {
                window.display_error_message();

                if (response.success) {
                    // Update the count for the row this picklist was merged into
                    if (response.new_count) {
                        let $tr = $("tr[data-id=\"" + new_picklist + "\"]");
                        $tr.find("td#count").text(response.new_count);
                    }

                    // Update the queue count as well
                    if (response.new_queue_count) {
                        let $tr = $("tr[data-id=\"" + new_picklist + "\"]");
                        $tr.find("td#queue_count").text(response.new_queue_count);
                    }

                    // Remove the row for the picklist we just removed
                    let $old_tr = $("tr[data-id=\"" + current_id + "\"]");
                    $old_tr.remove();
                } else {
                    window.display_error_message(response.errors);
                }
                $("#removePicklistModal").modal("hide");
            }
        });
    });

    $("#picklistNewModal .btn-primary").on("click", function() {
        // Ensure the date matches MM/DD/YYYY, if it doesn't, error
        var date = $("#datepicker").val();
        if (date !== "") {
            const regex = /^(0[1-9]|1[0-2])\/(0[1-9]|[12][0-9]|3[01])\/(2[0-9][0-9][0-9])$/;
            var is_valid = regex.test(date);
            $("#datepicker").toggleClass("is-invalid", !is_valid);
            if (!is_valid) { return; }
        }

        var description = $("#newpicklistdesc").val();
        var payload = {};

        if (date !== "") { payload["date"] = date; }
        if (description !== "") { payload["description"] = description; }

        $.ajax({
            url: "/picklists/create",
            type: "POST",
            headers: {
                "X-CSRFToken": window.csrf_token
            },
            contentType: "application/json",
            data: JSON.stringify(payload),
            success: function(response) {
                window.display_error_message();
                $("#picklistNewModal").modal("hide");

                if (response.success) {
                    window.location.reload();
                } else {
                    window.display_error_message(response.errors);
                }
            }
        });
    });

    // Disable the Create button if there is nothing to submit
    $("#newpicklistdesc, #datepicker").on("input", function() {
        var disabled = ($("#newpicklistdesc").val() === "" && $("#datepicker").val() === "");
        $("#picklistNewModal .btn-primary").attr("disabled", disabled);
    });

    // Initialize the date picker
    $("#datepicker").datepicker({
        // Ensure the date picker pops up in the modal
        beforeShow: function(input, inst) {
            $(inst.dpDiv).appendTo(".modal-body");
        },
        // Manually trigger the input event after date selection
        onSelect: function() {
            $(this).trigger("input");
        },
        minDate: 0,
        maxDate: 30
    });
});
