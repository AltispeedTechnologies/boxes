/**
 * @file mgmt/pickup.js
 * @description Staff pickup schedule rules and day CRUD.
 */

function init_pickup_mgmt_page() {
    let new_rule_id = 0;
    let new_day_id = 0;
    const deleted_rules = [];
    const deleted_days = [];

    const weekday_options = [
        ["", "—"],
        ["0", "Monday"],
        ["1", "Tuesday"],
        ["2", "Wednesday"],
        ["3", "Thursday"],
        ["4", "Friday"],
        ["5", "Saturday"],
        ["6", "Sunday"],
    ];

    function weekday_select_html(selected) {
        return weekday_options.map(function(pair) {
            const sel = String(selected) === String(pair[0]) ? " selected" : "";
            return "<option value=\"" + pair[0] + "\"" + sel + ">" + pair[1] + "</option>";
        }).join("");
    }

    $("#addrule").off("click").on("click", function() {
        const id = "NEW_" + (++new_rule_id);
        const row = $(
            "<tr data-id=\"" + id + "\">" +
            "<td><input class=\"form-control name\" maxlength=\"100\"></td>" +
            "<td><select class=\"form-select recurrence\">" +
            "<option value=\"none\">None</option>" +
            "<option value=\"weekly\" selected>Weekly</option></select></td>" +
            "<td><select class=\"form-select weekday\">" + weekday_select_html("") + "</select></td>" +
            "<td><input type=\"date\" class=\"form-control start_date\"></td>" +
            "<td><input type=\"date\" class=\"form-control end_date\"></td>" +
            "<td class=\"text-center\"><input type=\"checkbox\" class=\"form-check-input is_active\" checked></td>" +
            "<td><button type=\"button\" class=\"btn btn-danger btn-sm removerule\"><i class=\"fas fa-trash-alt\"></i></button></td>" +
            "</tr>"
        );
        $("#pickuprules").append(row);
    });

    $(document).off("click", ".removerule").on("click", ".removerule", function() {
        const tr = $(this).closest("tr");
        const id = tr.attr("data-id");
        if (id && !String(id).startsWith("NEW_")) {
            deleted_rules.push(id);
        }
        tr.remove();
    });

    $("#saverules").off("click").on("click", function() {
        $("#savingrulesicon").show();
        const rules = {};
        $("#pickuprules tr").each(function() {
            const id = $(this).attr("data-id");
            rules[id] = {
                name: $(this).find(".name").val(),
                recurrence: $(this).find(".recurrence").val(),
                weekday: $(this).find(".weekday").val(),
                start_date: $(this).find(".start_date").val(),
                end_date: $(this).find(".end_date").val() || null,
                is_active: $(this).find(".is_active").is(":checked"),
            };
        });
        window.ajax_request({
            type: "POST",
            url: "/mgmt/pickup/rules/update",
            payload: JSON.stringify({rules: rules, deleted: deleted_rules}),
            content_type: "application/json",
            on_success: function(response) {
                $.each(response.updated_rules || {}, function(key, new_id) {
                    $("#pickuprules tr[data-id=\"" + key + "\"]").attr("data-id", new_id);
                });
                deleted_rules.length = 0;
                $("#savingrulesicon").hide();
                $("#successrulesicon").show().fadeOut(2000);
            }
        });
    });

    $("#addday").off("click").on("click", function() {
        const id = "NEW_" + (++new_day_id);
        let picklist_opts = "<option value=\"\">—</option>";
        const existing = $("#pickupdays tr").first().find(".picklist_id");
        if (existing.length) {
            picklist_opts = existing.html();
        }
        const row = $(
            "<tr data-id=\"" + id + "\">" +
            "<td><input type=\"date\" class=\"form-control date\"></td>" +
            "<td class=\"text-center\"><input type=\"checkbox\" class=\"form-check-input is_active\" checked></td>" +
            "<td><input class=\"form-control notes\"></td>" +
            "<td><select class=\"form-select picklist_id\">" + picklist_opts + "</select></td>" +
            "<td><button type=\"button\" class=\"btn btn-danger btn-sm removeday\"><i class=\"fas fa-trash-alt\"></i></button></td>" +
            "</tr>"
        );
        row.find(".picklist_id").val("");
        $("#pickupdays").append(row);
    });

    $(document).off("click", ".removeday").on("click", ".removeday", function() {
        const tr = $(this).closest("tr");
        const id = tr.attr("data-id");
        if (id && !String(id).startsWith("NEW_")) {
            deleted_days.push(id);
        }
        tr.remove();
    });

    $("#savedays").off("click").on("click", function() {
        $("#savingdaysicon").show();
        const days = {};
        $("#pickupdays tr").each(function() {
            const id = $(this).attr("data-id");
            days[id] = {
                date: $(this).find(".date").val(),
                is_active: $(this).find(".is_active").is(":checked"),
                notes: $(this).find(".notes").val(),
                picklist_id: $(this).find(".picklist_id").val() || null,
            };
        });
        window.ajax_request({
            type: "POST",
            url: "/mgmt/pickup/days/update",
            payload: JSON.stringify({days: days, deleted: deleted_days}),
            content_type: "application/json",
            on_success: function(response) {
                $.each(response.updated_days || {}, function(key, new_id) {
                    $("#pickupdays tr[data-id=\"" + key + "\"]").attr("data-id", new_id);
                });
                deleted_days.length = 0;
                $("#savingdaysicon").hide();
                $("#successdaysicon").show().fadeOut(2000);
            }
        });
    });
}

$(init_pickup_mgmt_page);
