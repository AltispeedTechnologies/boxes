"""Generate API reference markdown from the live Boxes codebase.

Usage (from repo root, with env loaded)::

    ./env/bin/python manage.py generate_docs

Writes under ``docs/api/``. These files are generated; re-run after API changes.
Human-authored operational docs remain in ``docs/*.md`` outside ``docs/api/``.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
import re
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.fields import NOT_PROVIDED
from django.urls import URLPattern, URLResolver, get_resolver


class Command(BaseCommand):
    """Introspect URLs, models, views, backend, tasks, and settings into markdown."""

    help = (
        "Generate API reference docs under docs/api/ from the running codebase "
        "(routes, models, views, backend, tasks, settings, JS)."
    )

    def add_arguments(self, parser):
        """Register CLI options."""
        parser.add_argument(
            "--output-dir",
            default=None,
            help="Output directory (default: <BASE_DIR>/docs/api)",
        )

    def handle(self, *args, **options):
        """Generate all API reference pages."""
        out = Path(options["output_dir"] or Path(settings.BASE_DIR) / "docs" / "api")
        out.mkdir(parents=True, exist_ok=True)

        writers = [
            ("index.md", self._render_index),
            ("urls.md", self._render_urls),
            ("models.md", self._render_models),
            ("views.md", lambda: self._render_package("boxes.views", "Views")),
            ("backend.md", lambda: self._render_package("boxes.backend", "Backend")),
            ("tasks.md", self._render_tasks),
            ("settings.md", self._render_settings),
            ("templatetags.md", lambda: self._render_package("boxes.templatetags", "Template tags")),
            ("management.md", self._render_management),
            ("javascript.md", self._render_javascript),
        ]
        for name, renderer in writers:
            path = out / name
            path.write_text(renderer().rstrip() + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Wrote {path}"))

    def _unwrap(self, func):
        try:
            return inspect.unwrap(func)
        except (ValueError, AttributeError):
            return func

    def _doc(self, obj) -> str:
        return (inspect.getdoc(obj) or "").strip()

    def _sig(self, func) -> str:
        try:
            return str(inspect.signature(func))
        except (TypeError, ValueError):
            return "(...)"

    def _access_tier(self, callback) -> str:
        seen = set()
        fn = callback
        while fn is not None and id(fn) not in seen:
            seen.add(id(fn))
            tier = getattr(fn, "access_tier", None)
            if tier:
                return tier
            fn = getattr(fn, "__wrapped__", None)
        return "unknown"

    def _tier_from_name(self, name: str) -> str:
        from boxes import urls as urlconf

        def names(patterns):
            out = set()
            for p in patterns:
                if isinstance(p, URLResolver):
                    out |= names(p.url_patterns)
                elif getattr(p, "name", None):
                    out.add(p.name)
            return out

        if name in names(urlconf.public_urlpatterns):
            return "public"
        if name in names(urlconf.authenticated_urlpatterns):
            return "authenticated"
        if name in names(urlconf.staff_urlpatterns):
            return "staff"
        if name in names(urlconf.customer_urlpatterns):
            return "customer"
        return "unknown"

    def _walk_urls(self, patterns, prefix=""):
        rows = []
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                rows.extend(self._walk_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
            elif isinstance(pattern, URLPattern):
                callback = pattern.callback
                original = self._unwrap(callback)
                module = getattr(original, "__module__", "")
                name = getattr(original, "__name__", repr(original))
                if module.startswith("django."):
                    continue
                tier = self._access_tier(callback)
                if tier == "unknown" and pattern.name:
                    tier = self._tier_from_name(pattern.name)
                doc = self._doc(original)
                rows.append(
                    {
                        "path": prefix + str(pattern.pattern),
                        "name": pattern.name or "",
                        "callable": f"{module}.{name}",
                        "tier": tier,
                        "doc": doc.split("\n")[0] if doc else "",
                    }
                )
        return rows

    def _render_index(self) -> str:
        return """# API reference (generated)

This directory is produced by `manage.py generate_docs`. Do not hand-edit;
re-run the command after changing routes, models, views, tasks, or settings.

```bash
cd /var/www/mikes-boxes   # or your deploy root
./env/bin/python manage.py generate_docs
```

| Page | Source of truth |
|------|-----------------|
| [urls.md](urls.md) | Django URLConf + view callables |
| [models.md](models.md) | Model classes, fields, methods |
| [views.md](views.md) | View modules and callables |
| [backend.md](backend.md) | Non-HTTP business logic |
| [tasks.md](tasks.md) | Celery tasks + beat schedule |
| [settings.md](settings.md) | Django settings module values (non-secret) |
| [templatetags.md](templatetags.md) | Template filters/tags |
| [management.md](management.md) | Management commands |
| [javascript.md](javascript.md) | Static JS file headers and functions |

Human-written operational docs (setup, quirks, DB-backed settings map) live in
parent `docs/`.
"""

    def _render_urls(self) -> str:
        rows = self._walk_urls(get_resolver().url_patterns)
        lines = [
            "# HTTP routes (generated)",
            "",
            "Resolved from the live URLConf. Access tier uses decorator "
            "`access_tier` metadata when present, otherwise pattern-list membership "
            "in `boxes.urls`.",
            "",
            "| Tier | Path | Name | Callable | Summary |",
            "|------|------|------|----------|---------|",
        ]
        order = {"public": 0, "authenticated": 1, "staff": 2, "customer": 3, "unknown": 9}
        rows.sort(key=lambda r: (order.get(r["tier"], 9), r["path"]))
        for r in rows:
            summary = r["doc"].replace("|", "\\|")
            lines.append(
                f"| {r['tier']} | `{r['path']}` | `{r['name']}` | `{r['callable']}` | {summary} |"
            )
        lines.append("")
        lines.append(f"_Generated {len(rows)} application routes (Django admin omitted)._")
        return "\n".join(lines)

    def _render_models(self) -> str:
        lines = [
            "# Models (generated)",
            "",
            "Introspected from the Django app registry (`boxes` models only).",
            "",
        ]
        models = sorted(apps.get_app_config("boxes").get_models(), key=lambda m: m.__name__)
        for model in models:
            lines.append(f"## {model.__name__}")
            lines.append("")
            lines.append(f"`{model._meta.label}` — db table `{model._meta.db_table}`")
            lines.append("")
            doc = self._doc(model)
            if doc:
                lines.append(doc)
                lines.append("")
            lines.append("| Field | Type | Null | Default | Related | Help |")
            lines.append("|-------|------|------|---------|---------|------|")
            for field in model._meta.get_fields():
                if not hasattr(field, "name"):
                    continue
                try:
                    ftype = field.get_internal_type()
                except Exception:
                    ftype = field.__class__.__name__
                null = getattr(field, "null", "")
                default = getattr(field, "default", NOT_PROVIDED)
                if default is NOT_PROVIDED:
                    default_s = ""
                elif callable(default):
                    default_s = "(callable)"
                else:
                    default_s = repr(default)
                related = ""
                if getattr(field, "related_model", None) is not None:
                    related = field.related_model._meta.label
                help_text = getattr(field, "help_text", "") or ""
                lines.append(
                    f"| `{field.name}` | {ftype} | {null} | {default_s} | {related} | {help_text} |"
                )
            methods = []
            for name, member in model.__dict__.items():
                if name.startswith("_"):
                    continue
                if inspect.isfunction(member):
                    methods.append((name, member))
            if methods:
                lines.append("")
                lines.append("**Methods**")
                lines.append("")
                for name, member in sorted(methods, key=lambda x: x[0]):
                    d = self._doc(member).split("\n")[0] if self._doc(member) else ""
                    lines.append(f"- `{name}{self._sig(member)}` — {d}")
            lines.append("")
        return "\n".join(lines)

    def _iter_module_tree(self, package_name: str):
        package = importlib.import_module(package_name)
        yield package_name, package
        if not hasattr(package, "__path__"):
            return
        for mod in pkgutil.walk_packages(package.__path__, prefix=package_name + "."):
            name = mod.name
            if "migrations" in name.split("."):
                continue
            try:
                module = importlib.import_module(name)
            except Exception as exc:
                yield name, exc
                continue
            yield name, module

    def _render_package(self, package_name: str, title: str) -> str:
        lines = [
            f"# {title} (generated)",
            "",
            f"Public callables discovered under `{package_name}`.",
            "",
        ]
        for name, module in self._iter_module_tree(package_name):
            if isinstance(module, Exception):
                lines.append(f"## `{name}`")
                lines.append("")
                lines.append(f"_Import error: {module}_")
                lines.append("")
                continue
            items = []
            for attr_name, obj in inspect.getmembers(module):
                if attr_name.startswith("_"):
                    continue
                if inspect.isclass(obj) and getattr(obj, "__module__", None) == module.__name__:
                    items.append(("class", attr_name, obj))
                elif inspect.isfunction(obj) and getattr(obj, "__module__", None) == module.__name__:
                    items.append(("def", attr_name, obj))
            if not items and not self._doc(module):
                continue
            lines.append(f"## `{name}`")
            lines.append("")
            mdoc = self._doc(module)
            if mdoc:
                lines.append(mdoc)
                lines.append("")
            for kind, attr_name, obj in sorted(items, key=lambda x: (x[0], x[1])):
                if kind == "class":
                    lines.append(f"### class `{attr_name}`")
                    lines.append("")
                    cdoc = self._doc(obj)
                    if cdoc:
                        lines.append(cdoc)
                        lines.append("")
                    for mname, member in sorted(obj.__dict__.items()):
                        if mname.startswith("_") and mname != "__init__":
                            continue
                        if inspect.isfunction(member):
                            md = (self._doc(member) or "").split("\n")[0]
                            lines.append(f"- `{mname}{self._sig(member)}` — {md}")
                    lines.append("")
                else:
                    lines.append(f"### `{attr_name}{self._sig(obj)}`")
                    lines.append("")
                    d = self._doc(obj)
                    lines.append(d if d else "_No docstring._")
                    lines.append("")
        return "\n".join(lines)

    def _render_tasks(self) -> str:
        lines = [
            "# Celery tasks (generated)",
            "",
            "## Beat schedule",
            "",
            "From `settings.CELERY_BEAT_SCHEDULE`:",
            "",
            "| Name | Task | Schedule |",
            "|------|------|----------|",
        ]
        beat = getattr(settings, "CELERY_BEAT_SCHEDULE", {}) or {}
        for name, entry in sorted(beat.items()):
            lines.append(
                f"| `{name}` | `{entry.get('task', '')}` | `{entry.get('schedule', '')}` |"
            )
        lines.append("")
        # Append package docs without the outer title
        body = self._render_package("boxes.tasks", "Tasks")
        # drop first heading block
        parts = body.split("\n", 3)
        lines.append(parts[-1] if len(parts) > 3 else body)
        return "\n".join(lines)

    def _render_settings(self) -> str:
        secret_fragments = (
            "SECRET",
            "PASSWORD",
            "API_KEY",
            "ENDPOINT_SECRET",
            "TOKEN",
            "PRIVATE",
        )
        lines = [
            "# Settings (generated)",
            "",
            "Values from the loaded Django settings module. Secrets are redacted.",
            "",
            "| Setting | Value |",
            "|---------|-------|",
        ]
        for key in sorted(dir(settings)):
            if not key.isupper():
                continue
            try:
                value = getattr(settings, key)
            except Exception:
                continue
            if callable(value) and not isinstance(value, type):
                continue
            if any(s in key for s in secret_fragments):
                display = "**[redacted]**"
            else:
                display = repr(value)
                if len(display) > 120:
                    display = display[:117] + "..."
                display = display.replace("|", "\\|")
            lines.append(f"| `{key}` | `{display}` |")
        lines.append("")
        lines.append(
            "Environment loading: `environ.Env.read_env(ENV_PATH or /etc/boxes.env)`. "
            "Business settings stored in PostgreSQL are documented in "
            "`docs/DATABASE_SETTINGS.md`."
        )
        return "\n".join(lines)

    def _render_management(self) -> str:
        lines = [
            "# Management commands (generated)",
            "",
        ]
        cmd_dir = Path(settings.BASE_DIR) / "boxes" / "management" / "commands"
        for path in sorted(cmd_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            mod_name = f"boxes.management.commands.{path.stem}"
            try:
                mod = importlib.import_module(mod_name)
            except Exception as exc:
                lines.append(f"## `manage.py {path.stem}`")
                lines.append("")
                lines.append(f"_Import error: {exc}_")
                lines.append("")
                continue
            cmd_cls = getattr(mod, "Command", None)
            lines.append(f"## `manage.py {path.stem}`")
            lines.append("")
            if cmd_cls:
                help_text = getattr(cmd_cls, "help", "") or self._doc(cmd_cls)
                lines.append(help_text or "_No help text._")
                handle = getattr(cmd_cls, "handle", None)
                if handle and self._doc(handle):
                    lines.append("")
                    lines.append(self._doc(handle))
            lines.append("")
        return "\n".join(lines)

    def _render_javascript(self) -> str:
        root = Path(settings.BASE_DIR) / "boxes" / "static" / "js"
        lines = [
            "# JavaScript (generated)",
            "",
            "Parsed from `boxes/static/js` file headers and `function` declarations.",
            "",
        ]
        func_re = re.compile(r"^function\s+([A-Za-z0-9_]+)\s*\(", re.M)
        for path in sorted(root.rglob("*.js")):
            rel = path.relative_to(root).as_posix()
            src = path.read_text(encoding="utf-8")
            src_lines = src.splitlines()
            lines.append(f"## `{rel}`")
            lines.append("")
            stripped = src.lstrip()
            if stripped.startswith("/**"):
                m = re.match(r"/\*\*(.*?)\*/", stripped, re.S)
                if m:
                    header = []
                    for line in m.group(1).splitlines():
                        cleaned = re.sub(r"^\s*\*\s?", "", line).rstrip()
                        if cleaned:
                            header.append(cleaned)
                    if header:
                        lines.append("; ".join(header))
                        lines.append("")
            for match in func_re.finditer(src):
                fn = match.group(1)
                lineno = src.count("\n", 0, match.start()) + 1
                summary = ""
                i = lineno - 2
                while i >= 0 and src_lines[i].strip() == "":
                    i -= 1
                if i >= 0 and src_lines[i].strip() == "*/":
                    end = i
                    while i >= 0 and not src_lines[i].strip().startswith("/**"):
                        i -= 1
                    if i >= 0 and src_lines[i].strip().startswith("/**"):
                        # Skip the top-of-file @file header (starts at line 0)
                        if i == 0:
                            summary = ""
                        else:
                            block = src_lines[i : end + 1]
                            parts = []
                            for bl in block:
                                bls = bl.strip()
                                if bls.startswith("/**") or bls == "*/":
                                    continue
                                parts.append(re.sub(r"^\*\s?", "", bls).strip())
                            summary = " ".join(p for p in parts if p)
                lines.append(f"- `function {fn}()`" + (f" — {summary}" if summary else ""))
            for wm in re.finditer(r"^window\.([A-Za-z0-9_]+)\s*=\s*function\b", src, re.M):
                lines.append(f"- `window.{wm.group(1)} = function(...)`")
            lines.append("")
        return "\n".join(lines)
