# User states
# ---------------------------
NEW_USER = 'new_user'  #: User didn't perform any action. He's not in our DB yet.
INFO_NOT_VERIFIED = 'info_not_verified'  #: Basic info provided, not yet verified by IDM
INFO_PENDING_VERIFICATION = 'info_pending_verification'  #: Info provided, submitted to IDM, waiting for response
INFO_VERIFIED = 'info_verified'  #: Basic info was verified by IDM
INFO_DECLINED = 'info_declined'  #: Basic info was declined by IDM
INFO_FAILED = 'info_failed'  #: Failed to make a request to the IDM

ID_NOT_VERIFIED = 'id_not_verified'  #: ID pic provided but not submitted to IDM yet
ID_PENDING_VERIFICATION = 'id_pending_verification'  #: ID submitted to IDM, waiting for verification
ID_VERIFIED = 'id_verified'  #: IDM verified ID
ID_DECLINED = 'id_declined'  #: IDM declined ID pic
ID_FAILED = 'id_failed'  #: Failed to make id verification request to the IDM

CONTRIBUTED = 'contributed'  #: User successfully contributed to our ICO. Transaction has landed in the blockchain
APPROVED_NO_CAP = 'approved_no_cap'  #: Admin approved user, no cap set yet
APPROVED_CAP = 'approved_cap'  #: Admin approved and set personal token cap
DECLINED = 'declined'  #: Admin declined the user

STATE_FLOW = [
    NEW_USER,
    INFO_NOT_VERIFIED,
    INFO_PENDING_VERIFICATION,
    INFO_VERIFIED,
    ID_NOT_VERIFIED,
    ID_PENDING_VERIFICATION,
    ID_VERIFIED,
    APPROVED_NO_CAP,
    APPROVED_CAP,
    CONTRIBUTED,
]

FINAL_STATES = [
    DECLINED,
    ID_DECLINED,
    ID_FAILED,
    INFO_DECLINED,
    INFO_FAILED,
]

ALL_STATES = STATE_FLOW + FINAL_STATES
# ---------------------------

BANNED_COUNTRIES = ['CN', 'US', 'TW', 'HK']

# Decline reasons
DECLINE_COUNTRY = 'decline_country'  #: Provided country is blacklisted
DECLINE_IDM_INFO = 'decline_idm_info'  #: Declined by the IDM for basic info
DECLINE_IDM_ID = 'decline_idm_id'  #: Declined by the IDM for ID pic
DECLINE_ADMIN = 'decline_admin'  #: Admin declined

ALL_DECLINE_REASONS = [
    DECLINE_COUNTRY,
    DECLINE_IDM_INFO,
    DECLINE_IDM_ID,
    DECLINE_ADMIN,
]
