import modem


def test_prompt_select_port_valid():
    choices = ['/dev/ttyUSB0', '/dev/ttyUSB1']
    inputs = iter(['2'])
    selected = modem.prompt_select_port(choices, input_fn=lambda _prompt: next(inputs))
    assert selected == '/dev/ttyUSB1'


def test_prompt_select_port_cancel():
    choices = ['/dev/ttyUSB0', '/dev/ttyUSB1']
    inputs = iter([''])
    selected = modem.prompt_select_port(choices, input_fn=lambda _prompt: next(inputs))
    assert selected is None


def test_prompt_select_port_invalid_then_valid():
    choices = ['/dev/ttyUSB0', '/dev/ttyUSB1']
    inputs = iter(['x', '3', '1'])
    selected = modem.prompt_select_port(choices, input_fn=lambda _prompt: next(inputs))
    assert selected == '/dev/ttyUSB0'
