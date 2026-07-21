/**
 * @file setup_status.js
 * @description Refresh Management navbar warning icons after settings saves.
 */
(function(window, $) {
    "use strict";

    function applySetup(setup) {
        if (!setup || !setup.items) {
            return;
        }
        var any = !!setup.any_incomplete;
        var $dropWarn = $("#mgmt-dropdown-warn");
        if ($dropWarn.length) {
            $dropWarn.toggleClass("d-none", !any);
            var title = setup.required_incomplete
                ? "Required setup incomplete"
                : (any ? "Recommended setup remaining" : "Setup complete");
            $dropWarn.attr("title", title);
        }
        $("#mgmt-dropdown-menu [data-setup-key]").each(function() {
            var key = $(this).data("setup-key");
            var item = setup.items[key];
            var $icon = $(this).find(".setup-warn-icon");
            if (!$icon.length || !item) {
                return;
            }
            var ok = !!item.ok;
            $icon.toggleClass("d-none", ok);
            var tip = (item.issues && item.issues.length) ? item.issues.join(" ") : "OK";
            $icon.attr("title", tip);
        });
        // Page banners if present
        var $banner = $("#mgmt-setup-banner");
        if ($banner.length && setup.all_issues) {
            if (setup.any_incomplete) {
                $banner.removeClass("d-none");
            }
        }
    }

    function refresh(force) {
        var url = $("#app-navbar").data("mgmt-setup-url");
        if (!url) {
            return;
        }
        if (force) {
            url += (url.indexOf("?") >= 0 ? "&" : "?") + "refresh=1";
        }
        $.ajax({
            url: url,
            method: "GET",
            dataType: "json",
            headers: { "Accept": "application/json" }
        }).done(function(data) {
            if (data && data.success && data.setup) {
                applySetup(data.setup);
            }
        });
    }

    // After any successful staff AJAX that may change config, refresh icons
    $(document).on("boxes:setup-status-refresh", function() {
        refresh(true);
    });

    // Hook ajax_request success for known mgmt save URLs
    var originalAjax = window.ajax_request;
    if (typeof originalAjax === "function") {
        window.ajax_request = function(opts) {
            var userSuccess = opts.on_success;
            var url = opts.url || "";
            opts.on_success = function(response) {
                if (userSuccess) {
                    userSuccess(response);
                }
                if (/\/mgmt\/|\/carriers\/update|\/packages\/types\/update|charge|email\/update|email\/templates|pickup|general\/update/.test(url)) {
                    refresh(true);
                }
            };
            return originalAjax(opts);
        };
    }

    window.BoxesSetupStatus = {
        refresh: function() { refresh(true); },
        apply: applySetup
    };

    $(function() {
        // Soft refresh on staff pages so icons stay current after other tabs
        if ($("#app-navbar").data("auth") === "1" && $("#mgmt_dropdown").length) {
            // Debounced refresh when Management dropdown opens
            $("#mgmt_dropdown").on("show.bs.dropdown", function() {
                refresh(false);
            });
        }
    });
})(window, jQuery);
