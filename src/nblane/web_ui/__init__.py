"""nblane SPA frontend package.

Holds the React SPA source (``frontend/``) and its committed Vite build
output (``static/``). ``static/`` is declared as package data and served by
``nblane.web_api.spa.mount_spa`` via a ``__file__``-relative path, so it
works identically from an editable checkout and an installed wheel.
"""
