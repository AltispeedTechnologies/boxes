/**
 * @file mgmt/email_template.js
 * @description Jodit email template editor and save/load.
 * @see docs/api/javascript.md
 *
 * Merge fields are stored as `{token}` braces in the DB and shown as labeled
 * chips in the editor. Toolbar insert and load use the same chip markup.
 * The Jodit instance is destroyed on unmount so htmx navigations work.
 */

/** Single Jodit instance for the email template page (null when unmounted). */
let emailTemplateEditor = null;
let emailTemplateDirty = false;
let emailTemplateCurrentId = null;
let emailTemplateSuppressDirty = false;
let emailTemplateChipGuardBound = false;

const EMAIL_TOKEN_BUTTONS = [
    {name: "first_name", text: "First Name", token: "first_name"},
    {name: "last_name", text: "Last Name", token: "last_name"},
    {name: "full_name", text: "Full Name", token: "full_name"},
    {name: "tracking_code", text: "Tracking Code", token: "tracking_code"},
    {name: "carrier", text: "Carrier", token: "carrier"},
    {name: "comment", text: "Comment", token: "comment"}
];

/** @type {Object.<string, string>} token → display label */
const EMAIL_TOKEN_LABELS = EMAIL_TOKEN_BUTTONS.reduce(function(map, spec) {
    map[spec.token] = spec.text;
    return map;
}, {});

/**
 * Canonical HTML for a merge-field chip (same for toolbar insert and load).
 * @param {string} token
 * @returns {string}
 */
function build_token_chip_html(token) {
    const text = EMAIL_TOKEN_LABELS[token] || token;
    return (
        '<span contenteditable="false" draggable="false" ' +
        'style="user-select: none; -webkit-user-drag: none;" ' +
        'class="custom-block bg-light mx-1 px-2 py-1" data-token="' +
        token + '">' + text + "</span>"
    );
}

/**
 * Convert stored brace placeholders and legacy chips into editor chips.
 * @param {string} html
 * @returns {string}
 */
function normalize_email_template_html(html) {
    if (!html) {
        return "";
    }
    let out = String(html);

    out = out.replace(
        /<span\b[^>]*\bdata-token=["']([a-z_]+)["'][^>]*>[\s\S]*?<\/span>/gi,
        function(match, token) {
            if (!Object.prototype.hasOwnProperty.call(EMAIL_TOKEN_LABELS, token)) {
                return match;
            }
            return build_token_chip_html(token);
        }
    );

    out = out.replace(
        /<span\b[^>]*class=["'][^"']*custom-block[^"']*["'][^>]*>([^<]+)<\/span>/gi,
        function(match, label) {
            if (/\bdata-token\s*=/i.test(match)) {
                return match;
            }
            const key = String(label).trim().toLowerCase().replace(/\s+/g, "_");
            if (!Object.prototype.hasOwnProperty.call(EMAIL_TOKEN_LABELS, key)) {
                return match;
            }
            return build_token_chip_html(key);
        }
    );

    out = out.replace(/\{([a-z_]+)\}/g, function(match, token) {
        if (!Object.prototype.hasOwnProperty.call(EMAIL_TOKEN_LABELS, token)) {
            return match;
        }
        return build_token_chip_html(token);
    });

    return out;
}

/**
 * Convert editor chips back to stable `{token}` braces for storage.
 * @param {string} html
 * @returns {string}
 */
function denormalize_email_template_html(html) {
    if (!html) {
        return "";
    }
    let out = String(html);

    out = out.replace(
        /<span\b[^>]*\bdata-token=["']([a-z_]+)["'][^>]*>[\s\S]*?<\/span>/gi,
        function(match, token) {
            if (!Object.prototype.hasOwnProperty.call(EMAIL_TOKEN_LABELS, token)) {
                return match;
            }
            return "{" + token + "}";
        }
    );

    out = out.replace(
        /<span\b[^>]*class=["'][^"']*custom-block[^"']*["'][^>]*>([^<]+)<\/span>/gi,
        function(match, label) {
            if (/\bdata-token\s*=/i.test(match)) {
                return match;
            }
            const key = String(label).trim().toLowerCase().replace(/\s+/g, "_");
            if (!Object.prototype.hasOwnProperty.call(EMAIL_TOKEN_LABELS, key)) {
                return match;
            }
            return "{" + key + "}";
        }
    );

    // Strip Jodit zero-width artifacts
    out = out.replace(/\uFEFF/g, "");

    return out;
}

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
        exec: function(editor) {
            editor.selection.insertHTML(build_token_chip_html(spec.token) + "\u200b");
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
 * Destroy the Jodit instance if present (htmx leave / remount).
 */
function destroy_email_template_editor() {
    if (!emailTemplateEditor) {
        return;
    }
    try {
        if (typeof emailTemplateEditor.destruct === "function") {
            emailTemplateEditor.destruct();
        }
    } catch (err) {
        // Editor may already be detached after an htmx swap.
    }
    emailTemplateEditor = null;
}

/**
 * True when the live Jodit container is still in the document.
 * @returns {boolean}
 */
function email_template_editor_is_live() {
    if (!emailTemplateEditor) {
        return false;
    }
    try {
        const container = emailTemplateEditor.container || emailTemplateEditor.editor;
        return !!(container && document.body.contains(container));
    } catch (err) {
        return false;
    }
}

/**
 * Prevent native drag of merge-field chips inside the editor.
 * @param {Event} event
 */
function email_template_chip_drag_guard(event) {
    const t = event.target;
    if (!t || !t.closest) {
        return;
    }
    if (t.closest(".custom-block[data-token], .jodit-wysiwyg [data-token]")) {
        event.preventDefault();
    }
}

/**
 * Create the single Jodit instance if not already created for this DOM.
 * @returns {object|null}
 */
function ensure_email_template_editor() {
    if (email_template_editor_is_live()) {
        return emailTemplateEditor;
    }
    destroy_email_template_editor();

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
        disablePlugins: ["drag-and-drop", "drag-and-drop-element"],
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

    // Block dragstart on chips (contenteditable=false nodes can still drag).
    if (!emailTemplateChipGuardBound) {
        document.addEventListener("dragstart", email_template_chip_drag_guard, true);
        emailTemplateChipGuardBound = true;
    }

    // Initial textarea content uses {token} braces; rewrite to chips once.
    emailTemplateSuppressDirty = true;
    emailTemplateEditor.value = normalize_email_template_html(emailTemplateEditor.value || "");
    emailTemplateSuppressDirty = false;

    return emailTemplateEditor;
}

/**
 * Set editor HTML via editor.value, normalizing tokens to chips.
 * @param {string} html
 */
function set_editor_value(html) {
    const editor = ensure_email_template_editor();
    if (!editor) {
        return;
    }
    emailTemplateSuppressDirty = true;
    editor.value = normalize_email_template_html(html || "");
    emailTemplateSuppressDirty = false;
}

/**
 * Read editor HTML and convert chips to brace tokens for storage.
 * @returns {string}
 */
function get_editor_value() {
    const editor = ensure_email_template_editor();
    if (!editor) {
        return "";
    }
    return denormalize_email_template_html(editor.value || "");
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
 * Bind page controls (safe to call on remount).
 */
function bind_email_template_mgmt_page() {
    const editor = ensure_email_template_editor();
    if (!editor) {
        return;
    }

    const $selector = $("#template-selector");
    if ($selector.length && !$selector.hasClass("select2-hidden-accessible")) {
        $selector.select2();
        if (typeof window.select2properheight === "function") {
            window.select2properheight("#template-selector");
        }
    }

    emailTemplateCurrentId = $selector.val() || null;
    clear_email_template_dirty();

    $("#email_subject").off("input.emailtpl change.emailtpl").on("input.emailtpl change.emailtpl", function() {
        mark_email_template_dirty();
    });

    $selector.off("change.emailtpl").on("change.emailtpl", function() {
        const id = $(this).val();
        if (emailTemplateDirty) {
            const discard = window.confirm("You have unsaved changes. Discard them and switch templates?");
            if (!discard) {
                $selector.val(emailTemplateCurrentId).trigger("change.select2");
                return;
            }
        }
        load_email_template(id);
    });

    $("#save-btn").off("click.emailtpl").on("click.emailtpl", function() {
        const template_id = $selector.val();
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

    $("#addTemplateForm").off("submit.emailtpl").on("submit.emailtpl", function(event) {
        event.preventDefault();
        const template_name = $("#templateName").val();

        window.ajax_request({
            type: "POST",
            url: "/mgmt/email/templates/add",
            payload: {name: template_name},
            on_success: function(response) {
                clear_email_template_dirty();
                const new_option = new Option(template_name, response.id, true, true);
                $selector.append(new_option).trigger("change");
                $("#templateName").val("");
                hide_add_template_modal();
            }
        });
    });
}

/**
 * Initialize email template editor page (full document load).
 */
function init_email_template_mgmt_page() {
    bind_email_template_mgmt_page();
}

// Expose for console battle-testing.
window.normalize_email_template_html = normalize_email_template_html;
window.denormalize_email_template_html = denormalize_email_template_html;
window.build_token_chip_html = build_token_chip_html;

if (window.BoxesPage && typeof window.BoxesPage.register === "function") {
    window.BoxesPage.register("email-templates", {
        mount: function() {
            bind_email_template_mgmt_page();
        },
        unmount: function() {
            destroy_email_template_editor();
            emailTemplateDirty = false;
            emailTemplateCurrentId = null;
        }
    });
}

$(init_email_template_mgmt_page);
