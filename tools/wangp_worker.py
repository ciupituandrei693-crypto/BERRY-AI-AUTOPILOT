"""Run WanGP's own Python API with a user-exported settings file; no model downloads by BERRY."""
import json
import sys
from pathlib import Path


def main() -> None:
    root, settings_file, output, prompt = sys.argv[1:5]
    root, output = Path(root).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if not (root / 'shared' / 'api.py').is_file():
        raise RuntimeError('WanGP API shared/api.py nu a fost găsit')
    settings = json.loads(Path(settings_file).read_text(encoding='utf-8'))
    if not isinstance(settings, dict) or not settings.get('model_type'):
        raise ValueError('Export Settings WanGP trebuie să includă model_type')
    settings['prompt'] = prompt
    # Use WanGP's documented API, not its internal web UI endpoints.
    sys.path.insert(0, str(root))
    from shared.api import init
    session = init(root=root, output_dir=output, console_output=False)
    result = session.submit_task(settings).result()
    print(json.dumps({'success': bool(result.success), 'generated_count': len(result.generated_files or [])}))


if __name__ == '__main__':
    main()
