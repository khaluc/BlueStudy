import os
import pytest


@pytest.mark.skipif(os.environ.get('PADAYON_LIVE_E2E') != '1', reason='Opt-in: running Compose + Chrome + paid generation required')
def test_live_browser_flow():
    from scripts.smoke_web import main
    main()
