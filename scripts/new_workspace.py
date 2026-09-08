"""Create an independent clean template copy; never merge or overwrite a destination."""
import argparse
import json
import shutil
from pathlib import Path


def create(destination, name, profile):
    root = Path(__file__).resolve().parents[1]
    destination = Path(destination).resolve()
    if destination.exists() or destination == root or root in destination.parents:
        raise ValueError('Choose a new destination outside this template directory.')
    if profile not in ('research', 'operations', 'monitoring'):
        raise ValueError('Unknown domain profile.')
    if not name.strip() or len(name) > 120:
        raise ValueError('Name must contain 1–120 characters.')
    excluded = {'.git', '.agentos', '__pycache__', 'node_modules', '.DS_Store', 'test-results', 'private'}
    def ignore(directory, names):
        return [n for n in names if n in excluded or n.startswith('.env') or n.endswith(('.sqlite3', '.pyc'))
                or Path(directory, n).is_symlink()]
    shutil.copytree(root, destination, ignore=ignore)
    data = json.loads((root / 'examples' / (profile+'.json')).read_text())
    data['name'] = name.strip()
    (destination / 'workspace-profile.json').write_text(json.dumps(data, indent=2)+'\n')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination')
    parser.add_argument('--name', required=True)
    parser.add_argument('--profile', choices=('research', 'operations', 'monitoring'), default='operations')
    args = parser.parse_args()
    try:
        target = create(args.destination, args.name, args.profile)
    except ValueError as exc:
        parser.error(str(exc))
    print(f'Created {target}. Read AGENTS.md there, then run the reference or build your chosen domain.')
