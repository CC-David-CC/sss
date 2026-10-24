"""Inspected external-client identities, separate from the CPU mock fixture set."""
NPM_PINS = {
    'codex': ('@openai/codex', '0.164.0'),
    'opencode': ('@opencode/cli', '2.1.4'),
    'pi': ('@earendil-works/pi-coding-agent', '1.4.0'),
    'qwen': ('@qwen-code/qwen-code', '0.26.0'),
    'dsh': ('@deepseek-ai/dsh', '0.2.1-rc.2'),
}
HERMES_REVISION = '5894e750c3dba980d43b25aa29e3958149ba2c61'
CLIENTS = (*NPM_PINS, 'hermes')
