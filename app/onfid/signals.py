from onfid.const import CHECK_COMPLETE
from onfid.models import Check
from signals import connect


@connect(Check.on_update)
def update_user_property_on_complete(check: Check, **_):
    if check.status != CHECK_COMPLETE:
        return

    check.user.modify(onfid_status=check.result)
