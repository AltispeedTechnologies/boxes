from django.db import models

PACKAGE_STATES = {
    (0, "Received"),
    (1, "Checked in"),
    (2, "Checked out"),
    (3, "Mis-placed"),
}

class PackageType(models.Model):
    shortcode = models.CharField(max_length=1)
    description = models.CharField(max_length=64)


class Package(models.Model):
    account = models.ForeignKey("Account", on_delete=models.RESTRICT)
    carrier = models.ForeignKey("Carrier", on_delete=models.RESTRICT)
    package_type = models.ForeignKey(PackageType, on_delete=models.RESTRICT)
    tracking_code = models.CharField(max_length=30, unique=True)
    current_state = models.PositiveSmallIntegerField(choices=PACKAGE_STATES, default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def transition_state(self, new_state):
        # The state transitions should be locked only for regular users
        # TODO: Implement an override for admins, revisit this
        transitions = {
            "check_in": {"from": 0, "to": 1},
            "check_out": {"from": 1, "to": 2},
            "misplace": {"from": None, "to": 3},
        }

        if new_state in transitions and (
            transitions[new_state]["from"] is None or
            self.current_state == transitions[new_state]["from"]
        ):
            self.current_state = transitions[new_state]["to"]
            self.save()

    def check_in(self):
        self.transition_state("check_in")

    def check_out(self):
        self.transition_state("check_out")

    def misplace(self):
        self.transition_state("misplace")


class PackageLedger(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.RESTRICT)
    package_id = models.ForeignKey(Package, on_delete=models.RESTRICT)
    state = models.PositiveSmallIntegerField(choices=PACKAGE_STATES)
    timestamp = models.DateTimeField(auto_now_add=True)
