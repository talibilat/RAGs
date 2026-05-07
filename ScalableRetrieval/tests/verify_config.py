def test_qasper_eval_limit_setting():
    from src.config.settings import settings
    assert hasattr(settings, "QASPER_EVAL_LIMIT")
    assert isinstance(settings.QASPER_EVAL_LIMIT, int)
