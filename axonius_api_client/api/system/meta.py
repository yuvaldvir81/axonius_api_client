# -*- coding: utf-8 -*-
"""API model for working with system configuration."""
import math

from ..mixins import ChildMixins


class Meta(ChildMixins):
    """Child API model for working with instance metadata."""

    def about(self):
        """Get about page metadata.

        Returns:
            :obj:`dict`: about page metadata
        """
        data = self._about()
        data["Version"] = self._get_version(about=data)
        return data

    def historical_sizes(self):
        """Get disk usage metadata.

        Returns:
            :obj:`dict`: disk usage metadata
        """
        return parse_sizes(self._historical_sizes())

    def _get_version(self, about):
        """Pass."""
        version = about.pop("Version", "") or about.pop("Installed Version", "")
        version = version.replace("_", ".")
        return version

    @property
    def version(self):
        """Get the version of Axonius."""
        about = self.about()
        return about["Version"]

    def _init(self, parent):
        """Post init method for subclasses to use for extra setup.

        Args:
            parent (:obj:`.api.mixins.Model`): parent API model of this child
        """
        super(Meta, self)._init(parent=parent)

    def _about(self):
        """Direct API method to get the About page.

        Returns:
            :obj:`dict`: about page metadata
        """
        path = self.router.meta_about
        return self.request(method="get", path=path)

    def _historical_sizes(self):
        """Direct API method to get the metadata about disk usage.

        Returns:
            :obj:`dict`: disk usage metadata
        """
        path = self.router.meta_historical_sizes
        return self.request(method="get", path=path)


def parse_sizes(raw):
    """Pass."""
    parsed = {}
    parsed["disk_free_mb"] = math.floor(raw["disk_free"] / 1024 / 1024)
    parsed["disk_used_mb"] = math.ceil(raw["disk_used"] / 1024 / 1024)
    parsed["historical_sizes_devices"] = raw["entity_sizes"].get("Devices", {})
    parsed["historical_sizes_users"] = raw["entity_sizes"].get("Users", {})
    return parsed
