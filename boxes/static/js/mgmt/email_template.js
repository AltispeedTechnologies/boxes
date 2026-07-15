/**
 * @file mgmt/email_template.js
 * @description Jodit email template editor and save/load.
 * @see docs/api/javascript.md
 */

/** Single Jodit instance for the email template page. */
let emailTemplateEditor = null;
let emailTemplateDirty = false;
let emailTemplateCurrentId = null;
let emailTemplateSuppressDirty = false;

const EMAIL_TOKEN_BUTTONS = [
    {name: "first_name", text: "First Name", token: "first_name"},
    {name: "last_name", text: "Last Name", token: "last_name"},
    {name: "full_name", text: "Full Name", token: "full_name"},
    {name: "tracking_code", text: "Tracking Code", token: "tracking_code"},
    {name: "carrier", text: "Carrier", token: "carrier"},
    {name: "comment", text: "Comment", token: "comment"}
];

/**
 * Build a Jodit toolbar control that inserts a stable token chip.
 * @param {{name: string, text: string, token: string}} spec
 * @returns {object}
 */
function make_token_btn(spec) {
    return {
        name: spec.name,
        text: spec.text,
        tooltip: "Insert " + spec.text,
        exec: (editor) => {
            const chip =
                '<span contenteditable="false" style="user-select: none;" ' +
                'class="custom-block bg-light mx-1 p-2" data-token="' +
                spec.token + '">' + spec.text + "</span>";
            editor.selection.insertHTML(chip);
        }
    };
}

/**
 * Mark the editor form dirty unless updates are suppressed (load/reset).
 */
function mark_email_template_dirty() {
    if (!emailTemplateSuppressDirty) {
        emailTemplateDirty = true;
    }
}

/**
 * Clear dirty flag after load or successful save.
 */
function clear_email_template_dirty() {
    emailTemplateDirty = false;
}

/**
 * Hide the add-template modal via Bootstrap 5 API.
 */
function hide_add_template_modal() {
    const el = document.getElementById("addTemplateModal");
    if (!el || typeof bootstrap === "undefined") {
        return;
    }
    const instance = bootstrap.Modal.getInstance(el) || bootstrap.Modal.getOrCreateInstance(el);
    instance.hide();
}

/**
 * Create the single Jodit instance if not already created.
 * @returns {object|null}
 */
function ensure_email_template_editor() {
    if (emailTemplateEditor) {
        return emailTemplateEditor;
    }
    const textarea = document.getElementById("content-editor");
    if (!textarea || typeof Jodit === "undefined") {
        return null;
    }

    const controls = {};
    EMAIL_TOKEN_BUTTONS.forEach(function(spec) {
        controls[spec.name] = make_token_btn(spec);
    });

    emailTemplateEditor = Jodit.make("#content-editor", {
        height: 400,
        toolbarAdaptive: false,
        buttons: [
            "bold", "italic", "underline", "strikethrough", "|",
            "link", "|",
            "first_name", "last_name", "full_name", "tracking_code", "carrier", "comment", "|",
            "eraser"
        ],
        controls: controls
    });

    emailTemplateEditor.events.on("change", function() {
        mark_email_template_dirty();
    });

    return emailTemplateEditor;
}

/**
 * Set editor HTML via editor.value only.
 * @param {string} html
 */
function set_editor_value(html) {
    const editor = ensure_email_template_editor();
    if (!editor) {
        return;
    }
    emailTemplateSuppressDirty = true;
    editor.value = html || "";
    emailTemplateSuppressDirty = false;
}

/**
 * Read editor HTML via editor.value only.
 * @returns {string}
 */
function get_editor_value() {
    const editor = ensure_email_template_editor();
    if (!editor) {
        return "";
    }
    return editor.value || "";
}

/**
 * Load a template's subject/body into the form.
 * @param {string|number} id
 */
function load_email_template(id) {
    if (!id) {
        emailTemplateSuppressDirty = true;
        $("#email_subject").val("");
        set_editor_value("");
        emailTemplateSuppressDirty = false;
        emailTemplateCurrentId = null;
        clear_email_template_dirty();
        return;
    }

    window.ajax_request({
        type: "GET",
        url: "/mgmt/email/templates/fetch",
        payload: {id: id},
        on_success: function(response) {
            emailTemplateSuppressDirty = true;
            $("#email_subject").val(response.subject || "");
            set_editor_value(response.content || "");
            emailTemplateSuppressDirty = false;
            emailTemplateCurrentId = String(id);
            clear_email_template_dirty();
        }
    });
}

/**
 * Initialize email template editor page.
 */
function init_email_template_mgmt_page() {
    const editor = ensure_email_template_editor();
    if (!editor) {
        return;
    }

    $("#template-selector").select2();
    window.select2properheight("#template-selector");

    emailTemplateCurrentId = $("#template-selector").val() || null;
    clear_email_template_dirty();

    $("#email_subject").off("input.emailtpl change.emailtpl").on("input.emailtpl change.emailtpl", function() {
        mark_email_template_dirty();
    });

    $("#template-selector").off("change.emailtpl").on("change.emailtpl", function() {
        const id = $(this).val();
        if (emailTemplateDirty) {
            const discard = window.confirm("You have unsaved changes. Discard them and switch templates?");
            if (!discard) {
                // Revert selection without re-entering this handler's dirty check
                $("#template-selector").val(emailTemplateCurrentId).trigger("change.select2");
                return;
            }
        }
        load_email_template(id);
    });

    $("#save-btn").off("click").on("click", function() {
        const template_id = $("#template-selector").val();
        if (!template_id) {
            return;
        }
        $("#savingicon").show();
        $("#successicon").hide();
        const payload = {
            id: template_id,
            content: get_editor_value(),
            subject: $("#email_subject").val()
        };

        window.ajax_request({
            type: "POST",
            url: "/mgmt/email/templates/update",
            payload: payload,
            on_success: function() {
                $("#savingicon").hide();
                $("#successicon").show();
                $("#successicon").fadeOut(2000);
                emailTemplateCurrentId = String(template_id);
                clear_email_template_dirty();
            },
            on_error: function() {
                $("#savingicon").hide();
            }
        });
    });

    $("#addTemplateForm").off("submit").on("submit", function(event) {
        event.preventDefault();
        const template_name = $("#templateName").val();

        window.ajax_request({
            type: "POST",
            url: "/mgmt/email/templates/add",
            payload: {name: template_name},
            on_success: function(response) {
                // New template is empty; avoid dirty prompt when selecting it
                clear_email_template_dirty();
                const new_option = new Option(template_name, response.id, true, true);
                $("#template-selector").append(new_option).trigger("change");
                $("#templateName").val("");
                hide_add_template_modal();
            }
        });
    });
}

$(init_email_template_mgmt_page);
