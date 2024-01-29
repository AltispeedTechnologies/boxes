from django.db import models

PACKAGE_STATES = {
    (0, "Received"),
    (1, "Needs label printed"),
    (2, "Checked in"),
    (3, "Checked out"),
    (4, "Mis-placed"),
}

class Package(models.Model):
    account_id = models.ForeignKey("Account", on_delete=models.CASCADE)
    address_id = models.ForeignKey("Address", on_delete=models.CASCADE)
    tracking_code = models.CharField(max_length=30, unique=True)
    current_state = models.PositiveSmallIntegerField(choices=PACKAGE_STATES, default=0)

    def transition_state(self, new_state):
        # The state transitions should be locked only for regular users
        # TODO: Implement an override for admins, revisit this
        transitions = {
            "submit_for_label_printing": {"from": 0, "to": 1},
            "check_in": {"from": 1, "to": 2},
            "check_out": {"from": 2, "to": 3},
            "misplace": {"from": 2, "to": 4},
        }

        current_state = self.current_state

        if current_state == transitions[new_state]["from"]:
            self.current_state = transitions[new_state]["to"]
            self.save()

    def submit_for_label_printing(self):
        self.transition_state("submit_for_label_printing")

    def check_in(self):
        self.transition_state("check_in")

    def check_out(self):
        self.transition_state("check_out")

    def misplace(self):
        self.transition_state("misplace")


class PackageLedger(models.Model):
    user_id = models.ForeignKey("CustomUser", on_delete=models.RESTRICT)
    package_id = models.ForeignKey(Package, on_delete=models.CASCADE)
    state = models.PositiveSmallIntegerField(choices=PACKAGE_STATES)
    timestamp = models.DateTimeField(auto_now_add=True)
