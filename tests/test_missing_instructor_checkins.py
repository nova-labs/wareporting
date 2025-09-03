from datetime import datetime, timedelta


def test_missing_instructor_checkins_real_api(wa_context):
    import reports  # noqa: WPS433

    # Try progressively narrower windows to avoid exceeding event limit
    for days in (7, 3, 1):
        start_date = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        result = reports.get_missing_instructor_checkins(start_date)
        if isinstance(result, str) and result.startswith("Too many events found"):
            continue
        flawed_events, _ = result
        break
    else:
        # Last attempt still too many
        raise AssertionError("Query window still returned too many events; adjust test window.")

    # Print the number of missing instructor checkins found
    print(f"Missing instructor checkins found: {len(flawed_events)}")

    # Basic success assertion: function returned a list
    assert isinstance(flawed_events, list)
