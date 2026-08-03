from agent.tools.middleware import select_system_prompt


def test_report_prompt_is_selected_for_report_context():
    prompt = select_system_prompt(True)

    assert "DriveMind" in prompt
    assert "开环" in prompt
    assert "免责声明" in prompt


def test_main_prompt_is_selected_for_normal_context():
    prompt = select_system_prompt(False)

    assert "DriveMind" in prompt
    assert "评测" in prompt
