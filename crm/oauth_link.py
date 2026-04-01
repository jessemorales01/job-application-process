"""Signed OAuth state for linking Gmail without cache/session (CSRF + user binding)."""

OAUTH_LINK_SALT = 'crm.email.oauth.v1'
OAUTH_LINK_MAX_AGE = 600  # seconds; match initiate UX expectations
