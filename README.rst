!!! Important !!!
-----------------

This is a snapshot of our post-whitelist state of the service that handled whitelist. Tests are partially outdated
(as well as some bits of documentation).

Code here is FYI only. It is not in use any more and all data related to the whitelist is now wiped from S3 and our
servers.

The flow
--------

1. Obtain device fingerprint from Augur
2. Submit KYC data ``POST /v1/user {....}`` -> ``{"state": "<you need this>", "token": "<and this>", ....}``
3. Call ``GET /v1/user`` to check user's state. You're waiting for ``state: "info_approved"``
4. Get link for image1: ``POST /v1/upload {"filename": "...", "content_type": "...", "size": ...}`` -> ``{"put_url": "...", "id": "..."}``
5. Repeat for second image
6. Upload images to S3
7. Create ID package: ``POST /v1/ids {"upload1": "<id from upload route>", ...}`` -> ``{"id": "...", ...}``
8. Submit package to verification: ``POST /v1/ids/<id from ids route>/verify {}`` -> get user status
9. That's it. From now on it's only checking user's status

Heaviest routes for us are ``/v1/ids`` and ``/v1/ids/<id>/verify`` as they pull data from s3 and submit it to IDM

Example response for user data::

    {
      "address": {
        "address_components": [
          {
            "long_name": "Ashford Dunwoody Road Northeast",
            "short_name": "Ashford Dunwoody Rd NE",
            "types": [
              "route"
            ]
          },
          {
            "long_name": "Dunwoody",
            "short_name": "Dunwoody",
            "types": [
              "locality",
              "political"
            ]
          },
          {
            "long_name": "DeKalb County",
            "short_name": "Dekalb County",
            "types": [
              "administrative_area_level_2",
              "political"
            ]
          },
          {
            "long_name": "Georgia",
            "short_name": "GA",
            "types": [
              "administrative_area_level_1",
              "political"
            ]
          },
          {
            "long_name": "United States",
            "short_name": "US",
            "types": [
              "country",
              "political"
            ]
          }
        ],
        "description": "Ashford Dunwoody Road Northeast, Dunwoody, GA, United States",
        "formatted_address": "Ashford Dunwoody Rd NE, Dunwoody, GA, USA",
        "latitude": 33.9302397,
        "longitude": -84.3373449,
        "name": "Ashford Dunwoody Road Northeast",
        "place_id": "EilBc2hmb3JkIER1bndvb2R5IFJkIE5FLCBEdW53b29keSwgR0EsIFVTQQ",
        "scope": "GOOGLE",
        "types": [
          "route"
        ],
        "utc_offset": -300
      },
      "country_code": "AW",
      "dob": 1451862000,
      "email": "asdfasdf@example.com",
      "eth_address": "1212121212121212121212121212121212121212",
      "eth_amount": 123.4,
      "eth_cap": null,
      "id": "5a74cd021ba9f80001ecfc7e",
      "name": "asfdsadf qwdfas",
      "phone": "12345678",
      "state": "info_verified",
      "token": "WyI1YTc0Y2QwMjFiYTlmODAwMDFlY2ZjN2UiXQ.fXvNabow5av7twL4THqQbX0eCps"
    }

``POST /v1/user`` schema::

    schema = Schema({
        'name': All(Length(5, 30), str),
        'email': Email(),
        'dob': Coerce(to_datetime),  # unix timestamp
        'address': Coerce(to_addr),
        'country_code': All(Length(2, 3), str),
        'phone': All(Length(8, 20), str),
        'eth_address': Coerce(to_eth),  # ^(0x)?[0-9a-fA-F]{40}$
        'eth_amount': All(Range(0, 100), float),
        'telegram': Coerce(to_telegram),  # ^@?(?P<name>[0-9a-z_]{5,25})$
        'confirmed_location': bool,  # Should be True
        'dfp': All(Length(10, 300), str),
    }, extra=REMOVE_EXTRA, required=True)


``POST /v1/upload`` schema::

    schema = Schema({
        'filename': All(Length(3, 30), str),
        'content_type': All(Length(5, 20), str),   # gif or jpeg
        'size': Range(400 * 1024, 4 * 1024 * 1024),  # 400KB..4MB
    }, extra=REMOVE_EXTRA, required=True)

``POST /v1/ids`` schema::

    schema = Schema({
        'upload1': Coerce(ObjectId),
        'upload2': Coerce(ObjectId),
        'doc_type': In(DOC_TYPES),   # DL, PP, ID, RP, UB
        'doc_country': All(Length(2, 2), str),
        Optional('doc_state', default=None): Any(None, All(Length(2, 20), str)),
    }, extra=REMOVE_EXTRA, required=True)

