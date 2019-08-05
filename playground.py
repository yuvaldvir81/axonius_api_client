#!/usr/bin/env python -i
# -*- coding: utf-8 -*-
"""Utilities for this package."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json

# import click

import axonius_api_client as axonapi


def jdump(obj):
    """JSON dump utility."""
    print(json.dumps(obj, indent=2))


if __name__ == "__main__":
    try:
        ctx = axonapi.cli.main(standalone_mode=False)
    except SystemExit:
        print("system exit")
    # else:
    # if isinstance(ctx, click.core.Context):