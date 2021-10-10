from argparse import ArgumentParser, Namespace
from sys import exit
from pathlib import Path


def main():
    args = parse_arguments()
    for directory in args.directories:
        if directory.is_dir():
            print("Working on:" + str(directory))
            clean_directory(directory, args.extensions, args.unw_extensions, args.trash, args.dry_run)
        else:
            print('Unable to find directory: ' + str(directory) + '". Skipping')


def parse_arguments() -> Namespace:
    parser = ArgumentParser(description="Remove unmatched subtitles and info companion files. "
                                        "Files are removed unless they have the same name as a "
                                        "video file that exists in the directory DIR. removed extensions: "
                                        ".srt, .ass, .ssa, .sub, .idx, .vtt, .info, .nfo, .pgs")

    parser.add_argument("directories", metavar="DIR", type=Path, nargs="*", default=list(),
                        help="Path to directory where to remove unmatched companion files. "
                             "Default is current working directory", )

    parser.add_argument("--library", "-l", action="append", metavar="LIB", type=Path, dest="library", default=list(),
                        help="Path to library of directories to run script over.")

    parser.add_argument("--exclusive", "-e", action="append", metavar="EXC", nargs='*', type=str, dest="extensions", default=list(),
                        help="Default behaviour is to keep all matching companion files. If you wish to keep one or "
                             "multiple specific companion files then specify one or more EXC to keep. "
                             "example: -e .en.srt .nfo to keep english subtitle and nfo file for the video file")

    parser.add_argument("--trash", "-t", metavar="TRASH", type=Path, dest="trash", default=None,
                        help="Path to trash. Deleted files ends up in TRASH instead of being deleted. "
                             "If the trash path is relative it will be in relative to DIR. ")

    parser.add_argument("--unwanted-extension", action="append", metavar="U_EXT", type=str, dest="unw_extensions", default=list(),
                        help="!DANGEROUS OPTION!: Additional extensions to remove unless they are companion files "
                             "to a video file.")

    parser.add_argument("--dry-run", "-n", action="store_true", dest="dry_run",
                        help="Dry-run flag, Run program without altering any files or directories.")

    args: Namespace = parser.parse_args()

    # cleaning usage:

    directories: list = args.directories
    libraries: list = args.library
    extensions: list = args.extensions
    unw_extensions: list = args.unw_extensions
    trash: Path = args.trash

    final_ext = list()
    for lis in extensions:
        for ext in lis:
            final_ext.append(ext)
    extensions = final_ext

    for i in range(len(libraries)):
        if not Path.is_absolute(libraries[i]):
            libraries[i] = Path(Path.cwd(), libraries[i])

        if not libraries[i].is_dir():
            print('Library LIB is not a path to a directory. Skipping.')
            continue

        for directory in libraries[i].iterdir():
            if directory.is_dir:
                directories.append(Path(libraries[i], directory))

    for i in range(len(directories)):
        directory = directories[i]
        if not Path.is_absolute(directory):
            directories[i] = Path(Path.cwd(), directory)

    if len(directories) == 0:
        directories.append(Path.cwd)

    for i in range(len(extensions)):
        if extensions[i][:1] != ".":
            extensions[i] = "." + extensions[i]

    for i in range(len(unw_extensions)):
        if unw_extensions[i][:1] != ".":
            unw_extensions[i] = "." + unw_extensions[i]

    if trash is not None and trash.is_absolute() and not trash.is_dir():
        try:
            trash.mkdir(exist_ok=True)
        except FileExistsError:
            print("Unable to create trash directory, Exiting - File exists: \"" + str(trash) + "\"")
            exit()
        except FileNotFoundError:
            print("Unable to create trash directory, Exiting - Directory doesn't exist: \"" + str(trash.parent) + "\"")
            exit()

    args.directories = directories
    args.extensions = extensions
    args.unw_extensions = unw_extensions
    args.trash = trash

    return args


def clean_directory(directory, allowed_companions, unw_extensions, trash, dry_run):
    cleaning_exts = [".srt", ".ass", ".ssa", ".sub", ".idx", ".vtt", ".info", ".nfo", ".pgs"] + unw_extensions
    video_exts = [".mkv", ".mp4", ".avi", ".wmv"]

    video_files = list()
    for file in directory.iterdir():
        file: Path
        for ext in video_exts:
            if file.name[-len(ext):] == ext:
                video_files.append(file.name[:-len(ext)])

    if len(video_files) == 0:
        print("\tNo video file found, skipping directory.")
        return

    if len(allowed_companions) == 0:
        allowed_companions = cleaning_exts.copy()

    for file in directory.iterdir():
        delete = False
        file: Path
        file_name = file.name
        if any(file.name[-len(ext):] == ext for ext in cleaning_exts):
            delete = True
            for video_file in video_files:
                video_file: str
                if file_name[:len(video_file) + 1] == video_file + ".":
                    if any(file.name[-len(ext):] == ext for ext in allowed_companions):
                        delete = False
                        break
        if delete:
            if not dry_run:
                delete_file(file, trash)
            else:
                print("\tMoved/Removed file (dry-run): \"" + file.name + "\"")

    return


def delete_file(file: Path, trash: Path):
    if trash is None:
        file.unlink(missing_ok=True)
        print("\tRemoved file: \"" + file.name + "\"")
        return

    if not trash.is_absolute():
        target_trash = Path(file.parent, trash)
        "\tLocal trash: \"" + str(trash) + "\""
        try:
            target_trash.mkdir(exist_ok=True)
        except FileExistsError:
            print("\tUnable to create trash directory, skipping - File exists: \"" + str(trash) + "\"")
            return
        except FileNotFoundError:
            print("\tUnable to create trash directory, skipping - Directory doesn't exist: \"" + str(trash.parent) + "\"")
            return
    else:
        target_trash = trash

    trash_file = Path(target_trash, file.name)
    moved = False
    copies = 0
    while not moved:
        try:
            file.rename(trash_file)
            moved = True
            print("\tMoved file to trash: \"" + file.name + "\"")
        except FileExistsError:
            copies += 1
            trash_file = Path(trash, file.name + "_copy" + str(copies))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting - Interrupted")
        exit()
