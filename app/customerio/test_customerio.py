from customerio.client import customerio


def test_identify(customer_identify, user):
    data = user.to_json()
    with customer_identify(user, blop='blop', **data) as call:
        customerio.identify(user, blip='blop')
        assert call.called


def test_event(customer_event, user):
    with customer_event(user, 'event', blip='blop') as call:
        customerio.event(user, 'event', blip='blop')
        assert call.called
