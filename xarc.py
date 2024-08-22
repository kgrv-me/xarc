from argparse import ArgumentParser
from datetime import datetime
from getpass import getuser
from json import dumps, loads
from os import listdir
from pathlib import Path
from platform import system
from random import choice
from urllib import request

PACKAGE: str = 'xarc'
VERSION: str = '0.1.0'
REPOSITORY: str = f"https://github.com/kgrv-me/{PACKAGE}"
DESCRIPTION: str = 'A simple script to extract sidebar and archived items from Arc.'

ARGS = None
SYSTEM: str = system()

KEYWORD: str = '](http'
TIMESTAMP: str = '%Y-%m-%d %H:%M:%S'

COLORS: dict = {
    'blue': '\033[0;34m',
    'gray': '\033[2;37m',
    'green': '\033[0;32m',
    'purple': '\033[0;35m',
    'red': '\033[0;31m',
    'yellow': '\033[0;33m',
    'nc': '\033[0m',
}
MESSAGES: list[str] = [
    '[BEEP] was here',
    '4C 4F 56 45 20 55',
    'Aww yiss',
    'Bee Leaf in You',
    'Creating wormhole',
    'Delicious pizza awaits',
    'Have a yummy bite',
    'Hue hue hue',
    'I was never here',
    "I'm not as think as you drunk I am",
    'Oh no',
    'Something smells heavenly',
    'Stop! Have a wonderful day',
    'Wish you the very best of day',
    'You have earned a rest',
    "You're doing great",
]

def debug(string: str) -> None:
    if ARGS.debug: # type: ignore
        print(f"  {gray('DEBUG')} {string}")

def trace(string: str) -> None:
    if ARGS.trace: # type: ignore
        print(f"  {purple('TRACE')} {string}")

def info(string: str) -> None:
    print(f"  {blue('INFO')}  {string}")

def warn(string: str) -> None:
    print(yellow(f"  WARN  {string}"))

def error(string: str) -> None:
    print(red(f"  ERROR {string}"))

def blue(string: str) -> str:
    return f"{COLORS['blue']}{string}{COLORS['nc']}"

def gray(string: str) -> str:
    return f"{COLORS['gray']}{string}{COLORS['nc']}"

def green(string: str) -> str:
    return f"{COLORS['green']}{string}{COLORS['nc']}"

def purple(string: str) -> str:
    return f"{COLORS['purple']}{string}{COLORS['nc']}"

def red(string: str) -> str:
    return f"{COLORS['red']}{string}{COLORS['nc']}"

def yellow(string: str) -> str:
    return f"{COLORS['yellow']}{string}{COLORS['nc']}"

def version_check() -> None:
    if ARGS.no_version_check and not ARGS.version_check: # type: ignore
        return None

    url: str = f"{REPOSITORY.replace('github.com', 'api.github.com/repos')}/releases/latest"
    debug(url)
    api: str = loads(request.urlopen(url).read())
    tag_name: str = api['tag_name'] # type: ignore
    debug(f"tag_name {tag_name}")
    latest: list[str] = tag_name.strip('v').split('-')
    debug(f"latest {latest}")
    current: list[str] = VERSION.split('-')
    debug(f"current {current}")

    if (latest[0] > current[0]
        or latest[0] == current[0]
        and len(latest) < len(current)
        or len(latest) == len(current)
        and len(latest) == 2
        and latest[1] > current[1]):
        warn(f"Outdated! {green(latest[0])} available at {blue(f'{REPOSITORY}/releases/tag/{tag_name}')}")
    else:
        info(f"{green('Up-to-date!')}")

def generate_markdown(md: dict) -> None:
    now: str = datetime.now().strftime(TIMESTAMP)
    ts: str = '' if ARGS.no_timestamp else f"_{now.replace(':', '-').replace(' ', '_')}" # type: ignore
    path: str = f"{ARGS.output.rstrip('.md')}{ts}.md" # type: ignore
    info(f"Generating {blue(path)}")
    debug(f"Timestamp {green(now)}")

    content: str = '\n\n'.join((
        f"Timestamp **{now}**",
        f"Generated via **{PACKAGE}** `{VERSION}`",
        f"Repository [{REPOSITORY}]({REPOSITORY})",
        ''
    ))
    for cat in sorted(md, reverse=True):
        content += md[cat]

    cnt_none: int = content.count('None')
    if cnt_none:
        warn(f"Found {cnt_none} None instances")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_archived(json: dict) -> str:
    md: dict = {}
    for item in json['items']:
        if not isinstance(item, dict):
            continue

        debug(f"{blue('ID[AR]:')} {item['sidebarItem']['id']}")
        try:
            title: str | None = item['sidebarItem']['data']['tab']['savedTitle']
        except:
            title = None

        reason: str = item['reason']
        if reason not in md:
            md[reason] = []
        elem: str = f"- [{title}]({item['sidebarItem']['data']['tab']['savedURL']})"
        trace(elem)
        md[reason].append(elem)

    markdown: str = '\n# Archived'
    for reason in sorted(md):
        md_joined: str = '\n'.join(md[reason])
        info(f"Found {green(str(md_joined.count(KEYWORD)))} URLs as {blue(reason)}")
        markdown += f"\n## {reason.capitalize()}\n{md_joined}\n"
    return markdown

def sidebar_to_markdown(id: str, lookup: dict, indent: int) -> str:
    debug(f"{blue('ID[SB]:')} {id}")
    item: dict = lookup[id]
    heading: str = '> #### ' if item['childrenIds'] else ''

    if 'data' in item and 'tab' in item['data']:
        title: str = f"[{item['data']['tab']['savedTitle']}]({item['data']['tab']['savedURL']})"
    else:
        title = item['title']

    md: str = ''
    for child in item['childrenIds']:
        md += sidebar_to_markdown(child, lookup, indent + 2)
    if title or md and not md.startswith(f"{' ' * indent}-") and not md.startswith('#'):
        title = f"{' ' * indent}- {heading}{title}"
        trace(title)
        md = f"{title}\n{md}"
    return md

def create_spaces(json: dict) -> dict:
    spaces: dict = {}
    for space in json:
        if not isinstance(space, dict):
            continue
        data: dict = {
            'title': space['title'],
            'id': space['id'],
            'containers': {
                space['containerIDs'][0]: space['containerIDs'][1],
                space['containerIDs'][2]: space['containerIDs'][3]
            }
        }
        trace(dumps(data, indent=4))
        spaces[space['title']] = data
    info(f"Found {green(str(len(spaces)))} spaces")
    return spaces

def create_lookup(json: dict) -> dict:
    lookup: dict = {}
    for item in json:
        if isinstance(item, dict):
            lookup[item['id']] = item
    return lookup

def extract_sidebar(json: dict) -> str:
    for item in json['sidebar']['containers']:
        if not isinstance(item, dict) or 'spaces' not in item or 'items' not in item:
            continue

        spaces: dict = create_spaces(item['spaces'])
        lookup: dict = create_lookup(item['items'])

        md: str = '\n# Sidebar\n'
        for space in spaces:
            md += f"## {space}\n"
            space = spaces[space]
            for cat in sorted(space['containers']):
                md += f"### {cat.capitalize()}\n"
                md += sidebar_to_markdown(space['containers'][cat], lookup, -2)
            md += '\n'
    info(f"Found {green(str(md.count(KEYWORD)))} URLs")
    return md

def base_path() -> Path:
    home: Path = Path.home()
    debug(SYSTEM)
    debug(str(home))
    match SYSTEM:
        case 'Darwin':
            path: Path = Path(home, 'Library', 'Application Support', 'Arc')
        case 'Windows' | 'Linux':
            if SYSTEM == 'Linux':
                warn("Linux platform isn't supported. Assuming Windows Subsystem for Linux.")
                home = Path('/', 'mnt', 'c', 'Users', getuser())
                debug(str(home))
            path = Path(home, 'AppData', 'Local', 'Packages')
            arc: list[str] = [elem for elem in listdir(path) if elem.startswith('TheBrowserCompany.Arc')]
            debug(str(arc))
            path = Path(path, arc[0], 'LocalCache', 'Local', 'Arc')
    debug(str(path))
    return path

def parse_args() -> None:
    parser: ArgumentParser = ArgumentParser(
        prog=PACKAGE,
        description=DESCRIPTION,
        epilog=f"Repository {blue(REPOSITORY)}",
    )
    parser.add_argument('-o', '--output', default=f"{PACKAGE}.md", help='set output file')
    parser.add_argument('-d', '--debug', action='store_true', help='enable debug mode')
    parser.add_argument('-t', '--trace', action='store_true', help='enable trace mode')
    parser.add_argument('-nc', '--no-colors', action='store_true', help='disable ASCII colors')
    parser.add_argument('-nt', '--no-timestamp', action='store_true', help='disable filename timestamp')
    parser.add_argument('-nv', '--no-version-check', action='store_true', help='disable version check')
    parser.add_argument('-vc', '--version-check', action='store_true', help='run version check')
    args = parser.parse_args()

    if args.trace:
        args.debug = True
    if args.no_colors or SYSTEM == 'Windows':
        global COLORS
        for color in COLORS:
            COLORS[color] = ''
    global ARGS
    ARGS = args
    debug(str(args))

def run() -> None:
    parse_args()
    print(f"{PACKAGE} {green(VERSION)}")

    if ARGS.version_check: # type: ignore
        version_check()
        return None

    markdown: dict = {}
    base: Path = base_path()
    for arc_json in ['StorableSidebar.json', 'StorableArchiveItems.json']:
        path: Path = Path(arc_json)
        if not Path(arc_json).is_file():
            debug(f"{yellow(str(path))} not found, switching to system path")
            path = Path(base, arc_json)

        if not path.is_file():
            raise FileNotFoundError(f"Invalid file {red(str(path))}")

        info(f"Processing {blue(str(path))}")
        with open(path, encoding='utf-8') as f:
            json: dict = loads(f.read()) # Read in-memory first to mitigate error with Arc opened

        match arc_json:
            case 'StorableSidebar.json':
                cat: str = 'sidebar'
                md: str = extract_sidebar(json)
            case 'StorableArchiveItems.json':
                cat = 'archived'
                md = extract_archived(json)
        markdown[cat] = md
    generate_markdown(markdown)
    version_check()
    print(f"  {green('DONE')}  {choice(MESSAGES)}, {gray('bye!')}")

if __name__ == '__main__':
    try:
        run()
    except Exception as err:
        error(red(str(err)))
    except (EOFError, KeyboardInterrupt):
        error(f"Interrupted, {gray('bye')}!")
