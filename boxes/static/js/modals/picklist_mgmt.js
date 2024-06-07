var current_id = null;

function picklist_list_page() {
    window.picklist_data().then(function(data) {
        let picklist_data = data;

        $("#picklist-select").select2({
            data: picklist_data,
            dropdownParent: "#removePicklistModal",
            width: "100%"
        });

        window.select2properheight("#picklist-select");
    });

    $("#removePicklistModal .btn-primary").off("click").on("click", function() {
        var new_picklist = $("#picklist-select").val();

        if (new_picklist === "null") {
            var payload = {};
        } else {
            var payload = {picklist_id: new_picklist};
        }

        window.ajax_request({
            type: "POST",
            url: "/picklists/" + current_id + "/remove",
            payload: JSON.stringify(payload),
            content_type: "application/json",
            on_success: function(response) {
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
            },
            on_response: function() {
                $("#removePicklistModal").modal("hide");
            }
        });
    });

    $("#picklistNewModal .btn-primary").off("click").on("click", function() {
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

        window.ajax_request({
            type: "POST",
            url: "/picklists/create",
            payload: JSON.stringify(payload),
            content_type: "application/json",
            on_success: function() {
                window.location.reload();
            },
            on_response: function() {
                $("#picklistNewModal").modal("hide");
            }
        });
    });

    // Disable the Create button if there is nothing to submit
    $("#newpicklistdesc, #datepicker").off("input").on("input", function() {
        var disabled = ($("#newpicklistdesc").val() === "" && $("#datepicker").val() === "");
        $("#picklistNewModal .btn-primary").attr("disabled", disabled);
    });

    // If a picklist is targeted for removal, ensure the modal is updated accordingly
    $(document).off("click", ".removebtn").on("click", ".removebtn", function() {
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
}

if ($("div#picklistlist").length !== 0) {
    picklist_list_page();
}
