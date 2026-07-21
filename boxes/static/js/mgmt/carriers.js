/**
 * @file mgmt/carriers.js
 * @description Carrier management: always-inline fields, independent Active
 *              toggles, dirty tracking, and bulk save.
 * @see docs/api/javascript.md
 */

/** @type {number} */
let carrierNewIdSeq = 0;

/**
 * Read field values from a carrier table row.
 * @param {JQuery} $row
 * @returns {{name: string, phone_number: string, website: string, is_active: boolean, allow_duplicate_tracking: boolean}}
 */
function carrier_row_values($row) {
    return {
        name: ($row.find("input.name").val() || "").trim(),
        phone_number: ($row.find("input.phone_number").val() || "").trim(),
        website: ($row.find("input.website").val() || "").trim(),
        is_active: $row.find("input.is_active").is(":checked"),
        allow_duplicate_tracking: $row.find("input.allow_duplicate_tracking").is(":checked")
    };
}

/**
 * Whether a row differs from its data-original-* snapshot.
 * @param {JQuery} $row
 * @returns {boolean}
 */
function carrier_row_is_dirty($row) {
    if ($row.attr("data-new") === "1") {
        return true;
    }
    const v = carrier_row_values($row);
    const origActive = $row.attr("data-original-active") === "1";
    const origDup = $row.attr("data-original-dup") === "1";
    return (
        v.name !== ($row.attr("data-original-name") || "") ||
        v.phone_number !== ($row.attr("data-original-phone") || "") ||
        v.website !== ($row.attr("data-original-website") || "") ||
        v.is_active !== origActive ||
        v.allow_duplicate_tracking !== origDup
    );
}

/**
 * Validate name field styling on a row.
 * @param {JQuery} $row
 * @returns {boolean} true if valid
 */
function carrier_row_validate($row) {
    const $name = $row.find("input.name");
    const ok = ($name.val() || "").trim() !== "";
    $name.toggleClass("is-invalid", !ok);
    return ok;
}

/**
 * Update Save button, dirty hint, and per-row reset visibility.
 */
function carrier_refresh_ui_state() {
    const $rows = $("#carriers tr");
    let anyDirty = false;
    let allValid = true;

    $rows.each(function() {
        const $row = $(this);
        const dirty = carrier_row_is_dirty($row);
        const valid = carrier_row_validate($row);
        anyDirty = anyDirty || dirty;
        if (!valid) {
            allValid = false;
        }
        $row.toggleClass("table-warning", dirty);
        $row.find(".resetrow").toggleClass("d-none", !dirty || $row.attr("data-new") === "1");
    });

    $("#carriers-dirty-hint").toggleClass("d-none", !anyDirty);
    $("#savecarriers").prop("disabled", !anyDirty || !allValid);
}

/**
 * Snapshot current values as the row's "original" (after successful save).
 * @param {JQuery} $row
 */
function carrier_row_commit_original($row) {
    const v = carrier_row_values($row);
    $row.attr("data-original-name", v.name);
    $row.attr("data-original-phone", v.phone_number);
    $row.attr("data-original-website", v.website);
    $row.attr("data-original-active", v.is_active ? "1" : "0");
    $row.attr("data-original-dup", v.allow_duplicate_tracking ? "1" : "0");
    $row.removeAttr("data-new");
}

/**
 * Restore a row from its data-original-* attributes.
 * @param {JQuery} $row
 */
function carrier_row_reset($row) {
    $row.find("input.name").val($row.attr("data-original-name") || "");
    $row.find("input.phone_number").val($row.attr("data-original-phone") || "");
    $row.find("input.website").val($row.attr("data-original-website") || "");
    $row.find("input.is_active").prop("checked", $row.attr("data-original-active") === "1");
    $row.find("input.allow_duplicate_tracking").prop(
        "checked",
        $row.attr("data-original-dup") === "1"
    );
    carrier_refresh_ui_state();
}

/**
 * Bind carriers page handlers (safe on remount).
 */
function bind_carrier_mgmt_page() {
    const $root = $("#carriermgmt");
    if (!$root.length) {
        return;
    }

    carrierNewIdSeq = 0;

    $root.off(".carriers");

    $root.on("click.carriers", "#addcarrier", function() {
        const tpl = document.getElementById("carrier-row-template");
        if (!tpl || !tpl.content) {
            return;
        }
        const node = document.importNode(tpl.content, true);
        const $row = $(node).find("tr").addBack("tr").first();
        $row.attr("data-id", "NEW_" + (++carrierNewIdSeq));
        $("#carriers").append($row);
        $row.find("input.name").trigger("focus");
        carrier_refresh_ui_state();
    });

    $root.on("click.carriers", "#savecarriers", function() {
        const $table = $("#carriers");
        const payload = {};
        let valid = true;

        $table.find("tr").each(function() {
            const $row = $(this);
            if (!carrier_row_validate($row)) {
                valid = false;
                return;
            }
            const id = $row.attr("data-id");
            payload[id] = carrier_row_values($row);
        });

        if (!valid) {
            carrier_refresh_ui_state();
            return;
        }

        $("#savingicon").show();
        $("#successicon").hide();
        $("#savecarriers").prop("disabled", true);

        window.ajax_request({
            type: "POST",
            url: "/mgmt/packages/carriers/update",
            payload: JSON.stringify(payload),
            content_type: "application/json",
            on_success: function(response) {
                if (response && response.updated_carriers) {
                    $.each(response.updated_carriers, function(key, newId) {
                        $table.find('tr[data-id="' + key + '"]').attr("data-id", String(newId));
                    });
                }
                $table.find("tr").each(function() {
                    const $row = $(this);
                    carrier_row_commit_original($row);
                    // New rows: swap remove button for reset
                    if ($row.find(".removerow").length) {
                        $row.find("td").last().html(
                            '<button type="button" class="btn btn-outline-secondary btn-sm resetrow d-none" ' +
                            'title="Reset this row"><i class="fas fa-undo"></i></button>'
                        );
                    }
                });
                $("#savingicon").hide();
                $("#successicon").show();
                $("#successicon").fadeOut(2000);
                carrier_refresh_ui_state();
            },
            on_error: function() {
                $("#savingicon").hide();
                carrier_refresh_ui_state();
            }
        });
    });

    // Any field change (text or checkbox) updates dirty/save state
    $root.on(
        "input.carriers change.carriers",
        "#carriers input.form-control, #carriers input.form-check-input",
        function() {
            carrier_refresh_ui_state();
        }
    );

    $root.on("click.carriers", ".resetrow", function() {
        carrier_row_reset($(this).closest("tr"));
    });

    $root.on("click.carriers", ".removerow", function() {
        $(this).closest("tr").remove();
        carrier_refresh_ui_state();
    });

    carrier_refresh_ui_state();
}

function init_carrier_mgmt_page() {
    bind_carrier_mgmt_page();
}

if (window.BoxesPage && typeof window.BoxesPage.register === "function") {
    window.BoxesPage.register("carriers", {
        mount: function() {
            bind_carrier_mgmt_page();
        },
        unmount: function() {
            $("#carriermgmt").off(".carriers");
        }
    });
}

$(init_carrier_mgmt_page);
