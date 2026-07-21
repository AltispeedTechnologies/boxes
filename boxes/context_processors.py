"""Django template context processors for Boxes."""


def mgmt_setup_status(request):
    """Inject management setup status for staff navbar warning icons.

    Anonymous and non-staff users get an empty payload (no DB work beyond
    auth checks already done for the request).
    """
    empty = {
        "mgmt_setup": {
            "items": {},
            "order": [],
            "required_incomplete": False,
            "any_incomplete": False,
            "required_issues": [],
            "all_issues": [],
        }
    }
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return empty
    # has_staff_role may hit DB; only staff see Management menu
    try:
        if not user.has_staff_role():
            return empty
    except Exception:
        return empty

    from boxes.backend.setup_status import setup_status_for_template

    return {"mgmt_setup": setup_status_for_template()}
