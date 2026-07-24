/**
 * @file setup_status.js
 * @description Refresh Management navbar warning icons after settings saves,
 *              and client-side HTTP/3 connectivity checks.
 */
(function(window, $) {
    "use strict";

    function navAttr(name) {
        var nav = document.getElementById("app-navbar");
        if (!nav) {
            return null;
        }
        // Prefer getAttribute — jQuery .data() coerces "1" → 1 and breaks === "1"
        return nav.getAttribute(name);
    }

    function detectHttpProtocol() {
        try {
            if (window.performance && typeof performance.getEntriesByType === "function") {
                var entries = performance.getEntriesByType("navigation");
                if (entries && entries.length) {
                    var nhp = entries[0].nextHopProtocol;
                    if (nhp) {
                        return String(nhp);
                    }
                }
            }
        } catch (err) {
            // ignore
        }
        // Cleartext cannot be HTTP/3
        if (window.location && window.location.protocol === "http:") {
            return "http/1.1";
        }
        // https without a reported nextHopProtocol — still not proven h3
        if (window.location && window.location.protocol === "https:") {
            return "https-unknown";
        }
        return "unknown";
    }

    function isHttp3(proto) {
        if (!proto) {
            return false;
        }
        var p = String(proto).toLowerCase();
        return p === "h3" || p.indexOf("h3-") === 0 || p === "http/3" || p === "http/3.0";
    }

    function protocolLabel(proto) {
        if (!proto || proto === "unknown" || proto === "https-unknown") {
            return proto === "https-unknown" ? "HTTPS (protocol unknown)" : "Unknown";
        }
        var p = String(proto).toLowerCase();
        if (isHttp3(p)) {
            return "HTTP/3";
        }
        if (p === "h2" || p === "h2c" || p.indexOf("h2") === 0) {
            return "HTTP/2";
        }
        if (p === "http/1.1") {
            return "HTTP/1.1";
        }
        if (p === "http/1.0") {
            return "HTTP/1.0";
        }
        return String(proto);
    }

    function http3IssueMessage(label) {
        return (
            "This browser is connected with " + label +
            ". HTTP/3 is recommended for production (see Management → HTTP Connectivity)."
        );
    }

    /**
     * Paint the Management → HTTP Connectivity status box.
     * Vanilla DOM so this works even if jQuery selectors miss after htmx swaps.
     */
    function updateHttpConnectivityPanel(proto, label, ok) {
        var box = document.getElementById("http-connectivity-status");
        var detail = document.getElementById("http-connectivity-detail");
        if (!box) {
            return;
        }
        box.classList.remove(
            "alert-secondary", "alert-success", "alert-warning",
            "alert-danger", "alert-info"
        );
        // Drop spinner sibling if present
        var spinner = box.querySelector(".fa-spinner");
        if (spinner && spinner.parentElement && spinner.parentElement !== detail) {
            spinner.parentElement.remove();
        }

        var html;
        if (ok) {
            box.classList.add("alert-success");
            html = '<i class="fas fa-check-circle me-1" aria-hidden="true"></i>' +
                "Connected with <strong>" + label + "</strong>" +
                (proto && proto !== label ? ' <span class="text-muted">(' + proto + ")</span>" : "") +
                ".";
        } else if (proto === "unknown" || proto === "https-unknown") {
            box.classList.add("alert-warning");
            html = '<i class="fas fa-exclamation-triangle me-1" aria-hidden="true"></i>' +
                "Could not confirm HTTP/3 for this connection" +
                (label ? " (" + label + ")" : "") +
                ". HTTP/3 is recommended for production (see <code>docs/SETUP.md</code>).";
        } else {
            box.classList.add("alert-warning");
            html = '<i class="fas fa-exclamation-triangle me-1" aria-hidden="true"></i>' +
                "Connected with <strong>" + label + "</strong>" +
                (proto && proto !== label ? ' <span class="text-muted">(' + proto + ")</span>" : "") +
                ". This is below HTTP/3. Enable QUIC / HTTP/3 on NGINX for production " +
                "(see <code>docs/SETUP.md</code>).";
        }
        if (detail) {
            detail.innerHTML = html;
        } else {
            box.innerHTML = html;
        }
    }

    function paintHttpConnectivity() {
        var proto = detectHttpProtocol();
        var label = protocolLabel(proto);
        var ok = isHttp3(proto);
        updateHttpConnectivityPanel(proto, label, ok);
        return { proto: proto, label: label, ok: ok };
    }

    function mergeHttp3(setup) {
        if (!setup) {
            return setup;
        }
        var painted = paintHttpConnectivity();
        var proto = painted.proto;
        var label = painted.label;
        var ok = painted.ok;
        var issues = ok ? [] : [http3IssueMessage(label)];

        if (!setup.items) {
            setup.items = {};
        }
        var existing = setup.items.http3 || {};
        setup.items.http3 = {
            key: "http3",
            label: existing.label || "HTTP Connectivity",
            url_name: existing.url_name || "env_api_keys",
            required: false,
            ok: ok,
            issues: issues,
            url: existing.url || "/mgmt/env-keys#http-connectivity",
            protocol: proto,
            protocol_label: label
        };

        if (!ok) {
            setup.any_incomplete = true;
            setup.all_issues = setup.all_issues ? setup.all_issues.slice() : [];
            issues.forEach(function(msg) {
                if (setup.all_issues.indexOf(msg) < 0) {
                    setup.all_issues.push(msg);
                }
            });
        }

        return setup;
    }

    function rebuildBanner(setup) {
        var banner = document.getElementById("mgmt-setup-banner");
        if (!banner) {
            return;
        }
        var issues = (setup && setup.all_issues) ? setup.all_issues : [];
        var seen = {};
        var unique = [];
        issues.forEach(function(issue) {
            if (!issue || seen[issue]) {
                return;
            }
            seen[issue] = true;
            unique.push(issue);
        });

        if (!setup || !setup.any_incomplete || !unique.length) {
            banner.classList.add("d-none");
            return;
        }

        banner.classList.remove("d-none");
        if (setup.required_incomplete) {
            banner.classList.remove("alert-info");
            banner.classList.add("alert-warning");
            var strongReq = banner.querySelector("strong");
            if (strongReq) {
                strongReq.textContent = "Required setup incomplete";
            }
        } else {
            banner.classList.remove("alert-warning");
            banner.classList.add("alert-info");
            var strongRec = banner.querySelector("strong");
            if (strongRec) {
                strongRec.textContent = "Recommended setup";
            }
        }
        var ul = banner.querySelector("ul");
        if (ul) {
            ul.innerHTML = "";
            unique.forEach(function(issue) {
                var li = document.createElement("li");
                li.textContent = issue;
                ul.appendChild(li);
            });
        }
    }

    function applySetup(setup) {
        if (!setup || !setup.items) {
            // Still paint connectivity when payload is incomplete
            paintHttpConnectivity();
            return;
        }
        setup = mergeHttp3(setup);

        var any = !!setup.any_incomplete;
        var dropWarn = document.getElementById("mgmt-dropdown-warn");
        if (dropWarn) {
            dropWarn.classList.toggle("d-none", !any);
            var title = setup.required_incomplete
                ? "Required setup incomplete"
                : (any ? "Recommended setup remaining" : "Setup complete");
            dropWarn.setAttribute("title", title);
        }
        var menu = document.getElementById("mgmt-dropdown-menu");
        if (menu) {
            menu.querySelectorAll("[data-setup-key]").forEach(function(el) {
                var key = el.getAttribute("data-setup-key");
                var item = setup.items[key];
                var icon = el.querySelector(".setup-warn-icon");
                if (!icon || !item) {
                    return;
                }
                var ok = !!item.ok;
                icon.classList.toggle("d-none", ok);
                var tip = (item.issues && item.issues.length) ? item.issues.join(" ") : "OK";
                icon.setAttribute("title", tip);
            });
        }

        rebuildBanner(setup);
    }

    function refresh(force) {
        // Always paint HTTP connectivity first — never wait on AJAX for the panel
        paintHttpConnectivity();

        var url = navAttr("data-mgmt-setup-url");
        if (!url) {
            applySetup({ items: {}, order: [], any_incomplete: false, all_issues: [] });
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
            } else {
                applySetup({ items: {}, order: [], any_incomplete: false, all_issues: [] });
            }
        }).fail(function() {
            applySetup({ items: {}, order: [], any_incomplete: false, all_issues: [] });
        });
    }

    $(document).on("boxes:setup-status-refresh", function() {
        refresh(true);
    });

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
        apply: applySetup,
        detectHttpProtocol: detectHttpProtocol,
        isHttp3: isHttp3,
        paintHttpConnectivity: paintHttpConnectivity
    };

    function isStaffMgmtChrome() {
        var auth = navAttr("data-auth");
        return (auth === "1" || auth === "true") && !!document.getElementById("mgmt_dropdown");
    }

    function bootSetupStatus() {
        // Always paint connectivity panel if present (no AJAX wait)
        if (document.getElementById("http-connectivity-status")) {
            paintHttpConnectivity();
        }
        if (isStaffMgmtChrome()) {
            refresh(false);
            if ($) {
                $("#mgmt_dropdown").off("show.bs.dropdown.boxesSetup").on("show.bs.dropdown.boxesSetup", function() {
                    refresh(false);
                });
            }
        }
    }

    function onReady(fn) {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", fn);
        } else {
            fn();
        }
    }

    onReady(bootSetupStatus);

    document.addEventListener("htmx:afterSettle", function() {
        bootSetupStatus();
    });
})(window, window.jQuery);
