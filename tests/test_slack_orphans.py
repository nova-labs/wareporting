import os
import pandas as pd

def test_slack_orphans_count_real_api(wa_context):
    import reports  # noqa: WPS433 (import after fixture ensures path/context)
    import wadata  # noqa: WPS433 (import after fixture ensures path/context)

    # Load the provided dummy Slack export
    csv_path = os.path.join(os.path.dirname(__file__), "dummy_slack_users.csv")
    df = pd.read_csv(csv_path)

    orphans, num_valid_emails = reports.get_slack_orphans(df)

    # Expect 3 orphans based on test data and WA contacts
    assert len(orphans) == 3

    # Confirm we paginated: valid emails should exceed one page
    assert num_valid_emails > wadata.PAGE_SIZE

    # Print the number of Slack orphans found
    print(f"Slack orphans found: {len(orphans)}; valid emails: {num_valid_emails}")
