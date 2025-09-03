def test_makerschool_registrations_real_api(wa_context):
    import reports  # noqa: WPS433

    events, total_registrations, total_registration_limit = (
        reports.get_makerschool_registrations()
    )

    # Print the number of registrations found (sum over events)
    print(f"Makerschool registrations found: {total_registrations}")

    # Basic assertions for success
    assert isinstance(events, dict)
    assert isinstance(total_registrations, int)
    assert isinstance(total_registration_limit, int)
