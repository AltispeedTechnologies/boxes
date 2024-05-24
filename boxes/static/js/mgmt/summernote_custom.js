(function(factory) {
    if (typeof define === "function" && define.amd) {
        define(["jquery"], factory);
    } else if (typeof module === "object" && module.exports) {
        module.exports = factory(require("jquery"));
    } else {
        factory(jQuery);
    }
}(function($) {
    $.extend($.summernote.plugins, {
        "custom_block": function(context) {
            var self = this;
            var ui = $.summernote.ui;

            // Add button to the toolbar
            context.memo("button.custom_block", function() {
                var button = ui.button({
                    contents: "<i class=\"fa fa-cube\"></i>",
                    tooltip: "Insert Custom Block",
                    click: function() {
                        self.open_dialog();
                    }
                });

                return button.render();
            });

            // Open the dialog to select the block type
            self.open_dialog = function() {
                var body = "<div class=\"form-group\">" +
                           "<label>Block Type</label>" +
                           "<select class=\"note-input form-control block-type\">" +
                           "<option value=\"first_name\">First Name</option>" +
                           "<option value=\"last_name\">Last Name</option>" +
                           "<option value=\"tracking_code\">Tracking Code(s)</option>" +
                           "<option value=\"carrier\">Carrier(s)</option>" +
                           "<option value=\"comment\">Comment</option>" +
                           "</select></div>";

                var footer = "<button class=\"btn btn-primary note-btn note-btn-primary block-btn\">Insert</button>";

                var dialog = ui.dialog({
                    title: "Insert Custom Block",
                    body: body,
                    footer: footer
                }).render();

                ui.showDialog(dialog);

                $(dialog).find(".block-btn").click(function() {
                    var block_type = $(dialog).find(".block-type").val();
                    var block_label = "";

                    // Define labels based on selected block type
                    if (block_type === "first_name") {
                        block_label = "First Name";
                    } else if (block_type === "last_name") {
                        block_label = "Last Name";
                    } else if (block_type === "tracking_code") {
                        block_label = "Tracking Code";
                    } else if (block_type === "carrier") {
                        block_label = "Carrier";
                    } else if (block_type === "comment") {
                        block_label = "Comment";
                    }

                    // Insert the block with specific attributes
                    var node = $("<span contenteditable=\"false\" style=\"user-select: none;\" class=\"custom-block bg-light mx-1 p-2\">" + block_label + "</span>");
                    context.invoke("editor.insertNode", node[0]);
                    ui.hideDialog(dialog);
                });
            };
        }
    });
}));
