"""Storage backends used for overwrite-friendly uploads."""
from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):
    """FileSystemStorage that replaces existing files with the same name."""
    def get_available_name(self, name, max_length=None):
        """Return the name after deleting any existing file at that path."""
        if self.exists(name):
            self.delete(name)
        return name
